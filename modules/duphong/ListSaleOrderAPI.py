import requests
import json
import pandas as pd
# from modules.Product import Product
# from modules.Order import Order

from Product import Product
from Order import Order
input_filename = "order_codes.xlsx"
df_input = pd.read_excel(input_filename, engine="openpyxl")

if "Số đơn hàng" not in df_input.columns:
    print("❌ Lỗi: File Excel phải có các cột 'Số đơn hàng'")
    exit()

order_codes = df_input["Số đơn hàng"].dropna().astype(str).tolist()


# 1️⃣ API Xác thực để lấy Token
auth_url = "https://crmconnect.misa.vn/api/v2/Account"
auth_payload = {
    "client_id": "tranviettrinh",
    "client_secret": "KSC34LQX0mmCIx1IwnFW5XKWQaX61jzVkiBMbooTH4c="
}
headers = {"Content-Type": "application/json"}

auth_response = requests.post(auth_url, json=auth_payload, headers=headers)
auth_data = auth_response.json()

if not auth_data.get("success") or "data" not in auth_data:
    print("❌ Lỗi xác thực! Kiểm tra client_id và client_secret.")
    exit()

token = auth_data["data"]  # Bearer Token

# Gọi API Lấy dữ liệu khách hàng theo số đơn hàng
sale_order_url = "https://crmconnect.misa.vn/api/v2/SaleOrders/code"
sale_order_headers = {
    "Authorization": f"Bearer {token}",
    "Clientid": "tranviettrinh",
    "Content-Type": "application/json"
}
# 2️⃣ Khai báo mảng lưu trữ dữ liệu tạm thời
filtered_records = []
filtered_records_product = []
list_orders = []
list_products = []
index = 0
# 3️⃣ Gọi API Lấy danh sách Customers
while index < len(order_codes):
    code = order_codes[index]
    query_params = {"code": code}
    sale_order_response = requests.get(sale_order_url, headers=sale_order_headers, params=query_params)
    sale_order_data = sale_order_response.json()

    # 4️⃣ Kiểm tra điều kiện API có thành công không
    if sale_order_data.get("success") is True and sale_order_data.get("code") == 200:
        print(f"✅ API trả về thành công cho mã {code}! Đang xử lý dữ liệu...")
        # Chuyển dữ liệu JSON thành danh sách các dòng
        records = sale_order_data.get("data", [])
        for record in records:
            if record.get("is_deleted","") == False:
            # if record.get("sale_order_no", "") =="DH1MB02598":
                sale_order_code = record.get("sale_order_no", "")  # Mã khách hàng
                
                order = Order(record.get("sale_order_no", ""),record.get("sale_order_date", ""),record.get("account_code", ""),float(record.get("sale_order_amount", 0) or 0),record.get("book_date", ""),record.get("revenue_status", ""))
                

                # Xử lý thông tin từ sale_order_product_mappings
                product_mappings = record.get("sale_order_product_mappings", [])
                for product_dict in product_mappings:
                    order.add_item(
                        # customer_id = record.get("account_code","")
                        product_id=product_dict.get("product_code", ""),
                        warehouse=product_dict.get("stock_name", ""),
                        unit=product_dict.get("unit", ""), # Đơn vị tính
                        quantity=product_dict.get("amount", ""), # số lượng
                        unit_price=product_dict.get("price", ""), # Đơn giá
                        amount=product_dict.get("to_currency", ""), # Thành tiền
                        total=product_dict.get("total", "") # Tổng
                    )

                # list_orders.append(order)
                list_orders.append(order)

    else:
        print(f"❌ API trả về lỗi hoặc không đúng điều kiện cho mã {code}!")
    index += 1

# # 5️⃣ Sau khi vòng lặp kết thúc, ghi toàn bộ dữ liệu vào file Excel
# if filtered_records:
#     df_records = pd.DataFrame(filtered_records)
#     # df_records = df_records[df_records["Tình trạng ghi doanh số"].isin(["Đã ghi"]) & df_records["Mã Khách Hàng"].isin(["1MB5DLSL001"])]
#     df_records_product = pd.DataFrame(filtered_records_product)
#     # df_records_product = df_records_product[df_records_product["Tình trạng ghi doanh số"].isin(["Đã ghi"]) & df_records_product["Mã Khách Hàng"].isin(["1MB5DLSL001"])]
#     excel_filename="Sale_Order_All.xlsx"
#     with pd.ExcelWriter(excel_filename) as writer:    
#         df_records.to_excel(writer, sheet_name='Nhap khau Don hang', index=False)
#         df_records_product.to_excel(writer, sheet_name='Nhap khau Hang hoa', index=False)
#     print(f"✅ Dữ liệu đã được ghi vào {excel_filename} thành công!")
# else:
#     print("⚠️ Không có dữ liệu để ghi vào file Excel.")
