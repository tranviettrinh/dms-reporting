from datetime import datetime

from dms_reporting.config import ReportSettings
from dms_reporting.domain.models import Customer, DatasetBundle, Employee, Order, OrderBucket, OrderItem, Product, Territory, TerritoryManager
from dms_reporting.services.sales_report_service import SalesReportService


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
    for index, item in enumerate(items, start=1):
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


def test_customer_sales_report_exports_all_12_months():
    service = SalesReportService(build_dataset())
    report = service.build_customer_sales_report(ReportSettings(start_date="2026-01-01", end_date="2026-12-31"))

    assert report.loc[0, "Tháng 1"] == 600
    assert report.loc[0, "Tháng 5"] == 500
    assert report.loc[0, "Tháng 12"] == 0
    assert report.loc[0, "Phường/Xã"] == "Xã Hồng Hưng"
    assert report.loc[0, "Địa chỉ giao hàng đầy đủ"] == "12 Nguyễn Trãi, Xã Hồng Hưng, Hải Dương"
    assert report.loc[0, "Địa chỉ hóa đơn đầy đủ"] == "99 Lê Lợi, Phường Lê Thanh Nghị, Hải Dương"
    assert report.loc[0, "Vùng"] == "Miền Bắc"
    assert report.loc[0, "Loại hợp đồng"] == "1MB_HĐ001"


def test_calculate_monthly_sales_detail_returns_sales_by_product_group():
    service = SalesReportService(build_dataset())
    detail = service.calculate_monthly_sales_detail(
        customer_id="C001",
        month=1,
        start_date=datetime(2026, 1, 1),
        end_date=datetime(2026, 12, 31),
        sales_order_statuses=["Đã ghi"],
        return_order_statuses=[],
    )

    assert detail == {
        "doanh_so_dong_duoc": 100,
        "doanh_so_tan_duoc": 200,
        "doanh_so_tpcn": 300,
    }


def test_calculate_monthly_sales_uses_catalog_product_price():
    dataset = build_dataset()
    dataset.orders.purchase_orders = [
        build_order(
            "PO-CATALOG-1",
            "C001",
            1,
            [("PDD", 3, 50)],
        )
    ]

    service = SalesReportService(dataset)
    total = service.calculate_monthly_sales(
        customer_id="C001",
        month=1,
        start_date=datetime(2026, 1, 1),
        end_date=datetime(2026, 12, 31),
        sales_order_statuses=["Đã ghi"],
        return_order_statuses=[],
    )

    assert total == 300


def test_calculate_monthly_sales_detail_uses_catalog_product_price():
    dataset = build_dataset()
    dataset.orders.purchase_orders = [
        build_order(
            "PO-CATALOG-2",
            "C001",
            1,
            [("PTD", 2, 20)],
        )
    ]

    service = SalesReportService(dataset)
    detail = service.calculate_monthly_sales_detail(
        customer_id="C001",
        month=1,
        start_date=datetime(2026, 1, 1),
        end_date=datetime(2026, 12, 31),
        sales_order_statuses=["Đã ghi"],
        return_order_statuses=[],
    )

    assert detail == {
        "doanh_so_dong_duoc": 0.0,
        "doanh_so_tan_duoc": 400,
        "doanh_so_tpcn": 0.0,
    }


def test_build_customer_sales_detail_report_writes_group_columns_per_month():
    service = SalesReportService(build_dataset())
    report = service.build_customer_sales_detail_report(ReportSettings(start_date="2026-01-01", end_date="2026-12-31"))

    assert report.loc[0, "Tháng 1 (Đông dược)"] == 100
    assert report.loc[0, "Tháng 1 (Tân dược)"] == 200
    assert report.loc[0, "Tháng 1 (TPCN)"] == 300
    assert report.loc[0, "Tháng 5 (Đông dược)"] == 500
    assert report.loc[0, "Tháng 5 (Tân dược)"] == 0
    assert report.loc[0, "Địa chỉ giao hàng đầy đủ"] == "12 Nguyễn Trãi, Xã Hồng Hưng, Hải Dương"
    assert report.loc[0, "Địa chỉ hóa đơn đầy đủ"] == "99 Lê Lợi, Phường Lê Thanh Nghị, Hải Dương"


