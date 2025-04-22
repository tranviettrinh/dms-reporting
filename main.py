from modules.Product import Product
from modules.Order import Order
from modules.SalesReport import SalesReport
from modules.ListSaleOrder import list_orders
from modules.ListProducts import list_products
from modules.ListSaleOrderNPP import order_objects
from datetime import datetime
def main():
    
    # Create an instance of SalesReport
    sales_report = SalesReport()

    monthly_orders = [
        o for o in list_orders
        if o.payment_due and datetime.strptime(o.payment_due, "%Y-%m-%dT%H:%M:%S.%f%z").month == 4 and
           datetime.strptime(o.payment_due, "%Y-%m-%dT%H:%M:%S.%f%z").year == 2025
    ]
    # Add products and orders to the SalesReport
    sales_report.add_products(list_products)
    for order in monthly_orders:
        sales_report.add_order(order)
    
    # Giả sử sales_report đã được thêm đơn hàng và sản phẩm
    print(sales_report.print_customer_sales_report('1MB8DLNA001'))


    for i in range(0,11):
        sales_in_report = SalesReport()
        sales_out_report = SalesReport()
        sales_in_report.add_products(list_products)
        sales_out_report.add_products(list_products)
        for order in list_orders:
            sales_in_report.add_order(order)
        for order in order_objects:
            sales_out_report.add_order(order)
        sales_in_report.customer_sales_report()

if __name__ == '__main__':
    main()
