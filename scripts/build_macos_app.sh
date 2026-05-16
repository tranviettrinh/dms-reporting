#!/bin/zsh

set -euo pipefail

APP_NAME="DMS Reporting"
BUNDLE_ID="vn.abipha.dmsreporting"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Script nay chi build tren macOS." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
OUTPUT_DIR="${OUTPUT_DIR:-$HOME/Applications}"
USER_BUILD_ROOT="${BUILD_ROOT:-}"

if [[ -n "$USER_BUILD_ROOT" ]]; then
  BUILD_ROOT="$USER_BUILD_ROOT"
  CLEAN_BUILD_ROOT="false"
else
  BUILD_ROOT="$(mktemp -d /private/tmp/dms-reporting-build.XXXXXX)"
  CLEAN_BUILD_ROOT="true"
fi

DIST_PATH="$BUILD_ROOT/dist"
WORK_PATH="$BUILD_ROOT/build"
SPEC_PATH="$BUILD_ROOT/spec"
FINAL_APP_PATH="$OUTPUT_DIR/$APP_NAME.app"

cleanup() {
  if [[ "$CLEAN_BUILD_ROOT" == "true" && -d "$BUILD_ROOT" ]]; then
    rm -rf "$BUILD_ROOT"
  fi
}

trap cleanup EXIT

cd "$PROJECT_DIR"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Khong tim thay trinh thong dich Python: $PYTHON_BIN" >&2
  exit 1
fi

APP_VERSION="$(PYTHONPATH="$PROJECT_DIR" "$PYTHON_BIN" - <<'PY'
from dms_reporting.app_info import APP_VERSION
print(APP_VERSION)
PY
)"

if ! "$PYTHON_BIN" -c "import PyInstaller" >/dev/null 2>&1; then
  "$PYTHON_BIN" -m pip install ".[macos]"
fi

mkdir -p "$OUTPUT_DIR" "$DIST_PATH" "$WORK_PATH" "$SPEC_PATH"
rm -rf "$DIST_PATH" "$WORK_PATH" "$SPEC_PATH" "$FINAL_APP_PATH"

"$PYTHON_BIN" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "$APP_NAME" \
  --osx-bundle-identifier "$BUNDLE_ID" \
  --distpath "$DIST_PATH" \
  --workpath "$WORK_PATH" \
  --specpath "$SPEC_PATH" \
  --paths "$PROJECT_DIR" \
  "$PROJECT_DIR/main_macos.py"

ditto --noextattr --norsrc "$DIST_PATH/$APP_NAME.app" "$FINAL_APP_PATH"
xattr -cr "$FINAL_APP_PATH" || true
"$PYTHON_BIN" - <<'PY' "$FINAL_APP_PATH/Contents/Info.plist" "$APP_VERSION"
import plistlib
import sys
from pathlib import Path

info_plist_path = Path(sys.argv[1])
app_version = sys.argv[2]
plist_data = plistlib.loads(info_plist_path.read_bytes())
plist_data["CFBundleShortVersionString"] = app_version
plist_data["CFBundleVersion"] = app_version
info_plist_path.write_bytes(plistlib.dumps(plist_data))
PY
codesign --force --deep --sign - "$FINAL_APP_PATH"
codesign --verify --deep --strict --verbose=2 "$FINAL_APP_PATH"

if [[ "$CLEAN_BUILD_ROOT" == "false" ]]; then
  echo "Build root: $BUILD_ROOT"
fi
echo "App sach da tao tai: $FINAL_APP_PATH"
