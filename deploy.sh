#!/bin/bash
set -e

# Configuration
HOST="jinliang@pi.local"
REMOTE_DIR="~/dog_app/"
LOCAL_DIR="dog_app/"
SERVICE_NAME="dog_app.service"
LOG_FILE="~/dog_app/startup.log"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO] $1${NC}"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# 1. Sync Code
log_info "Step 1: Syncing code to $HOST..."
rsync -avz --exclude '__pycache__' --exclude '*.pyc' --exclude '.*' \
    "$LOCAL_DIR" "$HOST:$REMOTE_DIR"

if [ $? -ne 0 ]; then
    log_error "Rsync failed."
    exit 1
fi

# 2. Restart Service
log_info "Step 2: Restarting service..."
ssh "$HOST" "sudo systemctl restart $SERVICE_NAME"

if [ $? -ne 0 ]; then
    log_error "Failed to restart service."
    exit 1
fi

# 3. Verification
log_info "Step 3: Verifying service health..."

# Wait a moment for startup
sleep 5

# Check if active
STATUS=$(ssh "$HOST" "systemctl is-active $SERVICE_NAME")
if [ "$STATUS" != "active" ]; then
    log_error "Service is not active. Status: $STATUS"
    ssh "$HOST" "systemctl status $SERVICE_NAME"
    exit 1
fi

# Verification Loop
MAX_RETRIES=15
counter=0
success=false

log_info "Polling logs for success signals (timeout 30s)..."

while [ $counter -lt $MAX_RETRIES ]; do
    LOG_OUTPUT=$(ssh "$HOST" "tail -n 50 $LOG_FILE")
    
    # Check for crashes
    if echo "$LOG_OUTPUT" | grep -q "Traceback"; then
        log_error "Found Python Traceback in logs!"
        echo "$LOG_OUTPUT" | grep -A 20 "Traceback" -B 5
        exit 1
    fi
    
    # Check for Voice Client
    if echo "$LOG_OUTPUT" | grep -q "VoiceStreamingClient: Started"; then
         log_info "✓ Voice Client Started"
         success=true
         break
    fi
    
    # Check for Main App Idle (Alternative success if Voice is optional or slow)
    if echo "$LOG_OUTPUT" | grep -q "MainApp: System Idle"; then
         log_info "✓ MainApp Idle State Reached"
         success=true
         break
    fi

    # Still waiting
    echo -n "."
    sleep 2
    counter=$((counter+1))
done

echo "" # Newline

if [ "$success" = true ]; then
    log_info "Deployment and Verification SUCCESS!"
    # Print the last few lines for context
    echo "Recent Logs:"
    echo "$LOG_OUTPUT" | tail -n 5
    exit 0
else
    log_error "Verification Timed Out. Signals not found."
    echo "Recent Logs:"
    echo "$LOG_OUTPUT"
    exit 1
fi
