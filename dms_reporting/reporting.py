from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Iterable

from dms_reporting.config import (
    CompanyFileSpec,
    CompanyPaths,
    ReportSettings,
    format_company_file_requirement,
    missing_company_files,
)
from dms_reporting.constants import DEFAULT_RETURN_ORDER_STATUSES, DEFAULT_SALES_ORDER_STATUSES
from dms_reporting.repositories.excel_repository import ExcelCRMRepository
from dms_reporting.services.sales_report_service import SalesReportService

TERRITORY_BUNDLE_REPORT_ID = "invoice-territory"
TERRITORY_BUNDLE_REPORT_LABEL = "Chỉ phân tuyến Hoá đơn"
COMBINED_TERRITORY_REPORT_ID = "combined-territory"
COMBINED_TERRITORY_REPORT_LABEL = "Báo cáo phân tuyến KH Hoá đơn + Giao hàng"
TERRITORY_REPORT_LABELS: dict[str, str] = {
    "correct-territory": "Báo cáo khách hàng gán đúng địa bàn",
    "territory": "Báo cáo khách hàng sai địa bàn",
    "inactive-territory": "Báo cáo nhân viên đã nghỉ còn trong phân tuyến",
    "inactive-customer": "Báo cáo khách hàng còn gán cho nhân viên đã nghỉ việc",
}
TERRITORY_REPORT_IDS: tuple[str, ...] = tuple(TERRITORY_REPORT_LABELS)
SHIPPING_TERRITORY_REPORT_LABELS: dict[str, str] = {
    "correct-shipping-territory": "Báo cáo khách hàng gán đúng địa bàn Giao hàng",
    "shipping-territory": "Báo cáo khách hàng sai địa bàn Giao hàng",
}
SHIPPING_TERRITORY_REPORT_IDS: tuple[str, ...] = tuple(SHIPPING_TERRITORY_REPORT_LABELS)

REPORT_OPTIONS: tuple[tuple[str, str], ...] = (
    ("summary", "Báo cáo doanh số khách hàng"),
    ("detail", "Báo cáo doanh số nhóm sản phẩm"),
    ("employee-product", "Báo cáo doanh thu sản lượng sản phẩm theo nhân viên"),
    ("first-sales", "Báo cáo khách hàng phát sinh doanh số lần đầu"),
    (TERRITORY_BUNDLE_REPORT_ID, TERRITORY_BUNDLE_REPORT_LABEL),
    (COMBINED_TERRITORY_REPORT_ID, COMBINED_TERRITORY_REPORT_LABEL),
    ("correct-shipping-territory", "Báo cáo khách hàng gán đúng địa bàn Giao hàng"),
    ("shipping-territory", "Báo cáo khách hàng sai địa bàn Giao hàng"),
)
REPORT_LABELS: dict[str, str] = dict(REPORT_OPTIONS) | TERRITORY_REPORT_LABELS | SHIPPING_TERRITORY_REPORT_LABELS
ALL_REPORT_IDS: tuple[str, ...] = tuple(report_id for report_id, _ in REPORT_OPTIONS)
SUPPORTED_REPORT_IDS: tuple[str, ...] = ALL_REPORT_IDS + TERRITORY_REPORT_IDS
TERRITORY_OPTION_IDS: tuple[str, ...] = (
    TERRITORY_BUNDLE_REPORT_ID,
    COMBINED_TERRITORY_REPORT_ID,
) + SHIPPING_TERRITORY_REPORT_IDS
DATE_REQUIRED_REPORT_IDS = frozenset({"summary", "detail", "employee-product", "first-sales"})
ProgressCallback = Callable[[int, int, str], None]
REPORT_REQUIRED_FILE_KEYS: dict[str, tuple[str, ...]] = {
    "summary": (
        "customers",
        "products",
        "purchase_orders",
        "sales_orders",
        "return_purchase_orders",
        "return_sales_orders",
    ),
    "detail": (
        "customers",
        "products",
        "purchase_orders",
        "sales_orders",
        "return_purchase_orders",
        "return_sales_orders",
    ),
    "employee-product": (
        "customers",
        "products",
        "purchase_orders",
        "sales_orders",
        "return_purchase_orders",
        "return_sales_orders",
    ),
    "first-sales": (
        "customers",
        "products",
        "purchase_orders",
        "sales_orders",
    ),
    "correct-territory": (
        "customers",
        "employees",
        "territory",
    ),
    "territory": (
        "customers",
        "employees",
        "territory",
    ),
    "inactive-territory": (
        "employees",
        "territory",
    ),
    "inactive-customer": (
        "customers",
        "employees",
        "territory",
    ),
    COMBINED_TERRITORY_REPORT_ID: (
        "customers",
        "employees",
        "territory",
    ),
    "correct-shipping-territory": (
        "customers",
        "employees",
        "territory",
    ),
    "shipping-territory": (
        "customers",
        "employees",
        "territory",
    ),
}


