
import pandas as pd

from src.transformation import (
    transform_customers,
    transform_orders,
)


def test_order_total_amount_is_calculated_correctly():
    # Create one sample order.
    orders = pd.DataFrame({
        "source_record_id": ["SRC001"],
        "order_id": ["ORD001"],
        "customer_id": ["C1001"],
        "order_timestamp": ["2026-01-01T10:00:00Z"],
        "quantity": [3],
        "unit_price": [100.0],
        "status": ["PLACED"],
        "source_file": ["orders.csv"]
    })

    # Transform the order data.
    result = transform_orders(orders)

    # Check the calculated amount: 3 * 100 = 300.
    assert result["total_amount"].iloc[0] == 300.00


def test_order_status_is_standardized():
    # Create an order with lowercase status and extra spaces.
    orders = pd.DataFrame({
        "source_record_id": ["SRC002"],
        "order_id": ["ORD002"],
        "customer_id": ["C1001"],
        "order_timestamp": ["2026-01-01T10:00:00Z"],
        "quantity": [2],
        "unit_price": [50.0],
        "status": [" placed "],
        "source_file": ["orders.csv"]
    })

    result = transform_orders(orders)

    # Status should be trimmed and converted to uppercase.
    assert result["status"].iloc[0] == "PLACED"


def test_customer_text_fields_are_trimmed():
    # Create a customer with unnecessary spaces.
    customers = pd.DataFrame({
        "customer_id": [" C1001 "],
        "customer_name": [" Rahul "],
        "email": [" rahul@example.com "],
        "city": [" Hyderabad "],
        "created_at": ["2026-01-01T10:00:00Z"]
    })

    result = transform_customers(customers)

    # Check that text fields have been cleaned.
    assert result["customer_id"].iloc[0] == "C1001"
    assert result["customer_name"].iloc[0] == "Rahul"
    assert result["email"].iloc[0] == "rahul@example.com"
    assert result["city"].iloc[0] == "Hyderabad"

    # Transformation should not remove any customer records.
    assert len(result) == 1
