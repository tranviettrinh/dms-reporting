
import pandas as pd
from tabulate import tabulate
pd.options.display.float_format = '{:,.2f}'.format  # Định dạng số thực với 2 chữ số thập phân
class SalesReport:
    def __init__(self):
        self.orders = []  # Danh sách các đơn hàng
        self.products = []  # Danh sách sản phẩm

    def add_order(self, order):
        self.orders.append(order)

    def add_products(self, products):
        """Thêm danh sách sản phẩm để phục vụ cho việc thống kê theo danh mục."""
        self.products = products

    def total_sales(self):
        """Tính tổng giá trị của tất cả các đơn hàng."""
        return sum(order.order_value for order in self.orders)

    def sales_by_customer_id(self, customer_id):
        """Tạo báo cáo bán hàng theo mã khách hàng."""
        customer_sales = {}
        for order in self.orders:
            if order.customer_id == customer_id:
                for item in order.items:
                    product_id = item['product_id']
                    total = item.get('total', 0)
                    quantity = item.get('quantity', 0)
                    product_name = next((p.name for p in self.products if p.product_id == product_id), "Unknown Product")
                    
                    if product_id not in customer_sales:
                        customer_sales[product_id] = {
                            'total_non_zero': 0,
                            'quantity_non_zero': 0,
                            # 'total_zero': 0,
                            'quantity_zero': 0,
                            'name': product_name
                        }
                    
                    # Kiểm tra total và cộng dồn quantity và total tương ứng
                    if total > 0:
                        customer_sales[product_id]['total_non_zero'] += total
                        customer_sales[product_id]['quantity_non_zero'] += quantity
                    elif total == 0:
                        # customer_sales[product_id]['total_zero'] += total  # Thêm total dù biết total là 0, giữ cho đồng bộ cấu trúc
                        customer_sales[product_id]['quantity_zero'] += quantity

        return customer_sales
    # def sales_by_customer_id(self, customer_id):
    #     """Tạo báo cáo bán hàng theo mã khách hàng."""
    #     customer_sales = {}
    #     for order in self.orders:
    #         if order.customer_id == customer_id:
    #             for item in order.items:
    #                 product_id = item['product_id']
    #                 total = item.get('total', 0)
    #                 quantity = item.get('quantity', 0)
    #                 product_name = next((p.name for p in self.products if p.product_id == product_id), "Unknown Product")
                    
    #                 if product_id not in customer_sales:
    #                     customer_sales[product_id] = {'total': 0, 'quantity': 0, 'name': product_name}
                    
    #                 customer_sales[product_id]['total'] += total if total is not None else 0
    #                 customer_sales[product_id]['quantity'] += quantity

    #     return customer_sales
    def print_customer_sales_report(self, customer_id):
        sales_report = self.sales_by_customer_id(customer_id)
        df = pd.DataFrame.from_dict(sales_report, orient='index')
        df.columns = ['total_non_zero', 'quantity_non_zero','quantity_zero','name']
        # Định dạng lại cột Total Sales để hiển thị không dùng notations khoa học
        df['total_non_zero'] = df['total_non_zero'].apply(lambda x: f"{x:,.0f}")
        return tabulate(df, headers='keys', tablefmt='psql', showindex="always")

        
    def customer_sales_report(self, customer_id):
        sales_report = self.sales_by_customer_id(customer_id)
        df = pd.DataFrame.from_dict(sales_report, orient='index')
        df.columns = ['total_non_zero', 'quantity_non_zero','quantity_zero','name']
        # Định dạng lại cột Total Sales để hiển thị không dùng notations khoa học
        df['total_non_zero'] = df['total_non_zero'].apply(lambda x: f"{x:,.0f}")
        # return tabulate(df, headers='keys', tablefmt='psql', showindex="always")
        return df
    def __str__(self):
        report = f"Total Sales Value: {self.total_sales()} VND\n"
        report += "Detailed Sales Report:\n"
        return report