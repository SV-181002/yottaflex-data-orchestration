
"""
Stage 2: Data validation module.

Validates customer and order records, separates accepted and
rejected records, and generates a validation summary.
"""

from pathlib import Path
import pandas as pd
import json


# Project directories.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
QUARANTINE_DIR = PROJECT_ROOT / "data" / "quarantine"
REPORT_DIR = PROJECT_ROOT / "reports"

# Allowed order statuses.
ALLOWED_STATUSES = {
    "PLACED", "SHIPPED", "DELIVERED", "CANCELLED"
}


# Identify missing or blank values.
def is_blank(series):
    return (
        series.isna()
        | series.astype("string").str.strip().eq("")
    )


# Mark every occurrence of a duplicate value.
def duplicate_mask(series):
    values = series.astype("string").str.strip()

    return (
        values.notna()
        & values.ne("")
        & values.duplicated(keep=False)
    )


# Attach all applicable rejection reasons to each row.
def add_reason(reasons, mask, reason):
    for position, failed in enumerate(mask.fillna(False).tolist()):
        if failed:
            reasons[position].append(reason)


# Separate accepted and rejected records.
def separate_records(df, reasons):
    result = df.copy()

    result["rejection_reasons"] = [
        ";".join(row_reasons)
        for row_reasons in reasons
    ]

    rejected_mask = result["rejection_reasons"].ne("")

    valid = result.loc[~rejected_mask].copy()

    rejected = result.loc[rejected_mask].copy()

    valid = valid.drop(columns=["rejection_reasons"])

    return valid, rejected


# --------------------------------------------------
# CUSTOMER VALIDATION
# --------------------------------------------------

def validate_customers(customers):

    df = customers.copy().reset_index(drop=True)

    reasons = [[] for _ in range(len(df))]

    required_fields = [
        "customer_id",
        "customer_name",
        "email",
        "created_at"
    ]

    for column in required_fields:
        add_reason(
            reasons,
            is_blank(df[column]),
            f"missing_{column}"
        )

    # Check duplicate customer IDs.
    add_reason(
        reasons,
        duplicate_mask(df["customer_id"]),
        "duplicate_customer_id"
    )

    # Check basic email format.
    email = df["email"].astype("string").str.strip()

    valid_email = email.str.match(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        na=False
    )

    add_reason(
        reasons,
        ~is_blank(df["email"]) & ~valid_email,
        "invalid_email"
    )

    # Check customer timestamps.
    parsed_dates = pd.to_datetime(
        df["created_at"],
        errors="coerce",
        utc=True
    )

    add_reason(
        reasons,
        ~is_blank(df["created_at"]) & parsed_dates.isna(),
        "invalid_created_at"
    )

    return separate_records(df, reasons)


# --------------------------------------------------
# ORDER VALIDATION
# --------------------------------------------------

def validate_orders(orders, valid_customer_ids):

    df = orders.copy().reset_index(drop=True)

    reasons = [[] for _ in range(len(df))]

    required_fields = [
        "source_record_id",
        "order_id",
        "customer_id",
        "order_timestamp",
        "quantity",
        "unit_price",
        "status",
        "source_file"
    ]

    for column in required_fields:
        add_reason(
            reasons,
            is_blank(df[column]),
            f"missing_{column}"
        )

    # Check duplicate source record IDs.
    add_reason(
        reasons,
        duplicate_mask(df["source_record_id"]),
        "duplicate_source_record_id"
    )

    # Reject every occurrence of duplicate order IDs.
    add_reason(
        reasons,
        duplicate_mask(df["order_id"]),
        "duplicate_order_id"
    )

    # Check whether customer references exist.
    customer_ids = (
        df["customer_id"]
        .astype("string")
        .str.strip()
    )

    add_reason(
        reasons,
        ~is_blank(df["customer_id"])
        & ~customer_ids.isin(valid_customer_ids),
        "customer_not_found"
    )

    # Check order timestamps.
    parsed_dates = pd.to_datetime(
        df["order_timestamp"],
        errors="coerce",
        utc=True
    )

    add_reason(
        reasons,
        ~is_blank(df["order_timestamp"])
        & parsed_dates.isna(),
        "invalid_order_timestamp"
    )

    # Check quantity values.
    quantity = pd.to_numeric(
        df["quantity"],
        errors="coerce"
    )

    add_reason(
        reasons,
        ~is_blank(df["quantity"]) & quantity.isna(),
        "quantity_must_be_numeric"
    )

    add_reason(
        reasons,
        quantity.notna() & (quantity <= 0),
        "quantity_must_be_positive"
    )

    add_reason(
        reasons,
        quantity.notna() & (quantity % 1 != 0),
        "quantity_must_be_integer"
    )

    # Check unit prices.
    price = pd.to_numeric(
        df["unit_price"],
        errors="coerce"
    )

    add_reason(
        reasons,
        ~is_blank(df["unit_price"]) & price.isna(),
        "unit_price_must_be_numeric"
    )

    add_reason(
        reasons,
        price.notna() & (price < 0),
        "unit_price_must_be_non_negative"
    )

    # Check allowed statuses.
    status = (
        df["status"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    add_reason(
        reasons,
        ~is_blank(df["status"])
        & ~status.isin(ALLOWED_STATUSES),
        "invalid_order_status"
    )

    return separate_records(df, reasons)


# --------------------------------------------------
# SAVE OUTPUT FILES
# --------------------------------------------------

def save_outputs(
    valid_customers,
    rejected_customers,
    valid_orders,
    rejected_orders
):

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    valid_customers.to_csv(
        PROCESSED_DIR / "valid_customers.csv",
        index=False
    )

    valid_orders.to_csv(
        PROCESSED_DIR / "valid_orders.csv",
        index=False
    )

    rejected_customers.to_csv(
        QUARANTINE_DIR / "rejected_customers.csv",
        index=False
    )

    rejected_orders.to_csv(
        QUARANTINE_DIR / "rejected_orders.csv",
        index=False
    )


# --------------------------------------------------
# MAIN VALIDATION WORKFLOW
# --------------------------------------------------

def run_validation():

    # Read source files.
    customers = pd.read_csv(RAW_DIR / "customers.csv")

    orders = pd.read_csv(RAW_DIR / "orders.csv")

    # Validate customers first.
    valid_customers, rejected_customers = (
        validate_customers(customers)
    )

    # Use only accepted customer IDs for order validation.
    valid_customer_ids = set(
        valid_customers["customer_id"]
        .astype(str)
        .str.strip()
    )

    # Validate orders.
    valid_orders, rejected_orders = validate_orders(
        orders,
        valid_customer_ids
    )

    # Save all accepted and rejected files.
    save_outputs(
        valid_customers,
        rejected_customers,
        valid_orders,
        rejected_orders
    )

    # Build validation summary.
    summary = {
        "customers": {
            "input": len(customers),
            "accepted": len(valid_customers),
            "rejected": len(rejected_customers)
        },
        "orders": {
            "input": len(orders),
            "accepted": len(valid_orders),
            "rejected": len(rejected_orders)
        }
    }

    # Save summary as JSON.
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with open(
        REPORT_DIR / "validation_summary.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(summary, file, indent=4)

    print("STAGE 2 VALIDATION COMPLETED")
    print("----------------------------------")
    print("Customers:", summary["customers"])
    print("Orders:", summary["orders"])
    print("----------------------------------")

    return summary