@dataclass(slots=True)
class ReportRequest:
    company: str
    base_dir: Path
    start_date: str | None = None
    end_date: str | None = None
    sales_order_statuses: tuple[str, ...] | list[str] | None = None
    return_order_statuses: tuple[str, ...] | list[str] | None = None
    output: Path | None = None
    detail_output: Path | None = None
    employee_product_output: Path | None = None
    first_sales_output: Path | None = None
    correct_territory_output: Path | None = None
    territory_output: Path | None = None
    inactive_territory_output: Path | None = None
    inactive_customer_output: Path | None = None
    combined_territory_output: Path | None = None
    correct_shipping_territory_output: Path | None = None
    shipping_territory_output: Path | None = None
    selected_reports: tuple[str, ...] | list[str] | None = None
    authorized_reports: tuple[str, ...] | list[str] | None = None
    territory_only: bool = False


@dataclass(frozen=True, slots=True)
class GeneratedReport:
    label: str
    path: Path


@dataclass(slots=True)
class ReportGenerationResult:
    report_dir: Path
    generated_reports: list[GeneratedReport]


def normalize_report_ids(report_ids: Iterable[str]) -> tuple[str, ...]:
    normalized = tuple(dict.fromkeys(report_id.strip() for report_id in report_ids if report_id.strip()))
    invalid_ids = [report_id for report_id in normalized if report_id not in SUPPORTED_REPORT_IDS]
    if invalid_ids:
        valid_options = ", ".join(ALL_REPORT_IDS)
        invalid_value = ", ".join(invalid_ids)
        raise ValueError(f"Report không hợp lệ: {invalid_value}. Các giá trị hợp lệ: {valid_options}")
    return normalized


def collapse_report_ids(report_ids: Iterable[str]) -> tuple[str, ...]:
    collapsed: list[str] = []
    for report_id in normalize_report_ids(report_ids):
        canonical_report_id = (
            TERRITORY_BUNDLE_REPORT_ID
            if report_id in TERRITORY_REPORT_IDS
            else report_id
        )
        if canonical_report_id not in collapsed:
            collapsed.append(canonical_report_id)
    return tuple(collapsed)


def expand_report_ids(report_ids: Iterable[str]) -> tuple[str, ...]:
    expanded: list[str] = []
    for report_id in normalize_report_ids(report_ids):
        expanded_report_ids = TERRITORY_REPORT_IDS if report_id == TERRITORY_BUNDLE_REPORT_ID else (report_id,)
        for expanded_report_id in expanded_report_ids:
            if expanded_report_id not in expanded:
                expanded.append(expanded_report_id)
    return tuple(expanded)


def resolve_selected_reports(request: ReportRequest) -> tuple[str, ...]:
    if request.selected_reports is not None:
        selected_reports = normalize_report_ids(request.selected_reports)
    elif request.territory_only:
        selected_reports = TERRITORY_OPTION_IDS
    else:
        selected_reports = ALL_REPORT_IDS

    if not selected_reports:
        raise ValueError("Cần chọn ít nhất một loại báo cáo để xuất file")

    return selected_reports


def reports_require_dates(report_ids: Iterable[str]) -> bool:
    return any(report_id in DATE_REQUIRED_REPORT_IDS for report_id in report_ids)


def required_company_file_keys(report_ids: Iterable[str]) -> tuple[str, ...]:
    required_keys: list[str] = []
    for report_id in normalize_report_ids(report_ids):
        for file_key in REPORT_REQUIRED_FILE_KEYS.get(report_id, ()):
            if file_key not in required_keys:
                required_keys.append(file_key)
    return tuple(required_keys)


def collect_missing_required_company_files(
    company_paths: CompanyPaths,
    report_ids: Iterable[str],
) -> list[CompanyFileSpec]:
    return missing_company_files(company_paths.company_dir, required_company_file_keys(report_ids))


