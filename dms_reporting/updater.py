from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import urlopen

from dms_reporting.app_info import (
    APP_NAME,
    get_app_support_dir,
    get_app_version,
    get_default_update_manifest_candidates,
    get_running_bundle_path,
    get_update_settings_path,
)

ProgressCallback = Callable[[int, int, str], None]
REMOTE_SCHEMES = {"http", "https"}
FILE_SCHEME = "file"
UPDATE_SOURCE_ENV_VARS = ("DMS_REPORTING_UPDATE_SOURCE", "DMS_REPORTING_UPDATE_MANIFEST_URL")


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    download_url: str
    notes: str = ""
    published_at: str | None = None
    sha256: str | None = None


@dataclass(frozen=True)
class UpdateCheckResult:
    status: str
    current_version: str
    source: str | None = None
    update: UpdateInfo | None = None
    message: str = ""


@dataclass(frozen=True)
class PreparedUpdate:
    update: UpdateInfo
    work_dir: Path
    archive_path: Path
    extracted_app_path: Path


def load_saved_update_source(config_path: Path | None = None) -> str:
    settings_path = config_path or get_update_settings_path()
    if not settings_path.exists():
        return ""

    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""

    source = settings.get("source", "")
    return source.strip() if isinstance(source, str) else ""


def save_update_source(source: str, config_path: Path | None = None) -> Path:
    settings_path = config_path or get_update_settings_path()
    cleaned_source = source.strip()
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    if not cleaned_source:
        settings_path.unlink(missing_ok=True)
        return settings_path

    payload = {"source": cleaned_source}
    settings_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return settings_path


def resolve_update_source(
    source: str | None = None,
    config_path: Path | None = None,
    default_candidates: tuple[Path, ...] | None = None,
) -> str:
    cleaned_source = (source or "").strip()
    if cleaned_source:
        return cleaned_source

    for env_name in UPDATE_SOURCE_ENV_VARS:
        env_value = os.getenv(env_name, "").strip()
        if env_value:
            return env_value

    saved_source = load_saved_update_source(config_path)
    if saved_source:
        return saved_source

    candidate_paths = default_candidates if default_candidates is not None else get_default_update_manifest_candidates()
    for candidate in candidate_paths:
        if candidate.exists():
            return str(candidate)

    return ""


def check_for_updates(source: str | None = None, current_version: str | None = None) -> UpdateCheckResult:
    current = current_version or get_app_version()
    resolved_source = resolve_update_source(source)
    if not resolved_source:
        return UpdateCheckResult(
            status="missing-source",
            current_version=current,
            message="Chưa cấu hình nguồn cập nhật. Hãy nhập đường dẫn file latest-macos.json hoặc URL manifest.",
        )

    try:
        update_info = _load_update_info(resolved_source)
    except Exception as exc:
        return UpdateCheckResult(
            status="error",
            current_version=current,
            source=resolved_source,
            message=f"Không thể kiểm tra cập nhật: {exc}",
        )

    if is_newer_version(update_info.version, current):
        return UpdateCheckResult(
            status="available",
            current_version=current,
            source=resolved_source,
            update=update_info,
            message=f"Có bản cập nhật mới {update_info.version} (hiện tại {current}).",
        )

    return UpdateCheckResult(
        status="up-to-date",
        current_version=current,
        source=resolved_source,
        update=update_info,
        message=f"Bạn đang dùng phiên bản mới nhất {current}.",
    )


def can_self_update() -> bool:
    return get_running_bundle_path() is not None


def download_and_prepare_update(update: UpdateInfo, progress_callback: ProgressCallback | None = None) -> PreparedUpdate:
    work_dir = Path(tempfile.mkdtemp(prefix="dms-reporting-update."))
    archive_name = _derive_archive_name(update.download_url)
    archive_path = work_dir / archive_name
    extract_dir = work_dir / "expanded"

    _emit_progress(progress_callback, 1, 4, f"Đang tải gói cập nhật {update.version}...")
    _copy_from_source(update.download_url, archive_path)

    _emit_progress(progress_callback, 2, 4, "Đang kiểm tra gói cập nhật...")
    _verify_archive_checksum(archive_path, update.sha256)

    _emit_progress(progress_callback, 3, 4, "Đang giải nén gói cập nhật...")
    with zipfile.ZipFile(archive_path) as archive_file:
        archive_file.extractall(extract_dir)

    extracted_app_path = _find_app_bundle(extract_dir)
    _emit_progress(progress_callback, 4, 4, f"Đã sẵn sàng cài bản {update.version}.")
    return PreparedUpdate(
        update=update,
        work_dir=work_dir,
        archive_path=archive_path,
        extracted_app_path=extracted_app_path,
    )


