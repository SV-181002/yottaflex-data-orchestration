
# Data Dictionary

## 1. Customers

| Column | Data Type | Required | Description |
|---|---|---|---|
| customer_id | String | Yes | Unique customer identifier |
| customer_name | String | Yes | Customer full name |
| email | String | Yes | Customer email address |
| city | String | No | Customer city |
| created_at | Timestamp | Yes | Customer registration time |

Primary Key: customer_id

## 2. Orders

| Column | Data Type | Required | Description |
|---|---|---|---|
| source_record_id | String | Yes | Unique source record identifier |
| order_id | String | Yes | Unique order identifier |
| customer_id | String | Yes | Reference to customers |
| order_timestamp | Timestamp | Yes | Order creation time |
| quantity | Integer | Yes | Number of items |
| unit_price | Decimal | Yes | Price per item |
| status | String | Yes | Order status |
| source_file | String | Yes | Original source filename |

Primary Key: order_id

Foreign Key: customer_id references customers.customer_id

## 3. Relationships

One customer can have multiple orders.

One order belongs to one customer.

## 4. Derived Fields

total_amount = quantity * unit_price

## 5. Accepted Order Statuses

PLACED
SHIPPED
DELIVERED
CANCELLED

## 6. Business Rules

1. Order ID must be unique.
2. Customer ID must exist in the customer dataset.
3. Quantity must be greater than zero.
4. Unit price cannot be negative.
5. Order timestamp must be valid.
6. Required fields cannot be null.

## 7. Assumptions

1. One order represents one complete order record.
2. Each order has one customer.
3. Each order has one quantity and one unit price.
4. All timestamps are stored in UTC.
5. Invalid records must be quarantined, not silently deleted.
