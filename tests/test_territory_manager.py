from datetime import datetime

from dms_reporting.domain.models import Customer, Employee, Territory, TerritoryManager


def build_customer(
    owner_name: str,
    billing_province: str | None,
    billing_ward: str | None,
    *,
    shipping_province: str = "Bắc Ninh",
    shipping_ward: str = "Phường Suối Hoa",
) -> Customer:
    return Customer(
        account_number="C001",
        account_name="Khach A",
        account_type="1MB_HĐ001",
        sign_date=datetime(2026, 1, 1),
        phone=None,
        billing_street="99 Lê Lợi",
        billing_ward=billing_ward,
        billing_district="Hải Dương" if billing_province else None,
        billing_province=billing_province,
        billing_address=f"99 Lê Lợi, {billing_ward}, {billing_province}" if billing_province and billing_ward else None,
        tax_code=None,
        owner_name=owner_name,
        description=None,
        visiting_last_day=None,
        date_of_birthday=None,
        is_distributor=None,
        unit="Kinh doanh OTC Miền Bắc khu vực 3",
        shipping_street="12 Nguyễn Trãi",
        shipping_ward=shipping_ward,
        shipping_district="Hải Dương",
        shipping_province=shipping_province,
        shipping_address=f"12 Nguyễn Trãi, {shipping_ward}, {shipping_province}",
    )


def test_customer_owner_employee_id_extracts_code_from_owner_name():
    customer = build_customer("Nguyễn Hữu Nam - Hải Dương 1 (ABN-2025-18)", "Hải Dương", "Xã Thanh Xuân")
    assert customer.owner_employee_id == "ABN-2025-18"


def test_territory_manager_recognizes_correct_assignment_for_active_employee():
    employee = Employee(
        employee_id="ABN-2025-18",
        employee_name="Nguyễn Hữu Nam",
        employment_status="Đang làm việc",
        company_email="HAIDUONG01@com.vn",
    )
    territory = Territory(
        territory_id="territory-1",
        employee_email="HAIDUONG01@com.vn",
        province="Hải Dương",
        commune="Xã Thanh Xuân",
    )
    manager = TerritoryManager(employees=[employee], territories=[territory])
    customer = build_customer(
        "Nguyễn Hữu Nam - Hải Dương 1 (ABN-2025-18)",
        "Hải Dương",
        "Xã Thanh Xuân",
        shipping_province="Bắc Ninh",
        shipping_ward="Phường Suối Hoa",
    )

    assert manager.is_customer_correctly_assigned(customer) is True


def test_territory_manager_returns_wrong_assignments_for_mismatched_territory():
    employee = Employee(
        employee_id="ABN-2025-18",
        employee_name="Nguyễn Hữu Nam",
        employment_status="Đang làm việc",
        company_email="HAIDUONG01@com.vn",
    )
    territory = Territory(
        territory_id="territory-1",
        employee_email="HAIDUONG01@com.vn",
        province="Hải Dương",
        commune="Xã Thanh Xuân",
    )
    manager = TerritoryManager(employees=[employee], territories=[territory])
    wrong_customer = build_customer(
        "Nguyễn Hữu Nam - Hải Dương 1 (ABN-2025-18)",
        "Hải Dương",
        "Xã Hồng Hưng",
        shipping_province="Hải Dương",
        shipping_ward="Xã Thanh Xuân",
    )

    wrong_assignments = manager.get_wrong_assignments([wrong_customer])

    assert wrong_assignments == [wrong_customer]


def test_territory_manager_does_not_assign_territory_to_inactive_employee():
    employee = Employee(
        employee_id="ABN-2025-18",
        employee_name="Nguyễn Hữu Nam",
        employment_status="Đã nghỉ việc",
        company_email="HAIDUONG01@com.vn",
    )
    territory = Territory(
        territory_id="territory-1",
        employee_email="HAIDUONG01@com.vn",
        province="Hải Dương",
        commune="Xã Thanh Xuân",
    )
    manager = TerritoryManager(employees=[employee], territories=[territory])
    customer = build_customer("Nguyễn Hữu Nam - Hải Dương 1 (ABN-2025-18)", "Hải Dương", "Xã Thanh Xuân")

    assert employee.territories == []
    evaluation = manager.evaluate_customer_assignment(customer)
    assert evaluation["is_correct"] is False
    assert evaluation["reason"] == "Nhân viên không hoạt động"


def test_territory_manager_requires_billing_address_for_assignment():
    employee = Employee(
        employee_id="ABN-2025-18",
        employee_name="Nguyễn Hữu Nam",
        employment_status="Đang làm việc",
        company_email="HAIDUONG01@com.vn",
    )
    territory = Territory(
        territory_id="territory-1",
        employee_email="HAIDUONG01@com.vn",
        province="Hải Dương",
        commune="Xã Thanh Xuân",
    )
    manager = TerritoryManager(employees=[employee], territories=[territory])
    customer = build_customer(
        "Nguyễn Hữu Nam - Hải Dương 1 (ABN-2025-18)",
        None,
        None,
        shipping_province="Hải Dương",
        shipping_ward="Xã Thanh Xuân",
    )

    evaluation = manager.evaluate_customer_assignment(customer)

    assert evaluation["is_correct"] is False
    assert evaluation["reason"] == "Thiếu dữ liệu địa bàn hóa đơn của khách hàng"


def test_territory_manager_lists_inactive_employees_still_present_in_territory_file():
    active_employee = Employee(
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
    manager = TerritoryManager(
        employees=[active_employee, inactive_employee],
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

    inactive_entries = manager.get_inactive_employee_territories()

    assert len(inactive_entries) == 1
    assert inactive_entries[0]["employee"].employee_id == "ABN-2024-99"
    assert len(inactive_entries[0]["territories"]) == 1
