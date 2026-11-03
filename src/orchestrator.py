
from pathlib import Path
from datetime import datetime, timezone
import subprocess
import sys
import json
import time
import uuid
import logging
import os


# Locate the main project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Create folders for logs and reports.
LOG_DIR = PROJECT_ROOT / "logs"
REPORT_DIR = PROJECT_ROOT / "reports"

LOG_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Configure pipeline logging.
LOG_FILE = LOG_DIR / "pipeline.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    force=True
)

logger = logging.getLogger("pipeline")


# Define the tasks and their execution order.
# Each task runs in a separate Python process.
TASKS = [
    {
        "name": "validation",
        "description": "Read raw files and validate customer and order data",
        "code": "from src.validation import run_validation; run_validation()",
        "max_retries": 3,
        "timeout_seconds": 120
    },
    {
        "name": "transformation",
        "description": "Transform validated customer and order data",
        "code": "from src.transformation import run_transformation; run_transformation()",
        "max_retries": 3,
        "timeout_seconds": 120
    },
    {
        "name": "publishing",
        "description": "Publish transformed records into SQLite",
        "code": "from src.publishing import run_publishing; run_publishing()",
        "max_retries": 3,
        "timeout_seconds": 120
    }
]


def save_json(path, data):
    """Save a Python dictionary as a formatted JSON file."""

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def run_task(task, run_id):
    """
    Execute one pipeline task with retry and timeout handling.

    A task is successful only when its Python process exits
    with return code zero.
    """

    task_name = task["name"]
    max_attempts = task["max_retries"]
    timeout_seconds = task["timeout_seconds"]

    for attempt in range(1, max_attempts + 1):

        start_time = time.monotonic()

        logger.info(
            "RUN %s | TASK %s | ATTEMPT %s STARTED",
            run_id,
            task_name,
            attempt
        )

        print(
            f"\n[{task_name.upper()}] "
            f"Attempt {attempt}/{max_attempts}"
        )

        # Pass the run ID to the child Python process.
        environment = os.environ.copy()
        environment["PIPELINE_RUN_ID"] = run_id

        try:

            # Execute the task in a separate Python process.
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    task["code"]
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=environment
            )

            duration = round(
                time.monotonic() - start_time, 2
            )

            if result.stdout:
                print(result.stdout)

            if result.returncode == 0:

                logger.info(
                    "RUN %s | TASK %s | SUCCESS | ATTEMPT %s",
                    run_id,
                    task_name,
                    attempt
                )

                return {
                    "task": task_name,
                    "status": "SUCCESS",
                    "attempts": attempt,
                    "duration_seconds": duration,
                    "error": None
                }

            # A non-zero exit code means the task failed.
            error_message = (
                result.stderr.strip()
                or f"Process exited with code {result.returncode}"
            )

        except subprocess.TimeoutExpired:

            duration = round(
                time.monotonic() - start_time, 2
            )

            error_message = (
                f"Task exceeded {timeout_seconds} seconds"
            )

        except Exception as error:

            duration = round(
                time.monotonic() - start_time, 2
            )

            error_message = str(error)

        logger.error(
            "RUN %s | TASK %s | ATTEMPT %s FAILED | %s",
            run_id,
            task_name,
            attempt,
            error_message
        )

        print("Task failed:", error_message)

        # Retry if attempts are still available.
        if attempt < max_attempts:
            print("Retrying task...")
            time.sleep(2)

    # Return failure after all attempts are exhausted.
    return {
        "task": task_name,
        "status": "FAILED",
        "attempts": max_attempts,
        "duration_seconds": duration,
        "error": error_message
    }


def run_pipeline():

    # Generate a unique ID for this pipeline execution.
    run_id = str(uuid.uuid4())

    pipeline_start = datetime.now(timezone.utc)
    start_time = time.monotonic()

    print("\n======================================")
    print("DATA ORCHESTRATION PIPELINE STARTED")
    print("Run ID:", run_id)
    print("Started at:", pipeline_start.isoformat())
    print("======================================")

    logger.info("PIPELINE %s STARTED", run_id)

    task_results = []
    pipeline_failed = False

    # Execute tasks in dependency order.
    for index, task in enumerate(TASKS):

        if pipeline_failed:

            # Never execute downstream tasks after a failure.
            task_results.append({
                "task": task["name"],
                "status": "SKIPPED",
                "attempts": 0,
                "duration_seconds": 0,
                "error": "An upstream task failed"
            })

            print(
                f"\n[{task['name'].upper()}] SKIPPED "
                "- upstream failure"
            )

            continue

        result = run_task(task, run_id)
        task_results.append(result)

        if result["status"] == "FAILED":
            pipeline_failed = True

    # Calculate total execution duration.
    total_duration = round(
        time.monotonic() - start_time, 2
    )

    pipeline_end = datetime.now(timezone.utc)

    # Determine overall pipeline status.
    overall_status = (
        "FAILED" if pipeline_failed else "SUCCESS"
    )

    # Build the final execution report.
    summary = {
        "run_id": run_id,
        "status": overall_status,
        "started_at": pipeline_start.isoformat(),
        "finished_at": pipeline_end.isoformat(),
        "duration_seconds": total_duration,
        "tasks": task_results
    }

    # Save the latest run summary.
    summary_path = REPORT_DIR / "pipeline_run_summary.json"
    save_json(summary_path, summary)

    # Preserve the history of all pipeline runs.
    history_path = REPORT_DIR / "run_history.jsonl"

    with open(history_path, "a", encoding="utf-8") as file:
        file.write(json.dumps(summary) + "\n")

    logger.info(
        "PIPELINE %s FINISHED | STATUS %s",
        run_id,
        overall_status
    )

    print("\n======================================")
    print("PIPELINE EXECUTION SUMMARY")
    print("======================================")

    for result in task_results:
        print(
            result["task"].upper(),
            "|",
            result["status"],
            "| Attempts:",
            result["attempts"]
        )

    print("--------------------------------------")
    print("Overall status:", overall_status)
    print("Total duration:", total_duration, "seconds")
    print("Run ID:", run_id)
    print("======================================")

    if pipeline_failed:
        print("ALERT: Pipeline failed. Check the logs and reports.")

    else:
        print("SUCCESS: All pipeline tasks completed.")

    return summary


if __name__ == "__main__":
    run_pipeline()
