# main_window.py
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from order_table_widget import OrderTableWidget
from database_connection import Database

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pizza Orders")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize database connection and fetch grouped orders
        self.db = Database()
        self.grouped_orders = self.fetch_and_group_orders()
        self.db.close()  # Close the connection after fetching data

        # Initialize UI
        self.initUI()

    def fetch_and_group_orders(self):
        """Fetch orders from the database and group them by OrderID."""
        try:
            orders = self.db.fetch_orders()
            grouped = {}
            for order in orders:
                order_id, created_time, description, status = order
                if order_id not in grouped:
                    grouped[order_id] = {
                        "OrderID": order_id,
                        "CreatedTime": created_time,
                        "Description": [],
                        "Status": status,
                    }
                grouped[order_id]["Description"].append(description)
            return grouped
        except Exception as e:
            print(f"Error fetching orders: {e}")
            return {}

    def initUI(self):
        """Initialize the main UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Create and add the order table widget
        self.order_table = OrderTableWidget(self.grouped_orders)
        layout.addWidget(self.order_table)

        central_widget.setLayout(layout)
