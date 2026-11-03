
import pandas as pd

from src.validation import (
    validate_customers,
    validate_orders,
    duplicate_mask,
)


def test_duplicate_mask_detects_duplicates():
    values = pd.Series(["A101", "A102", "A101"])

    result = duplicate_mask(values)

    assert result.tolist() == [True, False, True]


def test_valid_customers_are_accepted():
    customers = pd.DataFrame({
        "customer_id": ["C1001"],
        "customer_name": ["Rahul"],
        "email": ["rahul@example.com"],
        "city": ["Hyderabad"],
        "created_at": ["2026-01-01T10:00:00Z"]
    })

    # Your validation function returns two DataFrames.
    valid, rejected = validate_customers(customers)

    assert len(valid) == 1
    assert len(rejected) == 0


def test_missing_customer_id_is_rejected():
    customers = pd.DataFrame({
        "customer_id": [None],
        "customer_name": ["Rahul"],
        "email": ["rahul@example.com"],
        "city": ["Hyderabad"],
        "created_at": ["2026-01-01T10:00:00Z"]
    })

    valid, rejected = validate_customers(customers)

    assert len(valid) == 0
    assert len(rejected) == 1


def test_duplicate_customer_ids_are_rejected():
    customers = pd.DataFrame({
        "customer_id": ["C1001", "C1001"],
        "customer_name": ["Rahul", "Kiran"],
        "email": ["rahul@example.com", "kiran@example.com"],
        "city": ["Hyderabad", "Guntur"],
        "created_at": [
            "2026-01-01T10:00:00Z",
            "2026-01-02T10:00:00Z"
        ]
    })

    valid, rejected = validate_customers(customers)

    assert len(valid) == 0
    assert len(rejected) == 2


def test_unknown_customer_reference_is_rejected():
    orders = pd.DataFrame({
        "source_record_id": ["SRC001"],
        "order_id": ["ORD001"],
        "customer_id": ["C9999"],
        "order_timestamp": ["2026-01-01T10:00:00Z"],
        "quantity": [2],
        "unit_price": [100.0],
        "status": ["PLACED"],
        "source_file": ["orders.csv"]
    })

    valid_customer_ids = set()

    valid, rejected = validate_orders(
        orders,
        valid_customer_ids
    )

    assert len(valid) == 0
    assert len(rejected) == 1
