import pandas as pd
from tabulate import tabulate
from datetime import datetime, timezone

pd.options.display.float_format = '{:,.2f}'.format

class SalesReport:
    def __init__(self):
        self.sales_orders = []  # Danh sách các đơn hàng bán hàng
        self.purchase_orders = []  # Danh sách các đơn hàng nhập hàng
        self.products = []  # Danh sách sản phẩm

    def add_sales_order(self, order):
        self.sales_orders.append(order)

    def add_purchase_order(self, order):
        self.purchase_orders.append(order)

    def add_products(self, products):
        self.products = products

    def check_customer_id(self, customer_id):
        # Kiểm tra xem có đơn hàng nào từ khách hàng này không
        if not any(order.customer_id == customer_id for order in self.sales_orders):
            return 0 
        else: return 1
    def customer_sales_report(self, customer_id, start_date, end_date, order_status=None):
        sales_report = {}

        for product in self.products:
            sales_report[product.product_id] = {
                'product_name': product.name,
                'initial_stock': 0,
                'received_promotion': 0,
                'received_purchase': 0,
                'sold_promotion': 0,
                'sold_regular': 0,
                'final_stock': 0,
                'order_status': []
            }

        date_range = pd.date_range(start=start_date, end=end_date, freq='M', tz='Asia/Ho_Chi_Minh')

        for date in date_range:
            month_start = date.replace(day=1)
            month_end = date

            for order in self.purchase_orders + self.sales_orders:
                order_date_str = getattr(order, 'date', None) or getattr(order, 'order_date', None) or getattr(order, 'created_date', None)
                if not order_date_str:
                    print(f"Order không có thuộc tính ngày: {order}")
                    continue

                # Chuyển đổi chuỗi ngày thành datetime với timezone
                if isinstance(order_date_str, str):
                    try:
                        order_date = datetime.strptime(order_date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
                    except ValueError:
                        print(f"Định dạng ngày không hợp lệ: {order_date_str}")
                        continue
                else:
                    order_date = order_date_str

                # Đảm bảo month_start và month_end có timezone
                month_start = month_start.tz_convert('Asia/Ho_Chi_Minh')
                month_end = month_end.tz_convert('Asia/Ho_Chi_Minh')

                if order.customer_id == customer_id and month_start <= order_date <= month_end:
                    for item in order.items:
                        product_id = item['product_id']
                        quantity = item.get('quantity', 0)
                        total = item.get('total', 0)
                        if order in self.purchase_orders:
                            if total == 0:
                                sales_report[product_id]['received_promotion'] += quantity
                            else:
                                sales_report[product_id]['received_purchase'] += quantity
                        else:
                            if total == 0:
                                sales_report[product_id]['sold_promotion'] += quantity
                            else:
                                sales_report[product_id]['sold_regular'] += quantity

            for product_id, data in sales_report.items():
                if date == date_range[0]:
                    data['initial_stock'] = 0
                else:
                    data['initial_stock'] = data.get('final_stock', 0)

                data['final_stock'] = data['initial_stock'] + data['received_promotion'] + data['received_purchase'] - (data['sold_promotion'] + data['sold_regular'])

        df = pd.DataFrame.from_dict(sales_report, orient='index')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'product_code'}, inplace=True)

        df['customer_id'] = customer_id
        df['start_date'] = start_date
        df['end_date'] = end_date

        return df
