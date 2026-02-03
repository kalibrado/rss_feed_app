#!/bin/bash

VENV_DIR=".venv"
PID_FILE="main.pid"
LOG_DIR="logs"

# Create log directory
mkdir -p "$LOG_DIR"

# Check if process is already running
if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if kill -0 "$OLD_PID" 2>/dev/null; then
    echo "Process already running with PID $OLD_PID"
  fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  python3.12 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install requirements
if [ -f "requirements.txt" ]; then
  pip install -q -r requirements.txt
fi

# Start main.py with nohup
nohup python main.py > "$LOG_DIR/stdout.log" 2> "$LOG_DIR/stderr.log" &
NEW_PID=$!
echo "$NEW_PID" > "$PID_FILE"
echo "Started main.py with PID $NEW_PID"
