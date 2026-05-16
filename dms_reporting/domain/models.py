from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Iterable

from dateutil import parser


@dataclass(slots=True)
class Product:
    product_id: str
    name: str
    category: str | None
    primary_unit: str | None
    price: float
    tax: float | None = None


@dataclass(slots=True)
class Customer:
    account_number: str
    account_name: str
    account_type: str | None
    sign_date: datetime | None
    phone: str | None
    billing_street: str | None
    billing_ward: str | None
    billing_district: str | None
    billing_province: str | None
    billing_address: str | None
    tax_code: str | None
    owner_name: str | None
    description: str | None
    visiting_last_day: datetime | None
    date_of_birthday: datetime | None
    is_distributor: str | None
    unit: str | None
    shipping_street: str | None = None
    shipping_ward: str | None = None
    shipping_district: str | None = None
    shipping_province: str | None = None
    shipping_address: str | None = None

    @property
    def region(self) -> str:
        unit = (self.unit or "").lower()
        if "miền bắc" in unit:
            return "Miền Bắc"
        if "miền nam" in unit:
            return "Miền Nam"
        if "miền trung" in unit:
            return "Miền Trung"
        return "Khác"

    @property
    def owner_employee_id(self) -> str | None:
        if not self.owner_name:
            return None
        match = re.search(r"\(([^)]+)\)", self.owner_name)
        return match.group(1).strip() if match else None

    @property
    def is_distributor_customer(self) -> bool:
        if not self.is_distributor:
            return False
        normalized = self.is_distributor.strip().lower()
        return normalized not in {"0", "false", "no", "không", "khong", "none", "nan"}

    @property
    def shipping_street_value(self) -> str | None:
        return self.shipping_street or self.billing_street

    @property
    def shipping_ward_value(self) -> str | None:
        return self.shipping_ward or self.billing_ward

    @property
    def shipping_district_value(self) -> str | None:
        return self.shipping_district or self.billing_district

    @property
    def shipping_province_value(self) -> str | None:
        return self.shipping_province or self.billing_province

    @property
    def shipping_address_value(self) -> str | None:
        return self.shipping_address or self.billing_address

    @property
    def billing_full_address(self) -> str | None:
        return self._compose_full_address(
            street=self.billing_street,
            ward=self.billing_ward,
            district=self.billing_district,
            province=self.billing_province,
            full_address=self.billing_address,
        )

    @property
    def shipping_full_address(self) -> str | None:
        return self._compose_full_address(
            street=self.shipping_street_value,
            ward=self.shipping_ward_value,
            district=self.shipping_district_value,
            province=self.shipping_province_value,
            full_address=self.shipping_address_value,
        )

    @staticmethod
    def _compose_full_address(
        *,
        street: str | None,
        ward: str | None,
        district: str | None,
        province: str | None,
        full_address: str | None,
    ) -> str | None:
        if full_address:
            return full_address
        parts = [street, ward, district, province]
        joined = ", ".join(part for part in parts if part)
        return joined or None


@dataclass(slots=True)
class Employee:
    employee_id: str
    employee_name: str
    mobile_phone: str | None = None
    organization_unit: str | None = None
    employment_status: str | None = None
    job_position: str | None = None
    birthday: datetime | None = None
    personal_email: str | None = None
    company_email: str | None = None
    account_email: str | None = None
    trial_date: datetime | None = None
    region_code: str | None = None
    territories: list["Territory"] = field(default_factory=list, repr=False)

    def add_territory(self, territory: "Territory") -> None:
        self.territories.append(territory)

    def is_active(self) -> bool:
        return self.employment_status == "Đang làm việc"


@dataclass(slots=True)
class Territory:
    territory_id: str
    employee_email: str
    province: str
    commune: str

    def matches(self, province: str | None, commune: str | None) -> bool:
        return self._normalize(self.province) == self._normalize(province) and self._normalize(self.commune) == self._normalize(commune)

    @staticmethod
    def _normalize(value: str | None) -> str:
        return " ".join((value or "").strip().upper().split())


