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
        self.return_purchase_orders = []     # Danh sách các đơn hàng trả lại hàng nhập (Order objects)
        self.return_sales_orders = []     # Danh sách các đơn hàng trả lại hàng bán (Order objects)
        self.products = []          # Danh sách sản phẩm (có thể là dict hoặc custom class nếu muốn sau này)
 
    def add_purchase_order(self, order: 'Order'):
        """Thêm một đơn hàng nhập vào báo cáo."""
        self.purchase_orders.append(order)
    def add_sales_order(self, order: 'Order'):
        """Thêm một đơn hàng bán vào báo cáo."""
        self.sales_orders.append(order)
    def add_return_purchase_orders(self, order: 'Order'):
        """Thêm một đơn hàng bán vào báo cáo."""
        self.return_purchase_orders.append(order)
    def add_return_sales_orders(self, order: 'Order'):
        """Thêm một đơn hàng bán vào báo cáo."""
        self.return_sales_orders.append(order)

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
    def getProductInventoryByCustomer(self, customer_id, product_id, start_day, end_day, status):
        start_date = parser.parse(start_day)
        end_date = parser.parse(end_day)
        soluong_nhap_dauky=0
        soluong_nhapKM_dauky=0
        soluong_ban_dauky =0
        soluong_banKM_dauky =0
        purchase_quantity = 0
        promo_purchase_quantity = 0
        sold_quantity = 0
        promo_sold_quantity = 0
        soluong_trahangmua_dauky_sl =0
        soluong_trahangmua_dauky_km =0
        soluong_trahangmua_sl =0
        soluong_trahangmua_km =0
        soluong_trahangban_dauky_sl =0
        soluong_trahangban_dauky_km =0
        soluong_trahangban_sl =0
        soluong_trahangban_km =0

        for order in self.purchase_orders:
            if order.customer_id != customer_id:
                continue
            # order_date = parser.parse(order.payment_due)
            if order.payment_due < start_date and order.status in status :
                for item in order.items:
                    if item['product_id'] == product_id:
                        total = item.get('total', 0)
                        quantity = item.get('quantity', 0)

                        if total is not None and total != 0:
                            soluong_nhap_dauky += quantity
                        elif total == 0:
                            soluong_nhapKM_dauky += quantity
            if start_date<=order.payment_due <= end_date and order.status in status:
                for item in order.items:
                    if item['product_id'] == product_id:
                        total = item.get('total', 0)
                        quantity = item.get('quantity', 0)

                        if total is not None and total != 0:
                            purchase_quantity += quantity
                        elif total == 0:
                            promo_purchase_quantity += quantity

        for order in self.sales_orders:
            if order.customer_id != customer_id:
                continue
            if order.payment_due < start_date and order.status in status:
                for item in order.items:
                    if item['product_id'] == product_id:
                        total = item.get('total', 0)
                        quantity = item.get('quantity', 0)

                        if total is not None and total != 0:
                            soluong_ban_dauky += quantity

                        elif total == 0:
                            soluong_banKM_dauky += quantity

            if start_date<=order.payment_due <= end_date and order.status in status:
                for item in order.items:
                    if item['product_id'] == product_id:
                        total = item.get('total', 0)
                        quantity = item.get('quantity', 0)

                        if total is not None and total != 0:
                            sold_quantity += quantity
                        elif total == 0:
                            promo_sold_quantity += quantity
                    # if product_id =="FEURAA0011":
                    #     print(order.order_number, product_id, sold_quantity, promo_sold_quantity)
                    #     input()
        for order in self.return_purchase_orders:
            if order.customer_id != customer_id:
                continue
            if order.payment_due < start_date and order.status == "Đã lập chứng từ":
                for item in order.items:
                    if item['product_id'] == product_id:
                        total = item.get('total', 0)
                        quantity = item.get('quantity', 0)

                        if total is not None and total != 0:
                            soluong_trahangmua_dauky_sl += quantity
                        elif total == 0:
                            soluong_trahangmua_dauky_km += quantity
            if start_date<=order.payment_due <= end_date and order.status == "Đã lập chứng từ":
                for item in order.items:
                    if item['product_id'] == product_id:
                        total = item.get('total', 0)
                        quantity = item.get('quantity', 0)

                        if total is not None and total != 0:
                            soluong_trahangmua_sl += quantity
                        elif total == 0:
                            soluong_trahangmua_km += quantity
        for order in self.return_sales_orders:
            if order.customer_id != customer_id:
                continue
            if order.payment_due < start_date and order.status == "Đã duyệt":
                for item in order.items:
                    if item['product_id'] == product_id:
                        total = item.get('total', 0)
                        quantity = item.get('quantity', 0)

                        if total is not None and total != 0:
                            soluong_trahangban_dauky_sl += quantity
                        elif total == 0:
                            soluong_trahangban_dauky_km += quantity
            if start_date<=order.payment_due <= end_date and order.status == "Đã duyệt":
                for item in order.items:
                    if item['product_id'] == product_id:
                        total = item.get('total', 0)
                        quantity = item.get('quantity', 0)

                        if total is not None and total != 0:
                            soluong_trahangban_sl += quantity
                        elif total == 0:
                            soluong_trahangban_km += quantity    
        tonkho_dauky_sl = soluong_nhap_dauky-soluong_ban_dauky - soluong_trahangmua_dauky_sl
        tonkho_dauky_km = soluong_nhapKM_dauky - soluong_banKM_dauky - soluong_trahangmua_dauky_km
        purchase_quantity = purchase_quantity - soluong_trahangmua_sl
        promo_purchase_quantity = promo_purchase_quantity - soluong_trahangmua_km
        sold_quantity = sold_quantity - soluong_trahangban_sl
        promo_sold_quantity = promo_sold_quantity - soluong_trahangban_km
        tonkho_cuoiky_sl = tonkho_dauky_sl+purchase_quantity-sold_quantity
        tonkho_cuoiky_km = tonkho_dauky_km+promo_purchase_quantity-promo_sold_quantity
        return [tonkho_dauky_sl,tonkho_dauky_km,purchase_quantity,promo_purchase_quantity,sold_quantity,promo_sold_quantity,tonkho_cuoiky_sl,tonkho_cuoiky_km,soluong_trahangmua_dauky_sl,soluong_trahangmua_dauky_km]
        # return tonkho_cuoiky_sl,tonkho_cuoiky_km

        # return [soluong_nhap_dauky,soluong_nhapKM_dauky,soluong_ban_dauky,soluong_banKM_dauky,purchase_quantity,promo_purchase_quantity,sold_quantity,promo_sold_quantity,soluong_trahangmua_dauky_sl,soluong_trahangmua_dauky_km,soluong_trahangmua_sl,soluong_trahangmua_km,soluong_trahangban_dauky_sl,soluong_trahangban_dauky_km,soluong_trahangban_sl,soluong_trahangban_km]
        