def test_build_first_sales_customers_report_uses_catalog_product_price():
    dataset = build_dataset()
    dataset.orders.purchase_orders = [
        build_order(
            "PO-FIRST-1",
            "C001",
            1,
            [("TPCN", 4, 10)],
        )
    ]

    service = SalesReportService(dataset)
    report = service.build_first_sales_customers_report(
        ReportSettings(start_date="2026-01-01", end_date="2026-01-31")
    )

    assert report.loc[0, "Doanh số ghi nhận lần đầu"] == 1200


def test_build_employee_product_sales_report_excludes_zero_price_items_and_nets_returns():
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
            [("PDD", 1, 20), ("TPCN", 1, 0)],
            status="Đã duyệt",
            owner_name="Nguyễn Hữu Nam - Hải Dương 1 (ABN-2025-18)",
        )
    ]

    service = SalesReportService(dataset)
    report = service.build_employee_product_sales_report(
        ReportSettings(
            start_date="2026-01-01",
            end_date="2026-01-31",
            sales_order_statuses=["Đã ghi"],
            return_order_statuses=["Đã duyệt"],
        )
    )

    assert len(report) == 1
    assert report.loc[0, "Mã nhân viên"] == "ABN-2025-18"
    assert report.loc[0, "Tên nhân viên"] == "Nguyễn Hữu Nam"
    assert report.loc[0, "Mã sản phẩm"] == "PDD"
    assert report.loc[0, "Đơn vị tính"] == "Hộp"
    assert report.loc[0, "Số lượng bán"] == 3
    assert report.loc[0, "Số lượng trả lại"] == 1
    assert report.loc[0, "Sản lượng thuần"] == 2
    assert report.loc[0, "Doanh thu bán"] == 300
    assert report.loc[0, "Doanh thu trả lại"] == 100
    assert report.loc[0, "Doanh thu thuần"] == 200


def test_build_employee_product_sales_report_excludes_distributor_customers():
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

    service = SalesReportService(dataset)
    report = service.build_employee_product_sales_report(
        ReportSettings(
            start_date="2026-01-01",
            end_date="2026-01-31",
            sales_order_statuses=["Đã ghi"],
            return_order_statuses=["Đã duyệt"],
        )
    )

    assert report.empty


