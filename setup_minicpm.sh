#!/bin/bash
# MiniCPM-o 2.6 All-in-One Setup Script
# This script sets up the full environment, clones code, installing dependencies, and downloads the model.

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  MiniCPM-o 2.6 Full Setup${NC}"
echo -e "${GREEN}========================================${NC}"

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="${SCRIPT_DIR}/mock_server/minicpm_o"
MODEL_REPO="openbmb/MiniCPM-o-2_6"
CONDA_ENV="chat_agent"

# ------------------------------------------------------------------
# Step 0: Proxy
# ------------------------------------------------------------------
if command -v startProxy &> /dev/null; then
    echo -e "\n${YELLOW}[Step 0/6] Enabling proxy...${NC}"
    startProxy
    echo "  Proxy enabled ✓"
elif [ -n "$http_proxy" ] || [ -n "$HTTP_PROXY" ]; then
    echo -e "\n${YELLOW}[Step 0/6] Proxy already configured${NC}"
    echo "  HTTP_PROXY: ${http_proxy:-$HTTP_PROXY}"
else
    echo -e "\n${YELLOW}[Step 0/6] No proxy configured${NC}"
    echo -e "  ${RED}Warning: Download may fail without proxy in some regions.${NC}"
fi

# ------------------------------------------------------------------
# Step 1: Checks
# ------------------------------------------------------------------
echo -e "\n${YELLOW}[Step 1/6] Checking prerequisites...${NC}"

if ! command -v conda &> /dev/null; then
    echo -e "${RED}Error: conda is not installed${NC}"
    exit 1
fi
echo "  Conda: ✓"

if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: git is not installed${NC}"
    exit 1
fi
echo "  Git: ✓"

# Check Memory
if [[ "$OSTYPE" == "darwin"* ]]; then
    TOTAL_MEM=$(sysctl -n hw.memsize)
    TOTAL_MEM_GB=$((TOTAL_MEM / 1024 / 1024 / 1024))
    echo "  Total Memory: ${TOTAL_MEM_GB}GB"
    if [ "$TOTAL_MEM_GB" -lt 16 ]; then
        echo -e "${RED}Warning: Recommend 16GB+ RAM. You have ${TOTAL_MEM_GB}GB.${NC}"
    fi
fi

# ------------------------------------------------------------------
# Step 2: Code Setup (Clone if missing)
# ------------------------------------------------------------------
echo -e "\n${YELLOW}[Step 2/6] Setting up Codebase...${NC}"

if [ -d "$WORK_DIR" ] && [ -d "$WORK_DIR/.git" ]; then
    echo "  Repository already exists at $WORK_DIR"
    echo "  Pulling latest changes..."
    cd "$WORK_DIR"
    git pull
    cd "$SCRIPT_DIR"
elif [ -d "$WORK_DIR" ]; then
    echo "  Directory exists but not a git repo: $WORK_DIR"
    echo "  Skipping clone (assuming code is present)."
else
    echo "  Cloning MiniCPM-V to workspace..."
    mkdir -p "$(dirname "$WORK_DIR")"
    git clone https://github.com/OpenBMB/MiniCPM-V.git "$WORK_DIR"
fi

# Ensure assets dir exists
mkdir -p "${WORK_DIR}/assets/ref_audios"
echo "  Codebase setup ✓"

# ------------------------------------------------------------------
# Step 3: Environment Setup
# ------------------------------------------------------------------
echo -e "\n${YELLOW}[Step 3/6] Setting up Conda Environment...${NC}"

# Check if env exists and has correct python version
NEED_RECREATE=0
if conda env list | grep -q "$CONDA_ENV"; then
    # Env exists, check python version (we need 3.10)
    CURRENT_PY=$(conda list -n "$CONDA_ENV" "^python$" | grep "^python" | awk '{print $2}' | cut -d. -f1,2)
    echo "  Found existing environment: $CONDA_ENV (Python $CURRENT_PY)"
    
    if [ "$CURRENT_PY" == "3.10" ]; then
        echo "  Python version matches. Skipping recreation."
    else
        echo "  Python version mismatch (need 3.10). Recreating..."
        conda remove -n "$CONDA_ENV" --all -y
        NEED_RECREATE=1
    fi
