from modules.SalesReport import SalesReport
from modules.Product import Product
from modules.Order import Order
from modules.Employee import Employee
from modules.Territory import Territory
from modules.TerritoryAssignment import TerritoryAssignment
from modules.TerritoryManager import TerritoryManager
from modules.ListSaleOrder import list_orders
from modules.ListProducts import list_products
from modules.ListSaleOrderNPP import order_objects
from modules.ListCustomers import list_customerNPP
from modules.ListReturnPurchaseOrder import list_orders as list_return_purchase_order
from modules.ListReturnSaleOrder import list_orders as list_return_sale_order

from datetime import datetime
import pandas as pd
from openpyxl.styles import Font
import re
from modules.File import file
all_list_orders = list_orders + order_objects
# df_employee = pd.read_excel('/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/'+file+'/Danh sách nhân viên.xlsx', engine='openpyxl', skiprows=3) #, header=4
# employees_none=["ABS-2025-025","ABS-2025-057","ABS-2025-058","ABN-2024-17c","ABS-2020-05","ABN-2012-04","ABN-2020-50","ABN-2020-65","ABN-2024-17b","ABN-2013-18",
#                 "ABN-2026-050","ABN-2026-004","NV000001","ABN-2013-06","ABN-2025-24-TK","NV000002","ABN-2019-25","ABN-2011-01","ABN-2013-03","ABN-2018-18",
#                 "ABC-2012-02","ABN-2024-08","ABS-2023-34","ABN-2015-04","ABN-2025-70","ABS-2016-12","ABN-2020-36","ABN-2015-09","ABS-2016-03"]
# employees_none=["NV001","GIS-2025-033","GIS-CTV-03","GIS-2025-039","GIN-CTV-32","GIN-CTV-22","GIN-CTV-21","GIN-CTV-17",
#                 "GIN-2024-10","GIN-TEST05","GIS-TEST06","GIN-TEST16","GIN-TEST14","GIN-TEST04","GIN-TEST03","GIS-2025-009",
#                 "GIN-2019-01","NV0002","GIN-TEST01","TEST002","TEST001","GIN-TEST18","GIN-TEST13","GIN-TEST09","GIN-TEST17",
#                 "GIN-TEST07","GIS-TEST12","GIN-TEST08","GIN-TEST15"]
# print("COLUMNS:")
# for col in df_employee.columns:
#     print(repr(col))
# df_employee = df_employee[df_employee['Trạng thái lao động (*)'].isin(["Đang làm việc"]) & ~df_employee['Mã nhân viên (*)'].isin(employees_none)]

# df_phanvung = pd.read_excel('/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/'+file+'/PhanTuyen.xlsx', sheet_name='Phân Vùng', engine='openpyxl')
# df_employee = df_employee.merge(
#     df_phanvung[["Email cơ quan", "Phân vùng"]],
#     how = 'left',
#     on = "Email cơ quan")
# print(df_employee['Email cơ quan'].is_unique)
# # Tạo danh sách các đối tượng Order
# list_employee = [Employee(row['Email cơ quan'], row['Họ và tên (*)'],"", "",row['Điện thoại di động'], row['Mã nhân viên (*)'], row['Email tài khoản'],row['Đơn vị công tác (*)'], row['Trạng thái lao động (*)'], row['Ngày thử việc'], row['Phân vùng']) for index, row in df_employee.iterrows()]
# # 🔥 CHUYỂN LIST → DICT
# employees = {e.employee_id: e for e in list_employee}
# df_territory = pd.read_excel('/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/'+file+'/PhanTuyen.xlsx', sheet_name='Phân tuyến', engine='openpyxl')
# # Chuyển thành list of dict
# customers = {c.account_number: c for c in list_customerNPP}
# territory_data = df_territory.to_dict(orient="records")
# territory_map = TerritoryMap()
# territory_map.load_territory(territory_data)
# def clean_str(x):
#     return str(x).strip() if x is not None and not pd.isna(x) else None
# def auto_assign_customers(customers, territory_map, employees):
#     assigned_customers = {}
#     unassigned_customers = []

#     for customer in customers:
#         emp_id = territory_map.get_employee_for_customer(customer)

#         if emp_id and emp_id in employees:
#             employees[emp_id].add_customer(customer)

#             # Lưu vào danh sách đã gán
#             assigned_customers.setdefault(emp_id,[]).append(customer)
#         else:
#             unassigned_customers.append(customer)

#     return assigned_customers, unassigned_customers

# # 3. Auto assign
# assigned, unassigned = auto_assign_customers(list_customerNPP, territory_map, employees)
# def extract_owner_code(owner_name):
#     # ❗ xử lý NaN / float / None
#     if owner_name is None or pd.isna(owner_name):
#         return None

#     owner_name = str(owner_name)  # ép về string an toàn
#     m = re.search(r"\((.*?)\)", owner_name)
#     return m.group(1) if m else None
# rows = []
# for emp_id, customer_list in assigned.items():
#     emp = employees.get(emp_id)   # 👈 lấy object Employee

#     for c in customer_list:
#         rows.append({
#             # ==== THÔNG TIN NHÂN VIÊN ====
#             "Mã nhân viên": emp.employee_id if emp else emp_id,
#             "Tên nhân viên": emp.employee_type if emp else None,
#             "Phân vùng": emp.employee_enday if emp else None,

#             # ==== THÔNG TIN KHÁCH HÀNG ====
#             "Mã khách hàng": c.account_number,
#             "Tên khách hàng": c.account_name,
#             "Điện thoại KH": c.phone,
#             "Tỉnh": c.billing_province,
#             "Xã/Phường": c.billing_ward,
#             "Chủ sở hữu": c.owner_name,
#             "Mã chủ sở hữu": extract_owner_code(c.owner_name),
#             "Loại khách hàng": c.account_type
#         })
# df_phantuyen = pd.DataFrame(rows)
# rows_unassigned = []

# for c in unassigned:
#     rows_unassigned.append({
#         "Mã khách hàng": clean_str(c.account_number),
#         "Tên khách hàng": clean_str(c.account_name),
#         "Tỉnh": clean_str(c.billing_province),
#         "Xã/Phường": clean_str(c.billing_ward),
#         "Lý do": "Không tìm thấy phân tuyến"
#     })

