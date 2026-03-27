import pandas as pd
from tabulate import tabulate
from datetime import datetime, timezone
from modules.Order import Order
from modules.ListProducts import list_products, list_products_DDTD
from dateutil import parser
from collections import defaultdict
from modules.ListCustomers import list_customerNPP
import math
from modules.File import file
pd.options.display.float_format = '{:,.2f}'.format

class SalesReport:
    def __init__(self):
        self.purchase_orders = []   # Danh sách các đơn hàng nhập (Order objects)
        self.sales_orders = []      # Danh sách các đơn hàng bán (Order objects)
        self.return_purchase_orders = []     # Danh sách các đơn hàng trả lại hàng nhập (Order objects)
        self.return_sales_orders = []     # Danh sách các đơn hàng trả lại hàng bán (Order objects)
        self.products = []          # Danh sách sản phẩm (có thể là dict hoặc custom class nếu muốn sau này)
        self.customers =[]          # Danh sách khách hàng
 
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

    def add_customers(self, customers):
        """Thêm danh sách khách hàng"""
        self.customers = customers

    def print_sales_summary(self):
        print("📦 SALES ORDERS SUMMARY")
        for order in self.sales_orders:
            print(order)

    def print_purchase_summary(self):
        print("📥 PURCHASE ORDERS SUMMARY")
        for order in self.purchase_orders:
            print(order)
    def getProductInventoryByCustomer(self, customer_id, product_id, start_day, end_day, status_list):
        start_date = parser.parse(start_day)
        end_date = parser.parse(end_day)

        def process_orders(orders, valid_statuses, is_before, factor):
            sl, km = 0, 0
            for order in orders:
                if order.customer_id != customer_id:
                    continue
                if (order.payment_due < start_date if is_before else start_date <= order.payment_due <= end_date) and order.status in valid_statuses:
                    for item in order.items:
                        if item['product_id'] != product_id:
                            continue
                        total = item.get('total', 0)
                        quantity = item.get('quantity', 0)
                        if total == 0:
                            km += factor * quantity
                        else:
                            sl += factor * quantity
            return sl, km

        # Đầu kỳ
        nhap_dk_sl, nhap_dk_km = process_orders(self.purchase_orders, status_list, is_before=True, factor=1)
        ban_dk_sl, ban_dk_km = process_orders(self.sales_orders, status_list, is_before=True, factor=-1)
        trahangmua_dk_sl, trahangmua_dk_km = process_orders(self.return_purchase_orders, ["Đã lập chứng từ"], is_before=True, factor=-1)
        trahangban_dk_sl, trahangban_dk_km = process_orders(self.return_sales_orders, ["Đã duyệt"], is_before=True, factor=1)

        # Trong kỳ
        nhap_ck_sl, nhap_ck_km = process_orders(self.purchase_orders, status_list, is_before=False, factor=1)
        ban_ck_sl, ban_ck_km = process_orders(self.sales_orders, status_list, is_before=False, factor=-1)
        trahangmua_ck_sl, trahangmua_ck_km = process_orders(self.return_purchase_orders, ["Đã lập chứng từ"], is_before=False, factor=-1)
        trahangban_ck_sl, trahangban_ck_km = process_orders(self.return_sales_orders, ["Đã duyệt"], is_before=False, factor=1)

        # Tính tổng đầu kỳ
        tonkho_dauky_sl = nhap_dk_sl + ban_dk_sl + trahangmua_dk_sl + trahangban_dk_sl
        tonkho_dauky_km = nhap_dk_km + ban_dk_km + trahangmua_dk_km + trahangban_dk_km

        # Tính phát sinh trong kỳ
        net_nhap_ck_sl = nhap_ck_sl + trahangban_ck_sl + ban_ck_sl + trahangmua_ck_sl
        net_nhap_ck_km = nhap_ck_km + trahangban_ck_km + ban_ck_km + trahangmua_ck_km

        # Tính tồn cuối kỳ
        tonkho_cuoiky_sl = tonkho_dauky_sl + net_nhap_ck_sl
        tonkho_cuoiky_km = tonkho_dauky_km + net_nhap_ck_km

        return [
            tonkho_dauky_sl, tonkho_dauky_km,
            nhap_ck_sl - trahangmua_ck_sl, nhap_ck_km - trahangmua_ck_km,  # mua trong kỳ trừ trả hàng mua
            -ban_ck_sl + trahangban_ck_sl, -ban_ck_km + trahangban_ck_km,  # bán trừ trả hàng bán
            tonkho_cuoiky_sl, tonkho_cuoiky_km,
            trahangmua_dk_sl, trahangmua_dk_km
        ]
    def calculate_monthly_sales(self, customer_id, start_day, end_day, month, statuses, product_price_map):
        start_date = parser.parse(start_day)
        end_date = parser.parse(end_day)

        doanhso_orders = 0
        doanhso_items = 0
        check_orders = []

        all_orders = [
            (self.purchase_orders, 1),
            (self.return_purchase_orders, -1),
            (self.sales_orders, 1),
            (self.return_sales_orders, -1)
        ]

        for orders, factor in all_orders:
            for order in orders:
                if order.customer_id != customer_id:
                    continue
                if not (start_date <= order.payment_due <= end_date and order.status in statuses and order.payment_due.month == month):
                    continue

                order_value = order.get('order_value', 0)

                order_value_actual = sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in order.items)
                # # ✅ Giá trị từ item * đơn giá sản phẩm
                # order_value_actual = 0
                # for item in order.items:
                #     product_id = item.get('product_id')
                #     if item.get('total') >0:
                #         quantity = item.get('quantity', 0)
                #         unit_price = product_price_map.get(product_id, 0)
                #         if product_id in list_products_DDTD:
                #             order_value_actual += (quantity * unit_price)/1.05
                #         # Log nếu thiếu giá
                #             if product_id not in product_price_map:
                #                 print(f"⚠️ Thiếu đơn giá cho sản phẩm: {product_id}, {order.get('order_number')}")
                #         else:
                #             order_value_actual += (quantity * unit_price)
                #         # Log nếu thiếu giá
                #             if product_id not in product_price_map:
                #                 print(f"⚠️ Thiếu đơn giá cho sản phẩm: {product_id}, {order.get('order_number')}")
                doanhso_orders += factor * order_value
                doanhso_items += factor * order_value_actual

                if order_value != order_value_actual:
                    check_orders.append(order.get('order_number', 'NA'))

        result = doanhso_items == doanhso_orders

        # print(f"Doanh số từ chi tiết đơn hàng: {month} là {doanhso_items:,.2f}")
        return [customer_id, month, doanhso_orders, doanhso_items, result, check_orders]

    def calculate_monthly_sales_detail(self, customer_id, start_day, end_day, month, statuses, product_price_map):
        start_date = parser.parse(start_day)
        end_date = parser.parse(end_day)

        doanhso_dongtanduoc = 0
        doanhso_tpcn = 0
        check_orders = []

        all_orders = [
            (self.purchase_orders, 1),
            (self.return_purchase_orders, -1),
            (self.sales_orders, 1),
            (self.return_sales_orders, -1)
        ]

        for orders, factor in all_orders:
            for order in orders:
                if order.customer_id != customer_id:
                    continue
                if not (start_date <= order.payment_due <= end_date and order.status in statuses and order.payment_due.month == month):
                    continue

                order_value = order.get('order_value', 0)

                # order_value_actual = sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in order.items)
                # ✅ Giá trị từ item * đơn giá sản phẩm
                order_value_actual_dongtanduoc = 0
                order_value_actual_tpcn =0
                for item in order.items:
                    product_id = item.get('product_id')
                    if item.get('total') >0:
                        quantity = item.get('quantity', 0)
                        unit_price = product_price_map.get(product_id, 0)
                        if product_id in list_products_DDTD:
                            order_value_actual_dongtanduoc += (quantity * unit_price)/1
                        # Log nếu thiếu giá
                            if product_id not in product_price_map:
                                print(f"⚠️ Thiếu đơn giá cho sản phẩm: {product_id}, {order.get('order_number')}")
                        else:
                            order_value_actual_tpcn += (quantity * unit_price)
                        # Log nếu thiếu giá
                            if product_id not in product_price_map:
                                print(f"⚠️ Thiếu đơn giá cho sản phẩm: {product_id}, {order.get('order_number')}")
                doanhso_dongtanduoc += factor * order_value_actual_dongtanduoc
                doanhso_tpcn += factor * order_value_actual_tpcn

        # print(f"Doanh số từ chi tiết đơn hàng: {month} là {doanhso_items:,.2f}")
        return [customer_id, month, doanhso_dongtanduoc, doanhso_tpcn]
    # def check_promotion(self, customer_id, start_day, end_day, month, statuses):
    #     checked=[]
    #     start_date = parser.parse(start_day)
    #     end_date = parser.parse(end_day)
    #     none_promotions = []

    #     for order in self.sales_orders: # + self.purchase_orders
    #         if order.customer_id != customer_id:
    #             continue
    #         if order.order_number in checked:
    #             continue
    #         if not (
    #             start_date <= order.payment_due <= end_date and
    #             order.status in statuses and
    #             order.payment_due.month == month
    #         ):
    #             continue

    #         # ✅ Chỉ thêm nếu có item không có promotion và quantity khác 1 hoặc 2
    #         if any(
    #             (item.get('promotion') == "nan" and int(item.get('quantity')) not in [1, 2,3,4] and item.get('product_id') not in list_products)
    #             for item in order.items
    #         ):
    #             none_promotions.append(order.get('order_number'))
    #     return [customer_id, none_promotions]
    def check_order(self,product_id, soluongban, soluongkm, loaikhachhang):
        class CheckOrder:
            def __init__(self, product_id, soluongmua, soluongtang):
                self.product_id = product_id  # Mã khách hàng
                self.soluongmua = soluongmua                # Tên khách hàng
                self.soluongtang = soluongtang          # Loại khách hàng
                # self.loaikhachhang = loaikhachhang              # Ngày ký hợp đồng
            def get(self, attr, default=None):
                """Tương tự ItemOrder.get: lấy giá trị thuộc tính, trả về default nếu không tồn tại."""
                return getattr(self, attr, default)
            def __str__(self):
                return (
                    f"Mã sản phẩm: {self.product_id}, Số lượng bán: {self.soluongmua}, Số lượng KM: {self.soluongtang}"
                )
        # Đọc Excel
        df_checkorder_GPP = pd.read_excel('/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/'+file+'/CheckOrder.xlsx', sheet_name='GPP',engine='openpyxl')
        df_checkorder_NOGPP = pd.read_excel('/Users/trinh/Desktop/Abipha/abipha_dms/api_misa/project/modules/'+file+'/CheckOrder.xlsx', sheet_name='NOGPP', engine='openpyxl')

        # Tạo danh sách các đối tượng Order
        list_checkorder_GPP = [CheckOrder(row['Mã hàng hóa'], row['Số lượng KM'], row['Số lượng tặng']) for index, row in df_checkorder_GPP.iterrows()]
        list_checkorder_NOGPP = [CheckOrder(row['Mã hàng hóa'], row['Số lượng KM'], row['Số lượng tặng']) for index, row in df_checkorder_NOGPP.iterrows()]
        
        soluongkm_dukien=0
        if loaikhachhang in ["1MB_HĐ015","1MB_HĐ002","1MB_HĐ003","1MB_HĐ005","1MB_KL001",
                            "2MT_HĐ015","2MT_HĐ002","2MT_HĐ003","2MT_HĐ005","2MT_KL001",
                            "3MN_HĐ015","3MN_HĐ002","3MN_HĐ003","3MN_HĐ005","3MN_KL001"]:

            for checker in list_checkorder_GPP:
                if product_id == checker.get('product_id'):
                    soluongkm_dukien = int(soluongban/int(checker.get('soluongmua')))
                    # print(soluongkm_dukien)
                    if soluongkm_dukien==soluongkm:
                        return True
                    else: return False
        elif loaikhachhang in ["1MB_KGPP_HĐ015","1MB_KGPP_HĐ002","1MB_KGPP_HĐ003","1MB_KGPP_HĐ005","1MB_KGPP_KL001",
                            "2MT_KGPP_HĐ015","2MT_KGPP_HĐ002","2MT_KGPP_HĐ003","2MT_KGPP_HĐ005","2MT_KGPP_KL001",
                            "3MN_KGPP_HĐ015","3MN_KGPP_HĐ002","3MN_KGPP_HĐ003","3MN_KGPP_HĐ005","3MN_KGPP_KL001"]:
            for checker in list_checkorder_NOGPP:
                if product_id == checker.get('product_id'):
                    if checker.get('soluongmua') ==0:
                        if soluongkm == 0:
                            return True
                        else: return False
                    elif checker.get('soluongmua') !=0:
                        soluongkm_dukien = int(soluongban/int(checker.get('soluongmua')))
                        # print(soluongkm_dukien)
                        if soluongkm_dukien==soluongkm:
                            return True
                        else: return False
        else: return False

    def check_discount_ginic(self, customer_id, start_day, end_day, month, statuses, product_price_map):
        start_date = parser.parse(start_day)
        end_date = parser.parse(end_day)

        
        check_orders = []

        all_orders = [
            (self.sales_orders, 1)
        ]
        customer_category =""
        discount=[]
        for cus in list_customerNPP:
            if cus.get('account_number') == customer_id:
                customer_category = cus.get('account_type')
            else: continue
        for orders, factor in all_orders:
            for order in orders:
                if order.customer_id != customer_id:
                    continue
                if not (start_date <= order.payment_due <= end_date and order.status in statuses and order.payment_due.month == month):
                    continue

                # order_value_actual = sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in order.items)
                # ✅ Giá trị từ item * đơn giá sản phẩm
                order_discount=0
                order_value_actual = 0
                k=0
                for item in order.items:
                    product_id = item.get('product_id')
                    if item.get('total') >0:
                        k=k+1
                        order_discount += int(item.get('promotion',0))
                        quantity = item.get('quantity', 0)
                        unit_price = product_price_map.get(product_id, 0)
                        order_value_actual += quantity * unit_price

                        # Log nếu thiếu giá
                        if product_id not in product_price_map:
                            print(f"⚠️ Thiếu đơn giá cho sản phẩm: {product_id}, {order.get('order_number')}")
                if customer_category in ["1MB_HĐ015","1MB_HĐ002","1MB_HĐ003","1MB_HĐ005",
                                    "2MT_HĐ015","2MT_HĐ002","2MT_HĐ003","2MT_HĐ005",
                                    "3MN_HĐ015","3MN_HĐ002","3MN_HĐ003","3MN_HĐ005",
                                    "1MB_KGPP_HĐ015","1MB_KGPP_HĐ002","1MB_KGPP_HĐ003","1MB_KGPP_HĐ005",
                                    "2MT_KGPP_HĐ015","2MT_KGPP_HĐ002","2MT_KGPP_HĐ003","2MT_KGPP_HĐ005",
                                    "3MN_KGPP_HĐ015","3MN_KGPP_HĐ002","3MN_KGPP_HĐ003","3MN_KGPP_HĐ005"]:
                    if order_value_actual >= 1500000:
                        if  float(order_discount/k) != 7:
                            discount.append(order.get('order_number'))
                        else: continue
                    elif 650000 <=order_value_actual <1500000:
                        if float(order_discount/k) !=5:
                            discount.append(order.get('order_number'))
                        else: continue
                    else: continue

                else: continue
                print(discount)

        # print(f"Doanh số từ chi tiết đơn hàng: {month} là {doanhso_items:,.2f}")
        return [customer_id, discount]
    def check_discount_abipha(self, customer_id, start_day, end_day, month, statuses, product_price_map):
        start_date = parser.parse(start_day)
        end_date = parser.parse(end_day)

        
        check_orders = []

        all_orders = [
            (self.sales_orders, 1)
        ]
        customer_category =""
        discount=[]
        for cus in list_customerNPP:
            if cus.get('account_number') == customer_id:
                customer_category = cus.get('account_type')
            else: continue
        for orders, factor in all_orders:
            for order in orders:
                if order.customer_id != customer_id:
                    continue
                if not (start_date <= order.payment_due <= end_date and order.status in statuses and order.payment_due.month == month):
                    continue

                # order_value_actual = sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in order.items)
                # ✅ Giá trị từ item * đơn giá sản phẩm
                order_discount_dongtanduoc=0
                order_discount_tpcn=0
                order_value_actual_dongtanduoc = 0
                order_value_actual_tpcn = 0
                dongtanduoc=0
                tpcn=0
                for item in order.items:
                    product_id = item.get('product_id')
                    if product_id in ["FVXACN0011","FHHACN0011","FTKACN0011","FHAACN0011","FBTACN0023","FATACN0021","FHTDCN0011",
                                        "FVKACN0011","FVVGCN0011","FATACN0012","FTDACN0011","FTTACN0012","FHNTCN0011","FHCQCN0013",
                                        "FNKGCN0011","FDTHCN0011","FHSMCN0011","FVGACN0011","FREPCN0041","FREPCN0011","FEUPCN0011",
                                        "FNYMCN0011","FBRACN0011","FREPCN0031","FABICN0011","FFEXCN0011","FEUPCN0021"]:
                        if item.get('total') >0:
                            dongtanduoc=dongtanduoc+1
                            order_discount_dongtanduoc += int(item.get('promotion',0))
                            # print(order_discount_dongtanduoc)
                            quantity = item.get('quantity', 0)
                            unit_price = product_price_map.get(product_id, 0)
                            order_value_actual_dongtanduoc += quantity * unit_price

                            # Log nếu thiếu giá
                            if product_id not in product_price_map:
                                print(f"⚠️ Thiếu đơn giá cho sản phẩm: {product_id}, {order.get('order_number')}")
                    else:
                        if item.get('total') >0:
                            tpcn=tpcn+1
                            order_discount_tpcn += int(item.get('promotion',0))
                            quantity = item.get('quantity', 0)
                            unit_price = product_price_map.get(product_id, 0)
                            order_value_actual_tpcn += quantity * unit_price

                            # Log nếu thiếu giá
                            if product_id not in product_price_map:
                                print(f"⚠️ Thiếu đơn giá cho sản phẩm: {product_id}, {order.get('order_number')}")
                if customer_category in ["1MB_HĐ015","1MB_HĐ002","1MB_HĐ003","1MB_HĐ005",
                                    "2MT_HĐ015","2MT_HĐ002","2MT_HĐ003","2MT_HĐ005",
                                    "3MN_HĐ015","3MN_HĐ002","3MN_HĐ003","3MN_HĐ005",
                                    "1MB_KGPP_HĐ015","1MB_KGPP_HĐ002","1MB_KGPP_HĐ003","1MB_KGPP_HĐ005",
                                    "2MT_KGPP_HĐ015","2MT_KGPP_HĐ002","2MT_KGPP_HĐ003","2MT_KGPP_HĐ005",
                                    "3MN_KGPP_HĐ015","3MN_KGPP_HĐ002","3MN_KGPP_HĐ003","3MN_KGPP_HĐ005"]:
                    if order_value_actual_dongtanduoc >= 500000:
                        if  float(order_discount_dongtanduoc/dongtanduoc) != 5:
                            discount.append(order.get('order_number'))
                        else: continue
                    if order_value_actual_tpcn >= 500000:
                        if  float(order_discount_tpcn/tpcn) != 5:
                            discount.append(order.get('order_number'))
                        else: continue
                    else: continue

                else: continue
                print(discount)

        # print(f"Doanh số từ chi tiết đơn hàng: {month} là {doanhso_items:,.2f}")
        return [customer_id, discount]

    def check_promotion(self, customer_id, start_day, end_day, month, statuses):
        checked=[]
        start_date = parser.parse(start_day)
        end_date = parser.parse(end_day)
        none_promotions = []
        customer_category =""
        for cus in list_customerNPP:
            if cus.get('account_number') == customer_id:
                customer_category = cus.get('account_type')
            else: continue
        for order in self.sales_orders: # + self.purchase_orders
            if order.customer_id != customer_id:
                continue
            if order.order_number in checked:
                continue
            if not (
                start_date <= order.payment_due <= end_date and
                order.status in statuses and
                order.payment_due.month == month
            ):
                continue
            check_lists_ban=[]
            for item in order.items:
                if item.get('unit_price') != 0:
                    check_ban=[item.get('product_id'),item.get('quantity'),0,customer_category,customer_id,order.get('order_number')]
                    check_lists_ban.append(check_ban)
                else: continue
            for item in order.items:
                if item.get('unit_price') == 0:
                    for check in check_lists_ban:
                        if item.get('product_id') == check[0]:
                            check[2]= item.get('quantity')
                        else: continue

                else: continue
            # for item in order.items:
            #     if item.get('quantity') ==0:
                    
            # ✅ Chỉ thêm nếu có item không có promotion và quantity khác 1 hoặc 2
            for check in check_lists_ban:
                if self.check_order(check[0],check[1],check[2],check[3]) == False:
                    print(check)
                    # input()
                    none_promotions.append(order.get('order_number'))

        return [customer_id, none_promotions]