else
    echo "  Environment not found. Creating..."
    NEED_RECREATE=1
fi

if [ "$NEED_RECREATE" -eq 1 ]; then
    echo "  Creating new environment: $CONDA_ENV with Python 3.10..."
    conda create -n "$CONDA_ENV" python=3.10 -y
fi

# Get absolute path to python in the environment
# Parse 'conda env list' to find the path (handles active '*' marker too)
ENV_PATH=$(conda env list | grep -w "$CONDA_ENV" | awk '{print $NF}')

if [ -z "$ENV_PATH" ]; then
    echo -e "${RED}Error: Could not find path for environment $CONDA_ENV${NC}"
    exit 1
fi

PYTHON_EXEC="${ENV_PATH}/bin/python"
echo "  Environment Path: $ENV_PATH"
echo "  Python executable: $PYTHON_EXEC"

# ------------------------------------------------------------------
# Step 4: Install Dependencies
# ------------------------------------------------------------------
echo -e "\n${YELLOW}[Step 4/6] Installing Dependencies...${NC}"

# Helper function to check if package is installed
check_package() {
    "$PYTHON_EXEC" -m pip show "$1" > /dev/null 2>&1
}

echo "  Checking core packages..."

if ! check_package "transformers"; then
    echo "  Installing core packages (transformers, torch, etc)..."
    "$PYTHON_EXEC" -m pip install --upgrade pip -q
    "$PYTHON_EXEC" -m pip install torch torchvision torchaudio -q
    "$PYTHON_EXEC" -m pip install transformers==4.44.2 accelerate pillow soundfile librosa gradio fastapi uvicorn -q
    "$PYTHON_EXEC" -m pip install huggingface_hub -q
else
    echo "  Core packages seemingly installed (skipping full reinstall). Verifying criticals..."
    # Always ensure huggingface_hub is there for step 5
    "$PYTHON_EXEC" -m pip install huggingface_hub -q
fi

echo "  Checking server packages..."
if ! check_package "zeroconf" || ! check_package "noisereduce" || ! check_package "websockets" || ! check_package "vector_quantize_pytorch"; then
    echo "  Installing server packages..."
    "$PYTHON_EXEC" -m pip install zeroconf noisereduce webrtcvad numpy websockets vector_quantize_pytorch vocos -q
else
    echo "  Server packages installed ✓"
fi

echo "  Dependencies verification complete ✓"

# ------------------------------------------------------------------
# Step 5: Download Model
# ------------------------------------------------------------------
echo -e "\n${YELLOW}[Step 5/6] Downloading Model (idempotent)...${NC}"
echo "  Model Repo: $MODEL_REPO"
MODEL_DIR="${WORK_DIR}/model"
echo "  Target Dir: $MODEL_DIR"

# Login check (optional, public model usually fine but better with token if gated)
# huggingface-cli login --token $HF_TOKEN 

echo "  Checking/Downloading model to local directory..."

# Use HF Mirror for faster download in China
export HF_ENDPOINT=https://hf-mirror.com

# Use absolute path to huggingface-cli in the environment
HF_CLI="${ENV_PATH}/bin/huggingface-cli"
if [ ! -f "$HF_CLI" ]; then
    echo -e "${RED}Error: huggingface-cli not found at $HF_CLI${NC}"
    exit 1
fi

"$HF_CLI" download "$MODEL_REPO" --local-dir "$MODEL_DIR" --exclude "*.bin"

echo "  Model download complete ✓"

# Create/Update .env file for server
echo "MINICPM_MODEL=${MODEL_DIR}" > "${SCRIPT_DIR}/.env"

# ------------------------------------------------------------------
# Step 6: Finalize
# ------------------------------------------------------------------
echo -e "\n${YELLOW}[Step 6/6] Finalizing...${NC}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "To start the Voice Server (CHAT Mode):"
echo -e "  ${BLUE}RESPONSE_MODE=CHAT ./start_server.sh${BLUE}"
echo ""

