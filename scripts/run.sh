#!/bin/bash
set -e

PROJECT_DIR="$HOME/projects/stock-tracker"
source "$PROJECT_DIR/venv/bin/activate"

cd "$PROJECT_DIR"
python -m src.main
