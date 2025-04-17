import requests
import json
import pandas as pd
from modules.Product import Product
from modules.Order import Order

# from Product import Product
# from Order import Order


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
pagenum = 1
con = True

# 2️⃣ Khai báo mảng lưu trữ dữ liệu tạm thời
filtered_records = []
filtered_records_product = []
list_orders = []
list_products = []
# 3️⃣ Gọi API Lấy danh sách Customers
while con:
    sale_order_url = "https://crmconnect.misa.vn/api/v2/SaleOrders"
    query_params = {
        "page": pagenum,
        "pageSize": 100,
        "isDescending": True
    }
    sale_order_headers = {
        "Authorization": f"Bearer {token}",
        "Clientid": "tranviettrinh",
        "Content-Type": "application/json"
    }

    sale_order_response = requests.get(sale_order_url, headers=sale_order_headers, params=query_params)
    sale_order_data = sale_order_response.json()

    # 4️⃣ Kiểm tra điều kiện API có thành công không
    if sale_order_data.get("success") is True and sale_order_data.get("code") == 200:
        print(f"✅ Trang {pagenum}: API trả về thành công! Đang lưu dữ liệu vào bộ nhớ...")

        # Chuyển dữ liệu JSON thành danh sách các dòng
        records = sale_order_data.get("data", [])

        # Nếu có dữ liệu, lọc chỉ các trường cần lấy và đổi tên cột
        if records:
            for record in records:
                sale_order_code = record.get("sale_order_no", "")  # Mã khách hàng
                
                filtered_records.append({
                    "is deleted": record.get("is_deleted",""),
                    "Tình trạng ghi doanh số": record.get("revenue_status",""),
                    "Giá trị đã xuất hoá đơn": record.get("invoiced_amount",""),
                    "Bố cục": record.get("form_layout",""),
                    "Tổng tiền": record.get("total_summary",""),
                    "Tiền chiết khấu": record.get("discount_summary",""),
                    "Thành tiền": record.get("to_currency_summary",""),
                    "Nhân viên được ghi DS": record.get("recorded_sale_users_name",""),
                    "Mã Khách Hàng": record.get("account_code",""),
                    "": record.get("",""),

                    "Sử dụng ngoại tệ":record.get("", ""),
                    "Loại tiền": record.get("", ""),
                    "Tỷ giá": record.get("", ""),
                    "Số đơn hàng (*)": sale_order_code,
                    "Ngày đặt hàng": record.get("sale_order_date", ""),
                    "Ngày ghi sổ": record.get("book_date", ""),
                    "Tình trạng": record.get("status", ""),
                    "Giá trị đơn hàng": record.get("sale_order_amount", ""),
                    "Diễn giải": record.get("sale_order_name", "N/A"),
                    "Hạn thanh toán": record.get("due_date", ""),
                    "Hạn giao hàng": record.get("deadline_date", ""),
                    "Đơn vị tính": record.get("", ""),
                    "Loại đơn hàng": record.get("sale_order_type", ""),
                    "Chiến dịch": record.get("", ""),
                    "Khách hàng": record.get("account_name", ""),
                    "Liên hệ": record.get("contact_name", ""),
                    "Cơ hội": record.get("", ""),
                    "Báo giá": record.get("", ""),
                    "Đơn hàng cha": record.get("", ""),
                    "Giá trị thanh lý": record.get("liquidate_amount", ""),
                    "Số ngày được nợ": record.get("", ""),
                    "Dự án bán hàng": record.get("", ""),
                    "Nguồn gốc": record.get("", ""),
                    "Quốc gia (Hóa đơn)": record.get("billing_country", "N/A"),
                    "Quốc gia (Giao hàng)": record.get("shipping_country", "N/A"),
                    "Tỉnh/Thành phố (Hóa đơn)": record.get("billing_province", "N/A"),
                    "Tỉnh/Thành phố (Giao hàng)": record.get("shipping_province", "N/A"),
                    "Quận/Huyện (Hóa đơn)": record.get("billing_district", "N/A"),
                    "Quận/Huyện (Giao hàng)": record.get("shipping_district", "N/A"),
                    "Phường/Xã (Hóa đơn)": record.get("billing_ward", "N/A"),
                    "Phường/Xã (Giao hàng)": record.get("shipping_ward", "N/A"),
                    "Số nhà, Đường phố (Hóa đơn)": record.get("billing_street", "N/A"),
                    "Số nhà, Đường phố (Giao hàng)": record.get("shipping_street", "N/A"),                    
                    "Địa chỉ (Hóa đơn)": record.get("billing_address", "N/A"),
                    "Địa chỉ (Giao hàng)": record.get("shipping_address", "N/A"),
                    "Mã vùng (Hóa đơn)": record.get("billing_code", ""),                    
                    "Mã vùng (Giao hàng)": record.get("shipping_code", ""),
                    "Khách hàng (Hóa đơn)": record.get("billing_account", ""),
                    "Người mua hàng": record.get("", ""),
                    "Điện thoại": record.get("phone", ""),
                    "Người nhận": record.get("", ""),
                    "Nhân viên kho": record.get("", ""),
                    "Nhân viên giao hàng": record.get("", ""),
                    "Ngày giao dự kiên": record.get("", ""),
                    "Tuyến vận chuyển": record.get("", ""),
                    "Mô tả": record.get("description", ""),
                    "Đối tác/CTV giới thiệu": record.get("", ""),
                    "Tình trạng giao hàng": record.get("delivery_status", ""),
                    "Thực thu": record.get("total_receipted_amount", ""),
                    "Tình trạng thanh toán": record.get("pay_status", ""),
                    "Đã xuất hóa đơn": record.get("is_invoiced", ""),
                    "Dự kiến chi": record.get("sale_order_process_cost", ""),
                    "Thực thu NT": record.get("", ""),
                    "Thực chi": record.get("", ""),
                    "Đơn vị được ghi DS": record.get("recorded_sale_organization_unit_name", ""),
                    "Người thực hiện": record.get("owner_name", ""),
                    "Người tạo": record.get("created_by", ""),
                    "Đơn vị": record.get("organization_unit_name", ""),
                    "Hàng KM": record.get("", ""),
                    
                })
                order = Order(record.get("sale_order_no", ""),record.get("sale_order_date", ""),record.get("account_code", ""),float(record.get("to_currency", 0) or 0),record.get("book_date", ""),record.get("revenue_status", ""))
                

                # Xử lý thông tin từ sale_order_product_mappings
                product_mappings = record.get("sale_order_product_mappings", [])
                for product_dict in product_mappings:
                    product_info = {
                    "is deleted": record.get("is_deleted",""),
                    "Thuế suất": product_dict.get("tax_percent",""),
                    "Kho": product_dict.get("stock_name",""),
                    "Đơn vị tính": product_dict.get("unit",""),
                    "Tiền chiết khấu": product_dict.get("discount",""),
                    "Tiền thuế": product_dict.get("tax",""),
                    "Mã Khách Hàng": record.get("account_code",""),
                    "Tình trạng ghi doanh số": record.get("revenue_status",""),
                    "Ngày đặt hàng": record.get("sale_order_date", ""),
                    "Ngày ghi sổ": record.get("book_date", ""),
                    "Loại hàng hóa": record.get("list_product_category", ""),
                    "": product_dict.get("",""),
                    "Mã hàng hoá": product_dict.get("product_code", ""),
                    "Diễn giải": product_dict.get("description", "N/A"),
                    "Số lượng": product_dict.get("amount", ""),
                    "Đơn giá sau thuế": product_dict.get("price_after_tax", ""),
                    "Đơn giá": product_dict.get("price", ""),
                    "Thành tiền": product_dict.get("to_currency", ""),
                    "Tổng tiền": product_dict.get("total", ""),
                    "Đơn hàng (*)": record.get("sale_order_no", ""),
                    "Chương trình KM": product_dict.get("promotion", "N/A"),
                    "Hàng KM": product_dict.get("is_promotion", ""),
                    # "Tiền chiết khấu": product_dict.get("", "N/A"),
                    # "Thuế suất": product_dict.get("", "N/A"),
                    # "Tiền thuế": product_dict.get("", "N/A"),
                    # "Tổng tiền": product_dict.get("", ""),
                    # "Số lô": product_dict.get("", ""),
                    # "Hạn sử dụng": product_dict.get("", "N/A"),
                    # "Hàng KM": product_dict.get("", "N/A"),
                    # "Đơn hàng NPP (*)": product_dict.get("", "N/A")
                    }
                    # Bổ sung thông tin sản phẩm vào bản ghi
                    filtered_records_product.append(product_info)
                    
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
            pagenum += 1
        else:
            con = False
            print("⚠️ Không có dữ liệu trên trang tiếp theo. Dừng lại!")

    else:
        con = False
        print("❌ API trả về lỗi hoặc không đúng điều kiện!")

# 5️⃣ Sau khi vòng lặp kết thúc, ghi toàn bộ dữ liệu vào file Excel
if filtered_records:
    df_records = pd.DataFrame(filtered_records)
    # df_records = df_records[df_records["Tình trạng ghi doanh số"].isin(["Đã ghi"]) & df_records["Mã Khách Hàng"].isin(["1MB5DLSL001"])]
    df_records_product = pd.DataFrame(filtered_records_product)
    # df_records_product = df_records_product[df_records_product["Tình trạng ghi doanh số"].isin(["Đã ghi"]) & df_records_product["Mã Khách Hàng"].isin(["1MB5DLSL001"])]
    excel_filename="Sale_Order_All.xlsx"
    with pd.ExcelWriter(excel_filename) as writer:    
        df_records.to_excel(writer, sheet_name='Nhap khau Don hang', index=False)
        df_records_product.to_excel(writer, sheet_name='Nhap khau Hang hoa', index=False)
    print(f"✅ Dữ liệu đã được ghi vào {excel_filename} thành công!")
else:
    print("⚠️ Không có dữ liệu để ghi vào file Excel.")

