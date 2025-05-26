from modules.Product import Product
import pandas as pd
# Đọc dữ liệu từ file Excel
file_path = '/Users/trinh/Desktop/Abipha/abipha_dms/chuong trinh khuyen mai/SanPham.xlsx'
product_df = pd.read_excel(file_path, sheet_name='Danh sách')
exclude_codes = ["FBGAAA0013.1_ACT1", "BMDGAA00210_TV","FMDGAA0022","FVXACN0011 T"]
product_df = product_df[~product_df['Mã hàng hóa'].isin(exclude_codes) & ~product_df['Loại hàng hóa'].isin(["Nhóm chiết khấu hợp đồng trừ tiền trên đơn","Nhóm VPP tại chi nhánh","Nhóm vật tư MKT - OTC","Nhóm vật tư bán hàng","Nhóm vật tư MKT - ETC","Nhóm hàng hóa ETC","Hàng hóa"])]
# Tạo danh sách các đối tượng Product
list_products = [Product(row['Mã hàng hóa'], row['Tên hàng hóa'], row['Loại hàng hóa'], row['Đơn vị tính chính'], row['Đơn giá bán']) for index, row in product_df.iterrows()]