def build_missing_company_files_message(company_paths: CompanyPaths, report_ids: Iterable[str]) -> str | None:
    missing_specs = collect_missing_required_company_files(company_paths, report_ids)
    if not missing_specs:
        return None

    lines = [f"Thiếu file Excel để tạo báo cáo trong thư mục: {company_paths.company_dir}"]
    for spec in missing_specs:
        lines.append(f"- {spec.label}: cần bổ sung {format_company_file_requirement(spec)}")
    return "\n".join(lines)


def validate_required_company_files(company_paths: CompanyPaths, report_ids: Iterable[str]) -> None:
    message = build_missing_company_files_message(company_paths, report_ids)
    if message is not None:
        raise ValueError(message)


def resolve_authorized_reports(request: ReportRequest) -> tuple[str, ...] | None:
    if request.authorized_reports is None:
        return None
    return collapse_report_ids(request.authorized_reports)


def resolve_sales_order_statuses(request: ReportRequest) -> list[str]:
    if request.sales_order_statuses is None:
        return list(DEFAULT_SALES_ORDER_STATUSES)
    return [status.strip() for status in request.sales_order_statuses if status.strip()]


def resolve_return_order_statuses(request: ReportRequest) -> list[str]:
    if request.return_order_statuses is None:
        selected_statuses = list(DEFAULT_RETURN_ORDER_STATUSES)
    else:
        selected_statuses = [status.strip() for status in request.return_order_statuses if status.strip()]

    expanded_statuses: list[str] = []
    for status in selected_statuses:
        if status == "Bản nháp":
            expanded_statuses.extend(["Bản nháp", "Bản pháp"])
            continue
        if status == "Bản pháp":
            expanded_statuses.extend(["Bản nháp", "Bản pháp"])
            continue
        expanded_statuses.append(status)

    return list(dict.fromkeys(expanded_statuses))


def available_companies(base_dir: Path) -> list[str]:
    modules_dir = base_dir / "modules"
    if not modules_dir.exists():
        return []

    return sorted(
        path.name
        for path in modules_dir.iterdir()
        if path.is_dir() and not path.name.startswith(".") and path.name != "__pycache__"
    )


