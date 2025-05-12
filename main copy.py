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

    orders_sale_in = [
        o for o in list_orders
            if o.payment_due and datetime.strptime(o.payment_due, "%Y-%m-%dT%H:%M:%S.%f%z").month <= 3 and
                datetime.strptime(o.payment_due, "%Y-%m-%dT%H:%M:%S.%f%z").year == 2025 and o.status == "Đã ghi"
    ]
    orders_sale_out = [
        o for o in order_objects
            if o.payment_due and pd.to_datetime(o.payment_due).month <= 3 and
                pd.to_datetime(o.payment_due).year == 2025 and o.status == "Đã ghi"
    ]

    with pd.ExcelWriter("Báo cáo tồn kho.xlsx", engine='openpyxl', mode='w') as writer:
        for i in range(0, len(list_customerNPP)):

            print(list_customerNPP[i]['Mã khách hàng (*)'])

            sales_in_report = SalesReport()
            sales_out_report = SalesReport()

            sales_in_report.add_products(list_products)
            sales_out_report.add_products(list_products)

            for order in orders_sale_in:
                sales_in_report.add_order(order)
            for order in orders_sale_out:
                sales_out_report.add_order(order)
            if sales_in_report.check_customer_id(list_customerNPP[i]['Mã khách hàng (*)']) == 1 and sales_out_report.check_customer_id(list_customerNPP[i]['Mã khách hàng (*)']) == 1:
                df_in = sales_in_report.customer_sales_report(list_customerNPP[i]['Mã khách hàng (*)'])
                df_out = sales_out_report.customer_sales_report(list_customerNPP[i]['Mã khách hàng (*)'])

                df_out = df_out[['product_code', 'quantity_non_zero', 'quantity_zero', 'total_non_zero']]
                df_in.sort_values(by='name', ascending=True, inplace=True)

                df_merged = pd.merge(df_in, df_out, on='product_code', how='left')
                df_merged.columns = ['Mã sản phẩm', 'Tên sản phẩm', 'SL mua', 'SL mua (KM)', 'Doanh số mua', 'SL bán','SL bán (KM)','Doanh số bán']
            
                # Thay giá trị NaN trong cột 'SL bán' bằng 0
                df_merged['SL bán'].fillna(0, inplace=True)
                df_merged['SL bán (KM)'].fillna(0, inplace=True)
                df_merged['SL tồn cuối kỳ'] = df_merged['SL mua'] - df_merged['SL bán']
                df_merged['KM tồn cuối kỳ'] = df_merged['SL mua (KM)'] - df_merged['SL bán (KM)']
                
                # Tên sheet
                sheet_filename = f"Sheet_{i+1}_{list_customerNPP[i]['Tỉnh/Thành phố (Hóa đơn)']}"

                # Ghi dữ liệu từ dòng 2 trở đi
                df_merged.to_excel(writer, sheet_name=sheet_filename, startrow=2, startcol=0, index=False)

                # Sau khi ghi, thêm dòng ở A1
                worksheet = writer.sheets[sheet_filename]  # Lấy sheet object từ writer
                cell = worksheet.cell(row=1, column=1, value=f"Báo cáo tồn kho: {list_customerNPP[i]['Mã khách hàng (*)']} {list_customerNPP[i]['Tên khách hàng (*)']}")
                # Áp dụng font bôi đậm và cỡ chữ lớn hơn
                cell.font = Font(bold=True, size=14)  # size có thể đổi theo nhu cầu (ví dụ: 16, 18,...)
            else: continue
if __name__ == '__main__':
    main()
