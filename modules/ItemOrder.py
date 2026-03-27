class ItemOrder:
    def __init__(self, order_id, product_id, warehouse, unit, quantity, unit_price, tax, amount, total, promotion):
        self.order_id = order_id # Mã đơn hàng
        self.product_id = product_id  # Mã hàng hóa
        self.warehouse = warehouse  # Kho hàng hoá NPP
        self.unit = unit  # Đơn vị tính
        self.quantity = quantity  # Số lượng
        self.unit_price = unit_price  # Đơn giá bán
        self.tax = tax # Thuế suất
        self.amount = amount # Thành tiền
        self.total = total # Tổng tiền
        self.promotion = promotion # Chương trình khuyến mại
    def get(self, attr, default=None):
        return getattr(self, attr, default)
    def __str__(self):
        return (f"Order ID: {self.order_id}, Product ID: {self.product_id}, Warehouse: {self.warehouse}, "
                f"Unit: {self.unit}, Quantity: {self.quantity}, Unit Price: {self.unit_price}, "
                f"Amount: {self.amount}, Total: {self.total} VND, Promotion:{self.promotion}")