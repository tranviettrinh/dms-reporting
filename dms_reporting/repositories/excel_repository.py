from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from dms_reporting.config import CompanyPaths
from dms_reporting.constants import EXCLUDED_CUSTOMER_CREATORS, EXCLUDED_CUSTOMER_TYPES
from dms_reporting.domain.models import Customer, DatasetBundle, Employee, Order, OrderBucket, OrderItem, Product, Territory, TerritoryManager


class DataValidationError(ValueError):
    pass


@dataclass(slots=True)
class ExcelCRMRepository:
    paths: CompanyPaths

    def load_dataset(self) -> DatasetBundle:
        employees = self.load_employees()
        territory_manager = self.load_territory_manager(employees)
        return DatasetBundle(
            products=self.load_products(),
            customers=self.load_customers(),
            orders=OrderBucket(
                purchase_orders=self.load_purchase_orders(),
                sales_orders=self.load_sales_orders(),
                return_purchase_orders=self.load_return_purchase_orders(),
                return_sales_orders=self.load_return_sales_orders(),
            ),
            employees=employees,
            territory_manager=territory_manager,
        )

    def load_products(self) -> list[Product]:
        df = self._read_excel(self.paths.products_file, sheet_name="Danh sách")
        required = ["Mã hàng hóa", "Tên hàng hóa", "Loại hàng hóa", "Đơn vị tính chính", "Đơn giá bán", "Thuế GTGT"]
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
        df = self._read_excel(self.paths.customers_file, sheet_name="Danh sách")
        required = [
            "Mã khách hàng", "Tên khách hàng", "Loại khách hàng", "Ngày ký hợp đồng", "Điện thoại",
            "Số nhà, Đường phố (Giao hàng)", "Phường/Xã (Giao hàng)", "Quận/Huyện (Giao hàng)",
            "Tỉnh/Thành phố (Giao hàng)", "Địa chỉ (Giao hàng)", "Mã số thuế", "Chủ sở hữu",
            "Mô tả", "Ngày ghé thăm gần nhất", "Ngày thành lập/Ngày sinh", "Là nhà phân phối", "Đơn vị", "Người tạo",
        ]
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

        df = self._read_excel(self.paths.employees_file, sheet_name="Danh sách nhân viên", skiprows=3)
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
        if not self.paths.territory_file.exists():
            return TerritoryManager(employees=employees, territories=[])

        territory_df = self._read_excel(self.paths.territory_file, sheet_name="Phân tuyến")
        required = ["emp_id", "province", "commune"]
        self._ensure_columns(territory_df, required, self.paths.territory_file)

        territories = [
            Territory(
                territory_id=f"territory-{index + 1}",
                employee_email=str(row["emp_id"]).strip(),
                province=str(row["province"]).strip(),
                commune=str(row["commune"]).strip(),
            )
            for index, row in territory_df.iterrows()
            if self._clean_str(row["emp_id"]) and self._clean_str(row["province"]) and self._clean_str(row["commune"])
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
        order_df = self._read_excel(path, sheet_name=order_sheet)
        item_df = self._read_excel(path, sheet_name=item_sheet)
        item_df = item_df.dropna(subset=["Đơn vị tính"]) if "Đơn vị tính" in item_df.columns else item_df

        required_order_columns = [column for column in order_column_map.values() if column]
        required_order_columns.extend([order_column_map["number"], order_column_map["order_date"], order_column_map["customer_id"]])
        self._ensure_columns(order_df, required_order_columns, path)

        required_item_columns = ["Mã hàng hóa", "Đơn vị tính", "SL theo ĐVTC", "Đơn giá sau thuế", "Thuế suất", "Thành tiền", "Tổng tiền"]
        if order_column_map["number"] == "Số đơn hàng":
            required_item_columns.insert(0, "Số đơn hàng")
        else:
            required_item_columns.insert(0, "Số đề nghị")
        if item_promotion_column:
            required_item_columns.append(item_promotion_column)
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
    def _read_excel(path: Path, *, sheet_name: str, skiprows: int = 0) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(f"Khong tim thay file du lieu: {path}")
        return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl", skiprows=skiprows)

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
            df = self._read_excel(self.paths.territory_file, sheet_name="Phân Vùng")
        except ValueError:
            return {}

        required = ["Email cơ quan", "Phân vùng"]
        self._ensure_columns(df, required, self.paths.territory_file)
        region_map: dict[str, str] = {}
        for _, row in df.iterrows():
            email = self._clean_str(row["Email cơ quan"])
            region = self._clean_str(row["Phân vùng"])
            if email and region:
                region_map[email] = region
        return region_map