def test_build_employee_product_sales_monthly_reports_splits_each_month_to_a_sheet():
    dataset = build_dataset()
    dataset.orders.purchase_orders = [
        build_order(
            "PO-EMP-1",
            "C001",
            1,
            [("PDD", 3, 40)],
            owner_name="Nguyễn Hữu Nam - Hải Dương 1 (ABN-2025-18)",
        ),
        build_order(
            "PO-EMP-2",
            "C001",
            2,
            [("PTD", 2, 50)],
            owner_name="Nguyễn Hữu Nam - Hải Dương 1 (ABN-2025-18)",
        ),
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

    service = SalesReportService(dataset)
    reports = service.build_employee_product_sales_monthly_reports(
        ReportSettings(
            start_date="2026-01-01",
            end_date="2026-02-28",
            sales_order_statuses=["Đã ghi"],
            return_order_statuses=["Đã duyệt"],
            months=[1, 2, 3],
        )
    )

    assert list(reports) == ["Tháng 1", "Tháng 2", "Tháng 3"]
    assert reports["Tháng 1"].loc[0, "Mã sản phẩm"] == "PDD"
    assert reports["Tháng 1"].loc[0, "Đơn vị tính"] == "Hộp"
    assert reports["Tháng 1"].loc[0, "Sản lượng thuần"] == 2
    assert reports["Tháng 1"].loc[0, "Doanh thu thuần"] == 200
    assert reports["Tháng 2"].loc[0, "Mã sản phẩm"] == "PTD"
    assert reports["Tháng 2"].loc[0, "Sản lượng thuần"] == 2
    assert reports["Tháng 2"].loc[0, "Doanh thu thuần"] == 400
    assert reports["Tháng 3"].empty


def test_build_first_sales_customers_report_returns_first_sale_in_selected_period():
    service = SalesReportService(build_dataset())
    report = service.build_first_sales_customers_report(ReportSettings(start_date="2026-01-01", end_date="2026-01-31"))

    assert len(report) == 1
    assert report.loc[0, "Mã khách hàng"] == "C001"
    assert report.loc[0, "Số đơn hàng đầu tiên"] == "PO-1"
    assert report.loc[0, "Tháng phát sinh doanh số đầu tiên"] == 1
    assert report.loc[0, "Doanh số ghi nhận lần đầu"] == 600


def test_build_first_sales_customers_monthly_reports_keeps_each_customer_in_its_first_month_only():
    dataset = build_dataset()
    dataset.orders.purchase_orders.append(build_order("PO-3", "C003", 5, [("PDD", 150)]))

    service = SalesReportService(dataset)
    reports = service.build_first_sales_customers_monthly_reports(
        ReportSettings(start_date="2026-01-01", end_date="2026-05-31", months=[1, 2, 3, 4, 5])
    )

    assert list(reports) == ["Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5"]
    assert reports["Tháng 1"]["Mã khách hàng"].tolist() == ["C001"]
    assert reports["Tháng 2"].empty
    assert reports["Tháng 5"]["Mã khách hàng"].tolist() == ["C003"]


def test_calculate_monthly_sales_uses_separate_status_filters_for_sales_and_returns():
    dataset = build_dataset()
    dataset.orders.purchase_orders.append(build_order("PO-3", "C001", 2, [("PDD", 1.6, 100)], status="Đề nghị ghi"))
    dataset.orders.return_purchase_orders.append(build_order("RPO-1", "C001", 2, [("PDD", 1, 100)], status="Đã duyệt"))

    service = SalesReportService(dataset)
    total = service.calculate_monthly_sales(
        customer_id="C001",
        month=2,
        start_date=datetime(2026, 1, 1),
        end_date=datetime(2026, 12, 31),
        sales_order_statuses=["Đề nghị ghi"],
        return_order_statuses=["Đã duyệt"],
    )

    assert total == 60


def test_build_wrong_territory_assignments_report_includes_reason():
    service = SalesReportService(build_dataset())
    report = service.build_wrong_territory_assignments_report()

    assert len(report) == 1
    assert report.loc[0, "Mã khách hàng"] == "C001"
    assert report.loc[0, "Mã nhân viên"] == "ABN-2025-18"
    assert report.loc[0, "Tỉnh/Thành phố (Hóa đơn)"] == "Hải Dương"
    assert report.loc[0, "Phường/Xã (Hóa đơn)"] == "Phường Lê Thanh Nghị"
    assert report.loc[0, "Địa bàn phân tuyến hợp lệ"] == "Hải Dương - Xã Thanh Xuân"
    assert report.loc[0, "Địa chỉ giao hàng đầy đủ"] == "12 Nguyễn Trãi, Xã Hồng Hưng, Hải Dương"
    assert report.loc[0, "Địa chỉ hóa đơn đầy đủ"] == "99 Lê Lợi, Phường Lê Thanh Nghị, Hải Dương"
    assert report.loc[0, "Lý do"] == "Địa bàn khách hàng không thuộc phân tuyến của nhân viên"


def test_build_correct_territory_assignments_report_lists_only_matching_customers():
    service = SalesReportService(build_dataset())
    report = service.build_correct_territory_assignments_report()

    assert len(report) == 1
    assert report.loc[0, "Mã khách hàng"] == "C003"
    assert report.loc[0, "Mã nhân viên"] == "ABN-2025-18"
    assert report.loc[0, "Tên nhân viên"] == "Nguyễn Hữu Nam"
    assert report.loc[0, "Tỉnh/Thành phố (Hóa đơn)"] == "Hải Dương"
    assert report.loc[0, "Phường/Xã (Hóa đơn)"] == "Xã Thanh Xuân"
    assert report.loc[0, "Địa bàn phân tuyến hợp lệ"] == "Hải Dương - Xã Thanh Xuân"
    assert report.loc[0, "Lý do"] == "Khách hàng thuộc đúng phân tuyến của nhân viên"


def test_build_correct_shipping_territory_assignments_report_lists_only_matching_customers():
    service = SalesReportService(build_dataset())
    report = service.build_correct_shipping_territory_assignments_report()

    assert len(report) == 1
    assert report.loc[0, "Mã khách hàng"] == "C001"
    assert report.loc[0, "Mã nhân viên"] == "ABN-2025-18"
    assert report.loc[0, "Tên nhân viên"] == "Nguyễn Hữu Nam"
    assert report.loc[0, "Tỉnh/Thành phố (Giao hàng)"] == "Hải Dương"
    assert report.loc[0, "Quận/Huyện (Giao hàng)"] == "Thanh Hà"
    assert report.loc[0, "Địa bàn phân tuyến giao hàng hợp lệ"] == "Hải Dương - Thanh Hà"
    assert report.loc[0, "Lý do"] == "Khách hàng thuộc đúng phân tuyến giao hàng của nhân viên"


def test_build_wrong_shipping_territory_assignments_report_includes_reason():
    service = SalesReportService(build_dataset())
    report = service.build_wrong_shipping_territory_assignments_report()

    assert len(report) == 1
    assert report.loc[0, "Mã khách hàng"] == "C003"
    assert report.loc[0, "Mã nhân viên"] == "ABN-2025-18"
    assert report.loc[0, "Tỉnh/Thành phố (Giao hàng)"] == "Hải Dương"
    assert report.loc[0, "Quận/Huyện (Giao hàng)"] == "Nam Sách"
    assert report.loc[0, "Địa bàn phân tuyến giao hàng hợp lệ"] == "Hải Dương - Thanh Hà"
    assert report.loc[0, "Địa chỉ giao hàng đầy đủ"] == "77 Nguyễn Văn Linh, Xã Thanh Xuân, Hải Dương"
    assert report.loc[0, "Lý do"] == "Địa bàn giao hàng của khách hàng không thuộc phân tuyến của nhân viên"


def test_build_combined_customer_territory_report_includes_billing_and_shipping_results():
    service = SalesReportService(build_dataset())
    report = service.build_combined_customer_territory_report()

    assert len(report) == 3

    customer_rows = {row["Mã khách hàng"]: row for _, row in report.iterrows()}

    assert customer_rows["C001"]["Kết quả địa chỉ Hóa đơn"] == "Sai"
    assert customer_rows["C001"]["Kết quả địa chỉ Giao hàng"] == "Đúng"
    assert customer_rows["C001"]["Lý do địa chỉ Hóa đơn"] == "Địa bàn khách hàng không thuộc phân tuyến của nhân viên"
    assert customer_rows["C001"]["Lý do địa chỉ Giao hàng"] == ""
    assert customer_rows["C001"]["Kết luận tổng hợp"] == "Sai địa chỉ Hoá đơn"

    assert customer_rows["C002"]["Kết quả địa chỉ Hóa đơn"] == "Sai"
    assert customer_rows["C002"]["Kết quả địa chỉ Giao hàng"] == "Sai"
    assert customer_rows["C002"]["Lý do địa chỉ Hóa đơn"] == "Nhân viên không hoạt động"
    assert customer_rows["C002"]["Lý do địa chỉ Giao hàng"] == "Nhân viên không hoạt động"
    assert customer_rows["C002"]["Kết luận tổng hợp"] == "Sai cả địa chỉ Hoá đơn và Giao hàng"

    assert customer_rows["C003"]["Kết quả địa chỉ Hóa đơn"] == "Đúng"
    assert customer_rows["C003"]["Kết quả địa chỉ Giao hàng"] == "Sai"
    assert customer_rows["C003"]["Lý do địa chỉ Hóa đơn"] == ""
    assert customer_rows["C003"]["Lý do địa chỉ Giao hàng"] == "Địa bàn giao hàng của khách hàng không thuộc phân tuyến của nhân viên"
    assert customer_rows["C003"]["Kết luận tổng hợp"] == "Sai địa chỉ Giao hàng"


def test_build_inactive_employee_territories_report_lists_only_inactive_employees_in_territory_file():
    service = SalesReportService(build_dataset())
    report = service.build_inactive_employee_territories_report()

    assert len(report) == 1
    assert report.loc[0, "Mã nhân viên"] == "ABN-2024-99"
    assert report.loc[0, "Trạng thái lao động"] == "Đã nghỉ việc"
    assert report.loc[0, "Số địa bàn còn trong file phân tuyến"] == 1
    assert report.loc[0, "Địa bàn còn trong file phân tuyến"] == "Hải Dương - Xã Gia Xuyên"


def test_build_customers_assigned_to_inactive_employees_report_lists_customers():
    service = SalesReportService(build_dataset())
    report = service.build_customers_assigned_to_inactive_employees_report()

    assert len(report) == 1
    assert report.loc[0, "Mã khách hàng"] == "C002"
    assert report.loc[0, "Mã nhân viên"] == "ABN-2024-99"
    assert report.loc[0, "Tên nhân viên"] == "Trần Văn Cũ"
    assert report.loc[0, "Trạng thái lao động"] == "Đã nghỉ việc"
    assert report.loc[0, "Tỉnh/Thành phố (Hóa đơn)"] == "Hải Dương"
    assert report.loc[0, "Phường/Xã (Hóa đơn)"] == "Phường Tứ Minh"
    assert report.loc[0, "Lý do"] == "Khách hàng vẫn đang gán cho nhân viên đã nghỉ việc"
