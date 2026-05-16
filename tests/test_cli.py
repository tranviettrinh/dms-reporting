from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

import dms_reporting.cli as cli
import dms_reporting.reporting as reporting
from dms_reporting.config import COMPANY_FILE_SPECS
from dms_reporting.domain.models import Customer, DatasetBundle, Employee, Order, OrderBucket, OrderItem, Product, Territory, TerritoryManager


def build_order(
    order_number: str,
    customer_id: str,
    month: int,
    items: list[tuple[str, float] | tuple[str, float, float]],
    status: str = "Đã ghi",
    owner_name: str = "Owner",
) -> Order:
    order = Order(
        order_number=order_number,
        order_date=datetime(2026, month, 1),
        customer_id=customer_id,
        order_value=sum(
            item[1] if len(item) == 2 else item[1] * item[2]
            for item in items
        ),
        payment_due=datetime(2026, month, 1),
        status=status,
        owner_name=owner_name,
        phone_number=None,
        shipping_address=None,
        shipping_ward=None,
        shipping_district=None,
        shipping_province=None,
    )
    for item in items:
        if len(item) == 2:
            product_id, total = item
            quantity = 1
            unit_price = total
        else:
            product_id, quantity, unit_price = item
            total = quantity * unit_price
        order.add_item(
            OrderItem(
                order_id=order_number,
                product_id=product_id,
                warehouse=None,
                unit="box",
                quantity=quantity,
                unit_price=unit_price,
                tax=0,
                amount=total,
                total=total,
                promotion=None,
            )
        )
    return order


