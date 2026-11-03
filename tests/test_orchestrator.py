
from pathlib import Path
from unittest.mock import patch

from src import orchestrator


def test_run_task_success():
    task = {
        "name": "validation",
        "code": "print('Task completed')",
        "max_retries": 3,
        "timeout_seconds": 10
    }

    with patch("src.orchestrator.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Task completed"
        mock_run.return_value.stderr = ""

        result = orchestrator.run_task(task, "TEST_RUN_001")

    assert result["status"] == "SUCCESS"
    assert result["attempts"] == 1
    assert result["error"] is None


def test_run_task_retries_after_failure():
    task = {
        "name": "validation",
        "code": "print('Testing')",
        "max_retries": 2,
        "timeout_seconds": 10
    }

    with patch("src.orchestrator.subprocess.run") as mock_run, \
         patch("src.orchestrator.time.sleep"):

        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "Simulated failure"

        result = orchestrator.run_task(task, "TEST_RUN_002")

    assert mock_run.call_count == 2
    assert result["status"] == "FAILED"
    assert result["attempts"] == 2
    assert result["error"] == "Simulated failure"


def test_run_task_handles_timeout():
    task = {
        "name": "validation",
        "code": "print('Testing')",
        "max_retries": 1,
        "timeout_seconds": 1
    }

    with patch(
        "src.orchestrator.subprocess.run",
        side_effect=orchestrator.subprocess.TimeoutExpired(
            cmd="test",
            timeout=1
        )
    ):

        result = orchestrator.run_task(task, "TEST_RUN_003")

    assert result["status"] == "FAILED"
    assert result["attempts"] == 1
    assert "exceeded 1 seconds" in result["error"]


def test_pipeline_skips_downstream_after_failure():
    test_tasks = [
        {
            "name": "validation",
            "code": "",
            "max_retries": 2,
            "timeout_seconds": 10
        },
        {
            "name": "transformation",
            "code": "",
            "max_retries": 2,
            "timeout_seconds": 10
        },
        {
            "name": "publishing",
            "code": "",
            "max_retries": 2,
            "timeout_seconds": 10
        }
    ]

    # Create the temporary report folder before saving reports.
    temporary_report_dir = Path("tests/temp_reports")
    temporary_report_dir.mkdir(parents=True, exist_ok=True)

    with patch.object(orchestrator, "TASKS", test_tasks):

        with patch.object(
            orchestrator,
            "run_task",
            return_value={
                "task": "validation",
                "status": "FAILED",
                "attempts": 2,
                "duration_seconds": 0.1,
                "error": "Simulated failure"
            }
        ) as mock_run_task:

            with patch.object(
                orchestrator,
                "REPORT_DIR",
                temporary_report_dir
            ):

                result = orchestrator.run_pipeline()

    # Only validation should have executed.
    assert mock_run_task.call_count == 1

    # Check the overall pipeline status.
    assert result["status"] == "FAILED"

    # Check that downstream tasks were skipped.
    assert result["tasks"][1]["status"] == "SKIPPED"
    assert result["tasks"][2]["status"] == "SKIPPED"
