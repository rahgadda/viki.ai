#!/bin/bash

# Check if directory is empty and clone the latest viki repository
if [ "$(ls -A .)" ]; then
    echo "Directory is not empty. Latest viki is not reloaded."
else
    echo "Directory is empty. Latest viki is reloaded."
    git clone https://github.com/rahgadda/viki.ai.git .
fi

# Kill any existing python server on port 5500
if pgrep -f "python.*http.server.*5500" > /dev/null; then
    echo "Killing existing python server on port 5500..."
    pkill -f "python.*http.server.*5500"
    sleep 2  # Wait for process to fully terminate
    echo "Existing server killed."
elif lsof -ti:5500 > /dev/null 2>&1; then
    echo "Port 5500 is in use by another process. Killing it..."
    kill -9 $(lsof -ti:5500) 2>/dev/null || true
    sleep 2
    echo "Port 5500 freed."
else
    echo "Port 5500 is available."
fi

# Starting UI with python alias support
CURRENT_ALIASES="$(alias)"
nohup env CURRENT_ALIASES="$CURRENT_ALIASES" bash -c "
shopt -s expand_aliases
eval \"\$CURRENT_ALIASES\"
python -m http.server 5500" > server.log 2>&1 &