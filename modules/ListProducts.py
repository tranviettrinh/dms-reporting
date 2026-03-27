from modules.Product import Product
import pandas as pd
from modules.File import file
# from Product import Product
# Đọc dữ liệu từ file Excel
file_path = '/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/'+file+'/CRM_Product.xlsx'
product_df = pd.read_excel(file_path, sheet_name='Danh sách')
exclude_codes = ["FBGAAA0013.1_ACT1", "BMDGAA00210_TV","FMDGAA0022","FVXACN0011 T","T24TDD","T23TDD","CKTL","CKĐH","DOIDIEM","FTTDCN0011"]
# product_df = product_df[~product_df['Mã hàng hóa'].isin(exclude_codes) & ~product_df['Loại hàng hóa'].isin(["Nhóm chiết khấu hợp đồng trừ tiền trên đơn","Nhóm VPP tại chi nhánh","Nhóm vật tư MKT - OTC","Nhóm vật tư bán hàng","Nhóm vật tư MKT - ETC","Nhóm hàng hóa ETC","Hàng hóa","nan"])]
# Tạo danh sách các đối tượng Product
list_products = [Product(row['Mã hàng hóa'], row['Tên hàng hóa'], row['Loại hàng hóa'], row['Đơn vị tính chính'], row['Đơn giá bán'], row['Thuế GTGT']) for index, row in product_df.iterrows()]
list_products_DDTD =[]
for product in list_products:
	print(product)
	if product.get('category') =="NHÓM THUỐC ĐÔNG DƯỢC" or product.get('category') =="NHÓM THUỐC TÂN DƯỢC":
		list_products_DDTD.append(product.get('product_id'))
print(list_products_DDTD)