def build_dataset() -> DatasetBundle:
    customer = Customer(
        account_number="C001",
        account_name="Khach A",
        account_type="1MB_HĐ001-OTC",
        sign_date=datetime(2026, 1, 10),
        phone=None,
        billing_street="99 Lê Lợi",
        billing_ward="Phường Lê Thanh Nghị",
        billing_district="Hải Dương",
        billing_province="Hải Dương",
        billing_address="99 Lê Lợi, Phường Lê Thanh Nghị, Hải Dương",
        tax_code=None,
        owner_name="Nguyễn Hữu Nam - Hải Dương 1 (ABN-2025-18)",
        description=None,
        visiting_last_day=None,
        date_of_birthday=None,
        is_distributor=None,
        unit="Kinh doanh OTC Miền Bắc khu vực 1",
        shipping_street="12 Nguyễn Trãi",
        shipping_ward="Xã Hồng Hưng",
        shipping_district="Thanh Hà",
        shipping_province="Hải Dương",
        shipping_address="12 Nguyễn Trãi, Xã Hồng Hưng, Hải Dương",
    )
    inactive_customer = Customer(
        account_number="C002",
        account_name="Khach B",
        account_type="1MB_HĐ001-OTC",
        sign_date=datetime(2026, 1, 10),
        phone=None,
        billing_street="88 Lý Thường Kiệt",
        billing_ward="Phường Tứ Minh",
        billing_district="Hải Dương",
        billing_province="Hải Dương",
        billing_address="88 Lý Thường Kiệt, Phường Tứ Minh, Hải Dương",
        tax_code=None,
        owner_name="Trần Văn Cũ - Hải Dương nghỉ (ABN-2024-99)",
        description=None,
        visiting_last_day=None,
        date_of_birthday=None,
        is_distributor=None,
        unit="Kinh doanh OTC Miền Bắc khu vực 1",
        shipping_street="34 Trần Hưng Đạo",
        shipping_ward="Xã Gia Xuyên",
        shipping_district="Tứ Kỳ",
        shipping_province="Hải Dương",
        shipping_address="34 Trần Hưng Đạo, Xã Gia Xuyên, Hải Dương",
    )
    correct_customer = Customer(
        account_number="C003",
        account_name="Khach C",
        account_type="1MB_HĐ001-OTC",
        sign_date=datetime(2026, 1, 10),
        phone=None,
        billing_street="77 Nguyễn Văn Linh",
        billing_ward="Xã Thanh Xuân",
        billing_district="Hải Dương",
        billing_province="Hải Dương",
        billing_address="77 Nguyễn Văn Linh, Xã Thanh Xuân, Hải Dương",
        tax_code=None,
        owner_name="Nguyễn Hữu Nam - Hải Dương 1 (ABN-2025-18)",
        description=None,
        visiting_last_day=None,
        date_of_birthday=None,
        is_distributor=None,
        unit="Kinh doanh OTC Miền Bắc khu vực 1",
        shipping_street="77 Nguyễn Văn Linh",
        shipping_ward="Xã Thanh Xuân",
        shipping_district="Nam Sách",
        shipping_province="Hải Dương",
        shipping_address="77 Nguyễn Văn Linh, Xã Thanh Xuân, Hải Dương",
    )
    employee = Employee(
        employee_id="ABN-2025-18",
        employee_name="Nguyễn Hữu Nam",
        employment_status="Đang làm việc",
        company_email="HAIDUONG01@com.vn",
    )
    inactive_employee = Employee(
        employee_id="ABN-2024-99",
        employee_name="Trần Văn Cũ",
        employment_status="Đã nghỉ việc",
        company_email="HAIDUONG99@com.vn",
    )
    shipping_employee = Employee(
        employee_id="ABN-2025-18",
        employee_name="Nguyễn Hữu Nam",
        employment_status="Đang làm việc",
        company_email="HAIDUONG01@com.vn",
    )
    shipping_inactive_employee = Employee(
        employee_id="ABN-2024-99",
        employee_name="Trần Văn Cũ",
        employment_status="Đã nghỉ việc",
        company_email="HAIDUONG99@com.vn",
    )
    territory_manager = TerritoryManager(
        employees=[employee, inactive_employee],
        territories=[
            Territory(
                territory_id="territory-1",
                employee_email="HAIDUONG01@com.vn",
                province="Hải Dương",
                commune="Xã Thanh Xuân",
            ),
            Territory(
                territory_id="territory-2",
                employee_email="HAIDUONG99@com.vn",
                province="Hải Dương",
                commune="Xã Gia Xuyên",
            ),
        ],
    )
    shipping_territory_manager = TerritoryManager(
        employees=[shipping_employee, shipping_inactive_employee],
        territories=[
            Territory(
                territory_id="shipping-territory-1",
                employee_email="HAIDUONG01@com.vn",
                province="Hải Dương",
                commune="Thanh Hà",
            ),
            Territory(
                territory_id="shipping-territory-2",
                employee_email="HAIDUONG99@com.vn",
                province="Hải Dương",
                commune="Tứ Kỳ",
            ),
        ],
    )
    return DatasetBundle(
        products=[
            Product(product_id="PDD", name="Dong duoc", category="NHÓM THUỐC ĐÔNG DƯỢC", primary_unit="box", price=100, tax=0),
            Product(product_id="PTD", name="Tan duoc", category="NHÓM THUỐC TÂN DƯỢC", primary_unit="box", price=200, tax=0),
            Product(product_id="TPCN", name="TPCN", category="THỰC PHẨM CHỨC NĂNG", primary_unit="box", price=300, tax=0),
        ],
        customers=[customer, inactive_customer, correct_customer],
        orders=OrderBucket(
            purchase_orders=[
                build_order("PO-1", "C001", 1, [("PDD", 100), ("PTD", 200), ("TPCN", 300)]),
                build_order("PO-2", "C001", 5, [("PDD", 5, 100)]),
            ],
            sales_orders=[],
            return_purchase_orders=[],
            return_sales_orders=[],
        ),
        employees=[employee, inactive_employee],
        territory_manager=territory_manager,
        shipping_territory_manager=shipping_territory_manager,
    )


def create_company_dir_with_excel_files(base_dir: Path, *file_names: str) -> Path:
    company_dir = base_dir / "modules" / "abipha"
    company_dir.mkdir(parents=True, exist_ok=True)
    selected_file_names = file_names or tuple(spec.exact_name for spec in COMPANY_FILE_SPECS.values())
    for file_name in selected_file_names:
        (company_dir / file_name).touch()
    return company_dir


