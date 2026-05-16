import hashlib
import json
import shutil
import tomllib
import zipfile
from pathlib import Path

from dms_reporting.app_info import APP_VERSION, get_running_bundle_path
from dms_reporting.updater import (
    check_for_updates,
    download_and_prepare_update,
    is_newer_version,
    load_saved_update_source,
    resolve_update_source,
    save_update_source,
)


def build_update_artifacts(base_dir: Path, version: str = "0.2.1") -> tuple[Path, Path, str]:
    app_dir = base_dir / "DMS Reporting.app"
    executable_path = app_dir / "Contents" / "MacOS" / "DMS Reporting"
    executable_path.parent.mkdir(parents=True)
    executable_path.write_text("binary", encoding="utf-8")

    zip_path = base_dir / "DMS Reporting.zip"
    with zipfile.ZipFile(zip_path, "w") as zip_file:
        zip_file.write(executable_path, arcname="DMS Reporting.app/Contents/MacOS/DMS Reporting")

    sha256 = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    manifest_path = base_dir / "latest-macos.json"
    manifest_path.write_text(
        json.dumps(
            {
                "version": version,
                "download_url": zip_path.name,
                "sha256": sha256,
                "published_at": "2026-04-28T09:00:00Z",
                "notes": "Them tinh nang cap nhat phan mem.",
            }
        ),
        encoding="utf-8",
    )
    return manifest_path, zip_path, sha256


def test_app_version_matches_pyproject():
    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    pyproject_data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    assert pyproject_data["project"]["version"] == APP_VERSION


def test_get_running_bundle_path_returns_app_root(tmp_path):
    executable_path = tmp_path / "DMS Reporting.app" / "Contents" / "MacOS" / "DMS Reporting"
    executable_path.parent.mkdir(parents=True)
    executable_path.touch()

    bundle_path = get_running_bundle_path(executable_path)

    assert bundle_path == tmp_path / "DMS Reporting.app"


def test_save_and_load_update_source(tmp_path):
    settings_path = tmp_path / "update_settings.json"
    source = str(tmp_path / "latest-macos.json")

    save_update_source(source, settings_path)

    assert load_saved_update_source(settings_path) == source
    assert resolve_update_source(config_path=settings_path, default_candidates=()) == source

    save_update_source("", settings_path)

    assert load_saved_update_source(settings_path) == ""
    assert resolve_update_source(config_path=settings_path, default_candidates=()) == ""


def test_is_newer_version_compares_semantic_parts():
    assert is_newer_version("0.2.0", "0.1.9")
    assert is_newer_version("1.0", "0.9.9")
    assert not is_newer_version("0.2.0", "0.2.0")
    assert not is_newer_version("0.1.9", "0.2.0")


def test_check_for_updates_supports_local_manifest(tmp_path):
    manifest_path, zip_path, _ = build_update_artifacts(tmp_path)

    result = check_for_updates(str(manifest_path), current_version="0.2.0")

    assert result.status == "available"
    assert result.update is not None
    assert result.update.version == "0.2.1"
    assert result.update.download_url == str(zip_path.resolve())


def test_check_for_updates_reports_up_to_date(tmp_path):
    manifest_path, _, _ = build_update_artifacts(tmp_path, version="0.2.0")

    result = check_for_updates(str(manifest_path), current_version="0.2.0")

    assert result.status == "up-to-date"


def test_download_and_prepare_update_extracts_app_bundle(tmp_path):
    manifest_path, _, _ = build_update_artifacts(tmp_path)
    result = check_for_updates(str(manifest_path), current_version="0.1.0")
    assert result.update is not None

    progress_messages: list[str] = []
    prepared_update = download_and_prepare_update(
        result.update,
        progress_callback=lambda current, total, message: progress_messages.append(
            f"{current}/{total}:{message}"
        ),
    )

    try:
        assert prepared_update.extracted_app_path.name == "DMS Reporting.app"
        assert prepared_update.archive_path.exists()
        assert len(progress_messages) == 4
    finally:
        shutil.rmtree(prepared_update.work_dir, ignore_errors=True)
