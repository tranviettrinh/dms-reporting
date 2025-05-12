from modules.Product import Product
from modules.Order import Order
from modules.SalesReport import SalesReport
from modules.ListSaleOrder import list_orders
from modules.ListProducts import list_products
from modules.ListSaleOrderNPP import order_objects
from modules.ListCustomers import list_customerNPP
from datetime import datetime
import pandas as pd
from openpyxl.styles import Font
def main():
    
    # Create an instance of SalesReport
    sales_report = SalesReport()

    with pd.ExcelWriter("Báo cáo tồn kho.xlsx", engine='openpyxl', mode='w') as writer:
        for i in range(0, len(list_customerNPP)):

            print(list_customerNPP[i]['Mã khách hàng (*)'])

            sales_report = SalesReport()

            sales_report.add_products(list_products)

            for order in list_orders:
                sales_report.add_sales_order(order)
            for order in order_objects:
                sales_report.add_purchase_order(order)
            if sales_report.check_customer_id(list_customerNPP[i]['Mã khách hàng (*)']) == 1:
                df_report = sales_report.customer_sales_report(list_customerNPP[i]['Mã khách hàng (*)'],"2025-04-01T00:00:00.000+07:00","2025-04-30T00:00:00.000+07:00","Đã ghi")
                
                # Tên sheet
                sheet_filename = f"Sheet_{i+1}_{list_customerNPP[i]['Tỉnh/Thành phố (Hóa đơn)']}"
                df_report.to_excel(writer, sheet_name=sheet_filename, startrow=2, startcol=0, index=False)

            else: continue
if __name__ == '__main__':
    main()