def test_cli_writes_summary_detail_and_territory_reports(tmp_path, monkeypatch):
    monkeypatch.setattr(reporting.ExcelCRMRepository, "load_dataset", lambda self: build_dataset())
    create_company_dir_with_excel_files(tmp_path)

    exit_code = cli.main(
        [
            "--company",
            "abipha",
            "--start-date",
            "2026-01-01",
            "--end-date",
            "2026-12-31",
            "--base-dir",
            str(tmp_path),
        ]
    )

    summary_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo doanh số khách hàng abipha.xlsx"
    detail_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo doanh số nhóm sản phẩm abipha.xlsx"
    employee_product_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo doanh thu sản lượng sản phẩm theo nhân viên abipha.xlsx"
    first_sales_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng phát sinh doanh số lần đầu abipha.xlsx"
    correct_territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng gán đúng địa bàn abipha.xlsx"
    territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng sai địa bàn abipha.xlsx"
    inactive_territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo nhân viên đã nghỉ còn trong phân tuyến abipha.xlsx"
    inactive_customer_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng còn gán cho nhân viên đã nghỉ việc abipha.xlsx"
    correct_shipping_territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng gán đúng địa bàn Giao hàng abipha.xlsx"
    shipping_territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng sai địa bàn Giao hàng abipha.xlsx"

    assert exit_code == 0
    assert summary_path.exists()
    assert detail_path.exists()
    assert employee_product_path.exists()
    assert first_sales_path.exists()
    assert correct_territory_path.exists()
    assert territory_path.exists()
    assert inactive_territory_path.exists()
    assert inactive_customer_path.exists()
    assert correct_shipping_territory_path.exists()
    assert shipping_territory_path.exists()

    detail_df = pd.read_excel(detail_path, sheet_name="Cả nước", engine="openpyxl")
    employee_product_df = pd.read_excel(employee_product_path, sheet_name="Tháng 1", engine="openpyxl")
    employee_product_month_2_df = pd.read_excel(employee_product_path, sheet_name="Tháng 2", engine="openpyxl")
    first_sales_df = pd.read_excel(first_sales_path, sheet_name="Tháng 1", engine="openpyxl")
    first_sales_month_2_df = pd.read_excel(first_sales_path, sheet_name="Tháng 2", engine="openpyxl")
    summary_df = pd.read_excel(summary_path, sheet_name="Cả nước", engine="openpyxl")
    correct_territory_df = pd.read_excel(correct_territory_path, sheet_name="Đúng địa bàn", engine="openpyxl")
    territory_df = pd.read_excel(territory_path, sheet_name="Sai địa bàn", engine="openpyxl")
    inactive_territory_df = pd.read_excel(inactive_territory_path, sheet_name="Nhân viên đã nghỉ", engine="openpyxl")
    inactive_customer_df = pd.read_excel(inactive_customer_path, sheet_name="Khách hàng gán NV nghỉ", engine="openpyxl")
    correct_shipping_territory_df = pd.read_excel(correct_shipping_territory_path, sheet_name="Đúng địa bàn GH", engine="openpyxl")
    shipping_territory_df = pd.read_excel(shipping_territory_path, sheet_name="Sai địa bàn GH", engine="openpyxl")
    assert summary_df.loc[0, "Địa chỉ giao hàng đầy đủ"] == "12 Nguyễn Trãi, Xã Hồng Hưng, Hải Dương"
    assert summary_df.loc[0, "Địa chỉ hóa đơn đầy đủ"] == "99 Lê Lợi, Phường Lê Thanh Nghị, Hải Dương"
    assert "Tháng 1 (Đông dược)" in detail_df.columns
    assert detail_df.loc[0, "Tháng 1 (TPCN)"] == 300
    assert detail_df.loc[0, "Địa chỉ giao hàng đầy đủ"] == "12 Nguyễn Trãi, Xã Hồng Hưng, Hải Dương"
    assert detail_df.loc[0, "Địa chỉ hóa đơn đầy đủ"] == "99 Lê Lợi, Phường Lê Thanh Nghị, Hải Dương"
    assert employee_product_df.loc[0, "Mã sản phẩm"] == "PDD"
    assert employee_product_df.loc[0, "Sản lượng thuần"] == 1
    assert employee_product_df.loc[0, "Doanh thu thuần"] == 100
    assert employee_product_month_2_df.empty
    assert first_sales_df.loc[0, "Mã khách hàng"] == "C001"
    assert first_sales_df.loc[0, "Số đơn hàng đầu tiên"] == "PO-1"
    assert first_sales_month_2_df.empty
    assert len(correct_territory_df) == 1
    assert correct_territory_df.loc[0, "Mã khách hàng"] == "C003"
    assert correct_territory_df.loc[0, "Phường/Xã (Hóa đơn)"] == "Xã Thanh Xuân"
    assert correct_territory_df.loc[0, "Địa bàn phân tuyến hợp lệ"] == "Hải Dương - Xã Thanh Xuân"
    assert correct_territory_df.loc[0, "Lý do"] == "Khách hàng thuộc đúng phân tuyến của nhân viên"
    assert len(territory_df) == 1
    assert territory_df.loc[0, "Tỉnh/Thành phố (Hóa đơn)"] == "Hải Dương"
    assert territory_df.loc[0, "Phường/Xã (Hóa đơn)"] == "Phường Lê Thanh Nghị"
    assert territory_df.loc[0, "Địa bàn phân tuyến hợp lệ"] == "Hải Dương - Xã Thanh Xuân"
    assert territory_df.loc[0, "Địa chỉ giao hàng đầy đủ"] == "12 Nguyễn Trãi, Xã Hồng Hưng, Hải Dương"
    assert territory_df.loc[0, "Địa chỉ hóa đơn đầy đủ"] == "99 Lê Lợi, Phường Lê Thanh Nghị, Hải Dương"
    assert territory_df.loc[0, "Lý do"] == "Địa bàn khách hàng không thuộc phân tuyến của nhân viên"
    assert inactive_territory_df.loc[0, "Mã nhân viên"] == "ABN-2024-99"
    assert inactive_territory_df.loc[0, "Địa bàn còn trong file phân tuyến"] == "Hải Dương - Xã Gia Xuyên"
    assert inactive_customer_df.loc[0, "Mã khách hàng"] == "C002"
    assert inactive_customer_df.loc[0, "Mã nhân viên"] == "ABN-2024-99"
    assert inactive_customer_df.loc[0, "Lý do"] == "Khách hàng vẫn đang gán cho nhân viên đã nghỉ việc"
    assert len(correct_shipping_territory_df) == 1
    assert correct_shipping_territory_df.loc[0, "Mã khách hàng"] == "C001"
    assert correct_shipping_territory_df.loc[0, "Quận/Huyện (Giao hàng)"] == "Thanh Hà"
    assert correct_shipping_territory_df.loc[0, "Địa bàn phân tuyến giao hàng hợp lệ"] == "Hải Dương - Thanh Hà"
    assert correct_shipping_territory_df.loc[0, "Lý do"] == "Khách hàng thuộc đúng phân tuyến giao hàng của nhân viên"
    assert len(shipping_territory_df) == 1
    assert shipping_territory_df.loc[0, "Mã khách hàng"] == "C003"
    assert shipping_territory_df.loc[0, "Quận/Huyện (Giao hàng)"] == "Nam Sách"
    assert shipping_territory_df.loc[0, "Địa bàn phân tuyến giao hàng hợp lệ"] == "Hải Dương - Thanh Hà"
    assert shipping_territory_df.loc[0, "Lý do"] == "Địa bàn giao hàng của khách hàng không thuộc phân tuyến của nhân viên"