# df_unassigned = pd.DataFrame(rows_unassigned)
# with pd.ExcelWriter("Phân tuyến khách hàng.xlsx", engine='openpyxl', mode='w') as writer:
#     df_phantuyen.to_excel(writer, sheet_name='Cả nước', index=False)
#     df_unassigned.to_excel(writer, sheet_name="Chưa phân tuyến", index=False)
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

    # province_MB=["Hà Nội","Bắc Giang","Bắc Kạn","Bắc Ninh","Cao Bằng","Điện Biên","Hà Giang","Hà Nam","Hà Tĩnh","Hải Dương","Hải Phòng","Hòa Bình","Hưng Yên","Lai Châu","Lạng Sơn","Lào Cai","Nam Định","Nghệ An","Ninh Bình","Phú Thọ","Quảng Ninh","Sơn La","Thái Bình","Thái Nguyên","Thanh Hóa","Tuyên Quang","Vĩnh Phúc","Yên Bái"]
    
    # province_MB01=["Huyện Mê Linh","Huyện Đông Anh","Huyện Sóc Sơn","Huyện Ba Vì","Thị xã Sơn Tây","Huyện Phúc Thọ","Huyện Quốc Oai","Huyện Thạch Thất","Huyện Ứng Hòa","Huyện Mỹ Đức","Huyện Thanh Oai","Huyện Thanh Trì","Huyện Thường Tín","Huyện Phú Xuyên"]
    province_MB01=["Kinh doanh OTC Miền Bắc khu vực 1"]
    # province_MB02=["Quận Ba Đình","Quận Đống Đa","Quận Tây Hồ","Quận Thanh Xuân","Quận Hà Đông","Quận Chương Mỹ","Quận Hoàng Mai","Quận Hai Bà Trưng","Quận Hoàn Kiếm","Quận Long Biên","Huyện Gia Lâm","Huyện Đan Phượng","Huyện Hoài Đức","Quận Cầu Giấy","Quận Bắc Từ Liêm","Quận Nam Từ Liêm"]
    province_MB02=["Kinh doanh OTC Miền Bắc khu vực 2"]
    # province_MB03=["Hải Phòng","Quảng Ninh","Hải Dương"]
    province_MB03=["Kinh doanh OTC Miền Bắc khu vực 3"]
    # province_MB04=["Thái Nguyên","Bắc Giang","Bắc Ninh","Lạng Sơn","Cao Bằng","Bắc Kạn"]
    province_MB04=["Kinh doanh OTC Miền Bắc khu vực 4"]
    # province_MB05=["Sơn La","Lai Châu","Điện Biên","Hưng Yên","Hà Nam","Hoà Bình"]
    province_MB05=["Kinh doanh OTC Miền Bắc khu vực 5"]
    # province_MB06=["Nam Định","Ninh Bình","Thái Bình","Thanh Hóa"]
    province_MB06=["Kinh doanh OTC Miền Bắc khu vực 6"]
    # province_MB07=["Thanh Hóa","Nghệ An","Hà Tĩnh"]
    province_MB07=["Kinh doanh OTC Miền Bắc khu vực 7"]
    # province_MB08=["Vĩnh Phúc","Phú Thọ","Yên Bái","Hà Giang","Tuyên Quang","Lào Cai"]
    province_MB08=["Kinh doanh OTC Miền Bắc khu vực 8"]
    # # Danh sách miền Trung
    # province_MT=['Đà Nẵng','Bình Định','Gia Lai','Kon Tum','Phú Yên','Quảng Bình','Quảng Nam','Quảng Ngãi','Quảng Trị','Huế']
    # province=['Thanh Hóa (VN)']
    province_MT0=["Kinh doanh OTC Miền Trung"]
    # Danh sách miền Nam
    # province_MN = ['Hồ Chí Minh','An Giang','Bà Rịa - Vũng Tàu','Bạc Liêu','Bến Tre','Bình Dương','Bình Phước','Bình Thuận','Cà Mau','Đắk Lắk','Đắk Nông','Đồng Nai','Đồng Tháp','Hậu Giang','Khánh Hòa','Kiên Giang','Lâm Đồng','Long An','Ninh Thuận','Sóc Trăng','Tây Ninh','Tiền Giang','Cần Thơ','Trà Vinh','Vĩnh Long']
    # province_MN01=["Quận 12","Huyện Củ Chi", "Huyện Hóc Môn","Quận Tân Phú","Quận Tân Bình","Quận Bình Tân","Quận 4","Quận 8","Quận 5","Quận 10","Quận 1","Quận 3"]
    province_MN01=["Kinh doanh OTC Miền Nam khu vực 1"]
    province_MN02=["Kinh doanh OTC Miền Nam khu vực 2"]
    # province_MN03=["Bình Phước","Bình Thuận","Ninh Thuận","Khánh Hòa","Đắk Lắk","Đắk Nông"]
    province_MN03=["Kinh doanh OTC Miền Nam khu vực 5"] # Quốc hội
    # province_MN04=["Bình Dương","Đồng Nai","Lâm Đồng","Bà Rịa - Vũng Tàu","Long An","Tây Ninh"] # Thanh Quang
    province_MN04=["Kinh doanh OTC Miền Nam khu vực 3"]
    # province_MN05=["Tiền Giang","Đồng Tháp","An Giang","Vĩnh Long","Bến Tre","Trà Vinh"]
    province_MN05=["Kinh doanh OTC Miền Nam khu vực 4"] # Khổng Duy
    # province_MN06=["Cần Thơ","Hậu Giang","Sóc Trăng","Bạc Liêu","Cà Mau","Kiên Giang"]
    province_MN06=["Kinh doanh OTC Miền Nam khu vực 6"]
    province_MN07=["Kinh doanh OTC Miền Nam khu vực 7"]
    vietnam = province_MB01 + province_MB02 + province_MB03 + province_MB04 + province_MB05 + province_MB06 + province_MB07 + province_MB08 + province_MN01 + province_MN02 + province_MN03 + province_MN04 + province_MN05 + province_MN06 + province_MN07 + province_MT0
    
    province_MB=province_MB01 + province_MB02 + province_MB03 + province_MB04 + province_MB05 + province_MB06 + province_MB07 + province_MB08
    province_MN=province_MN01 + province_MN02 + province_MN03 + province_MN04 + province_MN05 + province_MN06 + province_MN07
    vietnam_01 = province_MB02 + province_MB07 #province_MB01 + province_MB02 + province_MB03 + province_MB04 + province_MB05 + 
    print(vietnam)
    list_customer = ["1MBKV300000022"]
    statuses=["Đã ghi","Đề nghị ghi", "Đã lập chứng từ","Đã duyệt"] #,"Bản nháp","Đề nghị ghi",Đã ghi,,"Đề nghị ghi"
    start_time = "2026-01-01"
    end_time = "2026-12-13"
    months = [1,2,3,4,5,6,7,8,9,10,11,12] #3,4,5,6,7,8,9,
    # Mở ExcelWriter
    print(len(list_customerNPP))

    product_price_map = {
        p.product_id: p.price
        for p in list_products
    }
    
    # with pd.ExcelWriter("Báo cáo tồn kho.xlsx", engine='openpyxl', mode='w') as writer:
    #     for customer in list_customerNPP:
    #         # if (list_customerNPP[i]['Tỉnh/Thành phố (Hóa đơn)'] in province_MB) and (list_customerNPP[i]['Mã khách hàng (*)'] not in ["1MB8DLYB002","1MB4DLTN002","3MNĐLTV01","3MNĐLLĐ01","3MNĐLĐN07","3MNĐLĐT02","3MNĐLHG01","3MNĐLAG03","3MNĐLBTHU02","3MNĐLKG02"]):
    #         if (customer.get('billing_province') in province_MB) and (customer.get('account_number') in ["1MB4CBNT005"]):
    #             # Tên sheet
    #             sheet_filename = f"Sheet{customer.get('account_number')}_{customer.get('billing_province')}"
    #             rows=[]
    #             for product in list_products:
    #                 info=sales_report.getProductInventoryByCustomer(customer.get('account_number'),product.product_id,start_time,end_time,status)

    #                 rows.append({
    #                     "Mã sản phẩm": product.product_id,
    #                     "Tên sản phẩm": product.name,
    #                     "Đơn giá": product.price,
    #                     "Loại hàng hoá": product.category,
    #                     "Tồn kho đầu kỳ (SL)": info[0],
    #                     "Tồn kho đầu kỳ (KM)": info[1],
    #                     "Số lượng nhập (SL)": info[2],
    #                     "Số lượng nhập (KM)": info[3],
    #                     "Doanh số nhập": product.price * info[2],
    #                     "Số lượng bán (SL)": info[4],
    #                     "Số lượng bán (KM)": info[5],
    #                     "Doanh số bán": product.price * info[4],
    #                     "Tồn kho cuối kỳ (SL)": info[6],
    #                     "Tồn kho cuối kỳ (KM)": info[7],
    #                     "Công nợ": product.price * info[6]
    #                     })
    #                 # rows.append({
    #                 #     "Mã sản phẩm": product.product_id,
    #                 #     "Tên sản phẩm": product.name,
    #                 #     "soluong_nhap_dauky": info[0],
    #                 #     "soluong_nhapKM_dauky": info[1],
    #                 #     "soluong_ban_dauky": info[2],
    #                 #     "soluong_banKM_dauky": info[3],
    #                 #     "purchase_quantity": info[4],
    #                 #     "promo_purchase_quantity": info[5],
    #                 #     "sold_quantity": info[6],
    #                 #     "promo_sold_quantity": info[7],
    #                 #     "soluong_trahangmua_dauky_sl": info[8],
    #                 #     "soluong_trahangmua_dauky_km": info[9],
    #                 #     "soluong_trahangmua_sl": info[10],
    #                 #     "soluong_trahangmua_km": info[11],
    #                 #     "soluong_trahangban_dauky_sl": info[12],
    #                 #     "soluong_trahangban_dauky_km": info[13],
    #                 #     "soluong_trahangban_sl": info[14],
    #                 #     "soluong_trahangban_km": info[15]
    #                 #     })
    #             # Ghi sheet vào Excel
    #             df = pd.DataFrame(rows)
    #             df.to_excel(writer, sheet_name=sheet_filename, startrow=3, startcol=0, index=False)
    #             # Sau khi ghi, thêm dòng ở A1
    #             worksheet = writer.sheets[sheet_filename]  # Lấy sheet object từ writer
    #             cell = worksheet.cell(row=1, column=1, value=f"Báo cáo tồn kho: {list_customerNPP[i]['Mã khách hàng (*)']} {list_customerNPP[i]['Tên khách hàng (*)']}")
    #             thoigian = worksheet.cell(row=2, column=1, value=f"Từ {start_time} đến {end_time}")
    #             # Áp dụng font bôi đậm và cỡ chữ lớn hơn
    #             cell.font = Font(bold=True, size=14)  # size có thể đổi theo nhu cầu (ví dụ: 16, 18,...)



    # customers_report = []

    # for customer in list_customerNPP:
    #     loai = str(customer.get('account_type') or "")
    #     # if "3MN_HĐ00" not in loai:
    #     #     continue
    #     if customer.get('unit') in vietnam:
    #     # if customer.get('account_number') in list_customer:
    #         doanhso = []
    #         customer_id = customer.get('account_number')

    #         for month in months:
    #             monthly_sales = sales_report.calculate_monthly_sales(
    #                 customer_id=customer_id,
    #                 start_day=start_time,
    #                 end_day=end_time,
    #                 month=int(month),
    #                 statuses=statuses,
    #                 product_price_map=product_price_map
    #             )
    #             if int(monthly_sales[1]) == 11:
    #                 print(monthly_sales)
    #             doanhso.append(monthly_sales[3])  # Giữ nguyên nếu index 3 là đúng cấu trúc
    #         # if customer.get('sign_date').month == 7:
    #         customers_report.append({
    #             "Mã khách hàng": customer.get('account_number'),
    #             "Tên khách hàng": customer.get('account_name'),
    #             "Loại khách hàng": customer.get('account_type'),
    #             "Ngày ký hợp đồng": customer.get('sign_date'),
    #             "Mô tả": customer.get('description'),
    #             "Ngày ghé thăm gần nhất": customer.get('visting_lastday'),
    #             "Mã số thuế": customer.get('tax_code'),
    #             "Điện thoại": customer.get('phone'),
    #             "Số nhà": customer.get('billing_street'),
    #             "Phường/Xã": customer.get('billing_ward'),
    #             "Quận/Huyện": customer.get('billing_district'),
    #             "Tỉnh/Thành phố": customer.get('billing_province'),
    #             "Đơn vị": customer.get('unit'),
    #             "Chủ sở hữu": customer.get('owner_name'),
    #             "Là nhà phân phối": customer.get('is_distributor'),
    #             "Ngày sinh nhật": customer.get('date_of_birthday'),
    #             "Tháng 1": float(doanhso[0]),
    #             "Tháng 2": float(doanhso[1]),
    #             "Tháng 3": float(doanhso[2]),
    #             # "Tháng 4": str(doanhso[3]),
    #             # "Tháng 5": str(doanhso[4]),
    #             # "Tháng 6": str(doanhso[5]),
    #             # "Tháng 7": str(doanhso[6]),
    #             # "Tháng 8": str(doanhso[7]),
    #             # "Tháng 9": str(doanhso[8]),
    #             # "Tháng 10": str(doanhso[9])
    #         })

    # df = pd.DataFrame(customers_report)
    # targets = ["1MB_HĐ001", "1MB_HĐ015", "1MB_HĐ002", "1MB_HĐ003","1MB_HĐ005", "1MB_HĐ008","1MB_KL001",
    #             "1MB_KGPP_HĐ001", "1MB_KGPP_HĐ015", "1MB_KGPP_HĐ002", "1MB_KGPP_HĐ003","1MB_KGPP_HĐ005", "1MB_KGPP_HĐ008","1MB_KGPP_KL001",
    #             "2MT_HĐ001", "2MT_HĐ015", "2MT_HĐ002","2MT_HĐ003","2MT_HĐ005","2MT_KL001",
    #             "2MT_KGPP_HĐ001", "2MT_KGPP_HĐ015", "2MT_KGPP_HĐ002","2MT_KGPP_HĐ003","2MT_KGPP_HĐ005","2MT_KGPP_KL001",
    #             "3MN_HĐ001", "3MN_HĐ015", "3MN_HĐ002","3MN_HĐ003", "3MN_HĐ005","3MN_KL001",
    #             "3MN_KGPP_HĐ001", "3MN_KGPP_HĐ015", "3MN_KGPP_HĐ002","3MN_KGPP_HĐ003", "3MN_KGPP_HĐ005","3MN_KGPP_KL001"]  # chỉnh theo nhu cầu "1MBTINHDL",
    # pat = re.compile("|".join(re.escape(t) for t in targets))

    # df['Loại hợp đồng'] = (
    #     df['Loại khách hàng']
    #     .fillna("")
    #     .str.findall(pat)
    #     .apply(lambda xs: "; ".join(dict.fromkeys(xs)))
    # )

    # df['Loại phân vùng'] = (
    #     df['Loại khách hàng']
    #     .fillna("")
    #     .str.replace(pat, "", regex=True)
    #     .str.replace(r"[-_]+", " ", regex=True)
    #     .str.strip()
    #     .replace("", "Chưa xác định")
    # )    
    # df['Ngày ký hợp đồng'] = pd.to_datetime(df['Ngày ký hợp đồng'])
    # # df = df[~df['Mã khách hàng'].fillna("").str.contains("2MT", regex=False)]
    # # ORDER = ["Tỉnh/Thành phố","Quận/Huyện","Phường/Xã"]  # đổi theo tên cột của bạn
    # # df = df.sort_values(by=ORDER, na_position="last", kind="mergesort")

    # # df_province_MB = df[df['Đơn vị'].isin(province_MB) & df['Ngày ký hợp đồng'].dt.month.isin([2])]
    # # # df_province_MB = df[df['Đơn vị'].isin(province_MB) & df['Loại hợp đồng'].isin(["1MB_KL001"])]
    # # df_province_MN = df[df['Đơn vị'].isin(province_MN) & df['Ngày ký hợp đồng'].dt.month.isin([2])]
    # # df_province_MT = df[df['Đơn vị'].isin(province_MT0) & df['Ngày ký hợp đồng'].dt.month.isin([2])]

    # df_province_MB = df[df['Đơn vị'].isin(province_MB)]
    # df_province_MN = df[df['Đơn vị'].isin(province_MN)]
    # df_province_MT = df[df['Đơn vị'].isin(province_MT0)]

    # df_province_MB01 = df[df['Đơn vị'].isin(province_MB01)]
    # df_province_MB02 = df[df['Đơn vị'].isin(province_MB02)] #  & df['Loại hợp đồng'].isin(["1MB_HĐ001", "1MB_HĐ002", "1MB_HĐ003","1MB_HĐ005", "1MB_HĐ008"])
    # df_province_MB03 = df[df['Đơn vị'].isin(province_MB03)]
    # df_province_MB04 = df[df['Đơn vị'].isin(province_MB04)]
    # df_province_MB05 = df[df['Đơn vị'].isin(province_MB05)]
    # df_province_MB06 = df[df['Đơn vị'].isin(province_MB06)]
    # df_province_MB07 = df[df['Đơn vị'].isin(province_MB07)]
    # df_province_MB08 = df[df['Đơn vị'].isin(province_MB08)]

    # df_province_MN01 = df[df['Đơn vị'].isin(province_MN01)]
    # df_province_MN02 = df[df['Đơn vị'].isin(province_MN02)]
    # df_province_MN03 = df[df['Đơn vị'].isin(province_MN03)]
    # df_province_MN04 = df[df['Đơn vị'].isin(province_MN04)]
    # df_province_MN05 = df[df['Đơn vị'].isin(province_MN05)]
    # df_province_MN06 = df[df['Đơn vị'].isin(province_MN06)]
    # df_province_MN07 = df[df['Đơn vị'].isin(province_MN07)]
    # with pd.ExcelWriter("/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/"+file+"/report/Báo cáo doanh số khách hàng "+file+".xlsx", engine='openpyxl', mode='w') as writer:
    #     df.to_excel(writer, sheet_name='Cả nước', index=False)
    #     df_province_MB.to_excel(writer, sheet_name='Miền Bắc', index=False)
    #     df_province_MN.to_excel(writer, sheet_name='Miền Nam', index=False)
    #     df_province_MT.to_excel(writer, sheet_name='Miền Trung', index=False)
    #     df_province_MB01.to_excel(writer, sheet_name='MB01', index=False)
    #     df_province_MB02.to_excel(writer, sheet_name='MB02', index=False)
    #     df_province_MB03.to_excel(writer, sheet_name='MB03', index=False)
    #     df_province_MB04.to_excel(writer, sheet_name='MB04', index=False)
    #     df_province_MB05.to_excel(writer, sheet_name='MB05', index=False)
    #     df_province_MB06.to_excel(writer, sheet_name='MB06', index=False)
    #     df_province_MB07.to_excel(writer, sheet_name='MB07', index=False)
    #     df_province_MB08.to_excel(writer, sheet_name='MB08', index=False)

    #     df_province_MN01.to_excel(writer, sheet_name='MN01', index=False)
    #     df_province_MN02.to_excel(writer, sheet_name='MN02', index=False)
    #     df_province_MN03.to_excel(writer, sheet_name='MN03', index=False)
    #     df_province_MN04.to_excel(writer, sheet_name='MN04', index=False)
    #     df_province_MN05.to_excel(writer, sheet_name='MN05', index=False)
    #     df_province_MN06.to_excel(writer, sheet_name='MN06', index=False)
    #     df_province_MN07.to_excel(writer, sheet_name='MN07', index=False)
 


    # customers_report = []

    # for customer in list_customerNPP:
    #     loai = str(customer.get('account_type') or "")
    #     # if "3MN_HĐ00" not in loai:
    #     #     continue
    #     if customer.get('unit') in vietnam:
    #     # if customer.get('account_number') in list_customer:
    #         doanhso_dongtanduoc = []
    #         doanhso_tpcn = []
    #         customer_id = customer.get('account_number')

    #         for month in months:
    #             monthly_sales = sales_report.calculate_monthly_sales_detail(
    #                 customer_id=customer_id,
    #                 start_day=start_time,
    #                 end_day=end_time,
    #                 month=int(month),
    #                 statuses=statuses,
    #                 product_price_map=product_price_map
    #             )
    #             if int(monthly_sales[1]) == 11:
    #                 print(monthly_sales)
    #             doanhso_dongtanduoc.append(monthly_sales[2])  # Giữ nguyên nếu index 3 là đúng cấu trúc
    #             doanhso_tpcn.append(monthly_sales[3])
    #         # if customer.get('sign_date').month == 7:
    #         customers_report.append({
    #             "Mã khách hàng": customer.get('account_number'),
    #             "Tên khách hàng": customer.get('account_name'),
    #             "Loại khách hàng": customer.get('account_type'),
    #             "Ngày ký hợp đồng": customer.get('sign_date'),
    #             "Mô tả": customer.get('description'),
    #             "Ngày ghé thăm gần nhất": customer.get('visting_lastday'),
    #             "Mã số thuế": customer.get('tax_code'),
    #             "Điện thoại": customer.get('phone'),
    #             "Số nhà": customer.get('billing_street'),
    #             "Phường/Xã": customer.get('billing_ward'),
    #             "Quận/Huyện": customer.get('billing_district'),
    #             "Tỉnh/Thành phố": customer.get('billing_province'),
    #             "Đơn vị": customer.get('unit'),
    #             "Chủ sở hữu": customer.get('owner_name'),
    #             "Là nhà phân phối": customer.get('is_distributor'),
    #             "Ngày sinh nhật": customer.get('date_of_birthday'),
    #             "Tháng 1 (Thuốc)": float(doanhso_dongtanduoc[0]),
    #             "Tháng 1 (TPCN)": float(doanhso_tpcn[0]),
    #             "Tháng 2 (Thuốc)": float(doanhso_dongtanduoc[1]),
    #             "Tháng 2 (TPCN)": float(doanhso_tpcn[1]),
    #             "Tháng 3 (Thuốc)": float(doanhso_dongtanduoc[2]),
    #             "Tháng 3 (TPCN)": float(doanhso_tpcn[2]),
    #             # "Tháng 3": str(doanhso[2]),
    #             # "Tháng 4": str(doanhso[3]),
    #             # "Tháng 5": str(doanhso[4]),
    #             # "Tháng 6": str(doanhso[5]),
    #             # "Tháng 7": str(doanhso[6]),
    #             # "Tháng 8": str(doanhso[7]),
    #             # "Tháng 9": str(doanhso[8]),
    #             # "Tháng 10": str(doanhso[9])
    #         })

    # df = pd.DataFrame(customers_report)
    # targets = ["1MB_HĐ001", "1MB_HĐ015", "1MB_HĐ002", "1MB_HĐ003","1MB_HĐ005", "1MB_HĐ008","1MB_KL001",
    #             "1MB_KGPP_HĐ001", "1MB_KGPP_HĐ015", "1MB_KGPP_HĐ002", "1MB_KGPP_HĐ003","1MB_KGPP_HĐ005", "1MB_KGPP_HĐ008","1MB_KGPP_KL001",
    #             "2MT_HĐ001", "2MT_HĐ015", "2MT_HĐ002","2MT_HĐ003","2MT_HĐ005","2MT_KL001",
    #             "2MT_KGPP_HĐ001", "2MT_KGPP_HĐ015", "2MT_KGPP_HĐ002","2MT_KGPP_HĐ003","2MT_KGPP_HĐ005","2MT_KGPP_KL001",
    #             "3MN_HĐ001", "3MN_HĐ015", "3MN_HĐ002","3MN_HĐ003", "3MN_HĐ005","3MN_KL001",
    #             "3MN_KGPP_HĐ001", "3MN_KGPP_HĐ015", "3MN_KGPP_HĐ002","3MN_KGPP_HĐ003", "3MN_KGPP_HĐ005","3MN_KGPP_KL001"]  # chỉnh theo nhu cầu "1MBTINHDL",
    # pat = re.compile("|".join(re.escape(t) for t in targets))

    # df['Loại hợp đồng'] = (
    #     df['Loại khách hàng']
    #     .fillna("")
    #     .str.findall(pat)
    #     .apply(lambda xs: "; ".join(dict.fromkeys(xs)))
    # )

    # df['Loại phân vùng'] = (
    #     df['Loại khách hàng']
    #     .fillna("")
    #     .str.replace(pat, "", regex=True)
    #     .str.replace(r"[-_]+", " ", regex=True)
    #     .str.strip()
    #     .replace("", "Chưa xác định")
    # )    
    # df['Ngày ký hợp đồng'] = pd.to_datetime(df['Ngày ký hợp đồng'])
    # # df = df[~df['Mã khách hàng'].fillna("").str.contains("2MT", regex=False)]
    # # ORDER = ["Tỉnh/Thành phố","Quận/Huyện","Phường/Xã"]  # đổi theo tên cột của bạn
    # # df = df.sort_values(by=ORDER, na_position="last", kind="mergesort")
    # df['Mã nhân viên'] = df['Chủ sở hữu'].str.extract(r"\(([^)]+)\)")

    # df_province_MB = df[df['Đơn vị'].isin(province_MB)]
    # # df_province_MB = df[df['Đơn vị'].isin(province_MB) & df['Loại hợp đồng'].isin(["1MB_KL001"])]
    # df_province_MN = df[df['Đơn vị'].isin(province_MN)]
    # df_province_MT = df[df['Đơn vị'].isin(province_MT0)]

    # df_province_MB01 = df[df['Đơn vị'].isin(province_MB01)]
    # df_province_MB02 = df[df['Đơn vị'].isin(province_MB02)] #  & df['Loại hợp đồng'].isin(["1MB_HĐ001", "1MB_HĐ002", "1MB_HĐ003","1MB_HĐ005", "1MB_HĐ008"])
    # df_province_MB03 = df[df['Đơn vị'].isin(province_MB03)]
    # df_province_MB04 = df[df['Đơn vị'].isin(province_MB04)]
    # df_province_MB05 = df[df['Đơn vị'].isin(province_MB05)]
    # df_province_MB06 = df[df['Đơn vị'].isin(province_MB06)]
    # df_province_MB07 = df[df['Đơn vị'].isin(province_MB07)]
    # df_province_MB08 = df[df['Đơn vị'].isin(province_MB08)]

    # df_province_MN01 = df[df['Đơn vị'].isin(province_MN01)]
    # df_province_MN02 = df[df['Đơn vị'].isin(province_MN02)]
    # df_province_MN03 = df[df['Đơn vị'].isin(province_MN03)]
    # df_province_MN04 = df[df['Đơn vị'].isin(province_MN04)]
    # df_province_MN05 = df[df['Đơn vị'].isin(province_MN05)]
    # df_province_MN06 = df[df['Đơn vị'].isin(province_MN06)]
    # df_province_MN07 = df[df['Đơn vị'].isin(province_MN07)]
    # with pd.ExcelWriter("/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/"+file+"/Báo cáo doanh số khách hàng "+file+".xlsx", engine='openpyxl', mode='w') as writer:
    #     df.to_excel(writer, sheet_name='Cả nước', index=False)
    #     df_province_MB.to_excel(writer, sheet_name='Miền Bắc', index=False)
    #     df_province_MN.to_excel(writer, sheet_name='Miền Nam', index=False)
    #     df_province_MT.to_excel(writer, sheet_name='Miền Trung', index=False)
    #     df_province_MB01.to_excel(writer, sheet_name='MB01', index=False)
    #     df_province_MB02.to_excel(writer, sheet_name='MB02', index=False)
    #     df_province_MB03.to_excel(writer, sheet_name='MB03', index=False)
    #     df_province_MB04.to_excel(writer, sheet_name='MB04', index=False)
    #     df_province_MB05.to_excel(writer, sheet_name='MB05', index=False)
    #     df_province_MB06.to_excel(writer, sheet_name='MB06', index=False)
    #     df_province_MB07.to_excel(writer, sheet_name='MB07', index=False)
    #     df_province_MB08.to_excel(writer, sheet_name='MB08', index=False)

    #     df_province_MN01.to_excel(writer, sheet_name='MN01', index=False)
    #     df_province_MN02.to_excel(writer, sheet_name='MN02', index=False)
    #     df_province_MN03.to_excel(writer, sheet_name='MN03', index=False)
    #     df_province_MN04.to_excel(writer, sheet_name='MN04', index=False)
    #     df_province_MN05.to_excel(writer, sheet_name='MN05', index=False)
    #     df_province_MN06.to_excel(writer, sheet_name='MN06', index=False)
    #     df_province_MN07.to_excel(writer, sheet_name='MN07', index=False)
 



    # for unit in vietnam:
    #     customers_report = []

    #     for customer in list_customerNPP:
    #         loai = str(customer.get('account_type') or "")
    #         # if "3MN_HĐ00" not in loai:
    #         #     continue
    #         if customer.get('unit') == unit:
    #         # if customer.get('account_number') in list_customer:
    #             doanhso = []
    #             customer_id = customer.get('account_number')

    #             for month in months:
    #                 monthly_sales = sales_report.calculate_monthly_sales(
    #                     customer_id=customer_id,
    #                     start_day=start_time,
    #                     end_day=end_time,
    #                     month=int(month),
    #                     statuses=statuses
    #                 )
    #                 if int(monthly_sales[1]) == 9:
    #                     print(monthly_sales)
    #                 doanhso.append(monthly_sales[3])  # Giữ nguyên nếu index 3 là đúng cấu trúc
    #             # if customer.get('sign_date').month == 7:
    #             customers_report.append({
    #                 "Mã khách hàng": customer.get('account_number'),
    #                 "Tên khách hàng": customer.get('account_name'),
    #                 "Loại khách hàng": customer.get('account_type'),
    #                 "Ngày ký hợp đồng": customer.get('sign_date'),
    #                 "Mô tả": customer.get('description'),
    #                 "Ngày ghé thăm gần nhất": customer.get('visting_lastday'),
    #                 "Mã số thuế": customer.get('tax_code'),
    #                 "Điện thoại": customer.get('phone'),
    #                 "Số nhà": customer.get('billing_street'),
    #                 "Phường/Xã": customer.get('billing_ward'),
    #                 "Quận/Huyện": customer.get('billing_district'),
    #                 "Tỉnh/Thành phố": customer.get('billing_province'),
    #                 "Đơn vị": customer.get('unit'),
    #                 "Chủ sở hữu": customer.get('owner_name'),
    #                 "Là nhà phân phối": customer.get('is_distributor'),
    #                 "Tháng 3": str(doanhso[0]),
    #                 "Tháng 4": str(doanhso[1]),
    #                 "Tháng 5": str(doanhso[2]),
    #                 "Tháng 6": str(doanhso[3]),
    #                 "Tháng 7": str(doanhso[4]),
    #                 "Tháng 8": str(doanhso[5]),
    #                 "Tháng 9": str(doanhso[6]),
    #                 "Tháng 10": str(doanhso[7])
    #             })

    #     df = pd.DataFrame(customers_report)
    #     targets = ["1MB_HĐ001", "1MB_HĐ002", "1MB_HĐ003","1MB_HĐ005", "1MB_HĐ008","1MB_KL001","1MBTINHDL", "2MT_HĐ001","2MT_HĐ002","2MT_HĐ003","2MT_HĐ005","2MT_KL001","2MTTINHDL","3MN_HĐ001", "3MN_HĐ002","3MN_HĐ003", "3MN_HĐ005","3MN_KL001","3MN_ĐL"]  # chỉnh theo nhu cầu
    #     # Tạo regex OR an toàn
    #     pat = re.compile("|".join(re.escape(t) for t in targets))  # thêm flags=re.IGNORECASE nếu cần

    #     # Tìm và chỉ ghi đúng tên mã (nhiều mã -> nối bằng "; ")
    #     df['Loại hợp đồng'] = (df['Loại khách hàng'].astype(str)
    #                    .str.findall(pat)
    #                    .apply(lambda xs: "; ".join(dict.fromkeys(xs))))  # unique, giữ thứ tự
    #     df['Ngày ký hợp đồng'] = pd.to_datetime(df['Ngày ký hợp đồng'])
    #     with pd.ExcelWriter("/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/gmail/"+str(unit)+".xlsx", engine='openpyxl', mode='w') as writer:
    #         df.to_excel(writer, sheet_name='ALL', index=False)

    # promotion_report=[]
    # for customer in list_customerNPP:
    #     loai = str(customer.get('account_type') or "")
    #     # if "3MN_HĐ00" not in loai:
    #     #     continue
    #     if customer.get('unit') in vietnam:
    #     # if customer.get('account_number')=="1MBKV88004":
    #         customer_id = customer.get('account_number')
    #         list_promotion = []
    #         for month in months:
    #             monthly_promotion = sales_report.check_promotion(
    #                 customer_id=customer_id,
    #                 start_day=start_time,
    #                 end_day=end_time,
    #                 month=int(month),
    #                 statuses=statuses
    #             )
    #             # monthly_promotion = sales_report.check_discount_abipha(
    #             #     customer_id=customer_id,
    #             #     start_day=start_time,
    #             #     end_day=end_time,
    #             #     month=int(month),
    #             #     statuses=statuses,
    #             #     product_price_map=product_price_map
    #             # )
    #             list_promotion.append(monthly_promotion[1])
    #         # print(list_promotion)
    #         promotion_report.append({
    #                 "Mã khách hàng": customer.get('account_number'),
    #                 "Tên khách hàng": customer.get('account_name'),
    #                 "Loại khách hàng": customer.get('account_type'),
    #                 "Ngày ký hợp đồng": customer.get('sign_date'),
    #                 "Mô tả": customer.get('description'),
    #                 "Tỉnh/Thành phố": customer.get('billing_province'),
    #                 "Quận/Huyện": customer.get('billing_district'),
    #                 "Tháng 1": str(list_promotion[0]),
    #                 "Tháng 2": str(list_promotion[1]),
    #                 # "Tháng 3": str(list_promotion[2]),
    #                 # "Tháng 6": str(list_promotion[3]),
    #                 # "Tháng 7": str(list_promotion[4]),
    #                 # "Tháng 8": str(list_promotion[5]),
    #                 # "Tháng 9": str(list_promotion[6]),
    #                 # "Tháng 10": str(list_promotion[7]),
    #                 # "Tháng 11": str(list_promotion[8]),
    #                 # "Tháng 12": str(list_promotion[9]),
    #             })
    # df = pd.DataFrame(promotion_report)
    # with pd.ExcelWriter("/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/"+file+"/Báo cáo kiểm tra khuyến mại NPP "+file+".xlsx", engine='openpyxl', mode='w') as writer:
    #     df.to_excel(writer, sheet_name='ALL', index=False)
    


    
    # # for unit in vietnam:
    # #     loai = str(customer.get('account_type') or "")
    # #     if "3MN_HĐ00" not in loai:
    # #         continue
    # for unit in vietnam:
    #     customers_product_report = []
    #     for customer in list_customerNPP:
    #         # if customer.get('billing_province') in vietnam:
    #         if customer.get('unit') == unit:
    #         # if customer.get('unit') in vietnam:
    #             print(customer.get('unit'))
    #         # if customer.get('account_number') in list_customer:
    #             doanhso = []
    #             customer_id = customer.get('account_number')

    #             for month in months:
    #                 for product in list_products:
    #                     monthly_sales_product = sales_report.build_customer_product_table(
    #                         customer_id=customer_id,
    #                         start_day=start_time,
    #                         product_id=product.product_id,
    #                         end_day=end_time,
    #                         month=int(month),
    #                         statuses=statuses
    #                     )
    #                     if monthly_sales_product[1] == 'NaN':
    #                         print()
    #                     customers_product_report.append({
    #                         "Mã khách hàng": customer.get('account_number'),
    #                         "Tên khách hàng": customer.get('account_name'),
    #                         "Loại khách hàng": customer.get('account_type'),
    #                         "Ngày ký hợp đồng": customer.get('sign_date'),
    #                         "Điện thoại": customer.get('phone'),
    #                         "Phường/Xã": customer.get('billing_ward'),
    #                         "Quận/Huyện": customer.get('billing_district'),
    #                         "Tỉnh/Thành phố": customer.get('billing_province'),
    #                         "Chủ sở hữu": customer.get('owner_name'),
    #                         "Là nhà phân phối": customer.get('is_distributor'),
    #                         "Đơn vị": customer.get('unit'),
    #                         "Mã sản phẩm": product.get('product_id'),
    #                         "Tên sản phẩm": product.get('name'),
    #                         "Loại sản phẩm": product.get('category'),
    #                         "Tháng": month,
    #                         "Số lượng bán": int(monthly_sales_product[0]),
    #                         "Doanh số":  int(monthly_sales_product[1])# "Doanh sô": int(product.get('price'))* int(monthly_sales_product)
    #                     })
    #     df = pd.DataFrame(customers_product_report)
    #     targets = ["1MB_HĐ001", "1MB_HĐ015", "1MB_HĐ002", "1MB_HĐ003","1MB_HĐ005", "1MB_HĐ008","1MB_KL001",
    #                 "1MB_KGPP_HĐ001", "1MB_KGPP_HĐ015", "1MB_KGPP_HĐ002", "1MB_KGPP_HĐ003","1MB_KGPP_HĐ005", "1MB_KGPP_HĐ008","1MB_KGPP_KL001",
    #                 "2MT_HĐ001", "2MT_HĐ015", "2MT_HĐ002","2MT_HĐ003","2MT_HĐ005","2MT_KL001",
    #                 "2MT_KGPP_HĐ001", "2MT_KGPP_HĐ015", "2MT_KGPP_HĐ002","2MT_KGPP_HĐ003","2MT_KGPP_HĐ005","2MT_KGPP_KL001",
    #                 "3MN_HĐ001", "3MN_HĐ015", "3MN_HĐ002","3MN_HĐ003", "3MN_HĐ005","3MN_KL001",
    #                 "3MN_KGPP_HĐ001", "3MN_KGPP_HĐ015", "3MN_KGPP_HĐ002","3MN_KGPP_HĐ003", "3MN_KGPP_HĐ005","3MN_KGPP_KL001"] 

    #     # Tạo regex OR an toàn
    #     pat = re.compile("|".join(re.escape(t) for t in targets))  # thêm flags=re.IGNORECASE nếu cần

    #     # # Tìm và chỉ ghi đúng tên mã (nhiều mã -> nối bằng "; ")
    #     # df['Loại hợp đồng'] = (df['Loại khách hàng'].astype(str)
    #     #                .str.findall(pat)
    #     #                .apply(lambda xs: "; ".join(dict.fromkeys(xs))))  # unique, giữ thứ tự  
    #     df['Ngày ký hợp đồng'] = pd.to_datetime(df['Ngày ký hợp đồng'])  
    #     df = df[df['Số lượng bán'] != 0]
    #     df = df[~df['Là nhà phân phối'].isin(["ü"])]
    #     # with pd.ExcelWriter("/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/"+file+"/Báo cáo chi tiết đơn hàng "+file+".xlsx", engine='openpyxl', mode='w') as writer:
    #     with pd.ExcelWriter(str(unit)+".xlsx", engine='openpyxl', mode='w') as writer:
    #         df.to_excel(writer, sheet_name='ALL', index=False)


    # customers_product_report = []
    # for customer in list_customerNPP:
    #     # if customer.get('billing_province') in vietnam:
    #     # if customer.get('unit') == unit:
    #     if customer.get('unit') in vietnam:
    #         print(customer.get('unit'))
    #     # if customer.get('account_number') in list_customer:
    #         doanhso = []
    #         customer_id = customer.get('account_number')
       
    #         for product in list_products:
    #             monthly_sales_product = sales_report.build_customer_product_table_maxtric(
    #                 customer_id=customer_id,
    #                 start_day=start_time,
    #                 product_id=product.product_id,
    #                 end_day=end_time,
    #                 statuses=statuses
    #             )
    #             # print(monthly_sales_product)
    #             customers_product_report.append({
    #                 "Mã khách hàng": customer.get('account_number'),
    #                 "Tên khách hàng": customer.get('account_name'),
    #                 # "Loại khách hàng": customer.get('account_type'),
    #                 # "Ngày ký hợp đồng": customer.get('sign_date'),
    #                 # "Điện thoại": customer.get('phone'),
    #                 # "Phường/Xã": customer.get('billing_ward'),
    #                 # "Quận/Huyện": customer.get('billing_district'),
    #                 # "Tỉnh/Thành phố": customer.get('billing_province'),
    #                 # "Chủ sở hữu": customer.get('owner_name'),
    #                 "Là nhà phân phối": customer.get('is_distributor'),
    #                 "Đơn vị": customer.get('unit'),
    #                 "Mã sản phẩm": product.get('product_id'),
    #                 "Tên sản phẩm": product.get('name'),
    #                 # "Loại sản phẩm": product.get('category'),
    #                 # "Tháng": month,
    #                 "Số lượng bán": int(monthly_sales_product),
    #                 # "Doanh sô": int(product.get('price'))* int(monthly_sales_product)
    #             })
    # df = pd.DataFrame(customers_product_report)
    # df = df[df['Số lượng bán'] != 0]
    # # df = df[~df['Là nhà phân phối'].isin(["ü"])]
    # with pd.ExcelWriter("/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/"+file+"/Báo cáo chi tiết đơn hàng "+file+".xlsx", engine='openpyxl', mode='w') as writer:
    # # with pd.ExcelWriter(str(unit)+".xlsx", engine='openpyxl', mode='w') as writer:
        # df.to_excel(writer, sheet_name='ALL', index=False)
    
    # order_detail = sales_report.build_customer_product_table_detail(start_day=start_time, end_day=end_time, statuses=statuses)
    # df = pd.DataFrame(order_detail)
    # # df.columns = ["Mã đơn hàng","Người thực hiện","Mã khách hàng","Chủ sở hữu","Đơn vị","Là nhà phân phối","Mã sản phẩm","Tên sản phẩm","Nhóm sản phẩm","Tháng","Số lượng","Doanh số","KPI 1","KPI 2"]
    # with pd.ExcelWriter("Báo cáo chi tiết đơn hàng.xlsx", engine='openpyxl', mode='w') as writer:
    #     df.to_excel(writer, sheet_name='Cả nước', index=False)




    customers_report = []
    for customer in list_customerNPP:
        doanhso = []
        customer_id = customer.get('account_number')

        for month in months:
            monthly_sales = sales_report.calculate_monthly_sales(
                customer_id=customer_id,
                start_day=start_time,
                end_day=end_time,
                month=int(month),
                statuses=statuses,
                product_price_map=product_price_map

            )
            # print(monthly_sales)
            doanhso.append(monthly_sales[3])  # Giữ nguyên nếu index 3 là đúng cấu trúc
        # if customer.get('sign_date').month == 7:
        customers_report.append({
            "customer_id": customer.get('account_number'),
            "Tên khách hàng": customer.get('account_name'),
            # "Loại khách hàng": customer.get('account_type'),
            # "Ngày ký hợp đồng": customer.get('sign_date'),
            # "Mô tả": customer.get('description'),
            # "Ngày ghé thăm gần nhất": customer.get('visting_lastday'),
            "Mã số thuế": customer.get('tax_code'),
            "Điện thoại": customer.get('phone'),
            "Số nhà": customer.get('billing_street'),
            # "Phường/Xã": customer.get('billing_ward'),
            "Quận/Huyện": customer.get('billing_district'),
            # "Tỉnh/Thành phố": customer.get('billing_province'),
            # "Đơn vị": customer.get('unit'),
            # "Chủ sở hữu": customer.get('owner_name'),
            # "Là nhà phân phối": customer.get('is_distributor'),
            "Địa chỉ (Giao hàng)": customer.get('billing_address'),
            "Tháng 1": str(doanhso[0]),
            "Tháng 2": str(doanhso[1]),
            "Tháng 3": str(doanhso[2]),
            "Tháng 4": str(doanhso[3]),
            "Tháng 5": str(doanhso[4]),
            "Tháng 6": str(doanhso[5]),
            "Tháng 7": str(doanhso[6]),
            "Tháng 8": str(doanhso[7]),
            "Tháng 9": str(doanhso[8]),
            "Tháng 10": str(doanhso[9]),
            "Tháng 11": str(doanhso[10]),
            "Tháng 12": str(doanhso[11]),
            "Tổng":str(sum(doanhso[:12]))
        })

    df = pd.DataFrame(customers_report)
    df_khNoneAddress = df[df['Quận/Huyện'].isna() & ~(df['Tổng'].isin(["0"]))] # | df['Tháng 1'].isin(["0"])
    tmp_df = pd.DataFrame([o.__dict__ for o in all_list_orders])
    # lấy đơn gần nhất mỗi customer_id
    latest_df = (tmp_df
                 .sort_values(["customer_id", "order_date"])   # cũ -> mới
                 .groupby("customer_id", as_index=False)
                 .tail(1)
                 .reset_index(drop=True)
                )

    # Nếu muốn 1 cột "shipping_address" ghép từ các phần địa chỉ:
    latest_df["shipping_add"] = (
        latest_df[["shipping_address","shipping_ward", "shipping_district", "shipping_province"]]   # đổi tên cột cho đúng
        .fillna("")
        .agg(lambda x: ", ".join([i for i in x if str(i).strip() != ""]), axis=1)
    )
    # Kết quả bạn cần: 1 mã KH ↔ địa chỉ giao hàng (đơn gần nhất)
    df = pd.DataFrame(customers_report)
    result = latest_df[["customer_id", "phone_number","shipping_address","shipping_ward", "shipping_district", "shipping_province","shipping_add"]]

    df_out = df_khNoneAddress.merge(
        result[["customer_id","phone_number","shipping_address","shipping_ward","shipping_district","shipping_province","shipping_add"]],
        on="customer_id",
        how="left"
    )
    df_out = df_out[~df_out['shipping_district'].isna()]
    print(df_out)
    with pd.ExcelWriter("/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/"+file+"/report/Báo cáo cập nhật địa chỉ giao hàng "+file+".xlsx", engine='openpyxl', mode='w') as writer:
        df_out.to_excel(writer, sheet_name='Cả nước', index=False)
    


    # manager = TerritoryManager(
    #     employees=list_employees,
    #     customers=list_customers,
    #     territories=list_territories,
    #     assignments=list_assignments
    # )

    # wrong_customers = manager.get_wrong_assignments()
    # rows = []

    # for c in wrong_customers:
    #     rows.append({
    #         "Mã KH": c.cust_id,
    #         "Tên KH": c.name,
    #         "Tỉnh": c.province,
    #         "Xã": c.ward,
    #         "Mã NV": c.emp_id
    #     })

    # df_wrong = pd.DataFrame(rows)
    # df_wrong.to_excel("Khách hàng gán sai địa bàn.xlsx", index=False)


if __name__ == '__main__':
    main()
