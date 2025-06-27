#!/bin/bash

# Check if directory is empty and clone the latest viki repository
if [ "$(ls -A .)" ]; then
    echo "Directory is not empty. Latest viki is not reloaded."
else
    echo "Directory is empty. Latest viki is reloaded."
    git clone https://github.com/rahgadda/viki.ai.git .
fi

# Kill any existing python server
if pgrep -f "python -m http.server" > /dev/null; then
    echo "Killing existing python server..."
    pkill -f "python -m http.server"
else
    echo "No existing python server found."
fi

# Starting UI with python alias support
CURRENT_ALIASES="$(alias)"
nohup env CURRENT_ALIASES="$CURRENT_ALIASES" bash -c "
shopt -s expand_aliases
eval \"\$CURRENT_ALIASES\"
python -m http.server 5500" > server.log 2>&1 &