def test_cli_territory_only_writes_only_territory_report(tmp_path, monkeypatch):
    monkeypatch.setattr(reporting.ExcelCRMRepository, "load_dataset", lambda self: build_dataset())
    create_company_dir_with_excel_files(tmp_path)

    exit_code = cli.main(
        [
            "--company",
            "abipha",
            "--territory-only",
            "--base-dir",
            str(tmp_path),
        ]
    )

    summary_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo doanh số khách hàng abipha.xlsx"
    detail_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo doanh số nhóm sản phẩm abipha.xlsx"
    employee_product_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo doanh thu sản lượng sản phẩm theo nhân viên abipha.xlsx"
    first_sales_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng phát sinh doanh số lần đầu abipha.xlsx"
    correct_territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng gán đúng địa bàn abipha.xlsx"
    territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng sai địa bàn abipha.xlsx"
    inactive_territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo nhân viên đã nghỉ còn trong phân tuyến abipha.xlsx"
    inactive_customer_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng còn gán cho nhân viên đã nghỉ việc abipha.xlsx"
    correct_shipping_territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng gán đúng địa bàn Giao hàng abipha.xlsx"
    shipping_territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng sai địa bàn Giao hàng abipha.xlsx"

    assert exit_code == 0
    assert not summary_path.exists()
    assert not detail_path.exists()
    assert not employee_product_path.exists()
    assert not first_sales_path.exists()
    assert correct_territory_path.exists()
    assert territory_path.exists()
    assert inactive_territory_path.exists()
    assert inactive_customer_path.exists()
    assert correct_shipping_territory_path.exists()
    assert shipping_territory_path.exists()


