import tkinter as tk
from pathlib import Path

import pytest

import dms_reporting.macos_app as macos_app
from dms_reporting.config import COMPANY_FILE_SPECS
from dms_reporting.macos_app import (
    DEFAULT_COMPANY_CODE,
    UPDATE_ONLY_MACOS_MESSAGE,
    MacOSReportApp,
    is_company_data_dir,
    resolve_company_context,
    resolve_default_company_dir,
)
from dms_reporting.reporting import GeneratedReport, ReportGenerationResult
from dms_reporting.user_access import UserStore


def create_company_dir(base_dir: Path, company_code: str = DEFAULT_COMPANY_CODE) -> Path:
    company_dir = base_dir / "modules" / company_code
    company_dir.mkdir(parents=True)
    for file_name in (spec.exact_name for spec in COMPANY_FILE_SPECS.values()):
        (company_dir / file_name).touch()
    return company_dir


def test_resolve_company_context_accepts_company_dir_under_modules(tmp_path):
    company_dir = create_company_dir(tmp_path)

    base_dir, company_code = resolve_company_context(company_dir)

    assert base_dir == tmp_path
    assert company_code == DEFAULT_COMPANY_CODE


def test_resolve_company_context_accepts_project_root_and_defaults_to_abipha(tmp_path):
    create_company_dir(tmp_path)

    base_dir, company_code = resolve_company_context(tmp_path)

    assert base_dir == tmp_path
    assert company_code == DEFAULT_COMPANY_CODE


def test_resolve_company_context_accepts_incomplete_company_dir_under_modules(tmp_path):
    company_dir = tmp_path / "modules" / DEFAULT_COMPANY_CODE
    company_dir.mkdir(parents=True)

    base_dir, company_code = resolve_company_context(company_dir)

    assert base_dir == tmp_path
    assert company_code == DEFAULT_COMPANY_CODE


def test_resolve_company_context_rejects_invalid_path(tmp_path):
    with pytest.raises(ValueError, match="thư mục dữ liệu công ty"):
        resolve_company_context(tmp_path)


def test_is_company_data_dir_requires_expected_files(tmp_path):
    company_dir = tmp_path / "modules" / DEFAULT_COMPANY_CODE
    company_dir.mkdir(parents=True)
    (company_dir / "CRM_Account.xlsx").touch()

    assert not is_company_data_dir(company_dir)


def test_resolve_default_company_dir_prefers_runtime_root_modules(tmp_path, monkeypatch):
    company_dir = create_company_dir(tmp_path)
    other_dir = tmp_path / "elsewhere"
    other_dir.mkdir()
    monkeypatch.chdir(other_dir)
    monkeypatch.setattr(macos_app, "get_runtime_root", lambda: tmp_path)

    assert resolve_default_company_dir() == company_dir


def test_macos_app_organizes_report_and_update_sections_into_tabs(tmp_path):
    user_store = UserStore(tmp_path / "users.json")
    try:
        app = MacOSReportApp(user_store=user_store)
    except tk.TclError as exc:
        pytest.skip(f"Tk không khả dụng trong môi trường test: {exc}")

    try:
        app.withdraw()
        assert app.current_view == "login"
        tab_texts = [app.notebook.tab(tab_id, "text") for tab_id in app.notebook.tabs()]
        assert tab_texts == ["Báo cáo", "Cập nhật"]
    finally:
        app.destroy()


def test_macos_app_disables_embedded_updates_on_windows(tmp_path, monkeypatch):
    user_store = UserStore(tmp_path / "users.json")
    monkeypatch.setattr(macos_app.sys, "platform", "win32")

    try:
        app = MacOSReportApp(user_store=user_store)
    except tk.TclError as exc:
        pytest.skip(f"Tk không khả dụng trong môi trường test: {exc}")

    try:
        app.withdraw()
        assert app.update_status_var.get() == UPDATE_ONLY_MACOS_MESSAGE
        assert str(app.save_update_button.cget("state")) == "disabled"
        assert str(app.check_update_button.cget("state")) == "disabled"
        assert str(app.install_update_button.cget("state")) == "disabled"
    finally:
        app.destroy()


def test_macos_app_can_toggle_password_visibility_on_login_page(tmp_path):
    user_store = UserStore(tmp_path / "users.json")
    try:
        app = MacOSReportApp(user_store=user_store)
    except tk.TclError as exc:
        pytest.skip(f"Tk không khả dụng trong môi trường test: {exc}")

    try:
        app.withdraw()
        assert str(app.login_password_entry.cget("show")) == "*"

        app.login_show_password_var.set(True)
        app._toggle_login_password_visibility()
        assert str(app.login_password_entry.cget("show")) == ""

        app.login_show_password_var.set(False)
        app._toggle_login_password_visibility()
        assert str(app.login_password_entry.cget("show")) == "*"
    finally:
        app.destroy()


