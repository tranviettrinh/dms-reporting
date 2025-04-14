import requests
import json
import pandas as pd
from modules.Product import Product
from modules.Order import Order
from modules.ListProducts import product_category_list 


# Đọc dữ liệu từ file Excel
file_path = 'saleOrderNPP.xlsx'
orders_df = pd.read_excel(file_path, sheet_name='Danh sách')
products_df = pd.read_excel(file_path, sheet_name='Bảng hàng hoá')

# Tạo danh sách các đối tượng Order
order_objects = [Order(row['Mã đơn hàng'], row['Ngày đặt hàng'], row['Mã khách hàng'], row['Giá trị đơn hàng'], row['Ngày ghi sổ'], row['Tình trạng ghi doanh số']) for index, row in orders_df.iterrows()]

# Tạo danh sách các đối tượng Product
product_objects = [Product(row['Mã hàng hoá'], row['Name'], row['Category'], row['Price']) for index, row in products_df.iterrows()]