def test_available_companies_ignores_hidden_directories(tmp_path):
    (tmp_path / "modules" / "abipha").mkdir(parents=True)
    (tmp_path / "modules" / "ginic").mkdir()
    (tmp_path / "modules" / "__pycache__").mkdir()
    (tmp_path / "modules" / ".hidden").mkdir()

    assert reporting.available_companies(tmp_path) == ["abipha", "ginic"]


def test_cli_reports_option_writes_selected_reports_only(tmp_path, monkeypatch):
    monkeypatch.setattr(reporting.ExcelCRMRepository, "load_dataset", lambda self: build_dataset())
    create_company_dir_with_excel_files(tmp_path)

    exit_code = cli.main(
        [
            "--company",
            "abipha",
            "--reports",
            "summary",
            "invoice-territory",
            "--start-date",
            "2026-01-01",
            "--end-date",
            "2026-12-31",
            "--base-dir",
            str(tmp_path),
        ]
    )

    summary_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo doanh số khách hàng abipha.xlsx"
    detail_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo doanh số nhóm sản phẩm abipha.xlsx"
    employee_product_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo doanh thu sản lượng sản phẩm theo nhân viên abipha.xlsx"
    first_sales_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng phát sinh doanh số lần đầu abipha.xlsx"
    correct_territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng gán đúng địa bàn abipha.xlsx"
    territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng sai địa bàn abipha.xlsx"
    inactive_territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo nhân viên đã nghỉ còn trong phân tuyến abipha.xlsx"
    inactive_customer_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng còn gán cho nhân viên đã nghỉ việc abipha.xlsx"
    correct_shipping_territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng gán đúng địa bàn Giao hàng abipha.xlsx"
    shipping_territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng sai địa bàn Giao hàng abipha.xlsx"

    assert exit_code == 0
    assert summary_path.exists()
    assert correct_territory_path.exists()
    assert territory_path.exists()
    assert inactive_territory_path.exists()
    assert inactive_customer_path.exists()
    assert not detail_path.exists()
    assert not employee_product_path.exists()
    assert not first_sales_path.exists()
    assert not correct_shipping_territory_path.exists()
    assert not shipping_territory_path.exists()


def test_generate_reports_allows_territory_subset_without_dates(tmp_path, monkeypatch):
    monkeypatch.setattr(reporting.ExcelCRMRepository, "load_dataset", lambda self: build_dataset())
    create_company_dir_with_excel_files(tmp_path)

    result = reporting.generate_reports(
        reporting.ReportRequest(
            company="abipha",
            base_dir=tmp_path,
            selected_reports=("territory", "inactive-customer"),
        )
    )

    generated_labels = [report.label for report in result.generated_reports]

    assert generated_labels == [
        "Báo cáo khách hàng sai địa bàn",
        "Báo cáo khách hàng còn gán cho nhân viên đã nghỉ việc",
    ]


