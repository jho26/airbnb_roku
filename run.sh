#!/bin/bash

# Roku Welcome Screen Updater - Complete Shell Script
# Combines functionality from run.sh and update_roku.sh
# Usage: ./run.sh

# Script directory detection (robust method)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/update_roku_welcome.py"

# Change to script directory
cd "$SCRIPT_DIR"

# Add timestamp and environment info for cron debugging
echo "========================================="
echo "🚀 Roku Update Started: $(date)"
echo "Working Directory: $(pwd)"
echo "User: $(whoami)"
echo "Environment: $(env | grep -E '^(PATH|HOME|USER)=')"
echo "========================================="

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Error: Python script not found: $PYTHON_SCRIPT"
    echo "Failed ❌ at $(date)"
    echo "========================================="
    exit 1
fi

# Run the Python updater
echo "📥 Updating Roku welcome screen..."
python3 update_roku_welcome.py

# Check exit status and provide detailed feedback
if [ $? -eq 0 ]; then
    echo "✅ Update completed successfully at $(date)"
else
    echo "❌ Update failed at $(date)"
    echo "========================================="
    exit 1
fi
echo "========================================="
