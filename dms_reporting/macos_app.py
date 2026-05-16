from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from dms_reporting.app_info import get_app_version, get_runtime_root
from dms_reporting.config import CORE_COMPANY_FILE_KEYS, CompanyPaths, missing_company_files
from dms_reporting.constants import (
    DEFAULT_RETURN_ORDER_STATUSES,
    DEFAULT_SALES_ORDER_STATUSES,
    RETURN_ORDER_STATUS_OPTIONS,
    SALES_ORDER_STATUS_OPTIONS,
)
from dms_reporting.reporting import (
    REPORT_LABELS,
    REPORT_OPTIONS,
    TERRITORY_OPTION_IDS,
    ReportGenerationResult,
    ReportRequest,
    validate_required_company_files,
    generate_reports,
    reports_require_dates,
)
from dms_reporting.updater import (
    UpdateCheckResult,
    UpdateInfo,
    can_self_update,
    check_for_updates,
    download_and_prepare_update,
    install_prepared_update,
    resolve_update_source,
    save_update_source,
)
from dms_reporting.user_access import DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME, UserAccount, UserStore

DEFAULT_COMPANY_CODE = "abipha"
UPDATE_ONLY_MACOS_MESSAGE = "Tự cập nhật trong app hiện chỉ hỗ trợ bản macOS."


def resolve_default_company_dir(default_company_code: str = DEFAULT_COMPANY_CODE) -> Path:
    runtime_root = get_runtime_root()
    package_root = Path(__file__).resolve().parent.parent
    candidates = [Path.cwd(), runtime_root, package_root, Path.home() / "Documents", Path.home()]

    for candidate in candidates:
        company_dir = candidate / "modules" / default_company_code
        if is_company_data_dir(company_dir):
            return company_dir

    return package_root


def is_company_data_dir(path: Path) -> bool:
    return path.is_dir() and not missing_company_files(path, CORE_COMPANY_FILE_KEYS)


def resolve_company_context(selected_path: Path) -> tuple[Path, str]:
    data_dir = selected_path.expanduser().resolve()
    if is_company_data_dir(data_dir):
        if data_dir.parent.name != "modules":
            raise ValueError("Cần chọn đúng thư mục công ty nằm trong modules/, ví dụ: .../modules/abipha")
        return data_dir.parent.parent, data_dir.name

    default_company_dir = data_dir / "modules" / DEFAULT_COMPANY_CODE
    if data_dir.is_dir() and data_dir.parent.name == "modules":
        return data_dir.parent.parent, data_dir.name

    if default_company_dir.is_dir():
        return data_dir, DEFAULT_COMPANY_CODE

    if data_dir.name == "modules":
        nested_company_dir = data_dir / DEFAULT_COMPANY_CODE
        if nested_company_dir.is_dir():
            return data_dir.parent, DEFAULT_COMPANY_CODE

    raise ValueError("Cần chọn thư mục dữ liệu công ty, ví dụ: .../modules/abipha")


def supports_embedded_updates() -> bool:
    return sys.platform == "darwin"


