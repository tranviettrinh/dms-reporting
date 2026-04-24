from datetime import datetime

import pandas as pd

import dms_reporting.cli as cli
from dms_reporting.domain.models import Customer, DatasetBundle, Employee, Order, OrderBucket, OrderItem, Product, Territory, TerritoryManager


def build_order(order_number: str, customer_id: str, month: int, items: list[tuple[str, float]]) -> Order:
    order = Order(
        order_number=order_number,
        order_date=datetime(2026, month, 1),
        customer_id=customer_id,
        order_value=sum(value for _, value in items),
        payment_due=datetime(2026, month, 1),
        status="Đã ghi",
        owner_name="Owner",
        phone_number=None,
        shipping_address=None,
        shipping_ward=None,
        shipping_district=None,
        shipping_province=None,
    )
    for product_id, total in items:
        order.add_item(
            OrderItem(
                order_id=order_number,
                product_id=product_id,
                warehouse=None,
                unit="box",
                quantity=1,
                unit_price=total,
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
        shipping_district="Hải Dương",
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
        shipping_district="Hải Dương",
        shipping_province="Hải Dương",
        shipping_address="34 Trần Hưng Đạo, Xã Gia Xuyên, Hải Dương",
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
    return DatasetBundle(
        products=[
            Product(product_id="PDD", name="Dong duoc", category="NHÓM THUỐC ĐÔNG DƯỢC", primary_unit="box", price=100, tax=0),
            Product(product_id="PTD", name="Tan duoc", category="NHÓM THUỐC TÂN DƯỢC", primary_unit="box", price=200, tax=0),
            Product(product_id="TPCN", name="TPCN", category="THỰC PHẨM CHỨC NĂNG", primary_unit="box", price=300, tax=0),
        ],
        customers=[customer, inactive_customer],
        orders=OrderBucket(
            purchase_orders=[build_order("PO-1", "C001", 1, [("PDD", 100), ("PTD", 200), ("TPCN", 300)])],
            sales_orders=[],
            return_purchase_orders=[],
            return_sales_orders=[],
        ),
        employees=[employee, inactive_employee],
        territory_manager=territory_manager,
    )


def test_cli_writes_summary_detail_and_territory_reports(tmp_path, monkeypatch):
    monkeypatch.setattr(cli.ExcelCRMRepository, "load_dataset", lambda self: build_dataset())

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
    first_sales_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng phát sinh doanh số lần đầu abipha.xlsx"
    territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng sai địa bàn abipha.xlsx"
    inactive_territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo nhân viên đã nghỉ còn trong phân tuyến abipha.xlsx"
    inactive_customer_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng còn gán cho nhân viên đã nghỉ việc abipha.xlsx"

    assert exit_code == 0
    assert summary_path.exists()
    assert detail_path.exists()
    assert first_sales_path.exists()
    assert territory_path.exists()
    assert inactive_territory_path.exists()
    assert inactive_customer_path.exists()

    detail_df = pd.read_excel(detail_path, sheet_name="Cả nước", engine="openpyxl")
    first_sales_df = pd.read_excel(first_sales_path, sheet_name="Tháng 1", engine="openpyxl")
    first_sales_month_2_df = pd.read_excel(first_sales_path, sheet_name="Tháng 2", engine="openpyxl")
    summary_df = pd.read_excel(summary_path, sheet_name="Cả nước", engine="openpyxl")
    territory_df = pd.read_excel(territory_path, sheet_name="Sai địa bàn", engine="openpyxl")
    inactive_territory_df = pd.read_excel(inactive_territory_path, sheet_name="Nhân viên đã nghỉ", engine="openpyxl")
    inactive_customer_df = pd.read_excel(inactive_customer_path, sheet_name="Khách hàng gán NV nghỉ", engine="openpyxl")
    assert summary_df.loc[0, "Địa chỉ giao hàng đầy đủ"] == "12 Nguyễn Trãi, Xã Hồng Hưng, Hải Dương"
    assert summary_df.loc[0, "Địa chỉ hóa đơn đầy đủ"] == "99 Lê Lợi, Phường Lê Thanh Nghị, Hải Dương"
    assert "Tháng 1 (Đông dược)" in detail_df.columns
    assert detail_df.loc[0, "Tháng 1 (TPCN)"] == 300
    assert detail_df.loc[0, "Địa chỉ giao hàng đầy đủ"] == "12 Nguyễn Trãi, Xã Hồng Hưng, Hải Dương"
    assert detail_df.loc[0, "Địa chỉ hóa đơn đầy đủ"] == "99 Lê Lợi, Phường Lê Thanh Nghị, Hải Dương"
    assert first_sales_df.loc[0, "Mã khách hàng"] == "C001"
    assert first_sales_df.loc[0, "Số đơn hàng đầu tiên"] == "PO-1"
    assert first_sales_month_2_df.empty
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


def test_cli_territory_only_writes_only_territory_report(tmp_path, monkeypatch):
    monkeypatch.setattr(cli.ExcelCRMRepository, "load_dataset", lambda self: build_dataset())

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
    first_sales_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng phát sinh doanh số lần đầu abipha.xlsx"
    territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng sai địa bàn abipha.xlsx"
    inactive_territory_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo nhân viên đã nghỉ còn trong phân tuyến abipha.xlsx"
    inactive_customer_path = tmp_path / "modules" / "abipha" / "report" / "Báo cáo khách hàng còn gán cho nhân viên đã nghỉ việc abipha.xlsx"

    assert exit_code == 0
    assert not summary_path.exists()
    assert not detail_path.exists()
    assert not first_sales_path.exists()
    assert territory_path.exists()
    assert inactive_territory_path.exists()
    assert inactive_customer_path.exists()
