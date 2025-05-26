import pandas as pd
from modules.Product import Product
from modules.Order import Order
from modules.ItemOrder import ItemOrder


# from Product import Product
# from Order import Order
# from ItemOrder import ItemOrder
# from modules.ListProducts import product_category_list 


# Đọc dữ liệu từ file Excel
file_path = '/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/file/saleOrderNPP.xlsx'
orders_df = pd.read_excel(file_path, sheet_name='Danh sách')
products_df = pd.read_excel(file_path, sheet_name='Bảng hàng hóa')

# Tạo danh sách các đối tượng Order
order_objects = [Order(row['Mã đơn hàng'], row['Ngày đặt hàng'], row['Mã nhà phân phối'], row['Giá trị đơn hàng'], row['Ngày ghi sổ'], row['Tình trạng ghi doanh số']) for index, row in orders_df.iterrows()]
# Tạo danh sách các đối tượng Product
product_objects = [ItemOrder(row['Số đơn hàng'],row['Mã hàng hóa'], "", row['Đơn vị tính'], row['Số lượng'], row['Đơn giá'], row['Thành tiền'], row['Tổng tiền']) for index, row in products_df.iterrows()]

for item_order in order_objects:
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
            
