class Product:
    def __init__(self, product_id, warehouse, unit, quantity, unit_price, amount, total):
        self.product_id = product_id  # Mã hàng hóa
        self.warehouse = warehouse  # Tên hàng hóa
        self.unit = unit  # Loại hàng hóa
        self.quantity = quantity  # Đơn vị tính chính
        self.unit_price = unit_price  # Đơn giá bán
        self.amount = amount
        self.total = total

    def __str__(self):
        return (f"Product ID: {self.product_id}, Name: {self.name}, Category: {self.category}, "
                f"Unit: {self.primary_unit}, Price: {self.price} VND")