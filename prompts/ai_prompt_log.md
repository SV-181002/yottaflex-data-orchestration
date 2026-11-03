# AI Assistance and Prompt History

## Project: Data Orchestration Pipeline

## Disclosure

This record was prepared retrospectively from my ChatGPT
conversation history. The descriptions below are summaries
of the assistance received, not claims of verbatim prompts.

AI assistance was used for learning, design guidance,
code generation, debugging and understanding implementation.

I am responsible for reviewing, testing and understanding
the project before submission.

## Stage 1 - Synthetic Data Generation

### AI assistance used
- Guidance on setting up the Python environment.
- Guidance on creating the project folder structure.
- Assistance with synthetic customer and order data generation.
- Troubleshooting Jupyter file-path and folder errors.
- Guidance on inspecting generated CSV files.

### Verification
Generated customers.csv, orders.csv and
expected_rejects.csv and inspected the resulting data.

## Stage 2 - Data Ingestion and Validation

### AI assistance used
- Guidance on defining customer and order validation rules.
- Help identifying missing values, duplicate IDs,
  invalid customer references and invalid business values.
- Assistance designing quarantine and rejection reasons.
- AI-generated validation module for review and testing.
- Troubleshooting the __file__ error in Jupyter.
- Troubleshooting the missing run_validation import.
- Guidance on inspecting validation outputs and counts.

### Validation decisions
- Reject all occurrences of duplicate order IDs.
- Collect all applicable rejection reasons.
- Store rejected customers and orders separately.

### Verification results

Customers:
- Input: 100
- Accepted: 100
- Rejected: 0

Orders:
- Input: 200
- Accepted: 192
- Rejected: 8

Generated:
- valid_customers.csv
- valid_orders.csv
- rejected_customers.csv
- rejected_orders.csv
- validation_summary.json

## AI Assistance Disclosure

The validation implementation received substantial AI
coding assistance. I must review and understand the
implementation, test edge cases and be prepared to explain
the code and design decisions.

## Future Prompt Records

For every future AI interaction related to this assessment,
record the actual prompt, tool used, date, purpose and
whether the generated suggestions were reviewed or modified.


## Stage 3 - Data Transformation

### AI assistance used
- Guidance on transforming validated customer and order data.
- Generated Python transformation module for review.
- Standardised text fields and timestamps.
- Calculated total_amount using quantity multiplied by unit_price.
- Added row-count and output-quality checks.

### Verification results
- Customers input: 100
- Customers output: 100
- Orders input: 192
- Orders output: 192
- Total order amount: 570008.64
- Status: SUCCESS

## Stage 4 - SQLite Publishing

### AI assistance used
- Guidance on designing SQLite database tables.
- Generated Python publishing module for review.
- Added primary keys, foreign keys and database constraints.
- Used transactions to protect database operations.
- Used upsert logic to support safe reruns.
- Planned database reconciliation and idempotency checks.

### Verification results
- Customers processed: 100
- Orders processed: 192
- Customers in database: 100
- Orders in database: 192
- Database total amount: 570008.64
- Second publishing run: SUCCESS
- Duplicate records created: None observed
- Status: SUCCESS

## Ongoing AI Assistance Disclosure

AI-generated code and suggestions are reviewed and tested
as part of this project. I am responsible for understanding
the implementation, checking its correctness and documenting
any modifications or limitations.


## Stage 5 - Workflow Orchestration

### AI assistance used
- Guidance on designing a sequential task dependency workflow.
- AI-generated Python orchestration module for review.
- Implemented task execution using Python subprocesses.
- Added retry handling with a maximum of three attempts.
- Added a 120-second timeout for each task attempt.
- Added unique pipeline run IDs using UUID.
- Added task status tracking and failure handling.
- Added logic to skip downstream tasks after an upstream failure.
- Added logging and JSON execution reports.
- Added pipeline run history.

### Verification results
- Full pipeline execution: SUCCESS
- Validation: SUCCESS
- Transformation: SUCCESS
- Publishing: SUCCESS
- Unique run ID generated: YES
- Execution time in successful run: 4.7 seconds
- Controlled validation failure test: PENDING
- Retry handling test: PENDING
- Downstream task prevention test: PENDING
- Timeout handling test: PENDING

### AI assistance disclosure
The orchestration code was generated with AI assistance.
I am responsible for reviewing the implementation,
understanding its execution flow and testing its behaviour.


### Additional Stage 5 verification results

- Controlled validation failure test: PASSED
- Validation retry handling: PASSED (2 attempts)
- Downstream prevention after validation failure: PASSED
- Timeout handling test: PASSED
- Validation timeout: 1 second per attempt
- Timeout retry handling: PASSED (2 attempts)
- Transformation skipped after timeout: CONFIRMED
- Publishing skipped after timeout: CONFIRMED
- Original task configuration restored after tests: CONFIRMED

Both controlled failure and timeout scenarios were tested successfully.


## Stage 6 — Automated Testing

### AI assistance used
- Created pytest tests for validation, transformation, publishing, and orchestration.
- Used mocked subprocess execution to test orchestration without launching real pipeline tasks.
- Used an in-memory SQLite database to test publishing safely.
- Corrected test assumptions to match the actual function return values.
- Fixed the temporary report directory setup in the orchestrator test.

### Verification results
- Validation tests: 5 PASSED
- Transformation tests: 3 PASSED
- Publishing tests: 2 PASSED
- Orchestration tests: 4 PASSED
- Combined pytest execution: 14 PASSED, 0 FAILED


## Stage 7 — Scalability Testing (100,000 Orders)

### Dataset generation
- Customers generated: 10,000
- Orders generated: 100,000
- Random seed: 42
- Injected data-quality issues: Disabled
- Generation time: 7.17 seconds
- Customer CSV size: 0.78 MB
- Order CSV size: 7.98 MB
- Duplicate customer IDs: 0
- Duplicate order IDs: 0

### End-to-end pipeline verification
- Run ID: adb756fc-d953-4858-a836-722e17a8b07a
- Validation: SUCCESS — 100,000 orders accepted
- Transformation: SUCCESS — 100,000 orders transformed
- Publishing: SUCCESS — 100,000 orders published
- Customers published: 10,000
- Database orders: 100,000
- Database total order amount: 277975212.65
- Complete pipeline duration: 8.56 seconds
- All three tasks completed in one attempt each.

### Verification
- SQLite database counts matched generated dataset counts.
- Database total amount matched transformation output.
- Overall pipeline status: SUCCESS.


### Large-scale idempotency verification
- Re-published the same 10,000 customer and 100,000 order dataset.
- Second publishing status: SUCCESS.
- Customers after republishing: 10,000.
- Orders after republishing: 100,000.
- Database total amount remained: 277975212.65.
- No duplicate records were created.
- Idempotency verification: PASSED.
- Scope: repeated publishing with identical source and business identifiers.
