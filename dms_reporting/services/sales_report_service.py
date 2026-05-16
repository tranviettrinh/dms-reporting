from __future__ import annotations

import os
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from dateutil import parser

from dms_reporting.config import ReportSettings
from dms_reporting.constants import CONTRACT_CODES
from dms_reporting.domain.models import Customer, DatasetBundle, Employee, Order, Product


@dataclass(slots=True)
class SalesReportService:
    dataset: DatasetBundle
    customers_by_id: dict[str, Customer] = field(init=False)
    products_by_id: dict[str, Product] = field(init=False)
    product_price_map: dict[str, float] = field(init=False)
    employees_by_id: dict[str, Employee] = field(init=False)
    contract_pattern: re.Pattern[str] = field(init=False)
    customer_sales_cache: dict[tuple[object, ...], tuple[dict[str, dict[int, float]], dict[str, dict[int, dict[str, float]]]]] = field(
        init=False,
        default_factory=dict,
    )
    first_sales_cache: dict[tuple[str, ...], dict[str, dict[str, object]]] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        self.customers_by_id = {customer.account_number: customer for customer in self.dataset.customers}
        self.products_by_id = {product.product_id: product for product in self.dataset.products}
        self.product_price_map = {
            product.product_id: product.price
            for product in self.dataset.products
        }
        self.employees_by_id = {employee.employee_id: employee for employee in self.dataset.employees}
        self.contract_pattern = re.compile("|".join(re.escape(code) for code in CONTRACT_CODES))

    def build_customer_sales_report(self, settings: ReportSettings) -> pd.DataFrame:
        start_date = parser.parse(settings.start_date)
        end_date = parser.parse(settings.end_date)
        sales_by_customer, _ = self._get_customer_sales_aggregates(
            start_date=start_date,
            end_date=end_date,
            months=settings.months,
            sales_order_statuses=settings.sales_order_statuses,
            return_order_statuses=settings.return_order_statuses,
        )
        rows: list[dict[str, object]] = []

        for customer in self.dataset.customers:
            if not customer.unit:
                continue
            row = self._build_customer_base_row(customer)
            for month in settings.months:
                row[f"Tháng {month}"] = sales_by_customer.get(customer.account_number, {}).get(month, 0.0)
            rows.append(row)

        return pd.DataFrame(rows)

    def build_customer_sales_detail_report(self, settings: ReportSettings) -> pd.DataFrame:
        start_date = parser.parse(settings.start_date)
        end_date = parser.parse(settings.end_date)
        _, detail_by_customer = self._get_customer_sales_aggregates(
            start_date=start_date,
            end_date=end_date,
            months=settings.months,
            sales_order_statuses=settings.sales_order_statuses,
            return_order_statuses=settings.return_order_statuses,
        )
        rows: list[dict[str, object]] = []

        for customer in self.dataset.customers:
            if not customer.unit:
                continue
            row = self._build_customer_base_row(customer)
            for month in settings.months:
                detail = detail_by_customer.get(customer.account_number, {}).get(month, self._empty_sales_detail_totals())
                row[f"Tháng {month} (Đông dược)"] = detail["doanh_so_dong_duoc"]
                row[f"Tháng {month} (Tân dược)"] = detail["doanh_so_tan_duoc"]
                row[f"Tháng {month} (TPCN)"] = detail["doanh_so_tpcn"]
            rows.append(row)

        return pd.DataFrame(rows)

    def build_first_sales_customers_report(self, settings: ReportSettings) -> pd.DataFrame:
        start_date = parser.parse(settings.start_date)
        end_date = parser.parse(settings.end_date)
        first_sales_by_customer = self._get_first_sales_events(settings.sales_order_statuses)
        rows: list[dict[str, object]] = []

        for customer in self.dataset.customers:
            first_sale = first_sales_by_customer.get(customer.account_number)
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
        first_sales_by_customer = self._get_first_sales_events(settings.sales_order_statuses)
        rows: list[dict[str, object]] = []

        for customer in self.dataset.customers:
            first_sale = first_sales_by_customer.get(customer.account_number)
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

    def build_employee_product_sales_report(self, settings: ReportSettings) -> pd.DataFrame:
        start_date = parser.parse(settings.start_date)
        end_date = parser.parse(settings.end_date)
        return self._build_employee_product_sales_dataframe(
            start_date=start_date,
            end_date=end_date,
            sales_order_statuses=settings.sales_order_statuses,
            return_order_statuses=settings.return_order_statuses,
        )

    def build_employee_product_sales_monthly_reports(self, settings: ReportSettings) -> dict[str, pd.DataFrame]:
        start_date = parser.parse(settings.start_date)
        end_date = parser.parse(settings.end_date)
        valid_months = [month for month in settings.months if 1 <= month <= 12]
        rows_by_month: dict[int, dict[tuple[str, str], dict[str, object]]] = {
            month: {}
            for month in valid_months
        }

        for order, factor in self._iter_orders_for_reporting(
            sales_order_statuses=settings.sales_order_statuses,
            return_order_statuses=settings.return_order_statuses,
        ):
            if order.payment_due is None or not start_date <= order.payment_due <= end_date:
                continue
            month = order.payment_due.month
            if month not in rows_by_month or self._is_distributor_customer_order(order):
                continue
            self._accumulate_employee_product_order(rows_by_month[month], order, factor)

        reports_by_sheet: dict[str, pd.DataFrame] = {}
        for month in valid_months:
            reports_by_sheet[f"Tháng {month}"] = self._employee_product_rows_to_dataframe(rows_by_month[month])
        return reports_by_sheet

    def _build_employee_product_sales_dataframe(
        self,
        *,
        start_date,
        end_date,
        sales_order_statuses: list[str],
        return_order_statuses: list[str],
        month: int | None = None,
    ) -> pd.DataFrame:
        rows_by_key: dict[tuple[str, str], dict[str, object]] = {}

        for order, factor in self._iter_orders_for_reporting(
            sales_order_statuses=sales_order_statuses,
            return_order_statuses=return_order_statuses,
        ):
            if order.payment_due is None or not start_date <= order.payment_due <= end_date:
                continue
            if month is not None and order.payment_due.month != month:
                continue
            if self._is_distributor_customer_order(order):
                continue
            self._accumulate_employee_product_order(rows_by_key, order, factor)

        return self._employee_product_rows_to_dataframe(rows_by_key)

    def build_wrong_territory_assignments_report(self) -> pd.DataFrame:
        territory_manager = self.dataset.territory_manager
        if territory_manager is None:
            return pd.DataFrame(columns=self._territory_assignment_columns())

        rows: list[dict[str, object]] = []
        for customer in self.dataset.customers:
            evaluation = territory_manager.evaluate_customer_assignment(customer)
            if evaluation["is_correct"]:
                continue
            employee = evaluation["employee"]
            if employee is not None and not employee.is_active():
                continue
            rows.append(
                self._build_territory_assignment_row(
                    customer=customer,
                    employee=employee,
                    conclusion=str(evaluation["reason"]),
                )
            )
        return pd.DataFrame(rows, columns=self._territory_assignment_columns())

    def build_correct_territory_assignments_report(self) -> pd.DataFrame:
        territory_manager = self.dataset.territory_manager
        if territory_manager is None:
            return pd.DataFrame(columns=self._territory_assignment_columns())

        rows: list[dict[str, object]] = []
        for customer in self.dataset.customers:
            evaluation = territory_manager.evaluate_customer_assignment(customer)
            if not evaluation["is_correct"]:
                continue
            employee = evaluation["employee"]
            if employee is None or not employee.is_active():
                continue
            rows.append(
                self._build_territory_assignment_row(
                    customer=customer,
                    employee=employee,
                    conclusion="Khách hàng thuộc đúng phân tuyến của nhân viên",
                )
            )
        return pd.DataFrame(rows, columns=self._territory_assignment_columns())

    def build_wrong_shipping_territory_assignments_report(self) -> pd.DataFrame:
        territory_manager = self.dataset.shipping_territory_manager
        if territory_manager is None:
            return pd.DataFrame(columns=self._shipping_territory_assignment_columns())

        rows: list[dict[str, object]] = []
        for customer in self.dataset.customers:
            evaluation = territory_manager.evaluate_customer_shipping_assignment(customer)
            if evaluation["is_correct"]:
                continue
            employee = evaluation["employee"]
            if employee is not None and not employee.is_active():
                continue
            rows.append(
                self._build_shipping_territory_assignment_row(
                    customer=customer,
                    employee=employee,
                    conclusion=str(evaluation["reason"]),
                )
            )
        return pd.DataFrame(rows, columns=self._shipping_territory_assignment_columns())

    def build_correct_shipping_territory_assignments_report(self) -> pd.DataFrame:
        territory_manager = self.dataset.shipping_territory_manager
        if territory_manager is None:
            return pd.DataFrame(columns=self._shipping_territory_assignment_columns())

        rows: list[dict[str, object]] = []
        for customer in self.dataset.customers:
            evaluation = territory_manager.evaluate_customer_shipping_assignment(customer)
            if not evaluation["is_correct"]:
                continue
            employee = evaluation["employee"]
            if employee is None or not employee.is_active():
                continue
            rows.append(
                self._build_shipping_territory_assignment_row(
                    customer=customer,
                    employee=employee,
                    conclusion="Khách hàng thuộc đúng phân tuyến giao hàng của nhân viên",
                )
            )
        return pd.DataFrame(rows, columns=self._shipping_territory_assignment_columns())

    def build_combined_customer_territory_report(self) -> pd.DataFrame:
        rows: list[dict[str, object]] = []
        for customer in self.dataset.customers:
            invoice_evaluation = self._evaluate_billing_territory(customer)
            shipping_evaluation = self._evaluate_shipping_territory(customer)
            employee = self._resolve_customer_employee(
                customer,
                invoice_evaluation["employee"],
                shipping_evaluation["employee"],
            )
            rows.append(
                self._build_combined_territory_assignment_row(
                    customer=customer,
                    employee=employee,
                    invoice_evaluation=invoice_evaluation,
                    shipping_evaluation=shipping_evaluation,
                )
            )

        rows.sort(
            key=lambda row: (
                row["Kết luận tổng hợp"] == self._combined_territory_all_correct_label(),
                row["Tên nhân viên"] or "",
                row["Mã khách hàng"] or "",
            )
        )
        return pd.DataFrame(rows, columns=self._combined_territory_assignment_columns())

    def build_combined_customer_territory_report_sheets(self) -> dict[str, pd.DataFrame]:
        report_df = self.build_combined_customer_territory_report()
        issues_df = report_df[
            report_df["Kết luận tổng hợp"] != self._combined_territory_all_correct_label()
        ].reset_index(drop=True)
        return {
            "Tổng hợp": report_df,
            "Cần xử lý": issues_df,
        }

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

    @staticmethod
    def _territory_assignment_columns() -> list[str]:
        return [
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

    @staticmethod
    def _shipping_territory_assignment_columns() -> list[str]:
        return [
            "Mã khách hàng",
            "Tên khách hàng",
            "Chủ sở hữu",
            "Mã nhân viên",
            "Tên nhân viên",
            "Email cơ quan",
            "Trạng thái lao động",
            "Địa bàn phân tuyến giao hàng hợp lệ",
            "Đơn vị",
            "Tỉnh/Thành phố (Giao hàng)",
            "Quận/Huyện (Giao hàng)",
            "Địa chỉ giao hàng đầy đủ",
            "Địa chỉ hóa đơn đầy đủ",
            "Loại hợp đồng",
            "Loại phân vùng",
            "Vùng",
            "Lý do",
        ]

    @staticmethod
    def _combined_territory_assignment_columns() -> list[str]:
        return [
            "Mã khách hàng",
            "Tên khách hàng",
            "Chủ sở hữu",
            "Mã nhân viên",
            "Tên nhân viên",
            "Email cơ quan",
            "Trạng thái lao động",
            "Địa bàn phân tuyến hợp lệ (Hóa đơn)",
            "Tỉnh/Thành phố (Hóa đơn)",
            "Phường/Xã (Hóa đơn)",
            "Kết quả địa chỉ Hóa đơn",
            "Lý do địa chỉ Hóa đơn",
            "Địa bàn phân tuyến hợp lệ (Giao hàng)",
            "Tỉnh/Thành phố (Giao hàng)",
            "Quận/Huyện (Giao hàng)",
            "Kết quả địa chỉ Giao hàng",
            "Lý do địa chỉ Giao hàng",
            "Địa chỉ giao hàng đầy đủ",
            "Địa chỉ hóa đơn đầy đủ",
            "Đơn vị",
            "Loại hợp đồng",
            "Loại phân vùng",
            "Vùng",
            "Kết luận tổng hợp",
        ]

    def _build_territory_assignment_row(
        self,
        *,
        customer: Customer,
        employee: Employee | None,
        conclusion: str,
    ) -> dict[str, object]:
        return {
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
            "Lý do": conclusion,
        }

    def _build_combined_territory_assignment_row(
        self,
        *,
        customer: Customer,
        employee: Employee | None,
        invoice_evaluation: dict[str, object],
        shipping_evaluation: dict[str, object],
    ) -> dict[str, object]:
        return {
            "Mã khách hàng": customer.account_number,
            "Tên khách hàng": customer.account_name,
            "Chủ sở hữu": customer.owner_name,
            "Mã nhân viên": customer.owner_employee_id,
            "Tên nhân viên": employee.employee_name if employee else None,
            "Email cơ quan": employee.company_email if employee else None,
            "Trạng thái lao động": employee.employment_status if employee else None,
            "Địa bàn phân tuyến hợp lệ (Hóa đơn)": self._format_employee_territories(invoice_evaluation["employee"]),
            "Tỉnh/Thành phố (Hóa đơn)": customer.billing_province,
            "Phường/Xã (Hóa đơn)": customer.billing_ward,
            "Kết quả địa chỉ Hóa đơn": self._format_territory_result(invoice_evaluation["is_correct"]),
            "Lý do địa chỉ Hóa đơn": str(invoice_evaluation["reason"]),
            "Địa bàn phân tuyến hợp lệ (Giao hàng)": self._format_employee_territories(shipping_evaluation["employee"]),
            "Tỉnh/Thành phố (Giao hàng)": customer.shipping_province,
            "Quận/Huyện (Giao hàng)": customer.shipping_district,
            "Kết quả địa chỉ Giao hàng": self._format_territory_result(shipping_evaluation["is_correct"]),
            "Lý do địa chỉ Giao hàng": str(shipping_evaluation["reason"]),
            "Địa chỉ giao hàng đầy đủ": customer.shipping_full_address,
            "Địa chỉ hóa đơn đầy đủ": customer.billing_full_address,
            "Đơn vị": customer.unit,
            "Loại hợp đồng": self.extract_contract_types(customer.account_type),
            "Loại phân vùng": self.extract_partition_type(customer.account_type),
            "Vùng": customer.region,
            "Kết luận tổng hợp": self._build_combined_territory_conclusion(
                bool(invoice_evaluation["is_correct"]),
                bool(shipping_evaluation["is_correct"]),
            ),
        }

    def _build_shipping_territory_assignment_row(
        self,
        *,
        customer: Customer,
        employee: Employee | None,
        conclusion: str,
    ) -> dict[str, object]:
        return {
            "Mã khách hàng": customer.account_number,
            "Tên khách hàng": customer.account_name,
            "Chủ sở hữu": customer.owner_name,
            "Mã nhân viên": customer.owner_employee_id,
            "Tên nhân viên": employee.employee_name if employee else None,
            "Email cơ quan": employee.company_email if employee else None,
            "Trạng thái lao động": employee.employment_status if employee else None,
            "Địa bàn phân tuyến giao hàng hợp lệ": self._format_employee_territories(employee),
            "Đơn vị": customer.unit,
            "Tỉnh/Thành phố (Giao hàng)": customer.shipping_province,
            "Quận/Huyện (Giao hàng)": customer.shipping_district,
            "Địa chỉ giao hàng đầy đủ": customer.shipping_full_address,
            "Địa chỉ hóa đơn đầy đủ": customer.billing_full_address,
            "Loại hợp đồng": self.extract_contract_types(customer.account_type),
            "Loại phân vùng": self.extract_partition_type(customer.account_type),
            "Vùng": customer.region,
            "Lý do": conclusion,
        }

    def _evaluate_billing_territory(self, customer: Customer) -> dict[str, object]:
        territory_manager = self.dataset.territory_manager
        if territory_manager is None:
            return {"is_correct": False, "reason": "Không có dữ liệu phân tuyến Hoá đơn", "employee": None}
        return territory_manager.evaluate_customer_assignment(customer)

    def _evaluate_shipping_territory(self, customer: Customer) -> dict[str, object]:
        territory_manager = self.dataset.shipping_territory_manager
        if territory_manager is None:
            return {"is_correct": False, "reason": "Không có dữ liệu phân tuyến Giao hàng", "employee": None}
        return territory_manager.evaluate_customer_shipping_assignment(customer)

    def _resolve_customer_employee(
        self,
        customer: Customer,
        invoice_employee: Employee | None,
        shipping_employee: Employee | None,
    ) -> Employee | None:
        if invoice_employee is not None:
            return invoice_employee
        if shipping_employee is not None:
            return shipping_employee
        employee_id = customer.owner_employee_id
        if employee_id:
            return self.employees_by_id.get(employee_id)
        return None

    @staticmethod
    def _format_territory_result(is_correct: object) -> str:
        return "Đúng" if bool(is_correct) else "Sai"

    @staticmethod
    def _combined_territory_all_correct_label() -> str:
        return "Đúng cả địa chỉ Hoá đơn và Giao hàng"

    def _build_combined_territory_conclusion(self, invoice_correct: bool, shipping_correct: bool) -> str:
        if invoice_correct and shipping_correct:
            return self._combined_territory_all_correct_label()
        if invoice_correct:
            return "Sai địa chỉ Giao hàng"
        if shipping_correct:
            return "Sai địa chỉ Hoá đơn"
        return "Sai cả địa chỉ Hoá đơn và Giao hàng"

    def calculate_monthly_sales(
        self,
        *,
        customer_id: str,
        month: int,
        start_date,
        end_date,
        sales_order_statuses: list[str],
        return_order_statuses: list[str],
    ) -> float:
        sales_by_customer, _ = self._get_customer_sales_aggregates(
            start_date=start_date,
            end_date=end_date,
            months=[month],
            sales_order_statuses=sales_order_statuses,
            return_order_statuses=return_order_statuses,
        )
        return sales_by_customer.get(customer_id, {}).get(month, 0.0)

    def calculate_monthly_sales_detail(
        self,
        *,
        customer_id: str,
        month: int,
        start_date,
        end_date,
        sales_order_statuses: list[str],
        return_order_statuses: list[str],
    ) -> dict[str, float]:
        _, detail_by_customer = self._get_customer_sales_aggregates(
            start_date=start_date,
            end_date=end_date,
            months=[month],
            sales_order_statuses=sales_order_statuses,
            return_order_statuses=return_order_statuses,
        )
        cached_totals = detail_by_customer.get(customer_id, {}).get(month)
        if cached_totals is None:
            return self._empty_sales_detail_totals()
        return dict(cached_totals)

    def _find_first_sales_event(self, *, customer_id: str, sales_order_statuses: list[str]) -> dict[str, object] | None:
        first_event: dict[str, object] | None = None

        for order in self._iter_positive_sales_orders():
            if order.customer_id != customer_id or order.payment_due is None or order.status not in sales_order_statuses:
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
    def _is_order_in_scope(order: Order, customer_id: str, month: int, start_date, end_date) -> bool:
        if order.customer_id != customer_id or order.payment_due is None:
            return False
        return start_date <= order.payment_due <= end_date and order.payment_due.month == month

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
        def write_to_writer(writer: pd.ExcelWriter) -> None:
            report_df.to_excel(writer, sheet_name="Cả nước", index=False)
            for region in ["Miền Bắc", "Miền Nam", "Miền Trung", "Khác"]:
                region_df = report_df[report_df["Vùng"] == region]
                if not region_df.empty:
                    region_df.to_excel(writer, sheet_name=region, index=False)

        self._write_excel_file(output_path, write_to_writer)
        return output_path

    def write_flat_report(self, report_df: pd.DataFrame, output_path: Path, *, sheet_name: str = "Cả nước") -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_excel_file(
            output_path,
            lambda writer: report_df.to_excel(writer, sheet_name=sheet_name, index=False),
        )
        return output_path

    def write_multi_sheet_report(self, reports_by_sheet: dict[str, pd.DataFrame], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        def write_to_writer(writer: pd.ExcelWriter) -> None:
            if not reports_by_sheet:
                pd.DataFrame().to_excel(writer, sheet_name="Trống", index=False)
                return
            for sheet_name, report_df in reports_by_sheet.items():
                report_df.to_excel(writer, sheet_name=sheet_name[:31], index=False)

        self._write_excel_file(output_path, write_to_writer)
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

    def _iter_orders_for_reporting(
        self,
        *,
        sales_order_statuses: list[str],
        return_order_statuses: list[str],
    ):
        sales_status_lookup = set(sales_order_statuses)
        return_status_lookup = set(return_order_statuses)
        for order in self.dataset.orders.purchase_orders:
            if order.status in sales_status_lookup:
                yield order, 1
        for order in self.dataset.orders.sales_orders:
            if order.status in sales_status_lookup:
                yield order, 1
        for order in self.dataset.orders.return_purchase_orders:
            if order.status in return_status_lookup:
                yield order, -1
        for order in self.dataset.orders.return_sales_orders:
            if order.status in return_status_lookup:
                yield order, -1

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
    def _employee_product_columns() -> list[str]:
        return [
            "Mã nhân viên",
            "Tên nhân viên",
            "Người thực hiện",
            "Mã sản phẩm",
            "Tên sản phẩm",
            "Nhóm sản phẩm",
            "Đơn vị tính",
            "Số lượng bán",
            "Số lượng trả lại",
            "Sản lượng thuần",
            "Doanh thu bán",
            "Doanh thu trả lại",
            "Doanh thu thuần",
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

    def _resolve_order_employee(self, order: Order) -> dict[str, str]:
        customer = self.customers_by_id.get(order.customer_id)
        candidate_owners = [order.owner_name]
        if customer is not None:
            candidate_owners.append(customer.owner_name)

        for owner_name in candidate_owners:
            employee_id = self._extract_employee_id(owner_name)
            if employee_id:
                employee = self.employees_by_id.get(employee_id)
                return {
                    "group_key": employee_id,
                    "employee_id": employee_id,
                    "employee_name": employee.employee_name if employee else self._extract_owner_display_name(owner_name),
                    "owner_name": owner_name or (employee.employee_name if employee else None),
                }

        fallback_owner_name = next((owner_name for owner_name in candidate_owners if owner_name), None)
        fallback_name = self._extract_owner_display_name(fallback_owner_name)
        fallback_key = fallback_name or fallback_owner_name or "Không xác định"
        return {
            "group_key": fallback_key,
            "employee_id": "",
            "employee_name": fallback_name or "Không xác định",
            "owner_name": fallback_owner_name or fallback_name or "Không xác định",
        }

    def _is_distributor_customer_order(self, order: Order) -> bool:
        customer = self.customers_by_id.get(order.customer_id)
        return bool(customer and customer.is_distributor_customer)

    @staticmethod
    def _extract_employee_id(owner_name: str | None) -> str | None:
        if not owner_name:
            return None
        match = re.search(r"\(([^)]+)\)", owner_name)
        return match.group(1).strip() if match else None

    @staticmethod
    def _extract_owner_display_name(owner_name: str | None) -> str | None:
        if not owner_name:
            return None
        without_code = re.sub(r"\s*\([^)]+\)\s*$", "", owner_name).strip()
        if " - " in without_code:
            return without_code.split(" - ", 1)[0].strip()
        return without_code or None

    def _calculate_order_recognized_amount(self, order: Order) -> float:
        return sum(self._calculate_catalog_sales_amount(item) for item in order.items if item.total > 0)

    def _calculate_catalog_sales_amount(self, item) -> float:
        unit_price = self.product_price_map.get(item.product_id)
        if unit_price is None:
            unit_price = item.unit_price
        return item.quantity * unit_price

    def _get_customer_sales_aggregates(
        self,
        *,
        start_date,
        end_date,
        months: list[int],
        sales_order_statuses: list[str],
        return_order_statuses: list[str],
    ) -> tuple[dict[str, dict[int, float]], dict[str, dict[int, dict[str, float]]]]:
        cache_key = (
            start_date,
            end_date,
            tuple(months),
            tuple(sales_order_statuses),
            tuple(return_order_statuses),
        )
        cached = self.customer_sales_cache.get(cache_key)
        if cached is not None:
            return cached

        valid_months = {month for month in months if 1 <= month <= 12}
        sales_by_customer: dict[str, dict[int, float]] = {}
        detail_by_customer: dict[str, dict[int, dict[str, float]]] = {}

        for order, factor in self._iter_orders_for_reporting(
            sales_order_statuses=sales_order_statuses,
            return_order_statuses=return_order_statuses,
        ):
            if order.payment_due is None or not start_date <= order.payment_due <= end_date:
                continue
            month = order.payment_due.month
            if month not in valid_months:
                continue

            customer_sales = sales_by_customer.setdefault(order.customer_id, {})
            customer_sales[month] = customer_sales.get(month, 0.0)
            customer_detail = detail_by_customer.setdefault(order.customer_id, {})
            monthly_detail = customer_detail.setdefault(month, self._empty_sales_detail_totals())

            for item in order.items:
                if item.total <= 0:
                    continue
                amount = factor * self._calculate_catalog_sales_amount(item)
                customer_sales[month] += amount
                product = self.products_by_id.get(item.product_id)
                group_key = self._resolve_product_group(product)
                monthly_detail[group_key] += amount

        self.customer_sales_cache[cache_key] = (sales_by_customer, detail_by_customer)
        return sales_by_customer, detail_by_customer

    def _get_first_sales_events(self, sales_order_statuses: list[str]) -> dict[str, dict[str, object]]:
        cache_key = tuple(sales_order_statuses)
        cached = self.first_sales_cache.get(cache_key)
        if cached is not None:
            return cached

        sales_status_lookup = set(sales_order_statuses)
        first_events: dict[str, dict[str, object]] = {}

        for order in self._iter_positive_sales_orders():
            if order.payment_due is None or order.status not in sales_status_lookup:
                continue

            recognized_amount = self._calculate_order_recognized_amount(order)
            if recognized_amount <= 0:
                continue

            current = first_events.get(order.customer_id)
            if current is None or order.payment_due < current["payment_due"]:
                first_events[order.customer_id] = {
                    "order_number": order.order_number,
                    "payment_due": order.payment_due,
                    "recognized_amount": recognized_amount,
                }

        self.first_sales_cache[cache_key] = first_events
        return first_events

    def _accumulate_employee_product_order(
        self,
        rows_by_key: dict[tuple[str, str], dict[str, object]],
        order: Order,
        factor: int,
    ) -> None:
        employee_payload = self._resolve_order_employee(order)
        for item in order.items:
            if item.unit_price <= 0:
                continue

            product = self.products_by_id.get(item.product_id)
            product_code = item.product_id
            employee_key = employee_payload["group_key"]
            row = rows_by_key.setdefault(
                (employee_key, product_code),
                {
                    "Mã nhân viên": employee_payload["employee_id"],
                    "Tên nhân viên": employee_payload["employee_name"],
                    "Người thực hiện": employee_payload["owner_name"],
                    "Mã sản phẩm": product_code,
                    "Tên sản phẩm": product.name if product else None,
                    "Nhóm sản phẩm": product.category if product else None,
                    "Đơn vị tính": "Hộp",
                    "Số lượng bán": 0.0,
                    "Số lượng trả lại": 0.0,
                    "Sản lượng thuần": 0.0,
                    "Doanh thu bán": 0.0,
                    "Doanh thu trả lại": 0.0,
                    "Doanh thu thuần": 0.0,
                },
            )

            quantity = item.quantity
            revenue = self._calculate_catalog_sales_amount(item)
            if factor > 0:
                row["Số lượng bán"] += quantity
                row["Doanh thu bán"] += revenue
            else:
                row["Số lượng trả lại"] += quantity
                row["Doanh thu trả lại"] += revenue
            row["Sản lượng thuần"] = row["Số lượng bán"] - row["Số lượng trả lại"]
            row["Doanh thu thuần"] = row["Doanh thu bán"] - row["Doanh thu trả lại"]

    def _employee_product_rows_to_dataframe(
        self,
        rows_by_key: dict[tuple[str, str], dict[str, object]],
    ) -> pd.DataFrame:
        rows = list(rows_by_key.values())
        rows.sort(
            key=lambda row: (
                row["Tên nhân viên"] or "",
                row["Mã nhân viên"] or "",
                row["Mã sản phẩm"] or "",
            )
        )
        return pd.DataFrame(rows, columns=self._employee_product_columns())

    @staticmethod
    def _empty_sales_detail_totals() -> dict[str, float]:
        return {
            "doanh_so_dong_duoc": 0.0,
            "doanh_so_tan_duoc": 0.0,
            "doanh_so_tpcn": 0.0,
        }

    @staticmethod
    def _write_excel_file(output_path: Path, write_callback) -> None:
        fd, temp_name = tempfile.mkstemp(prefix="dms-report-", suffix=".xlsx")
        os.close(fd)
        temp_path = Path(temp_name)
        try:
            with pd.ExcelWriter(temp_path, engine="openpyxl", mode="w") as writer:
                write_callback(writer)
            shutil.move(str(temp_path), output_path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    @staticmethod
    def _sort_first_sales_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
        rows.sort(
            key=lambda row: (
                row["Ngày phát sinh doanh số đầu tiên"],
                row["Mã khách hàng"],
            )
        )
        return rows