#build_customer_product_table

    def build_customer_product_table(self, customer_id, start_day, product_id, end_day, month, statuses):
        start_date = parser.parse(start_day)
        end_date = parser.parse(end_day)

        total_quantity = 0 # tong san luong
        total_revenue = 0 # tong doanh thu ban hang

        all_orders = [
            (self.purchase_orders, 1),
            (self.return_purchase_orders, -1),
            (self.sales_orders, 1),
            (self.return_sales_orders, -1)
        ]

        for orders, factor in all_orders:
            for order in orders:
                if order.customer_id != customer_id:
                    continue
                if not (start_date <= order.payment_due <= end_date and order.status in statuses and order.payment_due.month == month):
                    continue
                owner_name = order.owner_name
                for item in order.items:
                    if item['product_id'] != product_id:
                        continue
                    if item['unit_price'] == 0:
                        continue
                    quantity = item.get('quantity', 0)
                    revenue = item.get('total',0)
                    total_quantity += factor * quantity  
                    total_revenue +=factor * revenue 

        return [total_quantity, total_revenue]

    def build_customer_product_table_maxtric(self, customer_id, start_day, product_id, end_day, statuses):
        start_date = parser.parse(start_day)
        end_date = parser.parse(end_day)

        total_quantity = 0

        all_orders = [
            (self.purchase_orders, 1),
            (self.return_purchase_orders, -1),
            (self.sales_orders, 1),
            (self.return_sales_orders, -1)
        ]

        for orders, factor in all_orders:
            for order in orders:
                if order.customer_id != customer_id:
                    continue
                if not (start_date <= order.payment_due <= end_date and order.status in statuses):
                    continue
                owner_name = order.owner_name
                for item in order.items:
                    if item['product_id'] != product_id:
                        continue
                    if item['unit_price'] == 0:
                        continue
                    quantity = item.get('quantity', 0)
                    total_quantity += factor * quantity              
        return total_quantity