def generate_reports(
    request: ReportRequest,
    *,
    progress_callback: ProgressCallback | None = None,
) -> ReportGenerationResult:
    company_code = request.company.strip()
    if not company_code:
        raise ValueError("Company code is required")

    selected_reports = resolve_selected_reports(request)
    expanded_selected_reports = expand_report_ids(selected_reports)
    authorized_reports = resolve_authorized_reports(request)
    if authorized_reports is not None:
        unauthorized_reports = [
            report_id
            for report_id in selected_reports
            if collapse_report_ids((report_id,))[0] not in authorized_reports
        ]
        if unauthorized_reports:
            report_names = ", ".join(REPORT_LABELS[report_id] for report_id in unauthorized_reports)
            raise ValueError(f"Tài khoản hiện tại không được phép chạy các báo cáo: {report_names}")
    total_steps = 1 + ExcelCRMRepository.LOAD_DATASET_STEP_COUNT + (2 * len(expanded_selected_reports))
    current_step = 0
    current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang kiểm tra tham số báo cáo...")
    base_dir = request.base_dir.expanduser().resolve()
    company_paths = CompanyPaths(base_dir=base_dir, company_code=company_code)
    if not company_paths.company_dir.exists():
        raise ValueError(f"Không tìm thấy thư mục công ty: {company_paths.company_dir}")

    if reports_require_dates(selected_reports):
        if not request.start_date or not request.end_date:
            raise ValueError("Cần nhập start date và end date cho các báo cáo doanh số theo định dạng YYYY-MM-DD")
        start_date = date.fromisoformat(request.start_date)
        end_date = date.fromisoformat(request.end_date)
        if start_date > end_date:
            raise ValueError("Start date phải nhỏ hơn hoặc bằng end date")

    validate_required_company_files(company_paths, expanded_selected_reports)

    repository = ExcelCRMRepository(company_paths)
    if progress_callback is None:
        dataset = repository.load_dataset()
        current_step += ExcelCRMRepository.LOAD_DATASET_STEP_COUNT
    else:
        repository_step = 0

        def repository_progress(message: str) -> None:
            nonlocal repository_step
            repository_step += 1
            progress_callback(current_step + repository_step, total_steps, message)

        dataset = repository.load_dataset(progress_callback=repository_progress)
        current_step += repository_step

    service = SalesReportService(dataset)
    report_dir = company_paths.ensure_report_dir()
    sales_order_statuses = resolve_sales_order_statuses(request)
    return_order_statuses = resolve_return_order_statuses(request)

    generated_reports: list[GeneratedReport] = []

    if "correct-territory" in expanded_selected_reports:
        current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang tạo báo cáo khách hàng gán đúng địa bàn...")
        correct_territory_report_df = service.build_correct_territory_assignments_report()
        correct_territory_output_path = (
            request.correct_territory_output.resolve()
            if request.correct_territory_output
            else report_dir / f"Báo cáo khách hàng gán đúng địa bàn {company_code}.xlsx"
        )
        current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang ghi file báo cáo khách hàng gán đúng địa bàn...")
        service.write_flat_report(
            correct_territory_report_df,
            correct_territory_output_path,
            sheet_name="Đúng địa bàn",
        )
        generated_reports.append(
            GeneratedReport(label=REPORT_LABELS["correct-territory"], path=correct_territory_output_path)
        )

    if "territory" in expanded_selected_reports:
        current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang tạo báo cáo khách hàng sai địa bàn...")
        territory_report_df = service.build_wrong_territory_assignments_report()
        territory_output_path = request.territory_output.resolve() if request.territory_output else report_dir / f"Báo cáo khách hàng sai địa bàn {company_code}.xlsx"
        current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang ghi file báo cáo khách hàng sai địa bàn...")
        service.write_flat_report(territory_report_df, territory_output_path, sheet_name="Sai địa bàn")
        generated_reports.append(GeneratedReport(label=REPORT_LABELS["territory"], path=territory_output_path))

    if "inactive-territory" in expanded_selected_reports:
        current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang tạo báo cáo nhân viên đã nghỉ còn trong phân tuyến...")
        inactive_territory_report_df = service.build_inactive_employee_territories_report()
        inactive_territory_output_path = (
            request.inactive_territory_output.resolve()
            if request.inactive_territory_output
            else report_dir / f"Báo cáo nhân viên đã nghỉ còn trong phân tuyến {company_code}.xlsx"
        )
        current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang ghi file báo cáo nhân viên đã nghỉ còn trong phân tuyến...")
        service.write_flat_report(
            inactive_territory_report_df,
            inactive_territory_output_path,
            sheet_name="Nhân viên đã nghỉ",
        )
        generated_reports.append(
            GeneratedReport(label=REPORT_LABELS["inactive-territory"], path=inactive_territory_output_path)
        )

    if "inactive-customer" in expanded_selected_reports:
        current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang tạo báo cáo khách hàng còn gán cho nhân viên đã nghỉ việc...")
        inactive_customer_report_df = service.build_customers_assigned_to_inactive_employees_report()
        inactive_customer_output_path = (
            request.inactive_customer_output.resolve()
            if request.inactive_customer_output
            else report_dir / f"Báo cáo khách hàng còn gán cho nhân viên đã nghỉ việc {company_code}.xlsx"
        )
        current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang ghi file báo cáo khách hàng còn gán cho nhân viên đã nghỉ việc...")
        service.write_flat_report(
            inactive_customer_report_df,
            inactive_customer_output_path,
            sheet_name="Khách hàng gán NV nghỉ",
        )
        generated_reports.append(
            GeneratedReport(label=REPORT_LABELS["inactive-customer"], path=inactive_customer_output_path)
        )

    if COMBINED_TERRITORY_REPORT_ID in expanded_selected_reports:
        current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang tạo báo cáo phân tuyến khách hàng tổng hợp...")
        combined_territory_reports = service.build_combined_customer_territory_report_sheets()
        combined_territory_output_path = (
            request.combined_territory_output.resolve()
            if request.combined_territory_output
            else report_dir / f"Báo cáo phân tuyến khách hàng Hoá đơn và Giao hàng {company_code}.xlsx"
        )
        current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang ghi file báo cáo phân tuyến khách hàng tổng hợp...")
        service.write_multi_sheet_report(combined_territory_reports, combined_territory_output_path)
        generated_reports.append(
            GeneratedReport(
                label=REPORT_LABELS[COMBINED_TERRITORY_REPORT_ID],
                path=combined_territory_output_path,
            )
        )

    if "correct-shipping-territory" in expanded_selected_reports:
        current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang tạo báo cáo khách hàng gán đúng địa bàn Giao hàng...")
        correct_shipping_territory_report_df = service.build_correct_shipping_territory_assignments_report()
        correct_shipping_territory_output_path = (
            request.correct_shipping_territory_output.resolve()
            if request.correct_shipping_territory_output
            else report_dir / f"Báo cáo khách hàng gán đúng địa bàn Giao hàng {company_code}.xlsx"
        )
        current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang ghi file báo cáo khách hàng gán đúng địa bàn Giao hàng...")
        service.write_flat_report(
            correct_shipping_territory_report_df,
            correct_shipping_territory_output_path,
            sheet_name="Đúng địa bàn GH",
        )
        generated_reports.append(
            GeneratedReport(
                label=REPORT_LABELS["correct-shipping-territory"],
                path=correct_shipping_territory_output_path,
            )
        )

    if "shipping-territory" in expanded_selected_reports:
        current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang tạo báo cáo khách hàng sai địa bàn Giao hàng...")
        shipping_territory_report_df = service.build_wrong_shipping_territory_assignments_report()
        shipping_territory_output_path = (
            request.shipping_territory_output.resolve()
            if request.shipping_territory_output
            else report_dir / f"Báo cáo khách hàng sai địa bàn Giao hàng {company_code}.xlsx"
        )
        current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang ghi file báo cáo khách hàng sai địa bàn Giao hàng...")
        service.write_flat_report(
            shipping_territory_report_df,
            shipping_territory_output_path,
            sheet_name="Sai địa bàn GH",
        )
        generated_reports.append(
            GeneratedReport(
                label=REPORT_LABELS["shipping-territory"],
                path=shipping_territory_output_path,
            )
        )

    if reports_require_dates(selected_reports):
        settings = ReportSettings(
            start_date=request.start_date,
            end_date=request.end_date,
            sales_order_statuses=sales_order_statuses,
            return_order_statuses=return_order_statuses,
        )

        if "summary" in selected_reports:
            current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang tạo báo cáo doanh số khách hàng...")
            report_df = service.build_customer_sales_report(settings)
            output_path = request.output.resolve() if request.output else report_dir / f"Báo cáo doanh số khách hàng {company_code}.xlsx"
            current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang ghi file báo cáo doanh số khách hàng...")
            service.write_customer_sales_report(report_df, output_path)
            generated_reports.append(GeneratedReport(label=REPORT_LABELS["summary"], path=output_path))

        if "detail" in selected_reports:
            current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang tạo báo cáo doanh số nhóm sản phẩm...")
            detail_report_df = service.build_customer_sales_detail_report(settings)
            detail_output_path = (
                request.detail_output.resolve()
                if request.detail_output
                else report_dir / f"Báo cáo doanh số nhóm sản phẩm {company_code}.xlsx"
            )
            current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang ghi file báo cáo doanh số nhóm sản phẩm...")
            service.write_customer_sales_report(detail_report_df, detail_output_path)
            generated_reports.append(GeneratedReport(label=REPORT_LABELS["detail"], path=detail_output_path))

        if "employee-product" in selected_reports:
            current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang tạo báo cáo doanh thu sản lượng theo nhân viên...")
            employee_product_reports = service.build_employee_product_sales_monthly_reports(settings)
            employee_product_output_path = (
                request.employee_product_output.resolve()
                if request.employee_product_output
                else report_dir / f"Báo cáo doanh thu sản lượng sản phẩm theo nhân viên {company_code}.xlsx"
            )
            current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang ghi file báo cáo doanh thu sản lượng theo nhân viên...")
            service.write_multi_sheet_report(employee_product_reports, employee_product_output_path)
            generated_reports.append(
                GeneratedReport(
                    label=REPORT_LABELS["employee-product"],
                    path=employee_product_output_path,
                )
            )

        if "first-sales" in selected_reports:
            current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang tạo báo cáo khách hàng phát sinh doanh số lần đầu...")
            first_sales_reports = service.build_first_sales_customers_monthly_reports(settings)
            first_sales_output_path = (
                request.first_sales_output.resolve()
                if request.first_sales_output
                else report_dir / f"Báo cáo khách hàng phát sinh doanh số lần đầu {company_code}.xlsx"
            )
            current_step = _advance_progress(progress_callback, current_step, total_steps, "Đang ghi file báo cáo khách hàng phát sinh doanh số lần đầu...")
            service.write_multi_sheet_report(first_sales_reports, first_sales_output_path)
            generated_reports.append(GeneratedReport(label=REPORT_LABELS["first-sales"], path=first_sales_output_path))

    return ReportGenerationResult(report_dir=report_dir, generated_reports=generated_reports)


def _advance_progress(
    progress_callback: ProgressCallback | None,
    current_step: int,
    total_steps: int,
    message: str,
) -> int:
    next_step = current_step + 1
    if progress_callback is not None:
        progress_callback(next_step, total_steps, message)
    return next_step
