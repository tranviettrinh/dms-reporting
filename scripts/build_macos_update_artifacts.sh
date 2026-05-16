#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
APP_PATH="${APP_PATH:-$HOME/Applications/DMS Reporting.app}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/releases/macos}"
DOWNLOAD_URL="${DOWNLOAD_URL:-}"
NOTES_FILE="${NOTES_FILE:-}"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Script nay chi chay tren macOS." >&2
  exit 1
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Khong tim thay trinh thong dich Python: $PYTHON_BIN" >&2
  exit 1
fi

if [[ ! -d "$APP_PATH" ]]; then
  echo "Khong tim thay app tai: $APP_PATH" >&2
  exit 1
fi

APP_VERSION="$(PYTHONPATH="$PROJECT_DIR" "$PYTHON_BIN" - <<'PY'
from dms_reporting.app_info import APP_VERSION
print(APP_VERSION)
PY
)"

mkdir -p "$OUTPUT_DIR"

ZIP_NAME="DMS Reporting-${APP_VERSION}-macos.zip"
ZIP_PATH="$OUTPUT_DIR/$ZIP_NAME"
MANIFEST_PATH="$OUTPUT_DIR/latest-macos.json"
PUBLISHED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

rm -f "$ZIP_PATH"
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"

SHA256="$(shasum -a 256 "$ZIP_PATH" | awk '{print $1}')"
if [[ -n "$DOWNLOAD_URL" ]]; then
  RESOLVED_DOWNLOAD_URL="$DOWNLOAD_URL"
else
  RESOLVED_DOWNLOAD_URL="$ZIP_NAME"
fi

NOTES_TEXT=""
if [[ -n "$NOTES_FILE" ]]; then
  NOTES_TEXT="$(cat "$NOTES_FILE")"
fi

"$PYTHON_BIN" - <<'PY' "$MANIFEST_PATH" "$APP_VERSION" "$RESOLVED_DOWNLOAD_URL" "$SHA256" "$PUBLISHED_AT" "$NOTES_TEXT"
import json
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
version = sys.argv[2]
download_url = sys.argv[3]
sha256 = sys.argv[4]
published_at = sys.argv[5]
notes = sys.argv[6]

payload = {
    "version": version,
    "download_url": download_url,
    "sha256": sha256,
    "published_at": published_at,
    "notes": notes,
}
manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
PY

echo "Da tao goi cap nhat:"
echo "- Zip: $ZIP_PATH"
echo "- Manifest: $MANIFEST_PATH"