def install_prepared_update(
    prepared_update: PreparedUpdate,
    target_app_path: Path | None = None,
    current_pid: int | None = None,
) -> Path:
    bundle_path = get_running_bundle_path()
    target_path = (target_app_path or bundle_path)
    if target_path is None:
        raise RuntimeError("Chỉ có thể cài tự động khi ứng dụng đang chạy từ file .app trên macOS.")

    target_path = target_path.expanduser().resolve()
    wait_pid = current_pid if current_pid is not None else os.getpid()
    should_wait_for_exit = bundle_path is not None and target_path == bundle_path.resolve()

    script_path = prepared_update.work_dir / "install_update.sh"
    log_path = prepared_update.work_dir / "install_update.log"
    script_path.write_text(
        _build_install_script(
            target_path=target_path,
            extracted_app_path=prepared_update.extracted_app_path,
            wait_pid=wait_pid if should_wait_for_exit else None,
            log_path=log_path,
        ),
        encoding="utf-8",
    )
    script_path.chmod(0o755)

    subprocess.Popen(
        ["/bin/zsh", str(script_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    return log_path


def is_newer_version(candidate_version: str, current_version: str) -> bool:
    return _normalize_version(candidate_version) > _normalize_version(current_version)


def _emit_progress(
    progress_callback: ProgressCallback | None,
    current_step: int,
    total_steps: int,
    message: str,
) -> None:
    if progress_callback is not None:
        progress_callback(current_step, total_steps, message)


def _load_update_info(source: str) -> UpdateInfo:
    manifest_text = _read_text_from_source(source)
    manifest_data = json.loads(manifest_text)

    if not isinstance(manifest_data, dict):
        raise ValueError("Manifest cập nhật không hợp lệ.")

    version = str(manifest_data.get("version", "")).strip()
    download_url = str(manifest_data.get("download_url", "")).strip()
    if not version:
        raise ValueError("Manifest thiếu trường version.")
    if not download_url:
        raise ValueError("Manifest thiếu trường download_url.")

    resolved_download_url = _resolve_download_url(source, download_url)
    notes = str(manifest_data.get("notes", "")).strip()
    published_at = str(manifest_data.get("published_at", "")).strip() or None
    sha256 = str(manifest_data.get("sha256", "")).strip() or None

    return UpdateInfo(
        version=version,
        download_url=resolved_download_url,
        notes=notes,
        published_at=published_at,
        sha256=sha256,
    )


def _read_text_from_source(source: str) -> str:
    parsed_source = urlparse(source)
    if parsed_source.scheme in REMOTE_SCHEMES:
        with urlopen(source, timeout=15) as response:
            return response.read().decode("utf-8")

    path = _source_to_path(source)
    return path.read_text(encoding="utf-8")


def _copy_from_source(source: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    parsed_source = urlparse(source)
    if parsed_source.scheme in REMOTE_SCHEMES:
        with urlopen(source, timeout=60) as response, destination.open("wb") as destination_file:
            shutil.copyfileobj(response, destination_file)
        return

    shutil.copy2(_source_to_path(source), destination)


def _verify_archive_checksum(archive_path: Path, expected_sha256: str | None) -> None:
    if not expected_sha256:
        return

    digest = hashlib.sha256()
    with archive_path.open("rb") as archive_file:
        for chunk in iter(lambda: archive_file.read(1024 * 1024), b""):
            digest.update(chunk)

    if digest.hexdigest().lower() != expected_sha256.lower():
        raise ValueError("Checksum gói cập nhật không khớp.")


def _find_app_bundle(root_dir: Path) -> Path:
    app_candidates = sorted(root_dir.rglob("*.app"))
    if not app_candidates:
        raise ValueError("Không tìm thấy file .app trong gói cập nhật.")
    return app_candidates[0]


def _build_install_script(
    *,
    target_path: Path,
    extracted_app_path: Path,
    wait_pid: int | None,
    log_path: Path,
) -> str:
    wait_block = ""
    if wait_pid is not None:
        wait_block = f"""
for _ in {{1..120}}; do
  if ! kill -0 {wait_pid} 2>/dev/null; then
    break
  fi
  sleep 1
done
"""

    return f"""#!/bin/zsh
set -euo pipefail

TARGET_APP={_shell_quote(str(target_path))}
SOURCE_APP={_shell_quote(str(extracted_app_path))}
BACKUP_APP="$TARGET_APP.previous"
LOG_FILE={_shell_quote(str(log_path))}

{wait_block}
{{
  rm -rf "$BACKUP_APP"
  if [[ -d "$TARGET_APP" ]]; then
    mv "$TARGET_APP" "$BACKUP_APP"
  fi

  if ditto --noextattr --norsrc "$SOURCE_APP" "$TARGET_APP"; then
    xattr -cr "$TARGET_APP" || true
    rm -rf "$BACKUP_APP"
  else
    rm -rf "$TARGET_APP"
    if [[ -d "$BACKUP_APP" ]]; then
      mv "$BACKUP_APP" "$TARGET_APP"
    fi
    exit 1
  fi
}} >> "$LOG_FILE" 2>&1
"""


def _normalize_version(version: str) -> tuple[int, ...]:
    version_parts = []
    for raw_part in version.replace("-", ".").split("."):
        digits = "".join(character for character in raw_part if character.isdigit())
        if digits:
            version_parts.append(int(digits))

    if not version_parts:
        return (0,)

    while len(version_parts) < 3:
        version_parts.append(0)

    return tuple(version_parts)


def _resolve_download_url(manifest_source: str, download_url: str) -> str:
    parsed_download = urlparse(download_url)
    if parsed_download.scheme in REMOTE_SCHEMES | {FILE_SCHEME}:
        return download_url

    parsed_manifest_source = urlparse(manifest_source)
    if parsed_manifest_source.scheme in REMOTE_SCHEMES:
        return urljoin(manifest_source, download_url)

    manifest_path = _source_to_path(manifest_source)
    return str((manifest_path.parent / download_url).resolve())


def _source_to_path(source: str) -> Path:
    parsed_source = urlparse(source)
    if parsed_source.scheme == FILE_SCHEME:
        return Path(unquote(parsed_source.path)).expanduser().resolve()
    return Path(source).expanduser().resolve()


def _derive_archive_name(download_url: str) -> str:
    source_path = _source_to_path(download_url) if urlparse(download_url).scheme == FILE_SCHEME else None
    if source_path is not None:
        return source_path.name or "DMS Reporting Update.zip"

    parsed_download = urlparse(download_url)
    file_name = Path(unquote(parsed_download.path)).name
    return file_name or "DMS Reporting Update.zip"


def _shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"
