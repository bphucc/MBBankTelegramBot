#!/bin/bash

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PATH="${SCRIPT_DIR}/venv"
SCRIPT_PATH="${SCRIPT_DIR}/main.py"
USERNAME="$1"
PASSWORD="$2"
LOG_FILE="${SCRIPT_DIR}/monitor_start.log"

# Check if username and password are provided
if [ -z "$USERNAME" ] || [ -z "$PASSWORD" ]; then
    echo "Error: Username or password not provided" | tee -a "$LOG_FILE"
    echo "Usage: $0 <username> <password>" | tee -a "$LOG_FILE"
    exit 1
fi

# Log the start time
echo "Starting MB Bank Monitor at $(date)" >> "$LOG_FILE"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH" | tee -a "$LOG_FILE"
    exit 1
fi

# Activate virtual environment and run the script
echo "Activating virtual environment and starting script..." >> "$LOG_FILE"
source "${VENV_PATH}/bin/activate" && echo "Virtual environment activated" >> "$LOG_FILE"
python "$SCRIPT_PATH" "$USERNAME" "$PASSWORD"

# Log exit status
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo "Script exited with error code $EXIT_CODE at $(date)" >> "$LOG_FILE"
else
    echo "Script completed successfully at $(date)" >> "$LOG_FILE"
fi

exit $EXIT_CODE