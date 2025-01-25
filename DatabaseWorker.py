from PyQt6.QtCore import QThread, pyqtSignal
from database_connection import Database
import logging
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseWorker(QThread):
    """Worker class for database operations."""
    new_orders_fetched = pyqtSignal(dict)  # Signal to emit when new orders are fetched

    def __init__(self, max_order_id):
        super().__init__()
        self.max_order_id = max_order_id
        self.running = True
    def run(self):
        """Fetch new orders from the database in a loop."""
        while self.running:
            try:
                with Database() as db:
                    new_orders = db.fetch_new_orders(self.max_order_id)
                    if new_orders:
                        grouped_orders = self.group_orders(new_orders)
                        self.new_orders_fetched.emit(grouped_orders)  # Emit the new orders
                        self.max_order_id = max(grouped_orders.keys(), default=self.max_order_id)
            except Exception as e:
                logger.error(f"Error in database worker: {e}")
            self.sleep(5)  # Wait for 5 seconds before fetching again

    def stop(self):
        """Stop the worker thread."""
        self.running = False

    @staticmethod
    def group_orders(orders):
        """Group orders by OrderID."""
        grouped_orders = {}
        for order in orders:
            order_id = order[0]
            if order_id not in grouped_orders:
                grouped_orders[order_id] = {
                    "CreatedTime": order[1],
                    "Description": [],
                    "Status": order[3],
                }
            grouped_orders[order_id]["Description"].append(order[2])
        return grouped_orders