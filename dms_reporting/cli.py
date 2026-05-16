from __future__ import annotations

import argparse
from pathlib import Path

from dms_reporting.constants import DEFAULT_RETURN_ORDER_STATUSES, DEFAULT_SALES_ORDER_STATUSES
from dms_reporting.reporting import ALL_REPORT_IDS, ReportRequest, generate_reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate customer sales report from MISA CRM Excel exports")
    parser.add_argument("--company", required=True, help="Company code under modules/, for example: abipha")
    parser.add_argument("--start-date", help="Report start date, format YYYY-MM-DD")
    parser.add_argument("--end-date", help="Report end date, format YYYY-MM-DD")
    parser.add_argument(
        "--base-dir",
        default=str(Path(__file__).resolve().parent.parent),
        help="Project base directory containing modules/",
    )
    parser.add_argument("--output", help="Optional explicit output Excel path")
    parser.add_argument("--detail-output", help="Optional explicit output Excel path for product-group detail report")
    parser.add_argument("--employee-product-output", help="Optional explicit output Excel path for employee-product sales report")
    parser.add_argument("--first-sales-output", help="Optional explicit output Excel path for first-sales customers report")
    parser.add_argument("--correct-territory-output", help="Optional explicit output Excel path for correct territory assignments report")
    parser.add_argument("--territory-output", help="Optional explicit output Excel path for wrong territory assignments report")
    parser.add_argument("--inactive-territory-output", help="Optional explicit output Excel path for inactive employees still appearing in territory assignments")
    parser.add_argument("--inactive-customer-output", help="Optional explicit output Excel path for customers still assigned to inactive employees")
    parser.add_argument("--combined-territory-output", help="Optional explicit output Excel path for combined invoice and shipping territory report")
    parser.add_argument("--correct-shipping-territory-output", help="Optional explicit output Excel path for correct shipping territory assignments report")
    parser.add_argument("--shipping-territory-output", help="Optional explicit output Excel path for wrong shipping territory assignments report")
    parser.add_argument(
        "--sales-order-statuses",
        nargs="+",
        metavar="STATUS",
        help=f"Trạng thái đơn bán ra. Mặc định: {', '.join(DEFAULT_SALES_ORDER_STATUSES)}",
    )
    parser.add_argument(
        "--return-order-statuses",
        nargs="+",
        metavar="STATUS",
        help=f"Trạng thái đơn trả lại. Mặc định: {', '.join(DEFAULT_RETURN_ORDER_STATUSES)}",
    )
    parser.add_argument(
        "--reports",
        nargs="+",
        metavar="REPORT",
        help=(
            "Danh sách report cần xuất. "
            f"Ví dụ: --reports summary detail invoice-territory. Giá trị hợp lệ: {', '.join(ALL_REPORT_IDS)}"
        ),
    )
    parser.add_argument("--territory-only", action="store_true", help="Only generate territory-related reports")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.territory_only and args.reports:
        parser.error("Không thể dùng đồng thời --territory-only và --reports")

    try:
        result = generate_reports(
            ReportRequest(
                company=args.company,
                start_date=args.start_date,
                end_date=args.end_date,
                base_dir=Path(args.base_dir),
                sales_order_statuses=tuple(args.sales_order_statuses) if args.sales_order_statuses else None,
                return_order_statuses=tuple(args.return_order_statuses) if args.return_order_statuses else None,
                output=Path(args.output) if args.output else None,
                detail_output=Path(args.detail_output) if args.detail_output else None,
                employee_product_output=Path(args.employee_product_output) if args.employee_product_output else None,
                first_sales_output=Path(args.first_sales_output) if args.first_sales_output else None,
                correct_territory_output=Path(args.correct_territory_output) if args.correct_territory_output else None,
                territory_output=Path(args.territory_output) if args.territory_output else None,
                inactive_territory_output=Path(args.inactive_territory_output) if args.inactive_territory_output else None,
                inactive_customer_output=Path(args.inactive_customer_output) if args.inactive_customer_output else None,
                combined_territory_output=Path(args.combined_territory_output) if args.combined_territory_output else None,
                correct_shipping_territory_output=Path(args.correct_shipping_territory_output) if args.correct_shipping_territory_output else None,
                shipping_territory_output=Path(args.shipping_territory_output) if args.shipping_territory_output else None,
                selected_reports=tuple(args.reports) if args.reports else None,
                territory_only=args.territory_only,
            )
        )
    except ValueError as exc:
        parser.error(str(exc))

    for report in result.generated_reports:
        print(f"Generated {report.label}: {report.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
