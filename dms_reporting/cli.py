from __future__ import annotations

import argparse
from pathlib import Path
import sys

from dms_reporting.config import CompanyPaths, ReportSettings
from dms_reporting.repositories.excel_repository import ExcelCRMRepository
from dms_reporting.services.sales_report_service import SalesReportService


def _default_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate customer sales report from MISA CRM Excel exports")
    parser.add_argument("--company", required=True, help="Company code under modules/, for example: abipha")
    parser.add_argument("--start-date", help="Report start date, format YYYY-MM-DD")
    parser.add_argument("--end-date", help="Report end date, format YYYY-MM-DD")
    parser.add_argument(
        "--base-dir",
        default=str(_default_base_dir()),
        help="Project base directory containing modules/",
    )
    parser.add_argument("--output", help="Optional explicit output Excel path")
    parser.add_argument("--detail-output", help="Optional explicit output Excel path for product-group detail report")
    parser.add_argument("--first-sales-output", help="Optional explicit output Excel path for first-sales customers report")
    parser.add_argument("--territory-output", help="Optional explicit output Excel path for wrong territory assignments report")
    parser.add_argument("--inactive-territory-output", help="Optional explicit output Excel path for inactive employees still appearing in territory assignments")
    parser.add_argument("--inactive-customer-output", help="Optional explicit output Excel path for customers still assigned to inactive employees")
    parser.add_argument("--territory-only", action="store_true", help="Only generate territory-related reports")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.territory_only and (not args.start_date or not args.end_date):
        parser.error("--start-date and --end-date are required unless --territory-only is used")

    company_paths = CompanyPaths(base_dir=Path(args.base_dir).resolve(), company_code=args.company)

    repository = ExcelCRMRepository(company_paths)
    dataset = repository.load_dataset()
    service = SalesReportService(dataset)
    report_dir = company_paths.ensure_report_dir()

    territory_report_df = service.build_wrong_territory_assignments_report()
    inactive_territory_report_df = service.build_inactive_employee_territories_report()
    inactive_customer_report_df = service.build_customers_assigned_to_inactive_employees_report()
    territory_output_path = (
        Path(args.territory_output).resolve()
        if args.territory_output
        else report_dir / f"Báo cáo khách hàng sai địa bàn {args.company}.xlsx"
    )
    inactive_territory_output_path = (
        Path(args.inactive_territory_output).resolve()
        if args.inactive_territory_output
        else report_dir / f"Báo cáo nhân viên đã nghỉ còn trong phân tuyến {args.company}.xlsx"
    )
    inactive_customer_output_path = (
        Path(args.inactive_customer_output).resolve()
        if args.inactive_customer_output
        else report_dir / f"Báo cáo khách hàng còn gán cho nhân viên đã nghỉ việc {args.company}.xlsx"
    )
    service.write_flat_report(territory_report_df, territory_output_path, sheet_name="Sai địa bàn")
    service.write_flat_report(
        inactive_territory_report_df,
        inactive_territory_output_path,
        sheet_name="Nhân viên đã nghỉ",
    )
    service.write_flat_report(
        inactive_customer_report_df,
        inactive_customer_output_path,
        sheet_name="Khách hàng gán NV nghỉ",
    )
    print(f"Generated territory report: {territory_output_path}")
    print(f"Generated inactive territory report: {inactive_territory_output_path}")
    print(f"Generated inactive customer report: {inactive_customer_output_path}")

    if args.territory_only:
        return 0

    settings = ReportSettings(start_date=args.start_date, end_date=args.end_date)
    report_df = service.build_customer_sales_report(settings)
    detail_report_df = service.build_customer_sales_detail_report(settings)
    first_sales_reports = service.build_first_sales_customers_monthly_reports(settings)

    output_path = Path(args.output).resolve() if args.output else report_dir / f"Báo cáo doanh số khách hàng {args.company}.xlsx"
    detail_output_path = (
        Path(args.detail_output).resolve()
        if args.detail_output
        else report_dir / f"Báo cáo doanh số nhóm sản phẩm {args.company}.xlsx"
    )
    first_sales_output_path = (
        Path(args.first_sales_output).resolve()
        if args.first_sales_output
        else report_dir / f"Báo cáo khách hàng phát sinh doanh số lần đầu {args.company}.xlsx"
    )
    service.write_customer_sales_report(report_df, output_path)
    service.write_customer_sales_report(detail_report_df, detail_output_path)
    service.write_multi_sheet_report(first_sales_reports, first_sales_output_path)
    print(f"Generated report: {output_path}")
    print(f"Generated detail report: {detail_output_path}")
    print(f"Generated first sales report: {first_sales_output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