def test_generate_reports_invoice_territory_group_writes_all_territory_reports_without_dates(tmp_path, monkeypatch):
    monkeypatch.setattr(reporting.ExcelCRMRepository, "load_dataset", lambda self: build_dataset())
    create_company_dir_with_excel_files(tmp_path)

    result = reporting.generate_reports(
        reporting.ReportRequest(
            company="abipha",
            base_dir=tmp_path,
            selected_reports=("invoice-territory",),
        )
    )

    generated_labels = [report.label for report in result.generated_reports]

    assert generated_labels == [
        "Báo cáo khách hàng gán đúng địa bàn",
        "Báo cáo khách hàng sai địa bàn",
        "Báo cáo nhân viên đã nghỉ còn trong phân tuyến",
        "Báo cáo khách hàng còn gán cho nhân viên đã nghỉ việc",
    ]


def test_generate_reports_writes_combined_customer_territory_report(tmp_path, monkeypatch):
    monkeypatch.setattr(reporting.ExcelCRMRepository, "load_dataset", lambda self: build_dataset())
    create_company_dir_with_excel_files(tmp_path)

    result = reporting.generate_reports(
        reporting.ReportRequest(
            company="abipha",
            base_dir=tmp_path,
            selected_reports=("combined-territory",),
        )
    )

    assert [report.label for report in result.generated_reports] == [
        "Báo cáo phân tuyến KH Hoá đơn + Giao hàng",
    ]

    report_path = (
        tmp_path
        / "modules"
        / "abipha"
        / "report"
        / "Báo cáo phân tuyến khách hàng Hoá đơn và Giao hàng abipha.xlsx"
    )
    assert report_path.exists()

    combined_df = pd.read_excel(report_path, sheet_name="Tổng hợp", engine="openpyxl")
    issues_df = pd.read_excel(report_path, sheet_name="Cần xử lý", engine="openpyxl")

    assert len(combined_df) == 3
    assert len(issues_df) == 3

    customer_rows = {row["Mã khách hàng"]: row for _, row in combined_df.iterrows()}
    assert customer_rows["C001"]["Kết quả địa chỉ Hóa đơn"] == "Sai"
    assert customer_rows["C001"]["Kết quả địa chỉ Giao hàng"] == "Đúng"
    assert customer_rows["C001"]["Kết luận tổng hợp"] == "Sai địa chỉ Hoá đơn"
    assert customer_rows["C003"]["Kết quả địa chỉ Hóa đơn"] == "Đúng"
    assert customer_rows["C003"]["Kết quả địa chỉ Giao hàng"] == "Sai"
    assert customer_rows["C003"]["Kết luận tổng hợp"] == "Sai địa chỉ Giao hàng"


def test_generate_reports_requires_dates_for_sales_reports(tmp_path):
    create_company_dir_with_excel_files(tmp_path)

    with pytest.raises(ValueError, match="start date và end date"):
        reporting.generate_reports(
            reporting.ReportRequest(
                company="abipha",
                base_dir=tmp_path,
                selected_reports=("summary",),
            )
        )


def test_generate_reports_lists_missing_excel_files_for_sales_reports(tmp_path):
    company_dir = tmp_path / "modules" / "abipha"
    company_dir.mkdir(parents=True)
    (company_dir / "CRM_Account.xlsx").touch()
    (company_dir / "CRM_Product.xlsx").touch()

    with pytest.raises(ValueError) as exc_info:
        reporting.generate_reports(
            reporting.ReportRequest(
                company="abipha",
                base_dir=tmp_path,
                start_date="2026-01-01",
                end_date="2026-12-31",
                selected_reports=("summary",),
            )
        )

    error_message = str(exc_info.value)

    assert "Thiếu file Excel để tạo báo cáo" in error_message
    assert "CRM_Saleorder.xlsx" in error_message
    assert "CRM_Distributor.xlsx" in error_message
    assert "CRM_Returnsale.xlsx" in error_message
    assert "CRM_Returndistributor.xlsx" in error_message


