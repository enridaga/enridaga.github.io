#!/bin/bash
set -e
.python3.12/bin/pip install -q -r requirements.txt
.python3.12/bin/python build.py
echo ""
echo "🌐  Preview at http://localhost:8000"
cd _site && ../.python3.12/bin/python -m http.server
