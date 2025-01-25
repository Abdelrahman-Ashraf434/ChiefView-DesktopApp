import pyodbc
from decouple import config
from typing import List, Tuple
import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        """Initialize the database connection."""
        # Load database credentials from environment variables
        self.DB_SERVER = config("DB_SERVER")
        self.DB_NAME = config("DB_NAME")
        self.DB_USER = config("DB_USER")
        self.DB_PASSWORD = config("DB_PASSWORD")
        self.conn = self.create_connection()

    def create_connection(self) -> pyodbc.Connection:
        """Create a new database connection."""
        try:
            conn = pyodbc.connect(
                Driver="{ODBC Driver 17 for SQL Server}",
                Server=self.DB_SERVER,
                Database=self.DB_NAME,
                uid=self.DB_USER,
                pwd=self.DB_PASSWORD,
                timeout=30,  # Add a connection timeout
            )
            logger.info("Database connection established successfully.")
            return conn
        except pyodbc.Error as e:
            logger.error(f"Error connecting to the database: {e}")
            raise

    def fetch_all_orders(self) -> List[Tuple]:
        """Fetch all orders from the database."""
        return self.fetch_orders()

    def fetch_orders(self) -> List[Tuple]:
        """Fetch all orders from the database."""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT  
                        a.OrderID,
                        FORMAT(a.[CreatedTime], 'yyyy-MM-dd HH:mm') AS CreatedTime,
                        c.ItemDesrciptionAR + ' (' + replace(str(b.Qty),' ','') + ')' Description,
                        a.[Status]
                    FROM [HotSectionDB].[dbo].[kitchenOrders] a
                    JOIN kitchenOrdersLines b ON a.OrderID = b.OrderID
                    JOIN KitchenItems c ON b.ItemCode = c.ItemCode
                    WHERE a.OrderType = 'Desktop'
                        AND a.Status IN ('Placed', 'Started', 'Ready')
                    ORDER BY OrderID
                """)
                result = cursor.fetchall()
                return result if result else []  # Return an empty list if no rows are found
        except pyodbc.Error as e:
            logger.error(f"Error fetching orders: {e}")
            return []

    def fetch_new_orders(self, max_order_id: int) -> List[Tuple]:
        """Fetch orders with OrderID greater than the specified value."""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT  
                        a.OrderID,
                        FORMAT(a.[CreatedTime], 'yyyy-MM-dd HH:mm') AS CreatedTime,
                        c.ItemDesrciptionAR + ' (' + replace(str(b.Qty),' ','') + ')' Description,
                        a.[Status]
                    FROM [HotSectionDB].[dbo].[kitchenOrders] a
                    JOIN kitchenOrdersLines b ON a.OrderID = b.OrderID
                    JOIN KitchenItems c ON b.ItemCode = c.ItemCode
                    WHERE a.OrderType = 'Desktop'
                        AND a.Status IN ('Placed', 'Started', 'Ready')
                        AND a.OrderID > ?
                    ORDER BY OrderID
                """, (max_order_id,))
                result = cursor.fetchall()
                return result if result else []  # Return an empty list if no rows are found
        except pyodbc.Error as e:
            logger.error(f"Error fetching new orders: {e}")
            return []

    def update_status(self, order_id: int, new_status: str) -> bool:
        """Update the status and timestamp fields of an order in the database."""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Correct datetime format
        try:
            with self.conn.cursor() as cursor:
                # Determine which timestamp field to update based on the new status
                if new_status == "Started":
                    query = "UPDATE kitchenOrders SET status = ?, StartedTime = ? WHERE OrderID = ?"
                elif new_status == "Ready":
                    query = "UPDATE kitchenOrders SET status = ?, ReadyTime = ? WHERE OrderID = ?"
                elif new_status == "Delivered":
                    query = "UPDATE kitchenOrders SET status = ?, DeliverdTime = ? WHERE OrderID = ?"
                else:
                    logger.error(f"Invalid status: {new_status}")
                    return False

                # Execute the query
                logger.info(f"Executing query: {query} with values: ({new_status}, {timestamp}, {order_id})")
                cursor.execute(query, (new_status, timestamp, order_id))
                self.conn.commit()
                logger.info(f"Status and timestamp updated for Order ID {order_id} to {new_status}.")
                return True
        except pyodbc.Error as e:
            logger.error(f"Error updating status for Order ID {order_id}: {e}")
            self.conn.rollback()  # Rollback in case of error
            return False

    def close(self):
        """Close the database connection."""
        try:
            if self.conn and not self.conn.closed:
                self.conn.close()
                logger.info("Database connection closed.")
        except pyodbc.Error as e:
            logger.error(f"Error closing the database connection: {e}")

    def __enter__(self):
        """Support for context manager (with statement)."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure the connection is closed when exiting the context."""
        self.close()