@dataclass(slots=True)
class TerritoryManager:
    employees: list[Employee] = field(default_factory=list)
    territories: list[Territory] = field(default_factory=list)
    employees_by_id: dict[str, Employee] = field(init=False)
    employees_by_company_email: dict[str, Employee] = field(init=False)

    def __post_init__(self) -> None:
        self.employees_by_id = {employee.employee_id: employee for employee in self.employees}
        self.employees_by_company_email = {
            employee.company_email: employee
            for employee in self.employees
            if employee.company_email
        }
        for employee in self.employees:
            employee.territories.clear()
        for territory in self.territories:
            employee = self.employees_by_company_email.get(territory.employee_email)
            if employee is not None and employee.is_active():
                employee.add_territory(territory)

    def find_employee(self, *, employee_id: str | None = None, company_email: str | None = None) -> Employee | None:
        if employee_id:
            return self.employees_by_id.get(employee_id)
        if company_email:
            return self.employees_by_company_email.get(company_email)
        return None

    def find_employee_by_customer(self, customer: Customer) -> Employee | None:
        return self.find_employee(employee_id=customer.owner_employee_id)

    def evaluate_customer_assignment(self, customer: Customer) -> dict[str, object]:
        return self._evaluate_assignment(
            customer=customer,
            province=customer.billing_province,
            area=customer.billing_ward,
            missing_reason="Thiếu dữ liệu địa bàn hóa đơn của khách hàng",
            mismatch_reason="Địa bàn khách hàng không thuộc phân tuyến của nhân viên",
        )

    def evaluate_customer_shipping_assignment(self, customer: Customer) -> dict[str, object]:
        return self._evaluate_assignment(
            customer=customer,
            province=customer.shipping_province,
            area=customer.shipping_district,
            missing_reason="Thiếu dữ liệu địa bàn giao hàng của khách hàng",
            mismatch_reason="Địa bàn giao hàng của khách hàng không thuộc phân tuyến của nhân viên",
        )

    def _evaluate_assignment(
        self,
        *,
        customer: Customer,
        province: str | None,
        area: str | None,
        missing_reason: str,
        mismatch_reason: str,
    ) -> dict[str, object]:
        employee_id = customer.owner_employee_id
        if not employee_id:
            return {"is_correct": False, "reason": "Không tách được mã nhân viên từ chủ sở hữu", "employee": None}

        employee = self.find_employee(employee_id=employee_id)
        if employee is None:
            return {"is_correct": False, "reason": "Không tìm thấy nhân viên", "employee": None}
        if not employee.is_active():
            return {"is_correct": False, "reason": "Nhân viên không hoạt động", "employee": employee}
        if not province or not area:
            return {"is_correct": False, "reason": missing_reason, "employee": employee}

        is_match = any(
            territory.matches(province, area)
            for territory in employee.territories
        )
        if is_match:
            return {"is_correct": True, "reason": "", "employee": employee}
        return {"is_correct": False, "reason": mismatch_reason, "employee": employee}

    def is_customer_correctly_assigned(self, customer: Customer) -> bool:
        return bool(self.evaluate_customer_assignment(customer)["is_correct"])

    def get_wrong_assignments(self, customers: Iterable[Customer]) -> list[Customer]:
        return [customer for customer in customers if not self.is_customer_correctly_assigned(customer)]

    def get_inactive_employee_territories(self) -> list[dict[str, object]]:
        by_employee_id: dict[str, dict[str, object]] = {}

        for territory in self.territories:
            employee = self.employees_by_company_email.get(territory.employee_email)
            if employee is None or employee.is_active():
                continue

            payload = by_employee_id.setdefault(
                employee.employee_id,
                {"employee": employee, "territories": []},
            )
            payload["territories"].append(territory)

        return list(by_employee_id.values())


@dataclass(slots=True)
class OrderItem:
    order_id: str
    product_id: str
    warehouse: str | None
    unit: str | None
    quantity: float
    unit_price: float
    tax: float | None
    amount: float
    total: float
    promotion: str | None = None

    @property
    def is_promotion_item(self) -> bool:
        return self.total == 0


@dataclass(slots=True)
class Order:
    order_number: str
    order_date: datetime | None
    customer_id: str
    order_value: float
    payment_due: datetime | None
    status: str | None
    owner_name: str | None
    phone_number: str | None
    shipping_address: str | None
    shipping_ward: str | None
    shipping_district: str | None
    shipping_province: str | None
    items: list[OrderItem] = field(default_factory=list)

    def add_item(self, item: OrderItem) -> None:
        self.items.append(item)

    @staticmethod
    def parse_datetime(value: object) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        text = str(value).strip()
        if not text or text.lower() == "nan":
            return None
        return parser.parse(text)


@dataclass(slots=True)
class OrderBucket:
    purchase_orders: list[Order]
    sales_orders: list[Order]
    return_purchase_orders: list[Order]
    return_sales_orders: list[Order]

    def iter_all(self) -> Iterable[tuple[list[Order], int]]:
        yield self.purchase_orders, 1
        yield self.return_purchase_orders, -1
        yield self.sales_orders, 1
        yield self.return_sales_orders, -1


@dataclass(slots=True)
class DatasetBundle:
    products: list[Product]
    customers: list[Customer]
    orders: OrderBucket
    employees: list[Employee] = field(default_factory=list)
    territory_manager: TerritoryManager | None = None
    shipping_territory_manager: TerritoryManager | None = None
