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
    echo "Initializing project 'viki_ai'."
    uv init viki_ai
fi