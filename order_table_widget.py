from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QHeaderView, QScrollArea, QVBoxLayout, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QBrush
from PyQt6.QtWidgets import QScroller, QSizePolicy
from database_connection import Database
import logging
from DatabaseWorker import DatabaseWorker
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderTableWidget(QWidget):
    """Displays orders in a table and handles status updates."""
    def __init__(self, grouped_orders):
        super().__init__()
        self.grouped_orders = grouped_orders  # Pass grouped_orders as an argument
        self.initUI()
        self.start_database_worker()

    def initUI(self):
        """Initialize the table UI."""
        # Create a main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins

        # Create a scroll area for the table
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Allow the widget to resize

        # Create a container widget for the table
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins

        # Create the table widget
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Order No", "Order Time", "Description", "Status", "Action"])

        # Set size policy for the table
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Set table styles
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;  /* White background */
                border: 1px solid #ddd;    /* Light gray border */
                font-size: 14px;
                color: #333;               /* Dark gray text */
                gridline-color: #ddd;      /* Light gray gridlines */
            }
            QTableWidget::item {
                padding: 10px;
            }
            QHeaderView::section {
                background-color: #4CAF50; /* Green header */
                color: white;
                padding: 10px;
                font-weight: bold;
                font-size: 16px;           /* Increase header font size */
                border: 1px solid #45a049; /* Darker green border */
            }
            QPushButton {
                background-color: #4CAF50; /* Green button */
                color: white;
                font-weight: bold; /* Bold text */
                border: none;
                padding: 5px 10px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049; /* Darker green on hover */
            }
            QPushButton:disabled {
                background-color: #cccccc; /* Gray for disabled buttons */
            }
        """)

        # Set font for table items (bold)
        font = QFont()
        font.setPointSize(12)  # Increase font size for better readability
        font.setBold(True)     # Make text bold
        self.table.setFont(font)

        # Enable word wrap for cells
        self.table.setWordWrap(True)

        # Set column widths (increase width as needed)
        self.table.setColumnWidth(0, 100)  # Order ID
        self.table.setColumnWidth(1, 130)  # Date and Time
        self.table.setColumnWidth(2, 600)  # Description (wider column)
        self.table.setColumnWidth(3, 80)  # Status
        self.table.setColumnWidth(4, 140)  # Action

        # Set row height to accommodate the button
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Stretch "Description" column
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Allow manual resizing of "Date and Time"
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)  # Resize rows to content

        # Populate table with grouped orders if available
        if self.grouped_orders:
            self.table.setRowCount(len(self.grouped_orders))
            for row, (order_id, order_data) in enumerate(self.grouped_orders.items()):
                self.populate_row(row, order_id, order_data)
        else:
            logger.warning("No orders found to display.")
            self.table.setRowCount(0)  # Set row count to 0 if no orders are found

        # Enable touch gestures for scrolling
        QScroller.grabGesture(self.table.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)

        # Add the table to the container widget's layout
        table_layout.addWidget(self.table)

        # Set the container widget as the widget for the scroll area
        scroll_area.setWidget(table_container)

        # Add the scroll area to the main layout
        main_layout.addWidget(scroll_area)

    def populate_row(self, row, order_id, order_data):
        """Populate a row in the table with order data."""
        # Set alternating row colors
        if row % 2 == 0:
            row_color = QColor("#ffffff")  # White
        else:
            row_color = QColor("#f2f2f2")  # Light gray

        # Order ID
        order_id_item = QTableWidgetItem(str(order_id))
        order_id_item.setFlags(order_id_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
        order_id_item.setBackground(QBrush(row_color))  # Set row color
        self.table.setItem(row, 0, order_id_item)

        # Date and Time
        created_time_item = QTableWidgetItem(str(order_data["CreatedTime"]))
        created_time_item.setFlags(created_time_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
        created_time_item.setBackground(QBrush(row_color))  # Set row color
        self.table.setItem(row, 1, created_time_item)

        # Description (combine multiple items into a text area)
        description_text = "\n".join(order_data["Description"])
        description_item = QTableWidgetItem(description_text)
        description_item.setBackground(QBrush(row_color))  # Set row color
        description_font = QFont()
        description_font.setPointSize(16)  # Increase font size (e.g., 14)
        description_font.setBold(True)     # Make text bold
        description_item.setFont(description_font)
        self.table.setItem(row, 2, description_item)

        # Status
        status_item = QTableWidgetItem(order_data["Status"])
        status_item.setFlags(status_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
        status_item.setBackground(QBrush(row_color))  # Set row color
        self.table.setItem(row, 3, status_item)

        # Action button to change status (with fixed size, bold text, and green background)
        action_button = QPushButton("✓")
        action_button.setFixedSize(30, 30)
        action_button.setProperty("OrderID", order_id)  # Store OrderID in the button
        action_button.clicked.connect(self.change_status)

        # Create a container widget for the button
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins

        # Add a spacer to push the button to the center
        button_layout.addStretch()  # Add stretchable space above the button
        button_layout.addWidget(action_button, alignment=Qt.AlignmentFlag.AlignCenter)  # Center the button
        button_layout.addStretch()  # Add stretchable space below the button

        # Set the container widget as the cell widget
        self.table.setCellWidget(row, 4, button_container)

    def change_status(self):
        """Change the status of the order using OrderID."""
        button = self.sender()  # Get the button that was clicked
        if not button:
            logger.error("Button not found")
            return

        order_id = button.property("OrderID")
        if not order_id:
            logger.error("OrderID not found")
            return

        # Find the row corresponding to the OrderID
        row = -1
        for i in range(self.table.rowCount()):
            if int(self.table.item(i, 0).text()) == order_id:
                row = i
                break

        if row == -1:
            logger.error(f"Row not found for OrderID: {order_id}")
            return

        # Get the status item
        status_item = self.table.item(row, 3)
        if not status_item:
            logger.error("Status item not found")
            return

        # Determine the new status
        current_status = status_item.text().strip()
        if current_status == "Placed":
            new_status = "Started"
        elif current_status == "Started":
            new_status = "Ready"
        elif current_status == "Ready":
            new_status = "Delivered"
        elif current_status == "Delivered":
            QMessageBox.information(self, "Order Status", "Order is already delivered.")
            return
        else:
            QMessageBox.critical(self, "Error", "Invalid status.")
            return

        # Ask for confirmation
        confirmation = QMessageBox.question(
            self,
            "Confirm Status Change",
            f"Do you want to change the status of Order {order_id} to '{new_status}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        # Update status in the database
        if confirmation == QMessageBox.StandardButton.Yes:
            try:
                with Database() as db:
                    db.update_status(order_id, new_status)
                # Update status in the table
                status_item.setText(new_status)
                self.update_row_color(row, new_status)

                if new_status == "Delivered":
                    button.setEnabled(False)  # Disable the button
                    message = f"Order {order_id} has been delivered."
                else:
                    message = f"Order {order_id} status changed to {new_status}."
                QMessageBox.information(self, "Order Status Updated", message)
            except Exception as e:
                logger.error(f"Error updating status for Order ID {order_id}: {e}")
                QMessageBox.critical(self, "Error", f"Failed to update status: {e}")
        else:
            logger.info(f"Status change for Order ID {order_id} was canceled by the user.")

    def update_row_color(self, row, status):
        """Update the background color of the entire row based on the status."""
        if row < 0 or row >= self.table.rowCount():
            logger.error(f"Invalid row index: {row}")
            return

        logger.info(f"Updating row {row} color for status: {status}")
        if status == "Started":
            row_color = QColor("#d4e4ed")  # Light blue for started
        elif status == "Ready":
            row_color = QColor("#fff3cd")  # Light yellow for ready
        elif status == "Delivered":
            row_color = QColor("#f8d7da")  # Light red for delivered
        else:
            row_color = QColor("#ffffff")  # Default white

        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(QBrush(row_color))
        self.remove_delivered_orders()
        
    def remove_delivered_orders(self):
        """Remove rows with a Delivered status from the table."""
        rows_to_remove = []
        for row in range(self.table.rowCount()):
            status_item = self.table.item(row, 3)  # Status is in column 3
            if status_item and status_item.text().strip() == "Delivered":
                rows_to_remove.append(row)

        # Remove rows in reverse order to avoid index issues
        for row in reversed(rows_to_remove):
            order_id = int(self.table.item(row, 0).text())  # OrderID is in column 0
            self.table.removeRow(row)  # Remove the row from the table
            if order_id in self.grouped_orders:
                del self.grouped_orders[order_id]  # Remove the order from grouped_orders

        logger.info(f"Removed {len(rows_to_remove)} delivered orders from the table.")
            

    def start_database_worker(self):
        """Start the database worker thread."""
        max_order_id = max(self.grouped_orders.keys(), default=0)
        self.database_worker = DatabaseWorker(max_order_id)
        self.database_worker.new_orders_fetched.connect(self.append_orders_to_table)
        self.database_worker.start()

    def append_orders_to_table(self, new_grouped_orders):
        """Append new orders to the table."""
        current_row_count = self.table.rowCount()
        self.table.setRowCount(current_row_count + len(new_grouped_orders))

        for row, (order_id, order_data) in enumerate(new_grouped_orders.items(), start=current_row_count):
            self.populate_row(row, order_id, order_data)

    def closeEvent(self, event):
        """Ensure the worker thread is stopped when the widget is closed."""
        self.database_worker.stop()
        self.database_worker.wait()
        event.accept()