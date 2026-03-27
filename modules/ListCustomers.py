import pandas as pd
from modules.Customer import Customer
import re
from modules.File import file
# Đọc Excel
df_customerAll = pd.read_excel('/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/'+file+'/CRM_Account.xlsx', engine='openpyxl', sheet_name='Danh sách')
df_customerAll = df_customerAll[~df_customerAll['Người tạo'].isin(["Phùng Thị Hà","Nguyễn Thị Mai","Nguyễn Thị Mai Duyên","Trinh Binh"]) & ~df_customerAll['Loại khách hàng'].isin(["1MBKLNB"])]
df_customerAll.to_excel("t.xlsx",index=False, engine="openpyxl")
targets = ["1MB_HĐ001", "1MB_HĐ015", "1MB_HĐ002", "1MB_HĐ003","1MB_HĐ005", "1MB_HĐ008","1MB_KL001",
            "1MB_KGPP_HĐ001", "1MB_KGPP_HĐ015", "1MB_KGPP_HĐ002", "1MB_KGPP_HĐ003","1MB_KGPP_HĐ005", "1MB_KGPP_HĐ008","1MB_KGPP_KL001",
            "2MT_HĐ001", "2MT_HĐ015", "2MT_HĐ002","2MT_HĐ003","2MT_HĐ005","2MT_KL001",
            "2MT_KGPP_HĐ001", "2MT_KGPP_HĐ015", "2MT_KGPP_HĐ002","2MT_KGPP_HĐ003","2MT_KGPP_HĐ005","2MT_KGPP_KL001",
            "3MN_HĐ001", "3MN_HĐ015", "3MN_HĐ002","3MN_HĐ003", "3MN_HĐ005","3MN_KL001",
            "3MN_KGPP_HĐ001", "3MN_KGPP_HĐ015", "3MN_KGPP_HĐ002","3MN_KGPP_HĐ003", "3MN_KGPP_HĐ005","3MN_KGPP_KL001"]  # chỉnh theo nhu cầu "1MBTINHDL",
# Tạo regex OR an toàn
pat = re.compile("|".join(re.escape(t) for t in targets))  # thêm flags=re.IGNORECASE nếu cần

# Tìm và chỉ ghi đúng tên mã (nhiều mã -> nối bằng "; ")
df_customerAll['Loại hợp đồng'] = (df_customerAll['Loại khách hàng'].astype(str)
               .str.findall(pat)
               .apply(lambda xs: "; ".join(dict.fromkeys(xs))))  # unique, giữ thứ tự

df_customerAll['Loại phân vùng'] = (
    df_customerAll['Loại khách hàng']
    .fillna("")
    .str.replace(pat, "", regex=True)
    .str.replace(r"[-_]+", " ", regex=True)
    .str.strip()
    .replace("", "Chưa xác định")
)
# Tạo danh sách các đối tượng Order
# list_customerNPP = [Customer(row['Mã khách hàng'], row['Tên khách hàng'], row['Loại khách hàng'], row['Ngày ký hợp đồng'], row['Điện thoại'], row['Số nhà, Đường phố (Giao hàng)'],row['Phường/Xã (Giao hàng)'], row['Quận/Huyện (Giao hàng)'], row['Tỉnh/Thành phố (Giao hàng)'], row['Mã số thuế'], row['Chủ sở hữu'], row['Mô tả'], row['Ngày ghé thăm gần nhất'], row['Ngày thành lập/Ngày sinh'], row['Là nhà phân phối'], row['Đơn vị']) for index, row in df_customerAll.iterrows()]
list_customerNPP = [Customer(row['Mã khách hàng'], row['Tên khách hàng'], row['Loại khách hàng'], row['Ngày ký hợp đồng'], row['Điện thoại'], row['Số nhà, Đường phố (Giao hàng)'],row['Phường/Xã (Giao hàng)'], row['Quận/Huyện (Giao hàng)'], row['Tỉnh/Thành phố (Giao hàng)'], row['Địa chỉ (Giao hàng)'],row['Mã số thuế'], row['Chủ sở hữu'], row['Mô tả'], row['Ngày ghé thăm gần nhất'], row['Ngày thành lập/Ngày sinh'],row['Là nhà phân phối'], row['Đơn vị']) for index, row in df_customerAll.iterrows()]
# list_customerNPP = [Customer(row['Mã khách hàng'], row['Tên khách hàng'], row['Loại khách hàng'], row['Ngày ký hợp đồng'], row['Điện thoại'], row['Số nhà, Đường phố (Hóa đơn)'],row['Phường/Xã (Hóa đơn)'], row['Quận/Huyện (Hóa đơn)'], row['Tỉnh/Thành phố (Hóa đơn)'], row['Địa chỉ (Hóa đơn)'],row['Mã số thuế'], row['Chủ sở hữu'], row['Mô tả'], row['Ngày ghé thăm gần nhất'], row['Ngày thành lập/Ngày sinh'],row['Là nhà phân phối'], row['Đơn vị']) for index, row in df_customerAll.iterrows()]

