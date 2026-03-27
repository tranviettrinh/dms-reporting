class Customer:
    def __init__(self, account_number, account_name, account_type, sign_date, phone, billing_street, billing_ward, billing_district, billing_province, billing_address, tax_code, owner_name, description,visting_lastday, date_of_birthday, is_distributor,unit):
        self.account_number = account_number  # Mã khách hàng
        self.account_name = account_name                # Tên khách hàng
        self.account_type = account_type          # Loại khách hàng
        self.sign_date = sign_date              # Ngày ký hợp đồng
        self.phone = phone              # Điện thoại
        self.billing_street= billing_street         # Số nhà (Hoá đơn)
        self.billing_ward = billing_ward            # Phường/xã (Hoá đơn)
        self.billing_district = billing_district      # Quận/huyện (Hoá đơn)
        self.billing_province = billing_province      # Tỉnh/Thành phố (Hoá đơn)
        self.billing_address = billing_address   # Địa chỉ ( Hoá đơn)
        self.tax_code = tax_code      # Mã số thuế
        self.owner_name = owner_name     # Chủ sở hữu
        self.description = description      # Mô tả
        self.visting_lastday = visting_lastday      # Ngày ghé thăm gần đây nhất
        self.date_of_birthday = date_of_birthday    # Ngày sinh nhật
        self.is_distributor = is_distributor      # 
        self.unit = unit      # Đơn vị tổ chức
        # self.join_date = join_date      # 
        
    def get(self, attr, default=None):
        """Tương tự ItemOrder.get: lấy giá trị thuộc tính, trả về default nếu không tồn tại."""
        return getattr(self, attr, default)

    def __str__(self):
        return (
            f"Account_number: {self.account_number}, Account_name: {self.account_name}, Account_type: {self.account_type}, Sign_date: {self.sign_date} "
            f"Phone: {self.phone},Billing_street: {self.billing_street}, Billing_ward: {self.billing_ward}, Billing_district: {self.billing_district}, Billing_province: {self.billing_province}"
            f"Tax_code: {self.tax_code}, Owner_name: {self.owner_name}, Description: {self.description}, Visting_lastday: {self.visting_lastday} "
            f"Is_distributor: {self.is_distributor}, Unit: {self.unit}"
        )
    def extract_value_in_brackets(s):
        # Kiểm tra s là chuỗi hay không trước khi áp dụng biểu thức chính quy
        if pd.isna(s):
            return None  # Trả về None nếu s là NaN
        if not isinstance(s, str):
            s = str(s)  # Chuyển đổi s thành chuỗi nếu nó không phải là chuỗi
        match = re.search(r'\((.*?)\)', s)
        return match.group(1) if match else None