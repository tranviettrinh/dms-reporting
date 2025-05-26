# from modules.Product import Product
# from modules.ItemOrder import ItemOrder
# from modules.Order import Order
# from modules.ListProducts import products
# from modules.ListSaleOrder import item_orders
# from modules.ListSaleOrderNPP import orders  # nếu có

from Product import Product
from ItemOrder import ItemOrder
from Order import Order
from ListProducts import list_products as products
from ListSaleOrder import list_orders as orders
# from ListSaleOrderNPP import orders  # nếu có

from collections import defaultdict
import pandas as pd

item_orders = []
for order in orders:
    for item in order.items:
        item_order = ItemOrder(
            order_id=order.order_number,
            product_id=item["product_id"],
            warehouse=item["warehouse"],
            unit=item["unit"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            amount=item["amount"],
            total=item["total"]
        )
        item_orders.append(item_order)
def generate_report(products: list, item_orders: list) -> pd.DataFrame:
    from collections import defaultdict
    import pandas as pd

    # Kiểm tra dữ liệu
    if not all(hasattr(i, "unit_price") for i in item_orders):
        raise ValueError("Danh sách item_orders không hợp lệ, mỗi phần tử phải có thuộc tính 'unit_price'.")

    # Tạo từ điển tra cứu tên sản phẩm
    product_info = {p.product_id: p.name for p in products}

    # Gom dữ liệu theo sản phẩm & đơn
    data = defaultdict(lambda: defaultdict(int))  # {product_id: {("bán"/"km", order_id): qty}}

    for item in item_orders:
        try:
            unit_price = float(item.unit_price or 0)
            quantity = int(item.quantity or 0)
        except (ValueError, TypeError):
            continue  # bỏ qua nếu dữ liệu không hợp lệ

        key = "bán" if item.unit_price not in [None, '', 0, '0'] and float(item.unit_price) > 0 else "km"
        data[item.product_id][(key, item.order_id)] += quantity

    # Tạo danh sách đơn hàng
    # all_order_ids = sorted({item.order_id for item in item_orders})
    all_order_ids = sorted({item.order_id for item in item_orders if item.order_id is not None})
    # Chuẩn bị dòng dữ liệu
    rows = []
    for product_id, order_map in data.items():
        row = {
            "Tên sản phẩm": product_info.get(product_id, "Không rõ"),
            "Mã sản phẩm": product_id
        }
        for order_id in all_order_ids:
            row[f"Số lượng bán ({order_id})"] = order_map.get(("bán", order_id), 0)
            row[f"Số lượng khuyến mại ({order_id})"] = order_map.get(("km", order_id), 0)
        rows.append(row)

    return pd.DataFrame(rows)

df = generate_report(products, item_orders)
df.to_excel("test.xlsx",index=False, engine="openpyxl")