class MacOSReportApp(tk.Tk):
    def __init__(self, user_store: UserStore | None = None) -> None:
        super().__init__()
        self.title("DMS Reporting")
        self.geometry("560x420")
        self.minsize(520, 380)

        self.user_store = user_store or UserStore()
        self.current_user: UserAccount | None = None
        self.current_view = "login"
        self._managed_usernames: list[str] = []
        self.report_checkbuttons: dict[str, ttk.Checkbutton] = {}
        self.management_report_checkbuttons: dict[str, ttk.Checkbutton] = {}

        today = date.today()
        self.base_dir_var = tk.StringVar(value=str(resolve_default_company_dir()))
        self.start_date_var = tk.StringVar(value=f"{today.year}-01-01")
        self.end_date_var = tk.StringVar(value=f"{today.year}-12-31")
        self.status_var = tk.StringVar(value="Vui lòng đăng nhập để chạy báo cáo.")
        self.progress_text_var = tk.StringVar(value="0%")
        self.progress_value_var = tk.DoubleVar(value=0.0)
        self.version_var = tk.StringVar(value=f"Phiên bản hiện tại: {get_app_version()}")
        self.update_source_var = tk.StringVar(value=resolve_update_source())
        self.update_status_var = tk.StringVar(
            value="Chưa kiểm tra cập nhật." if supports_embedded_updates() else UPDATE_ONLY_MACOS_MESSAGE
        )
        self.login_status_var = tk.StringVar(value="Đăng nhập để tiếp tục vào phần mềm.")
        self.current_user_var = tk.StringVar(value="Chưa đăng nhập.")
        self.user_status_var = tk.StringVar(value="Đăng nhập để dùng các loại báo cáo được cấp quyền.")
        self.login_username_var = tk.StringVar(
            value=DEFAULT_ADMIN_USERNAME if self.user_store.default_admin_created else ""
        )
        self.login_password_var = tk.StringVar()
        self.login_show_password_var = tk.BooleanVar(value=False)
        self.management_username_var = tk.StringVar()
        self.management_password_var = tk.StringVar()
        self.management_role_var = tk.StringVar(value="user")
        self.management_status_var = tk.StringVar(
            value="Chỉ tài khoản admin mới được quản lý phân quyền người dùng."
        )
        self.report_vars = {report_id: tk.BooleanVar(value=True) for report_id, _ in REPORT_OPTIONS}
        self.management_report_vars = {
            report_id: tk.BooleanVar(value=False)
            for report_id, _ in REPORT_OPTIONS
        }
        self.sales_status_vars = {
            status: tk.BooleanVar(value=status in DEFAULT_SALES_ORDER_STATUSES)
            for status in SALES_ORDER_STATUS_OPTIONS
        }
        self.return_status_vars = {
            status: tk.BooleanVar(value=status in DEFAULT_RETURN_ORDER_STATUSES)
            for status in RETURN_ORDER_STATUS_OPTIONS
        }

        self.last_result: ReportGenerationResult | None = None
        self.current_update: UpdateInfo | None = None
        self.login_page: ttk.Frame
        self.app_page: ttk.Frame
        self.notebook: ttk.Notebook
        self.report_tab: ttk.Frame
        self.update_tab: ttk.Frame
        self.reports_frame: ttk.LabelFrame
        self.report_actions_frame: ttk.Frame
        self.management_frame: ttk.LabelFrame
        self.run_button: ttk.Button
        self.open_button: ttk.Button
        self.check_update_button: ttk.Button
        self.install_update_button: ttk.Button
        self.save_update_button: ttk.Button
        self.login_button: ttk.Button
        self.login_show_password_button: ttk.Checkbutton
        self.logout_button: ttk.Button
        self.select_all_button: ttk.Button
        self.territory_reports_button: ttk.Button
        self.clear_reports_button: ttk.Button
        self.new_user_button: ttk.Button
        self.save_user_button: ttk.Button
        self.delete_user_button: ttk.Button
        self.start_entry: ttk.Entry
        self.end_entry: ttk.Entry
        self.output_text: tk.Text
        self.progress_bar: ttk.Progressbar
        self.login_username_entry: ttk.Entry
        self.login_password_entry: ttk.Entry
        self.management_username_entry: ttk.Entry
        self.management_password_entry: ttk.Entry
        self.management_role_combo: ttk.Combobox
        self.user_listbox: tk.Listbox
        self._ui_event_queue: queue.Queue[tuple[str, tuple[object, ...]]] = queue.Queue()
        self._ui_event_poll_after_id: str | None = None
        self._busy = False
        self._last_progress_message = ""

        self._build_layout()
        self._schedule_ui_event_poll()
        self._refresh_user_list()
        self._prepare_new_user_form()
        self._apply_access_control()
        self._toggle_date_fields()
        self._sync_action_buttons()
        self._show_login_page()

        if self.user_store.default_admin_created:
            bootstrap_message = (
                f"Đã tạo tài khoản mặc định {DEFAULT_ADMIN_USERNAME}/{DEFAULT_ADMIN_PASSWORD}. "
                "Hãy đăng nhập và đổi mật khẩu."
            )
            self.login_status_var.set(bootstrap_message)

    def destroy(self) -> None:
        if self._ui_event_poll_after_id is not None:
            try:
                self.after_cancel(self._ui_event_poll_after_id)
            except tk.TclError:
                pass
            self._ui_event_poll_after_id = None
        super().destroy()

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        page_container = ttk.Frame(self)
        page_container.grid(row=0, column=0, sticky="nsew")
        page_container.columnconfigure(0, weight=1)
        page_container.rowconfigure(0, weight=1)

        self.login_page = ttk.Frame(page_container, padding=24)
        self.app_page = ttk.Frame(page_container)
        self.login_page.grid(row=0, column=0, sticky="nsew")
        self.app_page.grid(row=0, column=0, sticky="nsew")

        self._build_login_page(self.login_page)
        self._build_app_page(self.app_page)

    def _build_login_page(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        login_card = ttk.Frame(parent, padding=32)
        login_card.grid(row=0, column=0)
        login_card.columnconfigure(0, weight=1)

        ttk.Label(login_card, text="DMS Reporting", font=("", 22, "bold")).grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 8),
        )
        ttk.Label(
            login_card,
            text="Đăng nhập tài khoản để vào màn hình báo cáo.",
            anchor="center",
            justify="center",
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 16),
        )
        ttk.Label(login_card, textvariable=self.version_var, anchor="center").grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(0, 24),
        )

        form_frame = ttk.LabelFrame(login_card, text="Đăng nhập", padding=18)
        form_frame.grid(row=3, column=0, sticky="ew")
        form_frame.columnconfigure(1, weight=1)

        ttk.Label(form_frame, text="Tên đăng nhập").grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.login_username_entry = ttk.Entry(form_frame, textvariable=self.login_username_var)
        self.login_username_entry.grid(row=0, column=1, sticky="ew", padx=(12, 0), pady=(0, 10))

        ttk.Label(form_frame, text="Mật khẩu").grid(row=1, column=0, sticky="w", pady=(0, 10))
        self.login_password_entry = ttk.Entry(form_frame, textvariable=self.login_password_var, show="*")
        self.login_password_entry.grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=(0, 10))
        self.login_password_entry.bind("<Return>", lambda _event: self._login())
        self.login_username_entry.bind("<Return>", lambda _event: self._login())

        self.login_show_password_button = ttk.Checkbutton(
            form_frame,
            text="Hiển thị mật khẩu",
            variable=self.login_show_password_var,
            command=self._toggle_login_password_visibility,
        )
        self.login_show_password_button.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.login_button = ttk.Button(form_frame, text="Đăng nhập", command=self._login)
        self.login_button.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        ttk.Label(
            login_card,
            textvariable=self.login_status_var,
            anchor="center",
            justify="center",
            wraplength=460,
        ).grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(18, 0),
        )

    def _build_app_page(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

        session_frame = ttk.LabelFrame(parent, text="Phiên làm việc", padding=12)
        session_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 12))
        session_frame.columnconfigure(0, weight=1)

        ttk.Label(session_frame, textvariable=self.current_user_var, anchor="w").grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 4),
        )
        ttk.Label(
            session_frame,
            textvariable=self.user_status_var,
            anchor="w",
            justify="left",
            wraplength=760,
        ).grid(
            row=1,
            column=0,
            sticky="ew",
        )
        self.logout_button = ttk.Button(session_frame, text="Đăng xuất", command=self._logout)
        self.logout_button.grid(row=0, column=1, rowspan=2, sticky="ns", padx=(12, 0))

        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 12))

        self.report_tab = ttk.Frame(self.notebook, padding=20)
        self.update_tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(self.report_tab, text="Báo cáo")
        self.notebook.add(self.update_tab, text="Cập nhật")

        self._build_report_tab(self.report_tab)
        self._build_update_tab(self.update_tab)

        output_frame = ttk.LabelFrame(parent, text="Kết quả và nhật ký", padding=20)
        output_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 12))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(output_frame, orient="vertical")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.output_text = tk.Text(output_frame, wrap="word", yscrollcommand=scrollbar.set, height=18)
        self.output_text.grid(row=0, column=0, sticky="nsew")
        self.output_text.configure(state="disabled")
        scrollbar.configure(command=self.output_text.yview)

        status_bar = ttk.Label(parent, textvariable=self.status_var, anchor="w", padding=(20, 0, 20, 14))
        status_bar.grid(row=3, column=0, sticky="ew")

    def _build_report_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)

        ttk.Label(parent, text="Thư mục dữ liệu").grid(row=0, column=0, sticky="w", pady=(0, 10))
        base_dir_entry = ttk.Entry(parent, textvariable=self.base_dir_var)
        base_dir_entry.grid(row=0, column=1, sticky="ew", padx=(12, 12), pady=(0, 10))
        ttk.Button(parent, text="Chọn thư mục", command=self._choose_base_dir).grid(
            row=0,
            column=2,
            sticky="ew",
            pady=(0, 10),
        )

        ttk.Label(parent, text="Start date").grid(row=1, column=0, sticky="w", pady=(0, 10))
        self.start_entry = ttk.Entry(parent, textvariable=self.start_date_var)
        self.start_entry.grid(row=1, column=1, sticky="ew", padx=(12, 12), pady=(0, 10))

        ttk.Label(parent, text="End date").grid(row=2, column=0, sticky="w", pady=(0, 10))
        self.end_entry = ttk.Entry(parent, textvariable=self.end_date_var)
        self.end_entry.grid(row=2, column=1, sticky="ew", padx=(12, 12), pady=(0, 10))

        self.reports_frame = ttk.LabelFrame(parent, text="Loại báo cáo", padding=12)
        self.reports_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        self.reports_frame.columnconfigure(0, weight=1)
        self.reports_frame.columnconfigure(1, weight=1)

        for index, (report_id, label) in enumerate(REPORT_OPTIONS):
            checkbox = ttk.Checkbutton(
                self.reports_frame,
                text=label,
                variable=self.report_vars[report_id],
                command=self._handle_report_selection_change,
            )
            checkbox.grid(row=index // 2, column=index % 2, sticky="w", padx=(0, 12), pady=4)
            self.report_checkbuttons[report_id] = checkbox

        self.report_actions_frame = ttk.Frame(self.reports_frame)
        self.report_actions_frame.grid(
            row=(len(REPORT_OPTIONS) + 1) // 2,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8, 0),
        )
        self.select_all_button = ttk.Button(self.report_actions_frame, text="Chọn tất cả", command=self._select_all_reports)
        self.select_all_button.grid(row=0, column=0, padx=(0, 8))
        self.territory_reports_button = ttk.Button(
            self.report_actions_frame,
            text="Chỉ phân tuyến",
            command=self._select_territory_reports,
        )
        self.territory_reports_button.grid(row=0, column=1, padx=(0, 8))
        self.clear_reports_button = ttk.Button(self.report_actions_frame, text="Bỏ chọn", command=self._clear_reports)
        self.clear_reports_button.grid(row=0, column=2)

        statuses_frame = ttk.Frame(parent)
        statuses_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        statuses_frame.columnconfigure(0, weight=1)
        statuses_frame.columnconfigure(1, weight=1)

        sales_status_frame = ttk.LabelFrame(statuses_frame, text="Trạng thái đơn bán ra", padding=12)
        sales_status_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        sales_status_frame.columnconfigure(0, weight=1)

        for index, status in enumerate(SALES_ORDER_STATUS_OPTIONS):
            ttk.Checkbutton(sales_status_frame, text=status, variable=self.sales_status_vars[status]).grid(
                row=index,
                column=0,
                sticky="w",
                pady=4,
            )

        return_status_frame = ttk.LabelFrame(statuses_frame, text="Trạng thái đơn trả lại", padding=12)
        return_status_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        return_status_frame.columnconfigure(0, weight=1)

        for index, status in enumerate(RETURN_ORDER_STATUS_OPTIONS):
            ttk.Checkbutton(return_status_frame, text=status, variable=self.return_status_vars[status]).grid(
                row=index,
                column=0,
                sticky="w",
                pady=4,
            )

        button_row = ttk.Frame(parent)
        button_row.grid(row=5, column=0, columnspan=3, sticky="ew")
        button_row.columnconfigure(0, weight=1)
        button_row.columnconfigure(1, weight=1)

        self.run_button = ttk.Button(button_row, text="Chạy báo cáo", command=self._start_generation)
        self.run_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.open_button = ttk.Button(
            button_row,
            text="Mở thư mục kết quả",
            command=self._open_report_dir,
            state="disabled",
        )
        self.open_button.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        progress_frame = ttk.Frame(parent)
        progress_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        progress_frame.columnconfigure(0, weight=1)

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            orient="horizontal",
            mode="determinate",
            maximum=100,
            variable=self.progress_value_var,
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        ttk.Label(progress_frame, textvariable=self.progress_text_var, width=14, anchor="e").grid(
            row=0,
            column=1,
            padx=(12, 0),
        )

    def _build_update_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

        update_frame = ttk.LabelFrame(parent, text="Cập nhật phần mềm", padding=12)
        update_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        update_frame.columnconfigure(1, weight=1)

        ttk.Label(update_frame, textvariable=self.version_var).grid(
            row=0,
            column=0,
            columnspan=4,
            sticky="w",
            pady=(0, 10),
        )
        ttk.Label(update_frame, text="Nguồn cập nhật").grid(row=1, column=0, sticky="w")
        ttk.Entry(update_frame, textvariable=self.update_source_var).grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(12, 12),
        )
        self.save_update_button = ttk.Button(update_frame, text="Lưu nguồn", command=self._save_update_source)
        self.save_update_button.grid(row=1, column=2, sticky="ew", padx=(0, 8))
        self.check_update_button = ttk.Button(
            update_frame,
            text="Kiểm tra cập nhật",
            command=self._start_update_check,
        )
        self.check_update_button.grid(row=1, column=3, sticky="ew")
        self.install_update_button = ttk.Button(
            update_frame,
            text="Cài bản mới",
            command=self._start_update_install,
            state="disabled",
        )
        self.install_update_button.grid(row=2, column=3, sticky="ew", pady=(10, 0))
        ttk.Label(
            update_frame,
            textvariable=self.update_status_var,
            anchor="w",
            justify="left",
            wraplength=700,
        ).grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(10, 0),
        )
        if not supports_embedded_updates():
            ttk.Label(
                update_frame,
                text="Bản Windows vẫn chạy báo cáo bình thường. Phần tự cập nhật trong app chỉ có trên macOS.",
                anchor="w",
                justify="left",
                wraplength=700,
            ).grid(
                row=3,
                column=0,
                columnspan=4,
                sticky="ew",
                pady=(10, 0),
            )

        self.management_frame = ttk.LabelFrame(parent, text="Phân quyền tài khoản", padding=12)
        self.management_frame.grid(row=2, column=0, sticky="nsew")
        self.management_frame.columnconfigure(1, weight=1)
        self.management_frame.rowconfigure(0, weight=1)

        user_list_frame = ttk.Frame(self.management_frame)
        user_list_frame.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        user_list_frame.rowconfigure(1, weight=1)

        ttk.Label(user_list_frame, text="Danh sách tài khoản").grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.user_listbox = tk.Listbox(user_list_frame, exportselection=False, height=12)
        self.user_listbox.grid(row=1, column=0, sticky="ns")
        self.user_listbox.bind("<<ListboxSelect>>", self._handle_user_selection)
        self.new_user_button = ttk.Button(user_list_frame, text="Tạo mới", command=self._prepare_new_user_form)
        self.new_user_button.grid(row=2, column=0, sticky="ew", pady=(8, 0))

        form_frame = ttk.Frame(self.management_frame)
        form_frame.grid(row=0, column=1, sticky="nsew")
        form_frame.columnconfigure(1, weight=1)

        ttk.Label(form_frame, text="Tên đăng nhập").grid(row=0, column=0, sticky="w")
        self.management_username_entry = ttk.Entry(form_frame, textvariable=self.management_username_var)
        self.management_username_entry.grid(row=0, column=1, sticky="ew", padx=(12, 0), pady=(0, 8))

        ttk.Label(form_frame, text="Mật khẩu").grid(row=1, column=0, sticky="w")
        self.management_password_entry = ttk.Entry(form_frame, textvariable=self.management_password_var, show="*")
        self.management_password_entry.grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=(0, 8))

        ttk.Label(form_frame, text="Vai trò").grid(row=2, column=0, sticky="w")
        self.management_role_combo = ttk.Combobox(
            form_frame,
            textvariable=self.management_role_var,
            values=("user", "admin"),
            state="readonly",
        )
        self.management_role_combo.grid(row=2, column=1, sticky="ew", padx=(12, 0), pady=(0, 8))
        self.management_role_combo.bind("<<ComboboxSelected>>", self._handle_management_role_change)

        permissions_frame = ttk.LabelFrame(form_frame, text="Loại báo cáo được phép dùng", padding=12)
        permissions_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(4, 8))
        permissions_frame.columnconfigure(0, weight=1)
        permissions_frame.columnconfigure(1, weight=1)

        for index, (report_id, label) in enumerate(REPORT_OPTIONS):
            checkbox = ttk.Checkbutton(
                permissions_frame,
                text=label,
                variable=self.management_report_vars[report_id],
            )
            checkbox.grid(row=index // 2, column=index % 2, sticky="w", padx=(0, 12), pady=4)
            self.management_report_checkbuttons[report_id] = checkbox

        action_frame = ttk.Frame(form_frame)
        action_frame.grid(row=4, column=0, columnspan=2, sticky="ew")
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)
        self.save_user_button = ttk.Button(action_frame, text="Lưu tài khoản", command=self._save_managed_user)
        self.save_user_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.delete_user_button = ttk.Button(action_frame, text="Xóa tài khoản", command=self._delete_managed_user)
        self.delete_user_button.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(
            form_frame,
            text="Để trống mật khẩu nếu chỉ muốn sửa quyền mà không đổi mật khẩu.",
            anchor="w",
            justify="left",
            wraplength=680,
        ).grid(
            row=5,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(8, 4),
        )
        ttk.Label(
            form_frame,
            textvariable=self.management_status_var,
            anchor="w",
            justify="left",
            wraplength=680,
        ).grid(
            row=6,
            column=0,
            columnspan=2,
            sticky="ew",
        )

    def _choose_base_dir(self) -> None:
        selected = filedialog.askdirectory(
            title="Chọn thư mục công ty, ví dụ modules/abipha",
            initialdir=self.base_dir_var.get() or str(Path.home()),
        )
        if not selected:
            return

        self.base_dir_var.set(selected)

    def _show_login_page(self) -> None:
        self.current_view = "login"
        self.geometry("560x420")
        self.minsize(520, 380)
        self.login_show_password_var.set(False)
        self._toggle_login_password_visibility()
        self.login_page.tkraise()
        target_widget = self.login_password_entry if self.login_username_var.get().strip() else self.login_username_entry
        self.after(0, target_widget.focus_set)

    def _toggle_login_password_visibility(self) -> None:
        self.login_password_entry.configure(show="" if self.login_show_password_var.get() else "*")

    def _show_app_page(self) -> None:
        self.current_view = "app"
        self.geometry("980x920")
        self.minsize(860, 760)
        self.app_page.tkraise()
        self.after(0, lambda: self.notebook.select(self.report_tab))

    def _selected_report_ids(self) -> list[str]:
        return [report_id for report_id, _ in REPORT_OPTIONS if self.report_vars[report_id].get()]

    def _selected_management_report_ids(self) -> tuple[str, ...]:
        return tuple(
            report_id
            for report_id, _ in REPORT_OPTIONS
            if self.management_report_vars[report_id].get()
        )

    @staticmethod
    def _selected_statuses(status_vars: dict[str, tk.BooleanVar]) -> list[str]:
        return [status for status, variable in status_vars.items() if variable.get()]

    def _handle_report_selection_change(self) -> None:
        self._toggle_date_fields()
        self._sync_action_buttons()

    def _toggle_date_fields(self) -> None:
        state = "normal" if self.current_user and reports_require_dates(self._selected_report_ids()) else "disabled"
        self.start_entry.configure(state=state)
        self.end_entry.configure(state=state)

    def _select_all_reports(self) -> None:
        allowed_reports = set(self._accessible_report_ids())
        for report_id, _ in REPORT_OPTIONS:
            self.report_vars[report_id].set(report_id in allowed_reports)
        self._toggle_date_fields()
        self._sync_action_buttons()

    def _select_territory_reports(self) -> None:
        allowed_reports = set(self._accessible_report_ids())
        for report_id, _ in REPORT_OPTIONS:
            self.report_vars[report_id].set(
                report_id in allowed_reports and report_id in TERRITORY_OPTION_IDS
            )
        self._toggle_date_fields()
        self._sync_action_buttons()

    def _clear_reports(self) -> None:
        for variable in self.report_vars.values():
            variable.set(False)
        self._toggle_date_fields()
        self._sync_action_buttons()

    def _login(self) -> None:
        username = self.login_username_var.get().strip()
        password = self.login_password_var.get()
        if not username or not password:
            messagebox.showerror("Thiếu dữ liệu", "Cần nhập đủ tên đăng nhập và mật khẩu.", parent=self)
            return

        account = self.user_store.authenticate(username, password)
        if account is None:
            messagebox.showerror("Đăng nhập thất bại", "Tên đăng nhập hoặc mật khẩu không đúng.", parent=self)
            return

        self.login_password_var.set("")
        self._set_current_user(account)
        self.login_status_var.set(f"Đăng nhập thành công: {account.username}")
        self.status_var.set(f"Đã đăng nhập tài khoản {account.username}.")
        self._append_output(f"Đăng nhập thành công: {account.username}\n")
        self.notebook.select(self.report_tab)

    def _logout(self) -> None:
        if self.current_user is None:
            return

        username = self.current_user.username
        self.login_username_var.set(username)
        self.login_password_var.set("")
        self._set_current_user(None)
        self.login_status_var.set("Đã đăng xuất. Hãy đăng nhập lại để tiếp tục.")
        self.status_var.set("Đã đăng xuất.")
        self._append_output(f"Đã đăng xuất tài khoản {username}\n")

    def _set_current_user(self, account: UserAccount | None) -> None:
        self.current_user = account
        if account is None:
            self.current_user_var.set("Chưa đăng nhập.")
            self.user_status_var.set("Đăng nhập để dùng các loại báo cáo được cấp quyền.")
            self.management_status_var.set("Chỉ tài khoản admin mới được quản lý phân quyền người dùng.")
            for variable in self.report_vars.values():
                variable.set(False)
            self._show_login_page()
        else:
            self.current_user_var.set(
                f"Đang đăng nhập: {account.username} ({'admin' if account.is_admin else 'user'})"
            )
            if account.is_admin:
                self.user_status_var.set(
                    "Tài khoản admin được quyền xem toàn bộ loại báo cáo và quản lý phân quyền người dùng."
                )
                self.management_status_var.set("Chọn tài khoản bên trái để sửa, hoặc bấm Tạo mới để thêm user.")
            else:
                allowed_labels = ", ".join(REPORT_LABELS[report_id] for report_id in account.accessible_reports)
                self.user_status_var.set(f"Tài khoản này được phép chạy: {allowed_labels}")
                self.management_status_var.set("Chỉ tài khoản admin mới được quản lý phân quyền người dùng.")

            allowed_reports = set(account.accessible_reports)
            if not any(self.report_vars[report_id].get() for report_id in allowed_reports):
                for report_id in allowed_reports:
                    self.report_vars[report_id].set(True)
            self._show_app_page()

        self._apply_access_control()
        self._refresh_user_list(select_username=account.username if account else None)

    def _accessible_report_ids(self) -> tuple[str, ...]:
        if self.current_user is None:
            return ()
        return self.current_user.accessible_reports

    def _apply_access_control(self) -> None:
        allowed_reports = set(self._accessible_report_ids())
        self._refresh_report_visibility(allowed_reports)
        for report_id, checkbox in self.report_checkbuttons.items():
            has_access = self.current_user is not None and report_id in allowed_reports and not self._busy
            checkbox.configure(state="normal" if has_access else "disabled")
            if report_id not in allowed_reports:
                self.report_vars[report_id].set(False)

        self._toggle_management_visibility()
        self._toggle_management_permission_checkboxes()
        self._toggle_date_fields()
        self._sync_action_buttons()

    def _refresh_report_visibility(self, allowed_reports: set[str]) -> None:
        visible_report_ids = [
            report_id
            for report_id, _ in REPORT_OPTIONS
            if self.current_user is not None and report_id in allowed_reports
        ]

        for report_id, checkbox in self.report_checkbuttons.items():
            if report_id not in visible_report_ids:
                checkbox.grid_remove()

        for visible_index, report_id in enumerate(visible_report_ids):
            self.report_checkbuttons[report_id].grid(
                row=visible_index // 2,
                column=visible_index % 2,
                sticky="w",
                padx=(0, 12),
                pady=4,
            )

        if visible_report_ids:
            self.report_actions_frame.grid(
                row=(len(visible_report_ids) + 1) // 2,
                column=0,
                columnspan=2,
                sticky="w",
                pady=(8, 0),
            )
            return

        self.report_actions_frame.grid_remove()

    def _toggle_management_visibility(self) -> None:
        admin_session = self.current_user is not None and self.current_user.is_admin
        if admin_session:
            if not self.management_frame.winfo_manager():
                self.management_frame.grid(row=1, column=0, sticky="nsew")
            return

        if self.management_frame.winfo_manager():
            self.management_frame.grid_remove()

    def _start_generation(self) -> None:
        try:
            request = self._build_request()
        except ValueError as exc:
            messagebox.showerror("Thiếu dữ liệu", str(exc), parent=self)
            return

        self.notebook.select(self.report_tab)
        self._set_busy(True)
        self._last_progress_message = ""
        self._set_output("Bắt đầu tạo báo cáo...\n")
        self._set_progress(0, 1, "Đang khởi động tiến trình báo cáo...")

        worker = threading.Thread(target=self._run_generation, args=(request,), daemon=True)
        worker.start()

    def _build_request(self) -> ReportRequest:
        if self.current_user is None:
            raise ValueError("Vui lòng đăng nhập trước khi chạy báo cáo.")

        base_dir_text = self.base_dir_var.get().strip()
        if not base_dir_text:
            raise ValueError("Cần chọn thư mục dữ liệu công ty, ví dụ: .../modules/abipha")

        selected_data_dir = Path(base_dir_text).expanduser()
        if not selected_data_dir.exists():
            raise ValueError(f"Không tìm thấy thư mục dữ liệu: {selected_data_dir}")
        base_dir, company = resolve_company_context(selected_data_dir)

        selected_reports = tuple(self._selected_report_ids())
        if not selected_reports:
            raise ValueError("Cần chọn ít nhất một loại báo cáo")

        accessible_reports = self._accessible_report_ids()
        unauthorized_reports = [report_id for report_id in selected_reports if report_id not in accessible_reports]
        if unauthorized_reports:
            report_names = ", ".join(REPORT_LABELS[report_id] for report_id in unauthorized_reports)
            raise ValueError(f"Tài khoản hiện tại không được phép chạy các báo cáo: {report_names}")

        sales_order_statuses = tuple(self._selected_statuses(self.sales_status_vars))
        return_order_statuses = tuple(self._selected_statuses(self.return_status_vars))
        start_date = self.start_date_var.get().strip() or None
        end_date = self.end_date_var.get().strip() or None

        if reports_require_dates(selected_reports):
            if not start_date or not end_date:
                raise ValueError("Cần nhập đủ start date và end date theo định dạng YYYY-MM-DD")
            date.fromisoformat(start_date)
            date.fromisoformat(end_date)

        validate_required_company_files(CompanyPaths(base_dir=base_dir, company_code=company), selected_reports)

        return ReportRequest(
            company=company,
            base_dir=base_dir,
            start_date=start_date,
            end_date=end_date,
            sales_order_statuses=sales_order_statuses,
            return_order_statuses=return_order_statuses,
            selected_reports=selected_reports,
            authorized_reports=accessible_reports,
        )

    def _run_generation(self, request: ReportRequest) -> None:
        try:
            result = generate_reports(request, progress_callback=self._queue_progress_update)
        except Exception as exc:
            self._queue_ui_event("generation-failure", str(exc))
            return

        self._queue_ui_event("generation-success", result)

    def _queue_progress_update(self, current_step: int, total_steps: int, message: str) -> None:
        self._queue_ui_event("progress", current_step, total_steps, message)

    def _handle_success(self, result: ReportGenerationResult) -> None:
        self.last_result = result
        self._set_progress(1, 1, f"Hoàn tất tạo {len(result.generated_reports)} file báo cáo.")
        self._append_output("\n")
        self._append_output(f"Đã tạo {len(result.generated_reports)} file báo cáo:\n")
        for report in result.generated_reports:
            self._append_output(f"- {report.label}: {report.path}\n")
        self.status_var.set(f"Hoàn tất. Kết quả nằm trong: {result.report_dir}")
        self._set_busy(False)

    def _handle_failure(self, error_message: str) -> None:
        self.status_var.set("Chạy báo cáo thất bại.")
        self._set_busy(False)
        self._append_output(f"\nKhông thể tạo báo cáo:\n{error_message}\n")
        messagebox.showerror("Lỗi", error_message, parent=self)

    def _save_update_source(self) -> bool:
        if not supports_embedded_updates():
            messagebox.showinfo("Cập nhật phần mềm", UPDATE_ONLY_MACOS_MESSAGE, parent=self)
            return False

        source = self.update_source_var.get().strip()
        try:
            save_update_source(source)
        except OSError as exc:
            messagebox.showerror("Lỗi", f"Không thể lưu nguồn cập nhật:\n{exc}", parent=self)
            return False

        if source:
            message = f"Đã lưu nguồn cập nhật: {source}"
        else:
            message = "Đã xóa nguồn cập nhật đã lưu."

        self.update_status_var.set(message)
        self.status_var.set(message)
        self._append_output(f"{message}\n")
        return True

    def _start_update_check(self) -> None:
        if not supports_embedded_updates():
            messagebox.showinfo("Cập nhật phần mềm", UPDATE_ONLY_MACOS_MESSAGE, parent=self)
            return

        source = self.update_source_var.get().strip()
        if source and not self._save_update_source():
            return

        self.notebook.select(self.update_tab)
        self._set_busy(True)
        self._last_progress_message = ""
        self._append_output("\nKiểm tra cập nhật phần mềm...\n")
        self._set_progress(0, 1, "Đang kiểm tra cập nhật phần mềm...")
        worker = threading.Thread(target=self._run_update_check, args=(source or None,), daemon=True)
        worker.start()

    def _run_update_check(self, source: str | None) -> None:
        result = check_for_updates(source)
        self._queue_ui_event("update-check-result", result)

    def _handle_update_check_result(self, result: UpdateCheckResult) -> None:
        self.current_update = result.update if result.status == "available" else None
        self._set_progress(1, 1, result.message)
        self.update_status_var.set(result.message)
        self._set_busy(False)

        if result.status == "available" and result.update is not None:
            if result.update.published_at:
                self._append_output(f"Ngày phát hành: {result.update.published_at}\n")
            if result.update.notes:
                self._append_output(f"Ghi chú cập nhật:\n{result.update.notes}\n")

            if messagebox.askyesno(
                "Có bản cập nhật mới",
                f"{result.message}\n\nBạn có muốn tải và cài ngay bây giờ không?",
                parent=self,
            ):
                self._start_update_install()
            return

        if result.status == "error":
            messagebox.showerror("Lỗi cập nhật", result.message, parent=self)
            return

        if result.status == "missing-source":
            messagebox.showinfo("Cập nhật phần mềm", result.message, parent=self)

    def _start_update_install(self) -> None:
        if self.current_update is None:
            messagebox.showinfo("Cập nhật phần mềm", "Hiện chưa có bản cập nhật nào sẵn sàng để cài.", parent=self)
            return

        if not can_self_update():
            messagebox.showinfo(
                "Không thể tự cập nhật",
                "Tự cập nhật chỉ hoạt động khi bạn đang mở file DMS Reporting.app trên macOS.",
                parent=self,
            )
            return

        self.notebook.select(self.update_tab)
        self._set_busy(True)
        self._last_progress_message = ""
        self._append_output(f"\nBắt đầu cài bản cập nhật {self.current_update.version}...\n")
        self._set_progress(0, 4, f"Đang chuẩn bị cài bản {self.current_update.version}...")
        worker = threading.Thread(target=self._run_update_install, args=(self.current_update,), daemon=True)
        worker.start()

    def _run_update_install(self, update: UpdateInfo) -> None:
        try:
            prepared_update = download_and_prepare_update(update, progress_callback=self._queue_progress_update)
            log_path = install_prepared_update(prepared_update)
        except Exception as exc:
            self._queue_ui_event("update-install-failure", str(exc))
            return

        self._queue_ui_event("update-install-scheduled", update, log_path)

    def _handle_update_install_scheduled(self, update: UpdateInfo, log_path: Path) -> None:
        message = f"Đã tải xong bản {update.version}. Ứng dụng sẽ đóng để cài đặt bản mới."
        self.update_status_var.set(message)
        self._set_progress(4, 4, message)
        self._append_output(f"Log cài đặt: {log_path}\n")
        self._append_output("Sau khi cập nhật xong, hãy mở lại DMS Reporting.app.\n")
        messagebox.showinfo(
            "Đang cài cập nhật",
            f"{message}\n\nSau khi cài xong, hãy mở lại DMS Reporting.app.\n\nLog: {log_path}",
            parent=self,
        )
        self.after(300, self.destroy)

    def _handle_update_failure(self, error_message: str) -> None:
        self.update_status_var.set("Cài cập nhật thất bại.")
        self.status_var.set("Cài cập nhật thất bại.")
        self._set_busy(False)
        self._append_output(f"\nKhông thể cài cập nhật:\n{error_message}\n")
        messagebox.showerror("Lỗi cập nhật", error_message, parent=self)

    def _refresh_user_list(self, select_username: str | None = None) -> None:
        users = self.user_store.list_users()
        self._managed_usernames = [user.username for user in users]
        self.user_listbox.delete(0, tk.END)

        for user in users:
            role_label = "admin" if user.is_admin else "user"
            self.user_listbox.insert(tk.END, f"{user.username} ({role_label})")

        if not users:
            return

        username_to_select = select_username
        if username_to_select is None:
            existing_selection = self._selected_management_username()
            username_to_select = existing_selection

        if username_to_select in self._managed_usernames:
            index = self._managed_usernames.index(username_to_select)
            self.user_listbox.selection_clear(0, tk.END)
            self.user_listbox.selection_set(index)
            self.user_listbox.see(index)

    def _selected_management_username(self) -> str | None:
        selected_indexes = self.user_listbox.curselection()
        if not selected_indexes:
            return None
        selected_index = selected_indexes[0]
        if selected_index >= len(self._managed_usernames):
            return None
        return self._managed_usernames[selected_index]

    def _prepare_new_user_form(self) -> None:
        self.user_listbox.selection_clear(0, tk.END)
        self.management_username_var.set("")
        self.management_password_var.set("")
        self.management_role_var.set("user")
        for variable in self.management_report_vars.values():
            variable.set(False)
        if self.current_user and self.current_user.is_admin:
            self.management_status_var.set("Nhập thông tin tài khoản mới rồi bấm Lưu tài khoản.")
        self._toggle_management_permission_checkboxes()
        self._sync_action_buttons()

    def _handle_user_selection(self, _event=None) -> None:
        username = self._selected_management_username()
        if username is None:
            return
        self._load_managed_user(username)

    def _load_managed_user(self, username: str) -> None:
        account = self.user_store.get_user(username)
        if account is None:
            return

        self.management_username_var.set(account.username)
        self.management_password_var.set("")
        self.management_role_var.set(account.role)
        allowed_reports = set(account.accessible_reports)
        for report_id, _ in REPORT_OPTIONS:
            self.management_report_vars[report_id].set(report_id in allowed_reports)
        if self.current_user and self.current_user.is_admin:
            self.management_status_var.set(f"Đang sửa tài khoản: {account.username}")
        self._toggle_management_permission_checkboxes()
        self._sync_action_buttons()

    def _handle_management_role_change(self, _event=None) -> None:
        self._toggle_management_permission_checkboxes()
        self._sync_action_buttons()

    def _toggle_management_permission_checkboxes(self) -> None:
        admin_session = self.current_user is not None and self.current_user.is_admin and not self._busy
        if self.management_role_var.get().strip().lower() == "admin":
            for variable in self.management_report_vars.values():
                variable.set(True)
        permissions_editable = admin_session and self.management_role_var.get().strip().lower() != "admin"
        for checkbox in self.management_report_checkbuttons.values():
            checkbox.configure(state="normal" if permissions_editable else "disabled")

    def _save_managed_user(self) -> None:
        if self.current_user is None or not self.current_user.is_admin:
            messagebox.showerror("Không đủ quyền", "Chỉ tài khoản admin mới được lưu phân quyền người dùng.", parent=self)
            return

        username = self.management_username_var.get().strip()
        role = self.management_role_var.get().strip().lower()
        password = self.management_password_var.get()
        allowed_reports = self._selected_management_report_ids()

        try:
            account = self.user_store.save_user(
                username=username,
                role=role,
                allowed_reports=allowed_reports,
                password=password or None,
            )
        except ValueError as exc:
            messagebox.showerror("Không thể lưu tài khoản", str(exc), parent=self)
            return

        self.management_password_var.set("")
        self.management_status_var.set(f"Đã lưu tài khoản: {account.username}")
        self._append_output(f"Đã lưu phân quyền cho tài khoản {account.username}\n")
        self._refresh_user_list(select_username=account.username)
        self._load_managed_user(account.username)

        if self.current_user.username == account.username:
            self.current_user = account
            self._set_current_user(account)
        else:
            self._apply_access_control()

    def _delete_managed_user(self) -> None:
        if self.current_user is None or not self.current_user.is_admin:
            messagebox.showerror("Không đủ quyền", "Chỉ tài khoản admin mới được xóa user.", parent=self)
            return

        username = self._selected_management_username() or self.management_username_var.get().strip()
        if not username:
            messagebox.showerror("Thiếu dữ liệu", "Cần chọn tài khoản muốn xóa.", parent=self)
            return

        if username == self.current_user.username:
            messagebox.showerror("Không thể xóa", "Không thể xóa tài khoản đang đăng nhập.", parent=self)
            return

        if not messagebox.askyesno("Xóa tài khoản", f"Bạn có chắc muốn xóa tài khoản {username} không?", parent=self):
            return

        try:
            self.user_store.delete_user(username)
        except ValueError as exc:
            messagebox.showerror("Không thể xóa tài khoản", str(exc), parent=self)
            return

        self.management_status_var.set(f"Đã xóa tài khoản: {username}")
        self._append_output(f"Đã xóa tài khoản {username}\n")
        self._refresh_user_list()
        self._prepare_new_user_form()
        self._apply_access_control()

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._apply_access_control()

    def _queue_ui_event(self, event_name: str, *payload: object) -> None:
        self._ui_event_queue.put((event_name, payload))

    def _schedule_ui_event_poll(self) -> None:
        self._drain_ui_event_queue()
        try:
            self._ui_event_poll_after_id = self.after(50, self._schedule_ui_event_poll)
        except tk.TclError:
            self._ui_event_poll_after_id = None

    def _drain_ui_event_queue(self) -> None:
        while True:
            try:
                event_name, payload = self._ui_event_queue.get_nowait()
            except queue.Empty:
                return

            if event_name == "progress":
                current_step, total_steps, message = payload
                self._set_progress(int(current_step), int(total_steps), str(message))
                continue
            if event_name == "generation-success":
                self._handle_success(payload[0])
                continue
            if event_name == "generation-failure":
                self._handle_failure(str(payload[0]))
                continue
            if event_name == "update-check-result":
                self._handle_update_check_result(payload[0])
                continue
            if event_name == "update-install-scheduled":
                update, log_path = payload
                self._handle_update_install_scheduled(update, log_path)
                continue
            if event_name == "update-install-failure":
                self._handle_update_failure(str(payload[0]))
                continue

    def _sync_action_buttons(self) -> None:
        has_authenticated_user = self.current_user is not None
        allowed_reports = set(self._accessible_report_ids())
        has_territory_access = any(report_id in TERRITORY_OPTION_IDS for report_id in allowed_reports)
        admin_session = self.current_user is not None and self.current_user.is_admin
        report_dir = self._resolve_report_dir() if has_authenticated_user else None

        self.run_button.configure(
            state="normal"
            if has_authenticated_user and not self._busy and bool(self._selected_report_ids())
            else "disabled"
        )
        self.select_all_button.configure(
            state="normal" if has_authenticated_user and not self._busy and bool(allowed_reports) else "disabled"
        )
        self.territory_reports_button.configure(
            state="normal" if has_authenticated_user and not self._busy and has_territory_access else "disabled"
        )
        self.clear_reports_button.configure(state="normal" if has_authenticated_user and not self._busy else "disabled")
        self.login_button.configure(state="disabled" if self._busy else "normal")
        self.login_show_password_button.configure(state="disabled" if self._busy else "normal")
        self.login_username_entry.configure(state="disabled" if self._busy else "normal")
        self.login_password_entry.configure(state="disabled" if self._busy else "normal")
        self.logout_button.configure(state="disabled" if self._busy or not has_authenticated_user else "normal")
        update_controls_enabled = supports_embedded_updates() and not self._busy
        self.save_update_button.configure(state="normal" if update_controls_enabled else "disabled")
        self.check_update_button.configure(state="normal" if update_controls_enabled else "disabled")
        self.install_update_button.configure(
            state="normal" if update_controls_enabled and self.current_update is not None else "disabled"
        )
        self.open_button.configure(state="disabled" if self._busy or report_dir is None else "normal")
        self.new_user_button.configure(state="normal" if admin_session and not self._busy else "disabled")
        self.save_user_button.configure(state="normal" if admin_session and not self._busy else "disabled")
        self.delete_user_button.configure(
            state="normal"
            if admin_session
            and not self._busy
            and bool(self._selected_management_username())
            and self._selected_management_username() != self.current_user.username
            else "disabled"
        )
        self.management_username_entry.configure(state="normal" if admin_session and not self._busy else "disabled")
        self.management_password_entry.configure(state="normal" if admin_session and not self._busy else "disabled")
        self.management_role_combo.configure(state="readonly" if admin_session and not self._busy else "disabled")
        self.user_listbox.configure(state="normal" if admin_session and not self._busy else "disabled")

    def _set_output(self, content: str) -> None:
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", content)
        self.output_text.configure(state="disabled")

    def _append_output(self, content: str) -> None:
        self.output_text.configure(state="normal")
        self.output_text.insert(tk.END, content)
        self.output_text.see(tk.END)
        self.output_text.configure(state="disabled")

    def _set_progress(self, current_step: int, total_steps: int, message: str) -> None:
        safe_total = max(total_steps, 1)
        safe_current = min(max(current_step, 0), safe_total)
        percent = (safe_current / safe_total) * 100
        self.progress_bar.configure(maximum=safe_total)
        self.progress_value_var.set(safe_current)
        self.progress_text_var.set(f"{percent:.0f}% ({safe_current}/{safe_total})")
        self.status_var.set(message)
        if message != self._last_progress_message:
            self._append_output(f"{message}\n")
            self._last_progress_message = message

    def _open_report_dir(self) -> None:
        report_dir = self._resolve_report_dir()
        if report_dir is None:
            messagebox.showerror(
                "Thiếu dữ liệu",
                "Không xác định được thư mục kết quả. Hãy kiểm tra lại thư mục dữ liệu công ty.",
                parent=self,
            )
            return

        if sys.platform == "darwin":
            subprocess.run(["open", str(report_dir)], check=False)
            return
        if sys.platform == "win32":
            startfile = getattr(os, "startfile", None)
            if startfile is not None:
                startfile(str(report_dir))
                return
        if sys.platform.startswith("linux"):
            subprocess.run(["xdg-open", str(report_dir)], check=False)
            return

        messagebox.showinfo("Đường dẫn kết quả", str(report_dir), parent=self)

    def _resolve_report_dir(self) -> Path | None:
        if self.last_result is not None:
            return self.last_result.report_dir

        base_dir_text = self.base_dir_var.get().strip()
        if not base_dir_text:
            return None

        try:
            base_dir, company_code = resolve_company_context(Path(base_dir_text).expanduser())
        except ValueError:
            return None

        return CompanyPaths(base_dir=base_dir, company_code=company_code).ensure_report_dir()


def launch() -> None:
    app = MacOSReportApp()
    app.mainloop()


if __name__ == "__main__":
    launch()