# Ham tinh KPI
    def build_customer_product_table_detail(self,start_day, end_day, statuses):
        start_date = parser.parse(start_day)
        end_date = parser.parse(end_day)

        total_quantity = 0

        all_orders = [
            (self.purchase_orders, 1),
            (self.return_purchase_orders, -1),
            (self.sales_orders, 1),
            (self.return_sales_orders, -1)
        ]
        orders_all = []
        for orders, factor in all_orders:
            for order in orders:
                if not (start_date <= order.payment_due <= end_date and order.status in statuses):
                    continue
                for item in order.items:
                    if item['unit_price'] == 0:
                        continue
                    quantity = item.get('quantity', 0)
                    quantity = factor * quantity
                    total = item.get('total',0)
                    total = factor * total
                    for cus in list_customerNPP:
                        if cus.get('account_number') == order.customer_id:
                            for pro in list_products:
                                if pro.get('product_id') == item['product_id']:
                                    if item['product_id'] in ["FVVGCN0011.1","FVXACN0011.1","FTKACN0011.1","FVKACN0011.1"]:
                                        kpi_2 = 1
                                    else: kpi_2 = 0
                                    if pro.get('category') in ['N1_TÂN DƯỢC','N1_THUỐC DD DÁN TEM', 'N1_THUỐC DD']:
                                        kpi_1 = 1
                                    else: kpi_1 = 0
                                    item_detail=[order.order_number, order.owner_name,order.customer_id,cus.get('owner_name'),cus.get('unit'),cus.get('is_distributor'),item['product_id'],pro.get('name'),pro.get('category'),order.payment_due.month,quantity, total, kpi_1, kpi_2]
                                    # print(item_detail)
                                    orders_all.append(item_detail)                                 
        return orders_all













