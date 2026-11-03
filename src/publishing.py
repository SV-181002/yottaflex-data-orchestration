
from pathlib import Path
import sqlite3
import json
import pandas as pd
from datetime import datetime, timezone


# Find the main project directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Define input, database and report locations.
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
WAREHOUSE_DIR = PROJECT_ROOT / "data" / "warehouse"
REPORT_DIR = PROJECT_ROOT / "reports"

# SQLite database file.
DATABASE_PATH = WAREHOUSE_DIR / "pipeline.db"


def create_tables(connection):
    """
    Create database tables if they do not already exist.

    Primary keys prevent duplicate business records.
    Foreign keys maintain relationships between customers and orders.
    """

    cursor = connection.cursor()

    # Create the customers table.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            email TEXT NOT NULL,
            city TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Create the orders table.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            source_record_id TEXT NOT NULL UNIQUE,
            customer_id TEXT NOT NULL,
            order_timestamp TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_price REAL NOT NULL CHECK(unit_price >= 0),
            total_amount REAL NOT NULL CHECK(total_amount >= 0),
            status TEXT NOT NULL CHECK(
                status IN ('PLACED', 'SHIPPED', 'DELIVERED', 'CANCELLED')
            ),
            source_file TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
        )
    """)

    connection.commit()


def publish_customers(connection, customers):
    """
    Insert new customers or update existing customers.

    ON CONFLICT makes repeated pipeline runs safe for the same
    customer IDs.
    """

    records = customers[
        [
            "customer_id",
            "customer_name",
            "email",
            "city",
            "created_at"
        ]
    ].where(pd.notna(customers), None)

    rows = list(records.itertuples(index=False, name=None))

    connection.executemany("""
        INSERT INTO customers (
            customer_id,
            customer_name,
            email,
            city,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT(customer_id) DO UPDATE SET
            customer_name = excluded.customer_name,
            email = excluded.email,
            city = excluded.city,
            created_at = excluded.created_at
    """, rows)

    return len(rows)


def publish_orders(connection, orders):
    """
    Insert new orders or update existing orders.

    ON CONFLICT(order_id) prevents duplicate orders during reruns.
    """

    records = orders[
        [
            "order_id",
            "source_record_id",
            "customer_id",
            "order_timestamp",
            "quantity",
            "unit_price",
            "total_amount",
            "status",
            "source_file"
        ]
    ].where(pd.notna(orders), None)

    rows = list(records.itertuples(index=False, name=None))

    connection.executemany("""
        INSERT INTO orders (
            order_id,
            source_record_id,
            customer_id,
            order_timestamp,
            quantity,
            unit_price,
            total_amount,
            status,
            source_file
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(order_id) DO UPDATE SET
            source_record_id = excluded.source_record_id,
            customer_id = excluded.customer_id,
            order_timestamp = excluded.order_timestamp,
            quantity = excluded.quantity,
            unit_price = excluded.unit_price,
            total_amount = excluded.total_amount,
            status = excluded.status,
            source_file = excluded.source_file
    """, rows)

    return len(rows)


def run_publishing():

    # Read transformed CSV files.
    customers = pd.read_csv(
        PROCESSED_DIR / "transformed_customers.csv"
    )

    orders = pd.read_csv(
        PROCESSED_DIR / "transformed_orders.csv"
    )

    # Create database directory if required.
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)

    # Open SQLite connection.
    connection = sqlite3.connect(DATABASE_PATH)

    # Enable foreign-key enforcement for this connection.
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        # Create database tables.
        create_tables(connection)

        # Start one transaction for both publishing operations.
        connection.execute("BEGIN")

        # Publish customers first because orders reference customers.
        customer_count = publish_customers(connection, customers)

        # Publish orders after customers.
        order_count = publish_orders(connection, orders)

        # Reconcile database counts.
        database_customer_count = connection.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]

        database_order_count = connection.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]

        # Confirm all incoming records are represented.
        assert database_customer_count >= len(customers)
        assert database_order_count >= len(orders)

        # Calculate the total amount stored in the database.
        database_total_amount = connection.execute(
            "SELECT ROUND(SUM(total_amount), 2) FROM orders"
        ).fetchone()[0]

        # Commit both publishing operations together.
        connection.commit()

        summary = {
            "status": "SUCCESS",
            "database": str(
                DATABASE_PATH.relative_to(PROJECT_ROOT)
            ),
            "customers_processed": customer_count,
            "orders_processed": order_count,
            "customers_in_database": database_customer_count,
            "orders_in_database": database_order_count,
            "database_total_amount": database_total_amount,
            "published_at": datetime.now(
                timezone.utc
            ).isoformat()
        }

    except Exception:
        # Roll back database changes if publishing fails.
        connection.rollback()
        raise

    finally:
        # Always close the connection.
        connection.close()

    # Save the publishing report.
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report_path = REPORT_DIR / "publishing_summary.json"

    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    print("STAGE 4 PUBLISHING COMPLETED")
    print("----------------------------------")
    print("Customers processed:", summary["customers_processed"])
    print("Orders processed:", summary["orders_processed"])
    print("Customers in database:", summary["customers_in_database"])
    print("Orders in database:", summary["orders_in_database"])
    print("Database total amount:", summary["database_total_amount"])
    print("Status:", summary["status"])
    print("----------------------------------")

    return summary
