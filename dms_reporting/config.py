from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .constants import DEFAULT_RETURN_ORDER_STATUSES, DEFAULT_SALES_ORDER_STATUSES


@dataclass(frozen=True, slots=True)
class CompanyFileSpec:
    key: str
    label: str
    exact_name: str
    patterns: tuple[str, ...] = ()


def resolve_company_file(company_dir: Path, exact_name: str, *patterns: str) -> Path:
    exact_path = company_dir / exact_name
    if exact_path.exists():
        return exact_path

    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(
            path
            for path in company_dir.glob(pattern)
            if path.is_file() and not path.name.startswith("~$")
        )

    if matches:
        return sorted(matches, key=lambda path: (path.stat().st_mtime, path.name), reverse=True)[0]

    return exact_path


COMPANY_FILE_SPECS: dict[str, CompanyFileSpec] = {
    "products": CompanyFileSpec(
        key="products",
        label="Danh mục sản phẩm",
        exact_name="CRM_Product.xlsx",
        patterns=("CRM_Product*.xlsx",),
    ),
    "customers": CompanyFileSpec(
        key="customers",
        label="Danh sách khách hàng",
        exact_name="CRM_Account.xlsx",
        patterns=("CRM_Account*.xlsx",),
    ),
    "employees": CompanyFileSpec(
        key="employees",
        label="Danh sách nhân viên",
        exact_name="Danh sách nhân viên.xlsx",
    ),
    "territory": CompanyFileSpec(
        key="territory",
        label="Phân tuyến",
        exact_name="PhanTuyen.xlsx",
    ),
    "purchase_orders": CompanyFileSpec(
        key="purchase_orders",
        label="Đơn hàng bán ra",
        exact_name="CRM_Saleorder.xlsx",
    ),
    "sales_orders": CompanyFileSpec(
        key="sales_orders",
        label="Đơn hàng nhà phân phối",
        exact_name="CRM_Distributor.xlsx",
    ),
    "return_purchase_orders": CompanyFileSpec(
        key="return_purchase_orders",
        label="Đơn hàng trả lại",
        exact_name="CRM_Returnsale.xlsx",
    ),
    "return_sales_orders": CompanyFileSpec(
        key="return_sales_orders",
        label="Đơn trả lại nhà phân phối",
        exact_name="CRM_Returndistributor.xlsx",
    ),
}

CORE_COMPANY_FILE_KEYS: tuple[str, ...] = ("customers", "products")


def get_company_file_spec(file_key: str) -> CompanyFileSpec:
    return COMPANY_FILE_SPECS[file_key]


def resolve_company_file_spec(company_dir: Path, file_key: str) -> Path:
    spec = get_company_file_spec(file_key)
    return resolve_company_file(company_dir, spec.exact_name, *spec.patterns)


def missing_company_files(company_dir: Path, file_keys: Iterable[str]) -> list[CompanyFileSpec]:
    missing_specs: list[CompanyFileSpec] = []
    for file_key in file_keys:
        spec = get_company_file_spec(file_key)
        if not resolve_company_file(company_dir, spec.exact_name, *spec.patterns).exists():
            missing_specs.append(spec)
    return missing_specs


def format_company_file_requirement(spec: CompanyFileSpec) -> str:
    if not spec.patterns:
        return spec.exact_name
    pattern_text = ", ".join(spec.patterns)
    return f"{spec.exact_name} hoặc {pattern_text}"


@dataclass(slots=True)
class CompanyPaths:
    base_dir: Path
    company_code: str

    @property
    def company_dir(self) -> Path:
        return self.base_dir / "modules" / self.company_code

    @property
    def report_dir(self) -> Path:
        return self.company_dir / "report"

    @property
    def products_file(self) -> Path:
        return resolve_company_file_spec(self.company_dir, "products")

    @property
    def customers_file(self) -> Path:
        return resolve_company_file_spec(self.company_dir, "customers")

    @property
    def employees_file(self) -> Path:
        return resolve_company_file_spec(self.company_dir, "employees")

    @property
    def territory_file(self) -> Path:
        return resolve_company_file_spec(self.company_dir, "territory")

    @property
    def purchase_orders_file(self) -> Path:
        return resolve_company_file_spec(self.company_dir, "purchase_orders")

    @property
    def sales_orders_file(self) -> Path:
        return resolve_company_file_spec(self.company_dir, "sales_orders")

    @property
    def return_purchase_orders_file(self) -> Path:
        return resolve_company_file_spec(self.company_dir, "return_purchase_orders")

    @property
    def return_sales_orders_file(self) -> Path:
        return resolve_company_file_spec(self.company_dir, "return_sales_orders")

    def ensure_report_dir(self) -> Path:
        self.report_dir.mkdir(parents=True, exist_ok=True)
        return self.report_dir


@dataclass(slots=True)
class ReportSettings:
    start_date: str
    end_date: str
    sales_order_statuses: list[str] = field(default_factory=lambda: list(DEFAULT_SALES_ORDER_STATUSES))
    return_order_statuses: list[str] = field(default_factory=lambda: list(DEFAULT_RETURN_ORDER_STATUSES))
    months: list[int] = field(default_factory=lambda: list(range(1, 13)))
