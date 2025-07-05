#!/bin/bash

# Check if current directory is 'service'
if [[ "$(basename "$PWD")" != "service" ]]; then
    echo "Error: Please run this script from the 'service' directory."
    exit 1
fi

# Check if project already initialized
if [[ -d "viki_ai" ]]; then
    echo "Project 'viki_ai' is already initialized."
    cd viki_ai
    uv sync
    cd ..
else
    echo "Project 'viki_ai' is not available."
    exit 1
fi

# Check if any Python process is running on port 8000 and kill it
pid=$(lsof -ti:8000 -sTCP:LISTEN -a -c python)
if [[ -n "$pid" ]]; then
    echo "Killing Python process on port 8000 (PID: $pid)"
    kill -9 $pid
fi

# Starting the viki_ai service
echo "Running viki_ai service"
source viki_ai/.venv/bin/activate
cd viki_ai
uv pip install -e .
cd ..
uv run -m viki_ai