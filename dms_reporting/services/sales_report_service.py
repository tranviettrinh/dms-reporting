from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from dateutil import parser

from dms_reporting.config import ReportSettings
from dms_reporting.constants import CONTRACT_CODES
from dms_reporting.domain.models import Customer, DatasetBundle, Order, Product


@dataclass(slots=True)
class SalesReportService:
    dataset: DatasetBundle
    customers_by_id: dict[str, Customer] = field(init=False)
    products_by_id: dict[str, Product] = field(init=False)
    contract_pattern: re.Pattern[str] = field(init=False)

    def __post_init__(self) -> None:
        self.customers_by_id = {customer.account_number: customer for customer in self.dataset.customers}
        self.products_by_id = {product.product_id: product for product in self.dataset.products}
        self.contract_pattern = re.compile("|".join(re.escape(code) for code in CONTRACT_CODES))

    def build_customer_sales_report(self, settings: ReportSettings) -> pd.DataFrame:
        start_date = parser.parse(settings.start_date)
        end_date = parser.parse(settings.end_date)
        rows: list[dict[str, object]] = []

        for customer in self.dataset.customers:
            if not customer.unit:
                continue
            monthly_sales = {
                month: self.calculate_monthly_sales(
                    customer_id=customer.account_number,
                    month=month,
                    start_date=start_date,
                    end_date=end_date,
                    statuses=settings.statuses,
                )
                for month in settings.months
            }
            row = self._build_customer_base_row(customer)
            for month in settings.months:
                row[f"Tháng {month}"] = monthly_sales[month]
            rows.append(row)

        return pd.DataFrame(rows)

    def build_customer_sales_detail_report(self, settings: ReportSettings) -> pd.DataFrame:
        start_date = parser.parse(settings.start_date)
        end_date = parser.parse(settings.end_date)
        rows: list[dict[str, object]] = []

        for customer in self.dataset.customers:
            if not customer.unit:
                continue
            row = self._build_customer_base_row(customer)
            for month in settings.months:
                detail = self.calculate_monthly_sales_detail(
                    customer_id=customer.account_number,
                    month=month,
                    start_date=start_date,
                    end_date=end_date,
                    statuses=settings.statuses,
                )
                row[f"Tháng {month} (Đông dược)"] = detail["doanh_so_dong_duoc"]
                row[f"Tháng {month} (Tân dược)"] = detail["doanh_so_tan_duoc"]
                row[f"Tháng {month} (TPCN)"] = detail["doanh_so_tpcn"]
            rows.append(row)

        return pd.DataFrame(rows)

    def build_first_sales_customers_report(self, settings: ReportSettings) -> pd.DataFrame:
        start_date = parser.parse(settings.start_date)
        end_date = parser.parse(settings.end_date)
        rows: list[dict[str, object]] = []

        for customer in self.dataset.customers:
            first_sale = self._find_first_sales_event(
                customer_id=customer.account_number,
                statuses=settings.statuses,
            )
            if first_sale is None or not start_date <= first_sale["payment_due"] <= end_date:
                continue
            rows.append(self._build_first_sales_row(customer, first_sale))

        return pd.DataFrame(
            self._sort_first_sales_rows(rows),
            columns=self._first_sales_columns(),
        )

    def build_first_sales_customers_monthly_reports(self, settings: ReportSettings) -> dict[str, pd.DataFrame]:
        start_date = parser.parse(settings.start_date)
        end_date = parser.parse(settings.end_date)
        rows: list[dict[str, object]] = []

        for customer in self.dataset.customers:
            first_sale = self._find_first_sales_event(
                customer_id=customer.account_number,
                statuses=settings.statuses,
            )
            if first_sale is None or not start_date <= first_sale["payment_due"] <= end_date:
                continue
            rows.append(self._build_first_sales_row(customer, first_sale))

        sorted_rows = self._sort_first_sales_rows(rows)
        columns = self._first_sales_columns()
        reports_by_sheet: dict[str, pd.DataFrame] = {}
        for month in settings.months:
            if month < 1 or month > 12:
                continue
            month_rows = [
                row
                for row in sorted_rows
                if row["Ngày phát sinh doanh số đầu tiên"].month == month
            ]
            reports_by_sheet[f"Tháng {month}"] = pd.DataFrame(month_rows, columns=columns)
        return reports_by_sheet

    def build_wrong_territory_assignments_report(self) -> pd.DataFrame:
        territory_manager = self.dataset.territory_manager
        if territory_manager is None:
            return pd.DataFrame(
                columns=[
                    "Mã khách hàng",
                    "Tên khách hàng",
                    "Chủ sở hữu",
                    "Mã nhân viên",
                    "Tên nhân viên",
                    "Email cơ quan",
                    "Trạng thái lao động",
                    "Địa bàn phân tuyến hợp lệ",
                    "Đơn vị",
                    "Tỉnh/Thành phố (Hóa đơn)",
                    "Phường/Xã (Hóa đơn)",
                    "Địa chỉ giao hàng đầy đủ",
                    "Địa chỉ hóa đơn đầy đủ",
                    "Loại hợp đồng",
                    "Loại phân vùng",
                    "Vùng",
                    "Lý do",
                ]
            )

        rows: list[dict[str, object]] = []
        for customer in self.dataset.customers:
            evaluation = territory_manager.evaluate_customer_assignment(customer)
            if evaluation["is_correct"]:
                continue
            employee = evaluation["employee"]
            if employee is not None and not employee.is_active():
                continue
            rows.append(
                {
                    "Mã khách hàng": customer.account_number,
                    "Tên khách hàng": customer.account_name,
                    "Chủ sở hữu": customer.owner_name,
                    "Mã nhân viên": customer.owner_employee_id,
                    "Tên nhân viên": employee.employee_name if employee else None,
                    "Email cơ quan": employee.company_email if employee else None,
                    "Trạng thái lao động": employee.employment_status if employee else None,
                    "Địa bàn phân tuyến hợp lệ": self._format_employee_territories(employee),
                    "Đơn vị": customer.unit,
                    "Tỉnh/Thành phố (Hóa đơn)": customer.billing_province,
                    "Phường/Xã (Hóa đơn)": customer.billing_ward,
                    "Địa chỉ giao hàng đầy đủ": customer.shipping_full_address,
                    "Địa chỉ hóa đơn đầy đủ": customer.billing_full_address,
                    "Loại hợp đồng": self.extract_contract_types(customer.account_type),
                    "Loại phân vùng": self.extract_partition_type(customer.account_type),
                    "Vùng": customer.region,
                    "Lý do": evaluation["reason"],
                }
            )
        return pd.DataFrame(rows)

    def build_inactive_employee_territories_report(self) -> pd.DataFrame:
        territory_manager = self.dataset.territory_manager
        if territory_manager is None:
            return pd.DataFrame(
                columns=[
                    "Mã nhân viên",
                    "Tên nhân viên",
                    "Email cơ quan",
                    "Trạng thái lao động",
                    "Phân vùng",
                    "Đơn vị công tác",
                    "Số địa bàn còn trong file phân tuyến",
                    "Địa bàn còn trong file phân tuyến",
                ]
            )

        rows: list[dict[str, object]] = []
        for payload in territory_manager.get_inactive_employee_territories():
            employee = payload["employee"]
            territories = payload["territories"]
            rows.append(
                {
                    "Mã nhân viên": employee.employee_id,
                    "Tên nhân viên": employee.employee_name,
                    "Email cơ quan": employee.company_email,
                    "Trạng thái lao động": employee.employment_status,
                    "Phân vùng": employee.region_code,
                    "Đơn vị công tác": employee.organization_unit,
                    "Số địa bàn còn trong file phân tuyến": len(territories),
                    "Địa bàn còn trong file phân tuyến": self._format_territory_list(territories),
                }
            )
        return pd.DataFrame(rows)

    def build_customers_assigned_to_inactive_employees_report(self) -> pd.DataFrame:
        territory_manager = self.dataset.territory_manager
        if territory_manager is None:
            return pd.DataFrame(
                columns=[
                    "Mã khách hàng",
                    "Tên khách hàng",
                    "Chủ sở hữu",
                    "Mã nhân viên",
                    "Tên nhân viên",
                    "Email cơ quan",
                    "Trạng thái lao động",
                    "Đơn vị",
                    "Tỉnh/Thành phố (Hóa đơn)",
                    "Phường/Xã (Hóa đơn)",
                    "Địa chỉ giao hàng đầy đủ",
                    "Địa chỉ hóa đơn đầy đủ",
                    "Loại hợp đồng",
                    "Loại phân vùng",
                    "Vùng",
                    "Lý do",
                ]
            )

        rows: list[dict[str, object]] = []
        for customer in self.dataset.customers:
            employee = territory_manager.find_employee_by_customer(customer)
            if employee is None or employee.is_active():
                continue
            rows.append(
                {
                    "Mã khách hàng": customer.account_number,
                    "Tên khách hàng": customer.account_name,
                    "Chủ sở hữu": customer.owner_name,
                    "Mã nhân viên": customer.owner_employee_id,
                    "Tên nhân viên": employee.employee_name,
                    "Email cơ quan": employee.company_email,
                    "Trạng thái lao động": employee.employment_status,
                    "Đơn vị": customer.unit,
                    "Tỉnh/Thành phố (Hóa đơn)": customer.billing_province,
                    "Phường/Xã (Hóa đơn)": customer.billing_ward,
                    "Địa chỉ giao hàng đầy đủ": customer.shipping_full_address,
                    "Địa chỉ hóa đơn đầy đủ": customer.billing_full_address,
                    "Loại hợp đồng": self.extract_contract_types(customer.account_type),
                    "Loại phân vùng": self.extract_partition_type(customer.account_type),
                    "Vùng": customer.region,
                    "Lý do": "Khách hàng vẫn đang gán cho nhân viên đã nghỉ việc",
                }
            )
        return pd.DataFrame(rows)

    def calculate_monthly_sales(self, *, customer_id: str, month: int, start_date, end_date, statuses: list[str]) -> float:
        total_value = 0.0
        for orders, factor in self.dataset.orders.iter_all():
            for order in orders:
                if not self._is_order_in_scope(order, customer_id, month, start_date, end_date, statuses):
                    continue
                item_total = sum(item.quantity * item.unit_price for item in order.items if item.total > 0)
                total_value += factor * item_total
        return total_value

    def calculate_monthly_sales_detail(
        self,
        *,
        customer_id: str,
        month: int,
        start_date,
        end_date,
        statuses: list[str],
    ) -> dict[str, float]:
        totals = {
            "doanh_so_dong_duoc": 0.0,
            "doanh_so_tan_duoc": 0.0,
            "doanh_so_tpcn": 0.0,
        }

        for orders, factor in self.dataset.orders.iter_all():
            for order in orders:
                if not self._is_order_in_scope(order, customer_id, month, start_date, end_date, statuses):
                    continue
                for item in order.items:
                    if item.total <= 0:
                        continue
                    product = self.products_by_id.get(item.product_id)
                    group_key = self._resolve_product_group(product)
                    totals[group_key] += factor * (item.quantity * item.unit_price)

        return totals

    def _find_first_sales_event(self, *, customer_id: str, statuses: list[str]) -> dict[str, object] | None:
        first_event: dict[str, object] | None = None

        for order in self._iter_positive_sales_orders():
            if order.customer_id != customer_id or order.payment_due is None or order.status not in statuses:
                continue

            recognized_amount = self._calculate_order_recognized_amount(order)
            if recognized_amount <= 0:
                continue

            if first_event is None or order.payment_due < first_event["payment_due"]:
                first_event = {
                    "order_number": order.order_number,
                    "payment_due": order.payment_due,
                    "recognized_amount": recognized_amount,
                }

        return first_event

    @staticmethod
    def _is_order_in_scope(order: Order, customer_id: str, month: int, start_date, end_date, statuses: list[str]) -> bool:
        if order.customer_id != customer_id or order.payment_due is None:
            return False
        return start_date <= order.payment_due <= end_date and order.status in statuses and order.payment_due.month == month

    def extract_contract_types(self, raw_account_type: str | None) -> str:
        if not raw_account_type:
            return ""
        matches = self.contract_pattern.findall(raw_account_type)
        return "; ".join(dict.fromkeys(matches))

    def extract_partition_type(self, raw_account_type: str | None) -> str:
        if not raw_account_type:
            return "Chưa xác định"
        cleaned = self.contract_pattern.sub("", raw_account_type)
        cleaned = re.sub(r"[-_]+", " ", cleaned).strip()
        return cleaned or "Chưa xác định"

    def write_customer_sales_report(self, report_df: pd.DataFrame, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(output_path, engine="openpyxl", mode="w") as writer:
            report_df.to_excel(writer, sheet_name="Cả nước", index=False)
            for region in ["Miền Bắc", "Miền Nam", "Miền Trung", "Khác"]:
                region_df = report_df[report_df["Vùng"] == region]
                if not region_df.empty:
                    region_df.to_excel(writer, sheet_name=region, index=False)
        return output_path

    def write_flat_report(self, report_df: pd.DataFrame, output_path: Path, *, sheet_name: str = "Cả nước") -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(output_path, engine="openpyxl", mode="w") as writer:
            report_df.to_excel(writer, sheet_name=sheet_name, index=False)
        return output_path

    def write_multi_sheet_report(self, reports_by_sheet: dict[str, pd.DataFrame], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(output_path, engine="openpyxl", mode="w") as writer:
            if not reports_by_sheet:
                pd.DataFrame().to_excel(writer, sheet_name="Trống", index=False)
                return output_path
            for sheet_name, report_df in reports_by_sheet.items():
                report_df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        return output_path

    def _build_customer_base_row(self, customer: Customer) -> dict[str, object]:
        return {
            "Mã khách hàng": customer.account_number,
            "Tên khách hàng": customer.account_name,
            "Loại khách hàng": customer.account_type,
            "Ngày ký hợp đồng": customer.sign_date,
            "Mô tả": customer.description,
            "Ngày ghé thăm gần nhất": customer.visiting_last_day,
            "Mã số thuế": customer.tax_code,
            "Điện thoại": customer.phone,
            "Số nhà": customer.shipping_street_value,
            "Phường/Xã": customer.shipping_ward_value,
            "Quận/Huyện": customer.shipping_district_value,
            "Tỉnh/Thành phố": customer.shipping_province_value,
            "Địa chỉ giao hàng đầy đủ": customer.shipping_full_address,
            "Địa chỉ hóa đơn đầy đủ": customer.billing_full_address,
            "Đơn vị": customer.unit,
            "Chủ sở hữu": customer.owner_name,
            "Là nhà phân phối": customer.is_distributor,
            "Ngày sinh nhật": customer.date_of_birthday,
            "Loại hợp đồng": self.extract_contract_types(customer.account_type),
            "Loại phân vùng": self.extract_partition_type(customer.account_type),
            "Vùng": customer.region,
        }

    def _build_first_sales_row(self, customer: Customer, first_sale: dict[str, object]) -> dict[str, object]:
        row = self._build_customer_base_row(customer)
        row.update(
            {
                "Ngày phát sinh doanh số đầu tiên": first_sale["payment_due"],
                "Tháng phát sinh doanh số đầu tiên": first_sale["payment_due"].month,
                "Số đơn hàng đầu tiên": first_sale["order_number"],
                "Doanh số ghi nhận lần đầu": first_sale["recognized_amount"],
            }
        )
        return row

    def _iter_positive_sales_orders(self) -> list[Order]:
        return self.dataset.orders.purchase_orders + self.dataset.orders.sales_orders

    def _first_sales_columns(self) -> list[str]:
        return [
            "Mã khách hàng",
            "Tên khách hàng",
            "Loại khách hàng",
            "Ngày ký hợp đồng",
            "Mô tả",
            "Ngày ghé thăm gần nhất",
            "Mã số thuế",
            "Điện thoại",
            "Số nhà",
            "Phường/Xã",
            "Quận/Huyện",
            "Tỉnh/Thành phố",
            "Địa chỉ giao hàng đầy đủ",
            "Địa chỉ hóa đơn đầy đủ",
            "Đơn vị",
            "Chủ sở hữu",
            "Là nhà phân phối",
            "Ngày sinh nhật",
            "Loại hợp đồng",
            "Loại phân vùng",
            "Vùng",
            "Ngày phát sinh doanh số đầu tiên",
            "Tháng phát sinh doanh số đầu tiên",
            "Số đơn hàng đầu tiên",
            "Doanh số ghi nhận lần đầu",
        ]

    @staticmethod
    def _format_employee_territories(employee) -> str:
        if employee is None:
            return ""
        return SalesReportService._format_territory_list(employee.territories)

    @staticmethod
    def _format_territory_list(territories) -> str:
        unique_territories = []
        seen = set()
        for territory in territories:
            label = f"{territory.province} - {territory.commune}"
            if label not in seen:
                seen.add(label)
                unique_territories.append(label)
        return "; ".join(unique_territories)

    @staticmethod
    def _resolve_product_group(product: Product | None) -> str:
        category = (product.category or "").upper() if product else ""
        if "ĐÔNG DƯỢC" in category:
            return "doanh_so_dong_duoc"
        if "TÂN DƯỢC" in category:
            return "doanh_so_tan_duoc"
        return "doanh_so_tpcn"

    @staticmethod
    def _calculate_order_recognized_amount(order: Order) -> float:
        return sum(item.quantity * item.unit_price for item in order.items if item.total > 0)

    @staticmethod
    def _sort_first_sales_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
        rows.sort(
            key=lambda row: (
                row["Ngày phát sinh doanh số đầu tiên"],
                row["Mã khách hàng"],
            )
        )
        return rows