def test_macos_app_hides_unauthorized_report_types(tmp_path):
    user_store = UserStore(tmp_path / "users.json")
    company_dir = create_company_dir(tmp_path)
    user_store.save_user(
        username="sales-user",
        role="user",
        allowed_reports=("summary", "invoice-territory"),
        password="secret123",
    )

    try:
        app = MacOSReportApp(user_store=user_store)
    except tk.TclError as exc:
        pytest.skip(f"Tk không khả dụng trong môi trường test: {exc}")

    try:
        app.withdraw()
        app.base_dir_var.set(str(company_dir))
        account = user_store.get_user("sales-user")
        assert account is not None

        app._set_current_user(account)

        assert app.current_view == "app"
        assert app.management_frame.winfo_manager() == ""
        assert app.report_checkbuttons["summary"].winfo_manager() == "grid"
        assert app.report_checkbuttons["invoice-territory"].winfo_manager() == "grid"
        assert app.report_checkbuttons["detail"].winfo_manager() == ""
        assert str(app.report_checkbuttons["summary"].cget("state")) == "normal"
        assert str(app.report_checkbuttons["invoice-territory"].cget("state")) == "normal"
        assert str(app.report_checkbuttons["detail"].cget("state")) == "disabled"
        assert str(app.run_button.cget("state")) == "normal"
        assert str(app.open_button.cget("state")) == "normal"
        assert app.report_vars["detail"].get() is False
        assert app._resolve_report_dir() == tmp_path / "modules" / DEFAULT_COMPANY_CODE / "report"
    finally:
        app.destroy()


def test_macos_app_build_request_lists_missing_excel_files_for_selected_reports(tmp_path):
    user_store = UserStore(tmp_path / "users.json")
    company_dir = tmp_path / "modules" / DEFAULT_COMPANY_CODE
    company_dir.mkdir(parents=True)
    (company_dir / "CRM_Account.xlsx").touch()
    user_store.save_user(
        username="sales-user",
        role="user",
        allowed_reports=("summary",),
        password="secret123",
    )

    try:
        app = MacOSReportApp(user_store=user_store)
    except tk.TclError as exc:
        pytest.skip(f"Tk không khả dụng trong môi trường test: {exc}")

    try:
        app.withdraw()
        app.base_dir_var.set(str(company_dir))
        account = user_store.get_user("sales-user")
        assert account is not None

        app._set_current_user(account)

        with pytest.raises(ValueError) as exc_info:
            app._build_request()

        error_message = str(exc_info.value)
        assert "Thiếu file Excel để tạo báo cáo" in error_message
        assert "CRM_Product.xlsx" in error_message
        assert "CRM_Saleorder.xlsx" in error_message
        assert "Cần chọn thư mục dữ liệu công ty" not in error_message
    finally:
        app.destroy()


def test_macos_app_shows_account_permissions_only_for_admin(tmp_path):
    user_store = UserStore(tmp_path / "users.json")

    try:
        app = MacOSReportApp(user_store=user_store)
    except tk.TclError as exc:
        pytest.skip(f"Tk không khả dụng trong môi trường test: {exc}")

    try:
        app.withdraw()
        admin_account = user_store.get_user("admin")
        assert admin_account is not None

        app._set_current_user(admin_account)

        assert app.current_view == "app"
        assert app.management_frame.winfo_manager() == "grid"
    finally:
        app.destroy()


def test_macos_app_returns_to_login_page_after_logout(tmp_path):
    user_store = UserStore(tmp_path / "users.json")
    user_store.save_user(
        username="sales-user",
        role="user",
        allowed_reports=("summary",),
        password="secret123",
    )

    try:
        app = MacOSReportApp(user_store=user_store)
    except tk.TclError as exc:
        pytest.skip(f"Tk không khả dụng trong môi trường test: {exc}")

    try:
        app.withdraw()
        account = user_store.get_user("sales-user")
        assert account is not None

        app._set_current_user(account)
        app.login_show_password_var.set(True)
        app._toggle_login_password_visibility()
        app._logout()

        assert app.current_view == "login"
        assert app.current_user is None
        assert app.login_username_var.get() == "sales-user"
        assert app.login_show_password_var.get() is False
        assert str(app.login_password_entry.cget("show")) == "*"
    finally:
        app.destroy()


