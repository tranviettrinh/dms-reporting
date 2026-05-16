from pathlib import Path

import dms_reporting.app_info as app_info


def test_get_app_support_dir_uses_windows_appdata(monkeypatch, tmp_path):
    monkeypatch.setattr(app_info.sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    monkeypatch.delenv("LOCALAPPDATA", raising=False)

    assert app_info.get_app_support_dir() == tmp_path / "Roaming" / app_info.APP_NAME


def test_get_runtime_root_uses_executable_parent_when_frozen(monkeypatch, tmp_path):
    executable_path = tmp_path / "DMS Reporting.exe"
    executable_path.write_text("exe", encoding="utf-8")
    monkeypatch.setattr(app_info.sys, "frozen", True, raising=False)
    monkeypatch.setattr(app_info.sys, "executable", str(executable_path))

    assert app_info.get_runtime_root() == tmp_path
