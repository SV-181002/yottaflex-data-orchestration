
# Data Pipeline Design

## Business Domain
E-commerce order processing.

## Source Entities
1. Customers
2. Orders

## Relationships
One customer can have multiple orders.

## Primary Keys
customers.customer_id
orders.order_id

## Foreign Key
orders.customer_id references customers.customer_id.

## Derived Field
total_amount = quantity * unit_price

## Pipeline Tasks
1. Ingestion
2. Validation
3. Transformation
4. Publishing

## Data Quality
- Required field validation
- Duplicate detection
- Referential integrity
- Invalid record quarantine

## Target Storage
SQLite database.

## Orchestration Requirements
- Task dependencies
- Retries
- Timeouts
- Run status
- Failure notifications
- Publishing protection