def test_macos_app_dispatches_generation_events_from_ui_queue(tmp_path, monkeypatch):
    user_store = UserStore(tmp_path / "users.json")
    company_dir = create_company_dir(tmp_path)
    user_store.save_user(
        username="sales-user",
        role="user",
        allowed_reports=("invoice-territory",),
        password="secret123",
    )
    notifications: list[tuple[str, str]] = []
    monkeypatch.setattr(
        macos_app.messagebox,
        "showerror",
        lambda title, message, parent=None: notifications.append((title, message)),
    )

    try:
        app = MacOSReportApp(user_store=user_store)
    except tk.TclError as exc:
        pytest.skip(f"Tk không khả dụng trong môi trường test: {exc}")

    try:
        app.withdraw()
        app.base_dir_var.set(str(company_dir))
        account = user_store.get_user("sales-user")
        assert account is not None
        app._set_current_user(account)
        app._set_busy(True)

        result = ReportGenerationResult(
            report_dir=tmp_path / "modules" / DEFAULT_COMPANY_CODE / "report",
            generated_reports=[
                GeneratedReport(
                    label="Báo cáo khách hàng sai địa bàn",
                    path=tmp_path / "modules" / DEFAULT_COMPANY_CODE / "report" / "test.xlsx",
                )
            ],
        )
        app._queue_ui_event("progress", 1, 2, "Đang tạo báo cáo thử nghiệm...")
        app._queue_ui_event("generation-success", result)
        app._drain_ui_event_queue()

        assert app._busy is False
        assert app.progress_text_var.get() == "100% (1/1)"
        assert app.status_var.get().startswith("Hoàn tất. Kết quả nằm trong:")
        assert notifications == []
    finally:
        app.destroy()


def test_macos_app_can_run_reports_multiple_times_in_same_session(tmp_path, monkeypatch):
    user_store = UserStore(tmp_path / "users.json")
    company_dir = create_company_dir(tmp_path)
    user_store.save_user(
        username="sales-user",
        role="user",
        allowed_reports=("invoice-territory",),
        password="secret123",
    )
    run_calls: list[tuple[str, ...]] = []

    def fake_generate_reports(request, progress_callback=None):
        run_calls.append(tuple(request.selected_reports or ()))
        if progress_callback is not None:
            progress_callback(1, 2, "Đang tạo báo cáo thử nghiệm...")
        return ReportGenerationResult(
            report_dir=tmp_path / "modules" / DEFAULT_COMPANY_CODE / "report",
            generated_reports=[
                GeneratedReport(
                    label="Báo cáo khách hàng sai địa bàn",
                    path=tmp_path / "modules" / DEFAULT_COMPANY_CODE / "report" / "test.xlsx",
                )
            ],
        )

    class ImmediateThread:
        def __init__(self, *, target=None, args=(), daemon=None):
            self._target = target
            self._args = args

        def start(self):
            if self._target is not None:
                self._target(*self._args)

    monkeypatch.setattr(macos_app, "generate_reports", fake_generate_reports)
    monkeypatch.setattr(macos_app.messagebox, "showerror", lambda *args, **kwargs: None)
    monkeypatch.setattr(macos_app.threading, "Thread", ImmediateThread)

    try:
        app = MacOSReportApp(user_store=user_store)
    except tk.TclError as exc:
        pytest.skip(f"Tk không khả dụng trong môi trường test: {exc}")

    try:
        app.withdraw()
        app.base_dir_var.set(str(company_dir))
        account = user_store.get_user("sales-user")
        assert account is not None
        app._set_current_user(account)

        for _ in range(2):
            app.run_button.invoke()
            app._drain_ui_event_queue()

            assert app._busy is False
            assert str(app.run_button.cget("state")) == "normal"

        assert run_calls == [("invoice-territory",), ("invoice-territory",)]
    finally:
        app.destroy()


def test_macos_app_reenables_run_button_after_selecting_single_report(tmp_path):
    user_store = UserStore(tmp_path / "users.json")
    company_dir = create_company_dir(tmp_path)
    user_store.save_user(
        username="territory-user",
        role="user",
        allowed_reports=("invoice-territory",),
        password="secret123",
    )

    try:
        app = MacOSReportApp(user_store=user_store)
    except tk.TclError as exc:
        pytest.skip(f"Tk không khả dụng trong môi trường test: {exc}")

    try:
        app.withdraw()
        app.base_dir_var.set(str(company_dir))
        account = user_store.get_user("territory-user")
        assert account is not None
        app._set_current_user(account)

        app._clear_reports()
        assert str(app.run_button.cget("state")) == "disabled"

        app.report_checkbuttons["invoice-territory"].invoke()

        assert app.report_vars["invoice-territory"].get() is True
        assert str(app.run_button.cget("state")) == "normal"
    finally:
        app.destroy()
