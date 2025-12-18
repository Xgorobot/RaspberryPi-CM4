#!/bin/bash

# Configuration
APP_MODULE="mock_server.main:app"
HOST="0.0.0.0"
PORT="8000"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load .env if exists (for MINICPM_MODEL path)
if [ -f "${SCRIPT_DIR}/.env" ]; then
    export $(grep -v '^#' "${SCRIPT_DIR}/.env" | xargs)
    echo "📄 Loaded .env configuration"
fi

# Determine Python command based on RESPONSE_MODE
# CHAT mode requires chat_agent conda environment with MiniCPM-o dependencies
if [ "$RESPONSE_MODE" = "CHAT" ]; then
    echo "📦 CHAT mode: Using chat_agent conda environment (Direct Path)"
    # Use absolute path to avoid activation issues
    PYTHON_CMD="/opt/homebrew/Caskroom/miniconda/base/envs/chat_agent/bin/python"
else
    # Use xgo_dog environment for ECHO/BEEP modes
    PYTHON_CMD="/opt/homebrew/Caskroom/miniconda/base/envs/xgo_dog/bin/python"
fi

# Auto-kill existing server if running
# Auto-kill existing server if running
# Improved: Use lsof to find process binding the port
PID=$(lsof -t -i:$PORT)
if [ ! -z "$PID" ]; then
    echo "⚠️  Stopping existing server on port $PORT..."
    echo "   Killing PID(s): $PID"
    
    # Try graceful kill first
    kill -15 $PID 2>/dev/null
    sleep 1
    
    # Check if still running
    if lsof -t -i:$PORT > /dev/null; then
        echo "❌ Ports still in use. Force killing..."
        kill -9 $PID 2>/dev/null
        sleep 1
    fi
    echo "   ✓ Stopped."
fi

echo "🚀 Starting Mock Voice Server..."
echo "   Host: $HOST"
echo "   Port: $PORT"
echo "   Mode: ${RESPONSE_MODE:-ECHO}"
echo "   Log:  mock_server.log"

# Run with unbuffered output and pipe to log file
export PYTHONUNBUFFERED=1
$PYTHON_CMD -m uvicorn $APP_MODULE --host $HOST --port $PORT 2>&1 | tee mock_server.log
