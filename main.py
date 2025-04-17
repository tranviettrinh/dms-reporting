from modules.Product import Product
from modules.Order import Order
from modules.SalesReport import SalesReport
from modules.ListSaleOrder import list_orders
from modules.ListProducts import list_products
from modules.ListSaleOrderNPP import order_objects
def main():
    
    # Create an instance of SalesReport
    sales_report = SalesReport()
    sales_report1 = SalesReport()
    
    # Add products and orders to the SalesReport
    sales_report.add_products(list_products)
    for order in list_orders:
        sales_report.add_order(order)
    
    # Giả sử sales_report đã được thêm đơn hàng và sản phẩm
    print(sales_report.print_customer_sales_report('1MB8DLNA001'))

    # Add products and orders to the SalesReport
    sales_report1.add_products(list_products)
    for order1 in order_objects:
        sales_report1.add_order(order1)
    
    # Giả sử sales_report đã được thêm đơn hàng và sản phẩm
    print(sales_report1.print_customer_sales_report('1MB8DLNA001'))
    
if __name__ == '__main__':
    main()
