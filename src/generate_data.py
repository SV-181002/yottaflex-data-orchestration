
"""
Synthetic E-commerce Data Generator

Purpose:
Generate reproducible customer and order datasets.
The generator supports normal records and deliberately
introduced data-quality problems for pipeline testing.
"""

# Import standard Python libraries.
import argparse
import random

from pathlib import Path
from datetime import datetime, timedelta, timezone

# Import external libraries.
import pandas as pd
from faker import Faker


def generate_data(
    customer_count=100,
    order_count=200,
    seed=42,
    inject_issues=True
):
    """
    Generate synthetic customers and orders.

    Parameters:
        customer_count: Number of customers to generate.
        order_count: Number of orders to generate.
        seed: Fixed random seed for reproducibility.
        inject_issues: Whether to introduce test anomalies.

    Returns:
        customers_df: Customer DataFrame.
        orders_df: Order DataFrame.
        expected_rejects_df: Separate expected rejection labels.
    """

    # Set fixed seeds so the generated data is reproducible.
    random.seed(seed)
    Faker.seed(seed)

    fake = Faker()
    rng = random.Random(seed)

    # Define the customer records.
    customers = []

    for i in range(1, customer_count + 1):

        customer_id = f"C{i:06d}"

        customers.append({
            "customer_id": customer_id,
            "customer_name": fake.name(),
            "email": f"{customer_id.lower()}@example.com",
            "city": fake.city(),
            "created_at": (
                datetime(2025, 1, 1, tzinfo=timezone.utc)
                + timedelta(days=rng.randint(0, 365))
            ).isoformat()
        })

    # Convert customer records into a DataFrame.
    customers_df = pd.DataFrame(customers)

    # Store the available customer IDs.
    valid_customer_ids = customers_df["customer_id"].tolist()

    # Define allowed order statuses.
    statuses = [
        "PLACED",
        "SHIPPED",
        "DELIVERED",
        "CANCELLED"
    ]

    # Generate order records.
    orders = []

    for i in range(1, order_count + 1):

        order_id = f"O{i:07d}"

        orders.append({
            "source_record_id": f"SRC{i:07d}",
            "order_id": order_id,
            "customer_id": rng.choice(valid_customer_ids),
            "order_timestamp": (
                datetime(2025, 1, 1, tzinfo=timezone.utc)
                + timedelta(days=rng.randint(0, 365))
            ).isoformat(),
            "quantity": rng.randint(1, 10),
            "unit_price": round(rng.uniform(10, 1000), 2),
            "status": rng.choice(statuses),
            "source_file": "orders.csv"
        })

    # Convert order records into a DataFrame.
    orders_df = pd.DataFrame(orders)

    # Create a separate list of expected rejection labels.
    expected_rejects = []

    if inject_issues and order_count >= 8:

        # Scenario 1: Duplicate order ID.
        orders_df.loc[1, "order_id"] = orders_df.loc[0, "order_id"]

        expected_rejects.append({
            "source_record_id": orders_df.loc[0, "source_record_id"],
            "expected_reason": "duplicate_order_id"
        })

        expected_rejects.append({
            "source_record_id": orders_df.loc[1, "source_record_id"],
            "expected_reason": "duplicate_order_id"
        })

        # Scenario 2: Missing customer ID.
        orders_df.loc[2, "customer_id"] = None

        expected_rejects.append({
            "source_record_id": orders_df.loc[2, "source_record_id"],
            "expected_reason": "missing_customer_id"
        })

        # Scenario 3: Customer reference does not exist.
        orders_df.loc[3, "customer_id"] = "C999999"

        expected_rejects.append({
            "source_record_id": orders_df.loc[3, "source_record_id"],
            "expected_reason": "invalid_customer_reference"
        })

        # Scenario 4: Invalid quantity.
        orders_df.loc[4, "quantity"] = 0

        expected_rejects.append({
            "source_record_id": orders_df.loc[4, "source_record_id"],
            "expected_reason": "invalid_quantity"
        })

        # Scenario 5: Negative price.
        orders_df.loc[5, "unit_price"] = -50

        expected_rejects.append({
            "source_record_id": orders_df.loc[5, "source_record_id"],
            "expected_reason": "negative_unit_price"
        })

        # Scenario 6: Unsupported status.
        orders_df.loc[6, "status"] = "UNKNOWN"

        expected_rejects.append({
            "source_record_id": orders_df.loc[6, "source_record_id"],
            "expected_reason": "invalid_status"
        })

        # Scenario 7: Malformed timestamp.
        orders_df.loc[7, "order_timestamp"] = "NOT_A_TIMESTAMP"

        expected_rejects.append({
            "source_record_id": orders_df.loc[7, "source_record_id"],
            "expected_reason": "invalid_timestamp"
        })

    # Convert expected rejection labels into a DataFrame.
    expected_rejects_df = pd.DataFrame(expected_rejects)

    return customers_df, orders_df, expected_rejects_df


def main():

    # Read generator settings from the command line.
    parser = argparse.ArgumentParser(
        description="Generate synthetic e-commerce data."
    )

    parser.add_argument("--customers", type=int, default=100)
    parser.add_argument("--orders", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--inject-issues", action="store_true")

    args = parser.parse_args()

    # Define project output directories.
    project_root = Path(__file__).resolve().parent.parent

    raw_folder = project_root / "data" / "raw"
    sample_folder = project_root / "data" / "sample"

    # Create folders if they do not exist.
    raw_folder.mkdir(parents=True, exist_ok=True)
    sample_folder.mkdir(parents=True, exist_ok=True)

    # Generate datasets.
    customers_df, orders_df, expected_rejects_df = generate_data(
        customer_count=args.customers,
        order_count=args.orders,
        seed=args.seed,
        inject_issues=args.inject_issues
    )

    # Save the source datasets.
    customers_df.to_csv(
        raw_folder / "customers.csv",
        index=False
    )

    orders_df.to_csv(
        raw_folder / "orders.csv",
        index=False
    )

    # Save expected rejection labels separately.
    expected_rejects_df.to_csv(
        sample_folder / "expected_rejects.csv",
        index=False
    )

    # Display generation summary.
    print("DATA GENERATION COMPLETED")
    print("-------------------------")
    print("Customers generated:", len(customers_df))
    print("Orders generated:", len(orders_df))
    print("Expected rejection labels:", len(expected_rejects_df))
    print("Random seed:", args.seed)
    print("Raw data folder:", raw_folder)
    print("Expected labels folder:", sample_folder)


if __name__ == "__main__":
    main()
