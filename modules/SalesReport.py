import pandas as pd
from tabulate import tabulate
from datetime import datetime, timezone
from modules.Order import Order
from dateutil import parser

pd.options.display.float_format = '{:,.2f}'.format

class SalesReport:
    def __init__(self):
        self.purchase_orders = []   # Danh sách các đơn hàng nhập (Order objects)
        self.sales_orders = []      # Danh sách các đơn hàng bán (Order objects)
        self.products = []          # Danh sách sản phẩm (có thể là dict hoặc custom class nếu muốn sau này)
 
    def add_purchase_order(self, order: 'Order'):
        """Thêm một đơn hàng nhập vào báo cáo."""
        self.purchase_orders.append(order)
    def add_sales_order(self, order: 'Order'):
        """Thêm một đơn hàng bán vào báo cáo."""
        self.sales_orders.append(order)

    def add_products(self, products):
        """Thêm danh sách sản phẩm (có thể là list dict hoặc list object)."""
        self.products = products

    def print_sales_summary(self):
        print("📦 SALES ORDERS SUMMARY")
        for order in self.sales_orders:
            print(order)

    def print_purchase_summary(self):
        print("📥 PURCHASE ORDERS SUMMARY")
        for order in self.purchase_orders:
            print(order)
    def getProductInventoryByCustomer(self, customer_id, product_id, start_day, status):
        start_date = parser.parse(start_day)
        purchase_quantity = 0
        promo_purchase_quantity = 0
        sold_quantity = 0
        promo_sold_quantity = 0

        for order in self.purchase_orders:
            if order.customer_id != customer_id:
                continue
            order_date = parser.parse(order.payment_due)
            if order_date <= start_date and order.status == status:
                for item in order.items:
                    if item['product_id'] == product_id:
                        print(order.payment_due)
                        input()
                        total = item.get('total', 0)
                        quantity = item.get('quantity', 0)

                        if total is not None and total != 0:
                            purchase_quantity += quantity
                        elif total == 0:
                            promo_purchase_quantity += quantity


        for order in self.sales_orders:
            if order.customer_id != customer_id:
                continue
            if order.payment_due <= start_date and order.status == status:
                for item in order.items:
                    if item['product_id'] == product_id:
                        print(order.payment_due)
                        input()
                        total = item.get('total', 0)
                        quantity = item.get('quantity', 0)

                        if total is not None and total != 0:
                            sold_quantity += quantity
                        elif total == 0:
                            promo_sold_quantity += quantity


        
        return purchase_quantity, promo_purchase_quantity, sold_quantity, promo_sold_quantity





