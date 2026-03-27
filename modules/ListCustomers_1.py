import requests
import json
import pandas as pd

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
list_customerNPP = []

# 3️⃣ Gọi API Lấy danh sách Customers
while con:
    customers_url = "https://crmconnect.misa.vn/api/v2/Customers"
    query_params = {
        "page": pagenum,
        "pageSize": 101,
        "isDescending": True
    }
    customers_headers = {
        "Authorization": f"Bearer {token}",
        "Clientid": "tranviettrinh",
        "Content-Type": "application/json"
    }

    customers_response = requests.get(customers_url, headers=customers_headers, params=query_params)
    customers_data = customers_response.json()

    # 4️⃣ Kiểm tra điều kiện API có thành công không
    if customers_data.get("success") is True and customers_data.get("code") == 200:
        print(f"✅ Trang {pagenum}: API trả về thành công! Đang lưu dữ liệu vào bộ nhớ...")

        # Chuyển dữ liệu JSON thành danh sách các dòng
        records = customers_data.get("data", [])

        # Nếu có dữ liệu, lọc chỉ các trường cần lấy và đổi tên cột
        if records:
            for record in records:
                # if record.get("is_distributor", "N/A") == False:
                    list_customerNPP.append({
                        "Mã khách hàng": record.get("account_number", "N/A"),
                        "Tên khách hàng": record.get("account_name", "N/A"),
                        # "Tên viết tắt": record.get("", ""),
                        
                        
                        # "Email": record.get("", ""),
                        # "Nguồn gốc": record.get("", ""),
                        "Loại khách hàng": record.get("account_type", "N/A"),
                        "Ngày ký hợp đồng": record.get("custom_field14", "N/A"),
                        "Điện thoại": record.get("office_tel", "N/A"),
                        # "Lĩnh vực": record.get("", ""),
                        # "Loại hình": record.get("", ""),
                        # "Ngành nghề": record.get("", ""),
                        # "Quốc gia (Hóa đơn)": record.get("billing_country", "N/A"),
                        # "Quốc gia (Giao hàng)": record.get("shipping_country", "N/A"),
                        # "Tỉnh/Thành phố (Hóa đơn)": record.get("billing_province", "N/A"),
                        # "Quận/Huyện (Hóa đơn)": record.get("billing_district", "N/A"),
                        # "Phường/Xã (Hóa đơn)": record.get("billing_ward", "N/A"),
                        # "Số nhà, Đường phố (Hóa đơn)": record.get("billing_street", "N/A"),

                        "Số nhà, Đường phố (Giao hàng)": record.get("shipping_street", "N/A"),
                        "Phường/Xã (Giao hàng)": record.get("shipping_ward", "N/A"),
                        "Quận/Huyện (Giao hàng)": record.get("shipping_district", "N/A"),
                        "Tỉnh/Thành phố (Giao hàng)": record.get("shipping_province", "N/A"),
                        "Mã số thuế": record.get("", ""),
                        
                        # "Địa chỉ (Hóa đơn)": record.get("billing_address", "N/A"),
                        # "Địa chỉ (Giao hàng)": record.get("shipping_address", "N/A"),
                        # "Mã vùng (Hóa đơn)": record.get("", ""),                    
                        # "Mã vùng (Giao hàng)": record.get("", ""),                    
                        # "Tài khoản ngân hàng": record.get("", ""),
                        # "Mở tại ngân hàng": record.get("", ""),
                        # "Ngày thành lập/Ngày sinh": record.get("", ""),
                        # "Là khách hàng từ": record.get("", ""),
                        # "Doanh thu": record.get("", ""),
                        # "Quy mô nhân sự": record.get("", ""),
                        # "Số ngày được nợ": record.get("", ""),
                        # "Website": record.get("", ""),
                        # "Hạn mức nợ": record.get("", ""),
                        # "Mô tả": record.get("", ""),
                        # "Dùng chung": record.get("", ""),
                        # "Ngừng theo dõi": record.get("", ""),
                        # "Là KH cá nhân": record.get("", ""),
                        # "Đối tác/CTV giới thiệu": record.get("", ""),
                        # "Là đối tác/cộng tác viên": record.get("", ""),
                        # "Giới tính": record.get("", ""),
                        # "Số CMND/CCCD": record.get("", ""),
                        # "Ngày cấp": record.get("", ""),
                        # "Nơi cấp": record.get("", ""),
                        # "Mã ngân sách": record.get("", ""),
                        # "Fax": record.get("", ""),
                        # "Đơn vị chủ quản": record.get("", ""),
                        # "Xếp hạng khách hàng": record.get("", ""),
                        # "Là nhà phân phối": record.get("is_distributor", "N/A"),
                        "Chủ sở hữu": record.get("owner_name", "N/A")

                })

            pagenum += 1
        else:
            con = False
            print("⚠️ Không có dữ liệu trên trang tiếp theo. Dừng lại!")

    else:
        con = False
        print("❌ API trả về lỗi hoặc không đúng điều kiện!")
# for i in range(0,len(list_customerNPP)):
#     print(list_customerNPP[i]['Mã khách hàng (*)'])
#     input()