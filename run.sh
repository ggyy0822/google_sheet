#!/usr/bin/env bash
set -euo pipefail

# run.sh - 一鍵建立虛擬環境、安裝依賴、匯出 Excel（可選：上傳到 SCM）
#
# 用法：
#   chmod +x run.sh
#   ./run.sh                 # 只做「匯出」
#   ./run.sh --upload        # 匯出後，接著執行上傳（需手動勾 reCAPTCHA）
#   ./run.sh --export-only   # 只匯出（預設）
#
# 你也可以用環境變數控制（可選）：
#   CRF_VENDOR_CODE / CRF_ACCOUNT / CRF_PASSWORD
#   CRF_UPLOAD_XLSX  （若不設，建議 carrefour_upload.py 內做「抓 output 最新檔」）

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

MODE="export"
if [[ "${1:-}" == "--upload" ]]; then
  MODE="upload"
elif [[ "${1:-}" == "--export-only" || "${1:-}" == "" ]]; then
  MODE="export"
else
  echo "Unknown option: ${1:-}"
  echo "Usage: ./run.sh [--export-only|--upload]"
  exit 2
fi

echo "[run] Project root: $ROOT_DIR"
cd "$ROOT_DIR"

# 1) 建立 venv
if [ ! -d "$VENV_DIR" ]; then
  echo "[run] 建立虛擬環境：$VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

# 2) 啟用 venv
echo "[run] 啟用虛擬環境"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# 3) 安裝依賴
echo "[run] 升級 pip 並安裝 requirements.txt"
python -m pip install --upgrade pip
python -m pip install -r "$ROOT_DIR/requirements.txt"

# 4) 匯出
echo "[run] 執行匯出：export_to_template.py"
python3 -u "$ROOT_DIR/export_to_template.py"

# 5) 可選：上傳
if [[ "$MODE" == "upload" ]]; then
  echo "[run] 執行上傳：carrefour_upload.py"
  echo "[run] 注意：上傳時通常需要你手動勾選 reCAPTCHA"
  python3 -u "$ROOT_DIR/carrefour_upload.py"
else
  echo "[run] 完成匯出（未執行上傳）。如要上傳請用：./run.sh --upload"
fi