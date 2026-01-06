#!/bin/bash
# Launch Stock Tracker UI
# Run this script from anywhere - it will cd to the correct directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source venv/bin/activate
streamlit run src/ui/app_live.py
