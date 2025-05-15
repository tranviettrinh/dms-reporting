from datetime import datetime
from dateutil import parser

class Order:
    def __init__(self, order_number, order_date, customer_id, order_value, payment_due, status):
        self.order_number = order_number
        self.order_date = self.normalize_datetime(order_date)   # chuẩn hoá ngày
        self.customer_id = customer_id
        self.order_value = order_value
        self.payment_due = self.normalize_datetime(payment_due) # chuẩn hoá ngày
        self.status = status
        self.items = []

    def normalize_datetime(self, date_input):
        # Dùng parser để xử lý nhiều định dạng đầu vào
        try:
            dt = parser.parse(date_input)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return date_input  # fallback nếu không parse được

    def get(self, attr, default=None):
        return getattr(self, attr, default)

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