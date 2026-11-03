
from pathlib import Path
import json
import pandas as pd


# Find the main project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Define input and output folders.
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports"


def transform_customers(customers):
    """
    Standardise customer data.

    Input:
        customers: DataFrame containing validated customers.

    Output:
        A transformed customer DataFrame.
    """

    customers = customers.copy()

    # Remove unnecessary spaces from text columns.
    for column in ["customer_id", "customer_name", "email", "city"]:
        if column in customers.columns:
            customers[column] = customers[column].astype("string").str.strip()

    # Convert customer creation timestamps to UTC.
    customers["created_at"] = pd.to_datetime(
        customers["created_at"],
        errors="raise",
        utc=True
    )

    # Store timestamps in ISO-8601 format.
    customers["created_at"] = customers["created_at"].apply(
        lambda value: value.isoformat()
    )

    return customers


def transform_orders(orders):
    """
    Standardise orders and calculate total_amount.

    Input:
        orders: DataFrame containing validated orders.

    Output:
        A transformed order DataFrame.
    """

    orders = orders.copy()

    # Remove unnecessary spaces from text columns.
    for column in [
        "source_record_id",
        "order_id",
        "customer_id",
        "status",
        "source_file"
    ]:
        orders[column] = orders[column].astype("string").str.strip()

    # Standardise order status to uppercase.
    orders["status"] = orders["status"].str.upper()

    # Convert order timestamps to UTC.
    orders["order_timestamp"] = pd.to_datetime(
        orders["order_timestamp"],
        errors="raise",
        utc=True
    )

    # Store timestamps in ISO-8601 format.
    orders["order_timestamp"] = orders["order_timestamp"].apply(
        lambda value: value.isoformat()
    )

    # Convert quantity and unit price to numeric values.
    orders["quantity"] = pd.to_numeric(
        orders["quantity"],
        errors="raise"
    ).astype("int64")

    orders["unit_price"] = pd.to_numeric(
        orders["unit_price"],
        errors="raise"
    )

    # Calculate the total order amount.
    # Round to two decimal places for monetary output.
    orders["total_amount"] = (
        orders["quantity"] * orders["unit_price"]
    ).round(2)

    return orders


def run_transformation():

    # Read validated input files.
    customers_path = PROCESSED_DIR / "valid_customers.csv"
    orders_path = PROCESSED_DIR / "valid_orders.csv"

    customers = pd.read_csv(customers_path)
    orders = pd.read_csv(orders_path)

    # Transform both datasets.
    transformed_customers = transform_customers(customers)
    transformed_orders = transform_orders(orders)

    # Verify that transformation did not change row counts.
    assert len(transformed_customers) == len(customers)
    assert len(transformed_orders) == len(orders)

    # Verify that every order has a calculated amount.
    assert transformed_orders["total_amount"].notna().all()

    # Verify the calculated amounts are not negative.
    assert (transformed_orders["total_amount"] >= 0).all()

    # Save transformed datasets.
    customer_output = PROCESSED_DIR / "transformed_customers.csv"
    order_output = PROCESSED_DIR / "transformed_orders.csv"

    transformed_customers.to_csv(customer_output, index=False)
    transformed_orders.to_csv(order_output, index=False)

    # Prepare a transformation report.
    summary = {
        "customers": {
            "input": len(customers),
            "output": len(transformed_customers)
        },
        "orders": {
            "input": len(orders),
            "output": len(transformed_orders)
        },
        "total_order_amount": round(
            float(transformed_orders["total_amount"].sum()), 2
        ),
        "output_files": [
            str(customer_output.relative_to(PROJECT_ROOT)),
            str(order_output.relative_to(PROJECT_ROOT))
        ],
        "status": "SUCCESS"
    }

    # Save the report as JSON.
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report_path = REPORT_DIR / "transformation_summary.json"

    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    print("STAGE 3 TRANSFORMATION COMPLETED")
    print("----------------------------------")
    print("Customers:", summary["customers"])
    print("Orders:", summary["orders"])
    print("Total order amount:", summary["total_order_amount"])
    print("Status:", summary["status"])
    print("----------------------------------")

    return summary