def test_generate_reports_lists_only_territory_files_needed_for_territory_reports(tmp_path):
    company_dir = tmp_path / "modules" / "abipha"
    company_dir.mkdir(parents=True)
    (company_dir / "CRM_Account.xlsx").touch()

    with pytest.raises(ValueError) as exc_info:
        reporting.generate_reports(
            reporting.ReportRequest(
                company="abipha",
                base_dir=tmp_path,
                selected_reports=("invoice-territory",),
            )
        )

    error_message = str(exc_info.value)

    assert "Thiếu file Excel để tạo báo cáo" in error_message
    assert "Danh sách nhân viên" in error_message
    assert "PhanTuyen.xlsx" in error_message
    assert "CRM_Product.xlsx" not in error_message
    assert "CRM_Saleorder.xlsx" not in error_message


def test_generate_reports_rejects_unauthorized_report_selection(tmp_path):
    create_company_dir_with_excel_files(tmp_path)

    with pytest.raises(ValueError, match="không được phép chạy"):
        reporting.generate_reports(
            reporting.ReportRequest(
                company="abipha",
                base_dir=tmp_path,
                start_date="2026-01-01",
                end_date="2026-12-31",
                selected_reports=("summary", "detail"),
                authorized_reports=("summary",),
            )
        )


def test_generate_reports_uses_custom_sales_and_return_statuses(tmp_path, monkeypatch):
    dataset = build_dataset()
    dataset.orders.purchase_orders.append(build_order("PO-3", "C001", 2, [("PDD", 1.6, 100)], status="Đề nghị ghi"))
    dataset.orders.return_purchase_orders.append(build_order("RPO-1", "C001", 2, [("PDD", 1, 100)], status="Đã duyệt"))
    monkeypatch.setattr(reporting.ExcelCRMRepository, "load_dataset", lambda self: dataset)
    create_company_dir_with_excel_files(tmp_path)

    reporting.generate_reports(
        reporting.ReportRequest(
            company="abipha",
            base_dir=tmp_path,
            start_date="2026-02-01",
            end_date="2026-02-28",
            selected_reports=("summary",),
            sales_order_statuses=("Đề nghị ghi",),
            return_order_statuses=("Đã duyệt",),
        )
    )

    summary_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo doanh số khách hàng abipha.xlsx"
    summary_df = pd.read_excel(summary_path, sheet_name="Cả nước", engine="openpyxl")

    assert summary_df.loc[0, "Tháng 2"] == 60


def test_generate_reports_emits_progress_updates(tmp_path, monkeypatch):
    def load_dataset(self, progress_callback=None):
        if progress_callback is not None:
            for message in [
                "Đang đọc danh mục sản phẩm...",
                "Đang đọc danh sách khách hàng...",
                "Đang đọc danh sách nhân viên...",
                "Đang đọc dữ liệu phân tuyến...",
                "Đang đọc đơn hàng bán ra...",
                "Đang đọc đơn hàng nhà phân phối...",
                "Đang đọc đơn hàng trả lại...",
                "Đang đọc đơn trả lại nhà phân phối...",
            ]:
                progress_callback(message)
        return build_dataset()

    monkeypatch.setattr(reporting.ExcelCRMRepository, "load_dataset", load_dataset)
    create_company_dir_with_excel_files(tmp_path)

    progress_events: list[tuple[int, int, str]] = []
    reporting.generate_reports(
        reporting.ReportRequest(
            company="abipha",
            base_dir=tmp_path,
            start_date="2026-01-01",
            end_date="2026-12-31",
            selected_reports=("summary",),
        ),
        progress_callback=lambda current, total, message: progress_events.append((current, total, message)),
    )

    assert progress_events[0] == (1, 11, "Đang kiểm tra tham số báo cáo...")
    assert progress_events[-1] == (11, 11, "Đang ghi file báo cáo doanh số khách hàng...")
    assert ("Đang đọc danh mục sản phẩm..." in [event[2] for event in progress_events])
    assert ("Đang tạo báo cáo doanh số khách hàng..." in [event[2] for event in progress_events])


