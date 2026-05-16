from __future__ import annotations

import os
import plistlib
import sys
from pathlib import Path

APP_NAME = "DMS Reporting"
APP_BUNDLE_ID = "vn.abipha.dmsreporting"
APP_VERSION = "0.3.0"
UPDATE_MANIFEST_NAME = "latest-macos.json"
UPDATE_SETTINGS_NAME = "update_settings.json"


def get_app_support_dir() -> Path:
    if sys.platform == "darwin":
        base_dir = Path.home() / "Library" / "Application Support"
    elif sys.platform == "win32":
        appdata_dir = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA")
        base_dir = Path(appdata_dir) if appdata_dir else Path.home() / "AppData" / "Roaming"
    else:
        xdg_config_home = os.getenv("XDG_CONFIG_HOME")
        base_dir = Path(xdg_config_home) if xdg_config_home else Path.home() / ".config"
    return base_dir / APP_NAME


def get_runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_update_settings_path() -> Path:
    return get_app_support_dir() / UPDATE_SETTINGS_NAME


def get_running_bundle_path(executable_path: Path | None = None) -> Path | None:
    if sys.platform != "darwin":
        return None
    candidate = (executable_path or Path(sys.executable)).resolve()
    for parent in candidate.parents:
        if parent.suffix == ".app":
            return parent
    return None


def get_app_version() -> str:
    bundle_path = get_running_bundle_path()
    if bundle_path is not None:
        info_plist_path = bundle_path / "Contents" / "Info.plist"
        if info_plist_path.exists():
            with info_plist_path.open("rb") as info_plist_file:
                plist_data = plistlib.load(info_plist_file)
            bundle_version = plist_data.get("CFBundleShortVersionString")
            if isinstance(bundle_version, str) and bundle_version.strip():
                return bundle_version.strip()
    return APP_VERSION


def get_default_update_manifest_candidates() -> tuple[Path, ...]:
    if sys.platform != "darwin":
        return ()

    package_root = get_runtime_root()
    candidates = [package_root / "releases" / "macos" / UPDATE_MANIFEST_NAME]

    bundle_path = get_running_bundle_path()
    if bundle_path is not None:
        candidates.append(bundle_path.parent / f"{APP_NAME} Updates" / UPDATE_MANIFEST_NAME)

    candidates.append(Path.home() / "Applications" / f"{APP_NAME} Updates" / UPDATE_MANIFEST_NAME)

    unique_candidates: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.expanduser()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique_candidates.append(resolved)

    return tuple(unique_candidates)
