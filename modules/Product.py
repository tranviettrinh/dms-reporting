class Product:
    def __init__(self, product_id, name, category, primary_unit, price, tax):
        self.product_id = product_id  # Mã hàng hóa
        self.name = name  # Tên hàng hóa
        self.category = category  # Loại hàng hóa
        self.primary_unit = primary_unit  # Đơn vị tính chính
        self.price = price  # Đơn giá bán
        self.tax = tax # Thuế

    def get(self, attr, default=None):
        return getattr(self, attr, default)
    def __str__(self):
        return (f"Product ID: {self.product_id}, Name: {self.name}, Category: {self.category}, "
                f"Unit: {self.primary_unit}, Price: {self.price} VND, Tax: {self.tax}")
    def __repr__(self):
        return f"Product({self.product_id}, price={self.price})"