def test_generate_reports_writes_employee_product_report(tmp_path, monkeypatch):
    dataset = build_dataset()
    dataset.orders.purchase_orders = [
        build_order(
            "PO-EMP-1",
            "C001",
            1,
            [("PDD", 3, 40), ("TPCN", 2, 0)],
            owner_name="Nguyễn Hữu Nam - Hải Dương 1 (ABN-2025-18)",
        )
    ]
    dataset.orders.return_purchase_orders = [
        build_order(
            "RPO-EMP-1",
            "C001",
            1,
            [("PDD", 1, 20)],
            status="Đã duyệt",
            owner_name="Nguyễn Hữu Nam - Hải Dương 1 (ABN-2025-18)",
        )
    ]
    monkeypatch.setattr(reporting.ExcelCRMRepository, "load_dataset", lambda self: dataset)
    create_company_dir_with_excel_files(tmp_path)

    reporting.generate_reports(
        reporting.ReportRequest(
            company="abipha",
            base_dir=tmp_path,
            start_date="2026-01-01",
            end_date="2026-01-31",
            selected_reports=("employee-product",),
            sales_order_statuses=("Đã ghi",),
            return_order_statuses=("Đã duyệt",),
        )
    )

    employee_product_path = (
        tmp_path / "modules" / "abipha" / "report" / "Báo cáo doanh thu sản lượng sản phẩm theo nhân viên abipha.xlsx"
    )
    employee_product_month_1_df = pd.read_excel(employee_product_path, sheet_name="Tháng 1", engine="openpyxl")
    employee_product_month_2_df = pd.read_excel(employee_product_path, sheet_name="Tháng 2", engine="openpyxl")

    assert len(employee_product_month_1_df) == 1
    assert employee_product_month_1_df.loc[0, "Mã nhân viên"] == "ABN-2025-18"
    assert employee_product_month_1_df.loc[0, "Tên nhân viên"] == "Nguyễn Hữu Nam"
    assert employee_product_month_1_df.loc[0, "Mã sản phẩm"] == "PDD"
    assert employee_product_month_1_df.loc[0, "Sản lượng thuần"] == 2
    assert employee_product_month_1_df.loc[0, "Doanh thu bán"] == 300
    assert employee_product_month_1_df.loc[0, "Doanh thu trả lại"] == 100
    assert employee_product_month_1_df.loc[0, "Doanh thu thuần"] == 200
    assert employee_product_month_2_df.empty


def test_generate_reports_excludes_distributor_customers_from_employee_product_report(tmp_path, monkeypatch):
    dataset = build_dataset()
    dataset.customers[0].is_distributor = "ü"
    dataset.orders.purchase_orders = [
        build_order(
            "PO-DIST-1",
            "C001",
            1,
            [("PDD", 3, 100)],
            owner_name="Nguyễn Hữu Nam - Hải Dương 1 (ABN-2025-18)",
        )
    ]
    monkeypatch.setattr(reporting.ExcelCRMRepository, "load_dataset", lambda self: dataset)
    create_company_dir_with_excel_files(tmp_path)

    reporting.generate_reports(
        reporting.ReportRequest(
            company="abipha",
            base_dir=tmp_path,
            start_date="2026-01-01",
            end_date="2026-01-31",
            selected_reports=("employee-product",),
            sales_order_statuses=("Đã ghi",),
            return_order_statuses=("Đã duyệt",),
        )
    )

    employee_product_path = (
        tmp_path / "modules" / "abipha" / "report" / "Báo cáo doanh thu sản lượng sản phẩm theo nhân viên abipha.xlsx"
    )
    employee_product_month_1_df = pd.read_excel(employee_product_path, sheet_name="Tháng 1", engine="openpyxl")

    assert employee_product_month_1_df.empty
