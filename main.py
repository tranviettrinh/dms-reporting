from modules.Product import Product
from modules.Order import Order
from modules.SalesReport import SalesReport
from modules.ListSaleOrder import list_orders
from modules.ListProducts import list_products
from modules.ListSaleOrderNPP import order_objects
from modules.ListCustomers import list_customerNPP
from modules.ListReturnPurchaseOrder import list_orders as list_return_purchase_order
from modules.ListReturnSaleOrder import list_orders as list_return_sale_order

from datetime import datetime
import pandas as pd
from openpyxl.styles import Font
def main():
    
    # Create an instance of SalesReport
    sales_report = SalesReport()
    sales_report.add_products(list_products)
    for order in list_orders:
        sales_report.add_purchase_order(order)
    # sales_report.print_purchase_summary()
    for order in order_objects:
        sales_report.add_sales_order(order)
    # sales_report.print_sales_summary()
    for order in list_return_purchase_order:
        sales_report.add_return_purchase_orders(order)
    for order in list_return_sale_order:
        sales_report.add_return_sales_orders(order)

    province_MB=["Bắc Giang","Bắc Kạn","Bắc Ninh","Cao Bằng","Điện Biên","Hà Giang","Hà Nam","Hà Tĩnh","Hải Dương","Hải Phòng","Hòa Bình","Hưng Yên","Lai Châu","Lạng Sơn","Lào Cai","Nam Định","Nghệ An","Ninh Bình","Phú Thọ","Quảng Ninh","Sơn La","Thái Bình","Thái Nguyên","Thanh Hóa","Tuyên Quang","Vĩnh Phúc","Yên Bái"]
    # # Danh sách miền Trung
    province_MT=['Bình Định','Gia Lai','Kon Tum','Phú Yên','Quảng Bình','Quảng Nam','Quảng Ngãi','Quảng Trị','Huế']
    # province=['Thanh Hóa (VN)']
    # Danh sách miền Nam
    province_MN = ['An Giang','Bà Rịa - Vũng Tàu','Bạc Liêu','Bến Tre','Bình Dương','Bình Phước','Bình Thuận','Cà Mau','Đắk Lắk','Đắk Nông','Đồng Nai','Đồng Tháp','Hậu Giang','Khánh Hòa','Kiên Giang','Lâm Đồng','Long An','Ninh Thuận','Sóc Trăng','Tây Ninh','Tiền Giang','Cần Thơ','Trà Vinh','Vĩnh Long']
    status=["Đã ghi","Đề nghị ghi","Bản nháp"]
    start_time = "2025-05-01"
    end_time = "2025-05-31"
    with pd.ExcelWriter("Báo cáo tồn kho.xlsx", engine='openpyxl', mode='w') as writer:
        for i in range(0, len(list_customerNPP)):
            # if (list_customerNPP[i]['Tỉnh/Thành phố (Hóa đơn)'] in province_MN) and (list_customerNPP[i]['Mã khách hàng (*)'] not in ["1MB8DLYB002","1MB4DLTN002","3MNĐLTV01","3MNĐLLĐ01","3MNĐLĐN07","3MNĐLĐT02","3MNĐLHG01","3MNĐLAG03","3MNĐLBTHU02","3MNĐLKG02"]):
            if (list_customerNPP[i]['Tỉnh/Thành phố (Hóa đơn)'] in province_MN) and (list_customerNPP[i]['Mã khách hàng (*)'] in ["3MNĐLKH01"]):
                # Tên sheet
                sheet_filename = f"Sheet_{i+1}_{list_customerNPP[i]['Tỉnh/Thành phố (Hóa đơn)']}"
                rows=[]
                for product in list_products:
                    info=sales_report.getProductInventoryByCustomer(list_customerNPP[i]['Mã khách hàng (*)'],product.product_id,start_time,end_time,status)

                    rows.append({
                        "Mã sản phẩm": product.product_id,
                        "Tên sản phẩm": product.name,
                        "Đơn giá": product.price,
                        "Loại hàng hoá": product.category,
                        "Tồn kho đầu kỳ (SL)": info[0],
                        "Tồn kho đầu kỳ (KM)": info[1],
                        "Số lượng nhập (SL)": info[2],
                        "Số lượng nhập (KM)": info[3],
                        "Doanh số nhập": product.price * info[2],
                        "Số lượng bán (SL)": info[4],
                        "Số lượng bán (KM)": info[5],
                        "Doanh số bán": product.price * info[4],
                        "Tồn kho cuối kỳ (SL)": info[6],
                        "Tồn kho cuối kỳ (KM)": info[7],
                        "Công nợ": product.price * info[6]
                        })
                    # rows.append({
                    #     "Mã sản phẩm": product.product_id,
                    #     "Tên sản phẩm": product.name,
                    #     "soluong_nhap_dauky": info[0],
                    #     "soluong_nhapKM_dauky": info[1],
                    #     "soluong_ban_dauky": info[2],
                    #     "soluong_banKM_dauky": info[3],
                    #     "purchase_quantity": info[4],
                    #     "promo_purchase_quantity": info[5],
                    #     "sold_quantity": info[6],
                    #     "promo_sold_quantity": info[7],
                    #     "soluong_trahangmua_dauky_sl": info[8],
                    #     "soluong_trahangmua_dauky_km": info[9],
                    #     "soluong_trahangmua_sl": info[10],
                    #     "soluong_trahangmua_km": info[11],
                    #     "soluong_trahangban_dauky_sl": info[12],
                    #     "soluong_trahangban_dauky_km": info[13],
                    #     "soluong_trahangban_sl": info[14],
                    #     "soluong_trahangban_km": info[15]
                    #     })
                # Ghi sheet vào Excel
                df = pd.DataFrame(rows)
                df.to_excel(writer, sheet_name=sheet_filename, startrow=3, startcol=0, index=False)
                # Sau khi ghi, thêm dòng ở A1
                worksheet = writer.sheets[sheet_filename]  # Lấy sheet object từ writer
                cell = worksheet.cell(row=1, column=1, value=f"Báo cáo tồn kho: {list_customerNPP[i]['Mã khách hàng (*)']} {list_customerNPP[i]['Tên khách hàng (*)']}")
                thoigian = worksheet.cell(row=2, column=1, value=f"Từ {start_time} đến {end_time}")
                # Áp dụng font bôi đậm và cỡ chữ lớn hơn
                cell.font = Font(bold=True, size=14)  # size có thể đổi theo nhu cầu (ví dụ: 16, 18,...)
if __name__ == '__main__':
    main()
