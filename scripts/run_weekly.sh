#!/bin/bash
set -e

#PROJECT_DIR="$HOME/projects/stock-tracker"
#VENV="$PROJECT_DIR/venv"
#source "$VENV/bin/activate"
#python "$PROJECT_DIR/src/main.py"

PROJECT_DIR="$HOME/projects/stock-tracker"
source "$PROJECT_DIR/venv/bin/activate"

cd "$PROJECT_DIR"
python -m src.main
