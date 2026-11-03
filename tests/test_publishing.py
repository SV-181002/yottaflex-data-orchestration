
import sqlite3
import pandas as pd

from src.publishing import (
    create_tables,
    publish_customers,
    publish_orders,
)


def create_test_database():
    # Create a temporary database stored only in memory.
    connection = sqlite3.connect(":memory:")

    # Enable foreign-key checking in SQLite.
    connection.execute("PRAGMA foreign_keys = ON")

    # Create the customers and orders tables.
    create_tables(connection)

    return connection


def create_sample_customers():
    # Prepare one valid customer record.
    return pd.DataFrame({
        "customer_id": ["C1001"],
        "customer_name": ["Rahul"],
        "email": ["rahul@example.com"],
        "city": ["Hyderabad"],
        "created_at": ["2026-01-01T10:00:00+00:00"]
    })


def create_sample_orders():
    # Prepare one valid order linked to the sample customer.
    return pd.DataFrame({
        "source_record_id": ["SRC001"],
        "order_id": ["ORD001"],
        "customer_id": ["C1001"],
        "order_timestamp": ["2026-01-02T10:00:00+00:00"],
        "quantity": [2],
        "unit_price": [100.0],
        "status": ["PLACED"],
        "source_file": ["orders.csv"],
        "total_amount": [200.0]
    })


def test_customers_and_orders_are_published():
    connection = create_test_database()

    try:
        customers = create_sample_customers()
        orders = create_sample_orders()

        # Publish customers first because orders reference customers.
        publish_customers(connection, customers)
        publish_orders(connection, orders)

        # Read the published record counts.
        customer_count = connection.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]

        order_count = connection.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]

        assert customer_count == 1
        assert order_count == 1

    finally:
        connection.close()


def test_republishing_same_data_does_not_create_duplicates():
    connection = create_test_database()

    try:
        customers = create_sample_customers()
        orders = create_sample_orders()

        # First publishing run.
        publish_customers(connection, customers)
        publish_orders(connection, orders)

        # Publish exactly the same records again.
        publish_customers(connection, customers)
        publish_orders(connection, orders)

        # Check that the second run did not duplicate records.
        customer_count = connection.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]

        order_count = connection.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]

        assert customer_count == 1
        assert order_count == 1

    finally:
        connection.close()
