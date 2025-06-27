#!/bin/bash

# Clone the repository
git clone https://github.com/rahgadda/viki.ai.git .

# Starting UI
python -m http.server 5500

# Starting Service