# list_customerNPP = [Customer(row['Mã khách hàng'], row['Tên khách hàng'], row['Loại phân vùng'], row['Ngày ký hợp đồng'], row['Điện thoại'], row['Số nhà, Đường phố (Giao hàng)'],row['Phường/Xã (Hóa đơn)'], row['Quận/Huyện (Hóa đơn)'], row['Tỉnh/Thành phố (Hóa đơn)'], row['Địa chỉ (Hóa đơn)'],row['Mã số thuế'], row['Chủ sở hữu'], row['Mô tả'], row['Ngày ghé thăm gần nhất'],row['Ngày thành lập/Ngày sinh'], row['Là nhà phân phối'], row['Đơn vị']) for index, row in df_customerAll.iterrows()]
# list_customerNPP = [Customer(row['Mã khách hàng'], row['Tên khách hàng'], row['Loại hợp đồng'], row['Ngày ký hợp đồng'], row['Điện thoại'], row['Số nhà, Đường phố (Giao hàng)'],row['Phường/Xã (Hóa đơn)'], row['Quận/Huyện (Hóa đơn)'], row['Tỉnh/Thành phố (Hóa đơn)'], row['Địa chỉ (Hóa đơn)'],row['Mã số thuế'], row['Chủ sở hữu'], row['Mô tả'], row['Ngày ghé thăm gần nhất'], row['Ngày thành lập/Ngày sinh'], row['Là nhà phân phối'], row['Đơn vị']) for index, row in df_customerAll.iterrows()]

 
# list_customers = [Customer(row['Mã khách hàng'], row['Tên khách hàng'], row['Loại khách hàng'], row['Ngày ký hợp đồng'], row['Điện thoại'], row['Phường/Xã (Hóa đơn)'], row['Quận/Huyện (Hóa đơn)'], row['Tỉnh/Thành phố (Hóa đơn)'], row['Phường/Xã (Giao hàng)'], row['Quận/Huyện (Giao hàng)'], row['Tỉnh/Thành phố (Giao hàng)'], row['Mã số thuế'], row['Chủ sở hữu'], row['Mô tả'], row['Ngày ghé thăm gần nhất']) for index, row in df_customerAll.iterrows()]
# Công ty Dược Phẩm Thái Nguyên
# df_contact_thainguyen=pd.read_excel('/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/'+file+'/CRM_Contact.xlsx', engine='openpyxl', sheet_name='Danh sách')
# list_customerNPP = [Customer(row['Mã liên hệ'], row['Tên khách hàng'], row['Phân loại khách hàng'], "01/01/2026", row['ĐT di động'], row['Số nhà, Đường phố (Giao hàng)'],row['Phường/Xã (Giao hàng)'], row['Quận/Huyện (Giao hàng)'], row['Tỉnh/Thành phố (Giao hàng)'], row['Địa chỉ (Giao hàng)'],"4600348798", row['Chủ sở hữu'], "", row['Ngày ghé thăm gần nhất'], row['Ngày sinh'],"", row['Đơn vị']) for index, row in df_contact_thainguyen.iterrows()]
