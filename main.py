from modules.Product import Product
from modules.Order import Order
from modules.SalesReport import SalesReport
from modules.ListSaleOrder import list_orders,list_products

def main():
    
    # Create an instance of SalesReport
    sales_report = SalesReport()
    
    # Add products and orders to the SalesReport
    sales_report.add_products(list_products)
    for order in list_orders:
        sales_report.add_order(order)
    
    # Giả sử sales_report đã được thêm đơn hàng và sản phẩm
    print(sales_report.print_customer_sales_report('1MB5DLSL001'))
if __name__ == '__main__':
    main()
