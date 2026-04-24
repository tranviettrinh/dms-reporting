from datetime import datetime

from dms_reporting.domain.models import Customer, Order


def test_order_parse_datetime_returns_datetime():
    value = Order.parse_datetime("2026-04-23 10:30:00")
    assert isinstance(value, datetime)
    assert value.month == 4


def test_customer_full_address_uses_shipping_and_billing_fields():
    customer = Customer(
        account_number="C001",
        account_name="Khach A",
        account_type=None,
        sign_date=None,
        phone=None,
        billing_street="99 Lê Lợi",
        billing_ward="Phường Lê Thanh Nghị",
        billing_district="Hải Dương",
        billing_province="Hải Dương",
        billing_address=None,
        tax_code=None,
        owner_name=None,
        description=None,
        visiting_last_day=None,
        date_of_birthday=None,
        is_distributor=None,
        unit=None,
        shipping_street="12 Nguyễn Trãi",
        shipping_ward="Xã Hồng Hưng",
        shipping_district="Hải Dương",
        shipping_province="Hải Dương",
        shipping_address=None,
    )

    assert customer.shipping_full_address == "12 Nguyễn Trãi, Xã Hồng Hưng, Hải Dương, Hải Dương"
    assert customer.billing_full_address == "99 Lê Lợi, Phường Lê Thanh Nghị, Hải Dương, Hải Dương"
