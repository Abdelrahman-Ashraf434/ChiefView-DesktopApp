# order.py
class Order:
    """Represents a single order."""
    def __init__(self, order_id, created_time, description, status):
        self.order_id = order_id
        self.created_time = created_time
        self.description = description
        self.status = status