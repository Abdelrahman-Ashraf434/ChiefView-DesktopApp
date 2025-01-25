# order_manager.py
class OrderManager:
    """Manages a list of orders and groups them by OrderID."""
    def __init__(self):
        self.orders = []

    def add_order(self, order):
        """Add an order to the list."""
        self.orders.append(order)

    def group_orders_by_id(self):
        """Group orders by OrderID and combine descriptions."""
        grouped = {}
        for order in self.orders:
            if order.order_id not in grouped:
                grouped[order.order_id] = {
                "OrderID": order.order_id,
                "CreatedTime": order.created_time,
                "Description": [],
                "Status": order.status,
                }
            grouped[order.order_id]["Description"].append(order.description)
        return grouped