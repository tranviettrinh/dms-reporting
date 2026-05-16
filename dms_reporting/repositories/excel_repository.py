from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from dms_reporting.config import CompanyPaths
from dms_reporting.constants import EXCLUDED_CUSTOMER_CREATORS, EXCLUDED_CUSTOMER_TYPES
from dms_reporting.domain.models import Customer, DatasetBundle, Employee, Order, OrderBucket, OrderItem, Product, Territory, TerritoryManager


class DataValidationError(ValueError):
    pass


ProgressCallback = Callable[[str], None]


@dataclass(slots=True)
class ExcelCRMRepository:
    paths: CompanyPaths
    LOAD_DATASET_STEP_COUNT = 8

    def load_dataset(self, progress_callback: ProgressCallback | None = None) -> DatasetBundle:
        self._emit_progress(progress_callback, "Đang đọc danh mục sản phẩm...")
        products = self.load_products()
        self._emit_progress(progress_callback, "Đang đọc danh sách khách hàng...")
        customers = self.load_customers()
        self._emit_progress(progress_callback, "Đang đọc danh sách nhân viên...")
        employees = self.load_employees()
        self._emit_progress(progress_callback, "Đang đọc dữ liệu phân tuyến...")
        territory_manager = self.load_territory_manager(employees)
        shipping_territory_manager = self.load_shipping_territory_manager(employees)
        self._emit_progress(progress_callback, "Đang đọc đơn hàng bán ra...")
        purchase_orders = self.load_purchase_orders()
        self._emit_progress(progress_callback, "Đang đọc đơn hàng nhà phân phối...")
        sales_orders = self.load_sales_orders()
        self._emit_progress(progress_callback, "Đang đọc đơn hàng trả lại...")
        return_purchase_orders = self.load_return_purchase_orders()
        self._emit_progress(progress_callback, "Đang đọc đơn trả lại nhà phân phối...")
        return_sales_orders = self.load_return_sales_orders()
        return DatasetBundle(
            products=products,
            customers=customers,
            orders=OrderBucket(
                purchase_orders=purchase_orders,
                sales_orders=sales_orders,
                return_purchase_orders=return_purchase_orders,
                return_sales_orders=return_sales_orders,
            ),
            employees=employees,
            territory_manager=territory_manager,
            shipping_territory_manager=shipping_territory_manager,
        )

    def load_products(self) -> list[Product]:
        required = ["Mã hàng hóa", "Tên hàng hóa", "Loại hàng hóa", "Đơn vị tính chính", "Đơn giá bán", "Thuế GTGT"]
        df = self._read_excel(
            self.paths.products_file,
            sheet_name="Danh sách",
            usecols=self._build_usecols(required),
        )
        self._ensure_columns(df, required, self.paths.products_file)
        return [
            Product(
                product_id=str(row["Mã hàng hóa"]),
                name=str(row["Tên hàng hóa"]),
                category=self._clean_str(row["Loại hàng hóa"]),
                primary_unit=self._clean_str(row["Đơn vị tính chính"]),
                price=self._to_float(row["Đơn giá bán"]),
                tax=self._to_float(row["Thuế GTGT"]),
            )
            for _, row in df.iterrows()
            if self._clean_str(row["Mã hàng hóa"])
        ]

    def load_customers(self) -> list[Customer]:
        required = [
            "Mã khách hàng", "Tên khách hàng", "Loại khách hàng", "Ngày ký hợp đồng", "Điện thoại",
            "Số nhà, Đường phố (Giao hàng)", "Phường/Xã (Giao hàng)", "Quận/Huyện (Giao hàng)",
            "Tỉnh/Thành phố (Giao hàng)", "Địa chỉ (Giao hàng)", "Mã số thuế", "Chủ sở hữu",
            "Mô tả", "Ngày ghé thăm gần nhất", "Ngày thành lập/Ngày sinh", "Là nhà phân phối", "Đơn vị", "Người tạo",
        ]
        optional_columns = [
            "Số nhà, Đường phố (Hóa đơn)",
            "Phường/Xã (Hóa đơn)",
            "Quận/Huyện (Hóa đơn)",
            "Tỉnh/Thành phố (Hóa đơn)",
            "Địa chỉ (Hóa đơn)",
        ]
        df = self._read_excel(
            self.paths.customers_file,
            sheet_name="Danh sách",
            usecols=self._build_usecols(required + optional_columns),
        )
        self._ensure_columns(df, required, self.paths.customers_file)
        df = df[
            ~df["Người tạo"].isin(EXCLUDED_CUSTOMER_CREATORS)
            & ~df["Loại khách hàng"].isin(EXCLUDED_CUSTOMER_TYPES)
        ]
        return [
            Customer(
                account_number=str(row["Mã khách hàng"]),
                account_name=str(row["Tên khách hàng"]),
                account_type=self._clean_str(row["Loại khách hàng"]),
                sign_date=Order.parse_datetime(row["Ngày ký hợp đồng"]),
                phone=self._clean_str(row["Điện thoại"]),
                billing_street=self._clean_str(row.get("Số nhà, Đường phố (Hóa đơn)")),
                billing_ward=self._clean_str(row.get("Phường/Xã (Hóa đơn)")),
                billing_district=self._clean_str(row.get("Quận/Huyện (Hóa đơn)")),
                billing_province=self._clean_str(row.get("Tỉnh/Thành phố (Hóa đơn)")),
                billing_address=self._clean_str(row.get("Địa chỉ (Hóa đơn)")),
                tax_code=self._clean_str(row["Mã số thuế"]),
                owner_name=self._clean_str(row["Chủ sở hữu"]),
                description=self._clean_str(row["Mô tả"]),
                visiting_last_day=Order.parse_datetime(row["Ngày ghé thăm gần nhất"]),
                date_of_birthday=Order.parse_datetime(row["Ngày thành lập/Ngày sinh"]),
                is_distributor=self._clean_str(row["Là nhà phân phối"]),
                unit=self._clean_str(row["Đơn vị"]),
                shipping_street=self._clean_str(row["Số nhà, Đường phố (Giao hàng)"]),
                shipping_ward=self._clean_str(row["Phường/Xã (Giao hàng)"]),
                shipping_district=self._clean_str(row["Quận/Huyện (Giao hàng)"]),
                shipping_province=self._clean_str(row["Tỉnh/Thành phố (Giao hàng)"]),
                shipping_address=self._clean_str(row["Địa chỉ (Giao hàng)"]),
            )
            for _, row in df.iterrows()
            if self._clean_str(row["Mã khách hàng"])
        ]

    def load_employees(self) -> list[Employee]:
        if not self.paths.employees_file.exists():
            return []

        required = [
            "Mã nhân viên (*)",
            "Họ và tên (*)",
            "Điện thoại di động",
            "Đơn vị công tác (*)",
            "Vị trí công việc",
            "Trạng thái lao động (*)",
            "Ngày sinh",
            "Email cá nhân",
            "Email cơ quan",
            "Email tài khoản",
            "Ngày thử việc",
        ]
        df = self._read_excel(
            self.paths.employees_file,
            sheet_name="Danh sách nhân viên",
            skiprows=3,
            usecols=self._build_usecols(required),
        )
        self._ensure_columns(df, required, self.paths.employees_file)
        region_map = self._load_employee_region_map()

        employees: list[Employee] = []
        for _, row in df.iterrows():
            employee_id = self._clean_str(row["Mã nhân viên (*)"])
            if not employee_id:
                continue
            company_email = self._clean_str(row["Email cơ quan"])
            employees.append(
                Employee(
                    employee_id=employee_id,
                    employee_name=str(row["Họ và tên (*)"]),
                    mobile_phone=self._clean_str(row["Điện thoại di động"]),
                    organization_unit=self._clean_str(row["Đơn vị công tác (*)"]),
                    employment_status=self._clean_str(row["Trạng thái lao động (*)"]),
                    job_position=self._clean_str(row["Vị trí công việc"]),
                    birthday=Order.parse_datetime(row["Ngày sinh"]),
                    personal_email=self._clean_str(row["Email cá nhân"]),
                    company_email=company_email,
                    account_email=self._clean_str(row["Email tài khoản"]),
                    trial_date=Order.parse_datetime(row["Ngày thử việc"]),
                    region_code=region_map.get(company_email) if company_email else None,
                )
            )
        return employees

    def load_territory_manager(self, employees: list[Employee]) -> TerritoryManager:
        return self._load_territory_manager_from_sheet(
            employees,
            sheet_name="Phân tuyến",
            area_column="commune",
            territory_prefix="territory",
        )

    def load_shipping_territory_manager(self, employees: list[Employee]) -> TerritoryManager:
        return self._load_territory_manager_from_sheet(
            self._clone_employees(employees),
            sheet_name="Phân tuyến Giao hàng",
            area_column="district",
            territory_prefix="shipping-territory",
        )

    def _load_territory_manager_from_sheet(
        self,
        employees: list[Employee],
        *,
        sheet_name: str,
        area_column: str,
        territory_prefix: str,
    ) -> TerritoryManager:
        if not self.paths.territory_file.exists():
            return TerritoryManager(employees=employees, territories=[])

        required = ["emp_id", "province", area_column]
        try:
            territory_df = self._read_excel(
                self.paths.territory_file,
                sheet_name=sheet_name,
                usecols=self._build_usecols(required),
            )
        except ValueError:
            return TerritoryManager(employees=employees, territories=[])

        self._ensure_columns(territory_df, required, self.paths.territory_file)

        territories = [
            Territory(
                territory_id=f"{territory_prefix}-{index + 1}",
                employee_email=str(row["emp_id"]).strip(),
                province=str(row["province"]).strip(),
                commune=str(row[area_column]).strip(),
            )
            for index, row in territory_df.iterrows()
            if self._clean_str(row["emp_id"]) and self._clean_str(row["province"]) and self._clean_str(row[area_column])
        ]
        return TerritoryManager(employees=employees, territories=territories)

    def load_purchase_orders(self) -> list[Order]:
        return self._load_order_file(
            path=self.paths.purchase_orders_file,
            order_sheet="Danh sách",
            item_sheet="Bảng hàng hóa",
            order_column_map={
                "number": "Số đơn hàng",
                "order_date": "Ngày đặt hàng",
                "customer_id": "Mã khách hàng",
                "order_value": "Giá trị đơn hàng",
                "payment_due": "Ngày ghi sổ",
                "status": "Tình trạng ghi doanh số",
                "owner_name": "Người thực hiện",
                "phone_number": "Điện thoại",
                "shipping_address": "Số nhà, Đường phố (Giao hàng)",
                "shipping_ward": "Phường/Xã (Giao hàng)",
                "shipping_district": "Quận/Huyện (Giao hàng)",
                "shipping_province": "Tỉnh/Thành phố (Giao hàng)",
            },
            item_promotion_column="CTKM",
        )

    def load_sales_orders(self) -> list[Order]:
        return self._load_order_file(
            path=self.paths.sales_orders_file,
            order_sheet="Danh sách",
            item_sheet="Bảng hàng hóa",
            order_column_map={
                "number": "Số đơn hàng",
                "order_date": "Ngày đặt hàng",
                "customer_id": "Mã khách hàng",
                "order_value": "Giá trị đơn hàng",
                "payment_due": "Ngày ghi sổ",
                "status": "Tình trạng ghi doanh số",
                "owner_name": "Người thực hiện",
                "phone_number": None,
                "shipping_address": "Số nhà, Đường phố (Giao hàng)",
                "shipping_ward": "Phường/Xã (Giao hàng)",
                "shipping_district": "Quận/Huyện (Giao hàng)",
                "shipping_province": "Tỉnh/Thành phố (Giao hàng)",
            },
            item_promotion_column="Tỷ lệ chiết khấu",
        )

    def load_return_purchase_orders(self) -> list[Order]:
        return self._load_order_file(
            path=self.paths.return_purchase_orders_file,
            order_sheet="Danh sách",
            item_sheet="Bảng hàng hóa",
            order_column_map={
                "number": "Số đề nghị",
                "order_date": "Ngày đề nghị",
                "customer_id": "Mã khách hàng",
                "order_value": "Tổng tiền",
                "payment_due": "Ngày đề nghị",
                "status": "Tình trạng",
                "owner_name": "Người thực hiện",
                "phone_number": None,
                "shipping_address": None,
                "shipping_ward": None,
                "shipping_district": None,
                "shipping_province": None,
            },
            item_promotion_column=None,
        )

    def load_return_sales_orders(self) -> list[Order]:
        return self._load_order_file(
            path=self.paths.return_sales_orders_file,
            order_sheet="Danh sách",
            item_sheet="Bảng hàng hóa",
            order_column_map={
                "number": "Số đề nghị",
                "order_date": "Ngày đề nghị",
                "customer_id": "Mã khách hàng",
                "order_value": "Tổng tiền",
                "payment_due": "Ngày đề nghị",
                "status": "Tình trạng",
                "owner_name": "Người thực hiện",
                "phone_number": None,
                "shipping_address": None,
                "shipping_ward": None,
                "shipping_district": None,
                "shipping_province": None,
            },
            item_promotion_column=None,
        )

    def _load_order_file(
        self,
        *,
        path: Path,
        order_sheet: str,
        item_sheet: str,
        order_column_map: dict[str, str | None],
        item_promotion_column: str | None,
    ) -> list[Order]:
        required_order_columns = [column for column in order_column_map.values() if column]
        required_order_columns.extend([order_column_map["number"], order_column_map["order_date"], order_column_map["customer_id"]])

        required_item_columns = ["Mã hàng hóa", "Đơn vị tính", "SL theo ĐVTC", "Đơn giá sau thuế", "Thuế suất", "Thành tiền", "Tổng tiền"]
        if order_column_map["number"] == "Số đơn hàng":
            required_item_columns.insert(0, "Số đơn hàng")
        else:
            required_item_columns.insert(0, "Số đề nghị")
        if item_promotion_column:
            required_item_columns.append(item_promotion_column)

        order_df = self._read_excel(path, sheet_name=order_sheet, usecols=self._build_usecols(required_order_columns))
        item_df = self._read_excel(path, sheet_name=item_sheet, usecols=self._build_usecols(required_item_columns))
        item_df = item_df.dropna(subset=["Đơn vị tính"]) if "Đơn vị tính" in item_df.columns else item_df

        self._ensure_columns(order_df, required_order_columns, path)
        self._ensure_columns(item_df, required_item_columns, path)

        order_key = order_column_map["number"]
        orders_by_number: dict[str, Order] = {}
        for _, row in order_df.iterrows():
            order_number = self._clean_str(row[order_key])
            customer_id = self._clean_str(row[order_column_map["customer_id"]])
            if not order_number or not customer_id:
                continue
            orders_by_number[order_number] = Order(
                order_number=order_number,
                order_date=Order.parse_datetime(row[order_column_map["order_date"]]),
                customer_id=customer_id,
                order_value=self._to_float(row[order_column_map["order_value"]]),
                payment_due=Order.parse_datetime(row[order_column_map["payment_due"]]),
                status=self._clean_str(row[order_column_map["status"]]),
                owner_name=self._read_optional(row, order_column_map["owner_name"]),
                phone_number=self._read_optional(row, order_column_map["phone_number"]),
                shipping_address=self._read_optional(row, order_column_map["shipping_address"]),
                shipping_ward=self._read_optional(row, order_column_map["shipping_ward"]),
                shipping_district=self._read_optional(row, order_column_map["shipping_district"]),
                shipping_province=self._read_optional(row, order_column_map["shipping_province"]),
            )

        item_order_key = "Số đơn hàng" if "Số đơn hàng" in item_df.columns else "Số đề nghị"
        for _, row in item_df.iterrows():
            order_number = self._clean_str(row[item_order_key])
            if not order_number:
                continue
            order = orders_by_number.get(order_number)
            if order is None:
                continue
            order.add_item(
                OrderItem(
                    order_id=order_number,
                    product_id=str(row["Mã hàng hóa"]),
                    warehouse=None,
                    unit=self._clean_str(row["Đơn vị tính"]),
                    quantity=self._to_float(row["SL theo ĐVTC"]),
                    unit_price=self._to_float(row["Đơn giá sau thuế"]),
                    tax=self._to_float(row["Thuế suất"]),
                    amount=self._to_float(row["Thành tiền"]),
                    total=self._to_float(row["Tổng tiền"]),
                    promotion=self._read_optional(row, item_promotion_column),
                )
            )

        return list(orders_by_number.values())

    @staticmethod
    def _read_excel(
        path: Path,
        *,
        sheet_name: str,
        skiprows: int = 0,
        usecols: list[str] | Callable[[str], bool] | None = None,
    ) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(f"Khong tim thay file du lieu: {path}")
        return pd.read_excel(
            path,
            sheet_name=sheet_name,
            engine="openpyxl",
            skiprows=skiprows,
            usecols=usecols,
        )

    @staticmethod
    def _ensure_columns(df: pd.DataFrame, required_columns: list[str], path: Path) -> None:
        missing = [column for column in required_columns if column not in df.columns]
        if missing:
            raise DataValidationError(f"File {path.name} thieu cot: {missing}")

    @staticmethod
    def _clean_str(value: Any) -> str | None:
        if value is None or pd.isna(value):
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _to_float(value: Any) -> float:
        if value is None or pd.isna(value):
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip().replace(",", "")
        if not text:
            return 0.0
        if text.endswith("%"):
            text = text[:-1]
        try:
            return float(text)
        except ValueError:
            return 0.0

    def _read_optional(self, row: pd.Series, column_name: str | None) -> str | None:
        if not column_name:
            return None
        return self._clean_str(row[column_name])

    def _load_employee_region_map(self) -> dict[str, str]:
        if not self.paths.territory_file.exists():
            return {}
        try:
            required = ["Email cơ quan", "Phân vùng"]
            df = self._read_excel(
                self.paths.territory_file,
                sheet_name="Phân Vùng",
                usecols=self._build_usecols(required),
            )
        except ValueError:
            return {}

        self._ensure_columns(df, required, self.paths.territory_file)
        region_map: dict[str, str] = {}
        for _, row in df.iterrows():
            email = self._clean_str(row["Email cơ quan"])
            region = self._clean_str(row["Phân vùng"])
            if email and region:
                region_map[email] = region
        return region_map

    @staticmethod
    def _emit_progress(progress_callback: ProgressCallback | None, message: str) -> None:
        if progress_callback is not None:
            progress_callback(message)

    @staticmethod
    def _clone_employees(employees: list[Employee]) -> list[Employee]:
        return [
            Employee(
                employee_id=employee.employee_id,
                employee_name=employee.employee_name,
                mobile_phone=employee.mobile_phone,
                organization_unit=employee.organization_unit,
                employment_status=employee.employment_status,
                job_position=employee.job_position,
                birthday=employee.birthday,
                personal_email=employee.personal_email,
                company_email=employee.company_email,
                account_email=employee.account_email,
                trial_date=employee.trial_date,
                region_code=employee.region_code,
            )
            for employee in employees
        ]

    @staticmethod
    def _build_usecols(columns: list[str]) -> Callable[[str], bool]:
        allowed = set(columns)
        return lambda column_name: column_name in allowed
