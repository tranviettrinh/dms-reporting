import pandas as pd
from modules.Product import Product
from modules.Order import Order
from modules.ItemOrder import ItemOrder
from modules.File import file

# from Product import Product
# from Order import Order
# from ItemOrder import ItemOrder
# from modules.ListProducts import product_category_list 


# Đọc dữ liệu từ file Excel
file_path = '/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/'+file+'/CRM_Distributor.xlsx'
orders_df = pd.read_excel(file_path, sheet_name='Danh sách')
products_df = pd.read_excel(file_path, sheet_name='Bảng hàng hóa')
products_df = products_df.dropna(subset=['Đơn vị tính'])

# 1) Danh sách cột dùng để tạo Order
order_cols = [
    "Số đơn hàng", "Ngày đặt hàng", "Mã khách hàng", "Giá trị đơn hàng",
    "Ngày ghi sổ", "Tình trạng ghi doanh số", "Người thực hiện", #"Điện thoại",
    "Số nhà, Đường phố (Giao hàng)", "Phường/Xã (Giao hàng)",
    "Quận/Huyện (Giao hàng)", "Tỉnh/Thành phố (Giao hàng)"
]

# 2) Check thiếu cột (làm trước khi iterrows)
missing_cols = [c for c in order_cols if c not in orders_df.columns]
if missing_cols:
    raise KeyError(f"Thiếu cột trong sheet 'Danh sách': {missing_cols}")

# 3) (Khuyến nghị) Lọc các row bắt buộc phải có
required = ["Số đơn hàng", "Ngày đặt hàng", "Mã khách hàng"]
valid_mask = orders_df[required].notna().all(axis=1)

# Nếu muốn xem các dòng bị thiếu
invalid_rows = orders_df.loc[~valid_mask, required]
print("Số dòng thiếu thông tin bắt buộc ListSaleOrderNPP:", len(invalid_rows))
input()

# Tạo danh sách các đối tượng Order 'Mã nhà phân phối', 'Mã khách hàng'
order_objects = [Order(row['Số đơn hàng'], row['Ngày đặt hàng'], row['Mã khách hàng'], row['Giá trị đơn hàng'], row['Ngày ghi sổ'], row['Tình trạng ghi doanh số'], row['Người thực hiện'], "", row['Số nhà, Đường phố (Giao hàng)'], row['Phường/Xã (Giao hàng)'], row['Quận/Huyện (Giao hàng)'], row['Tỉnh/Thành phố (Giao hàng)']) for index, row in orders_df.iterrows()]
# Tạo danh sách các đối tượng Product
product_objects = [ItemOrder(row['Số đơn hàng'],row['Mã hàng hóa'], "", row['Đơn vị tính'], row['SL theo ĐVTC'], row['Đơn giá sau thuế'], row['Thuế suất'], row['Thành tiền'], row['Tổng tiền'], row['Tỷ lệ chiết khấu']) for index, row in products_df.iterrows()]

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
                        tax= item_product.get("tax",""), # Thuế suất
                        amount=item_product.get("amount", ""), # Thành tiền
                        total=item_product.get("total", ""), # Tổng
                        promotion=item_product.get("promotion","") # Chương trình khuyến mại
                    )
            
