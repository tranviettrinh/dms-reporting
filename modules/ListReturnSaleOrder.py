import pandas as pd
from modules.Product import Product
from modules.Order import Order
from modules.ItemOrder import ItemOrder


# from Product import Product
# from Order import Order
# from ItemOrder import ItemOrder
# from modules.ListProducts import product_category_list 


# Đọc dữ liệu từ file Excel
file_path = '/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/file/CRM_Returndistributor.xlsx'
orders_df = pd.read_excel(file_path, sheet_name='Danh sách')
products_df = pd.read_excel(file_path, sheet_name='Bảng hàng hóa')

# Tạo danh sách các đối tượng Order
list_orders = [Order(row['Số đề nghị'], row['Ngày đề nghị'], row['Mã khách hàng'], row['Tổng tiền'], row['Ngày đề nghị'], row['Tình trạng']) for index, row in orders_df.iterrows()]
# Tạo danh sách các đối tượng Product
product_objects = [ItemOrder(row['Số đề nghị'],row['Mã hàng hóa'], "", row['Đơn vị tính'], row['Số lượng'], row['Đơn giá'], row['Thành tiền'], row['Tổng tiền']) for index, row in products_df.iterrows()]

for item_order in list_orders:
    for item_product in product_objects:
        a = item_order.order_number
        b = item_product.order_id
        if a==b:
            item_order.add_item(
                        # customer_id = record.get("account_code","")
                        product_id=item_product.get("product_id",""),
                        warehouse=item_order.get("warehouse", ""),
                        unit=item_product.get("unit", ""), # Đơn vị tính
                        quantity=item_product.get("quantity", ""), # số lượng
                        unit_price=item_product.get("unit_price", ""), # Đơn giá
                        amount=item_product.get("amount", ""), # Thành tiền
                        total=item_product.get("total", "") # Tổng
                    )
            
