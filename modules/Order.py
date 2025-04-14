class Order:
    def __init__(self, order_number, order_date, customer_id, order_value, payment_due, status):
        self.order_number = order_number  # Số đơn hàng
        self.order_date = order_date  # Ngày đặt hàng
        self.customer_id = customer_id  # Khách hàng
        self.order_value = order_value  # Giá trị đơn hàng
        self.payment_due = payment_due  # Hạn thanh toán
        self.status = status  # Tình trạng đơn hàng
        self.items = []  # Danh sách các mặt hàng trong đơn

    def add_item(self, product_id, warehouse, unit, quantity, unit_price, amount, total):
        self.items.append({
            "product_id": product_id,
            "warehouse": warehouse,
            "unit": unit,
            "quantity": quantity,
            "unit_price": unit_price,
            "amount": amount,
            "total": total
        })

    def __str__(self):
        order_details = f"Order Number: {self.order_number}, Date: {self.order_date}, Customer: {self.customer_id}\n"
        order_details += f"Order Value: {self.order_value} VND, Due: {self.payment_due}, Status: {self.status}\n"
        order_details += "Items:\n"
        for item in self.items:
            order_details += (f"  Product ID: {item['product_id']}, Warehouse: {item['warehouse']}, "
                              f"Unit: {item['unit']}, Quantity: {item['quantity']}, "
                              f"Unit Price: {item['unit_price']} VND, Amount: {item['amount']} VND, "
                              f"Total: {item['total']} VND\n")
        return order_details