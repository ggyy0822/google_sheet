#!/usr/bin/env bash
set -euo pipefail

# run.sh - 建立虛擬環境、安裝依賴並執行 google_sheet.py
# 使用方式：
#   chmod +x run.sh
#   ./run.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "建立虛擬環境：$VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

echo "啟用虛擬環境"
source "$VENV_DIR/bin/activate"

echo "升級 pip 並安裝 requirements.txt"
python -m pip install --upgrade pip
python -m pip install -r "$ROOT_DIR/requirements.txt"

echo "執行 google_sheet.py"
python3 -u "$ROOT_DIR/google_sheet.py"
