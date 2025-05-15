from modules.Product import Product
from modules.Order import Order
from modules.SalesReport import SalesReport
from modules.ListSaleOrder import list_orders
from modules.ListProducts import list_products
from modules.ListSaleOrderNPP import order_objects
# from modules.ListCustomers import list_customerNPP
from datetime import datetime
import pandas as pd
from openpyxl.styles import Font
def main():
    
    # Create an instance of SalesReport
    sales_report = SalesReport()
    sales_report.add_products(list_products)
    for order in list_orders:
        sales_report.add_purchase_order(order)
    sales_report.print_purchase_summary()
    for order in order_objects:
        sales_report.add_sales_order(order)
    sales_report.print_sales_summary()
    print(sales_report.getProductInventoryByCustomer("1MB5DLSL001","FVITAA0021","2025-05-16","Đã ghi"))

if __name__ == '__main__':
    main()
