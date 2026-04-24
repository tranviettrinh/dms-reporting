from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .constants import DEFAULT_STATUSES


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
        return self.company_dir / "CRM_Product.xlsx"

    @property
    def customers_file(self) -> Path:
        return self.company_dir / "CRM_Account.xlsx"

    @property
    def employees_file(self) -> Path:
        return self.company_dir / "Danh sách nhân viên.xlsx"

    @property
    def territory_file(self) -> Path:
        return self.company_dir / "PhanTuyen.xlsx"

    @property
    def purchase_orders_file(self) -> Path:
        return self.company_dir / "CRM_Saleorder.xlsx"

    @property
    def sales_orders_file(self) -> Path:
        return self.company_dir / "CRM_Distributor.xlsx"

    @property
    def return_purchase_orders_file(self) -> Path:
        return self.company_dir / "CRM_Returnsale.xlsx"

    @property
    def return_sales_orders_file(self) -> Path:
        return self.company_dir / "CRM_Returndistributor.xlsx"

    def ensure_report_dir(self) -> Path:
        self.report_dir.mkdir(parents=True, exist_ok=True)
        return self.report_dir


@dataclass(slots=True)
class ReportSettings:
    start_date: str
    end_date: str
    statuses: list[str] = field(default_factory=lambda: list(DEFAULT_STATUSES))
    months: list[int] = field(default_factory=lambda: list(range(1, 13)))
