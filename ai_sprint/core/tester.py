"""Tester agent - validation execution."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ai_sprint.config.settings import Settings
from ai_sprint.services.quality_gates import QualityGateRunner
from ai_sprint.services.state_manager import (
    consume_events,
    get_db,
    get_task,
    publish_event,
    update_task_status,
    update_task_validation_results,
)
from ai_sprint.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# T039: Tester agent base (validation execution)
# =============================================================================

class TesterAgent:
    """
    Tester agent - validates implementations.

    Responsibilities:
    - Run test suites
    - Measure code coverage
    - Run mutation testing
    - Validate acceptance criteria
    - Report validation results
    """

    def __init__(
        self,
        agent_id: str,
        db_path: str = "~/.ai-sprint/beads.db",
        worktree_path: Optional[Path] = None,
        settings: Optional[Settings] = None,
    ):
        """
        Initialize Tester agent.

        Args:
            agent_id: Unique agent identifier (e.g., "test-001")
            db_path: Path to SQLite database
            worktree_path: Path to git worktree for this agent
            settings: Application settings
        """
        self.agent_id = agent_id
        self.db_path = db_path
        self.worktree_path = worktree_path or Path.cwd()
        self.settings = settings or Settings()

    def process_events(self) -> None:
        """Process RUN_TESTS events."""
        with get_db(self.db_path) as conn:
            events = consume_events(conn, self.agent_id, limit=10)

            for event in events:
                if event["event_type"] == "RUN_TESTS":
                    task_id = event["payload"]["task_id"]
                    self.validate_task(task_id)

    def validate_task(self, task_id: str) -> bool:
        """
        Validate a task's implementation.

        Implementation of T079: Integrate test gates into Tester agent.

        Args:
            task_id: Task to validate

        Returns:
            True if validation passed, False otherwise
        """
        logger.info(f"Validating task: {task_id}")

        with get_db(self.db_path) as conn:
            task = get_task(conn, task_id)
            if not task:
                logger.error(f"Task not found: {task_id}")
                return False

            if task["status"] != "in_tests":
                logger.error(f"Task {task_id} not in testing status")
                return False

            # Run test quality gates
            runner = QualityGateRunner(self.settings, self.worktree_path)
            results = runner.run_all_gates(stage="tests")

            if runner.all_gates_passed():
                logger.info(f"Task {task_id} passed test quality gates")

                # Store validation results
                validation_results = {
                    "coverage_percent": next(
                        (r.score for r in results if r.gate_type.value == "coverage"),
                        None,
                    ),
                    "mutation_score": next(
                        (r.score for r in results if r.gate_type.value == "mutation"),
                        None,
                    ),
                    "tests_passed": True,
                    "validated_at": datetime.now().isoformat(),
                }

                update_task_validation_results(conn, task_id, validation_results)

                # Move to in_docs status
                update_task_status(conn, task_id, "in_docs")

                # Publish event to Refinery
                publish_event(
                    conn,
                    agent_id="refinery",
                    event_type="SECURITY_SCAN",
                    payload={"task_id": task_id},
                )

                return True
            else:
                # Failed test gates - reject with specific feedback
                failure_message = runner.get_failure_message()
                logger.warning(f"Task {task_id} failed test gates: {failure_message}")

                self.reject_validation(task_id, failure_message)
                return False

    def reject_validation(
        self,
        task_id: str,
        reason: str,
    ) -> None:
        """
        Reject task validation and send back to developer.

        Args:
            task_id: Task to reject
            reason: Specific test failures or coverage issues
        """
        logger.info(f"Rejecting validation for {task_id}: {reason}")

        with get_db(self.db_path) as conn:
            # Send back to in_progress
            update_task_status(conn, task_id, "in_progress")

            # Publish rework event
            publish_event(
                conn,
                agent_id="developer",
                event_type="REWORK_NEEDED",
                payload={"task_id": task_id, "reason": reason},
            )

    def run_coverage(self, source_dir: Path) -> dict[str, Any]:
        """
        Run code coverage analysis.

        Args:
            source_dir: Directory containing source code

        Returns:
            Coverage results
        """
        logger.info(f"Running coverage for: {source_dir}")
        # TODO: Run pytest-cov
        return {"coverage_percent": 0, "lines_covered": 0, "lines_total": 0}

    def run_mutation_tests(self, source_dir: Path) -> dict[str, Any]:
        """
        Run mutation testing.

        Args:
            source_dir: Directory containing source code

        Returns:
            Mutation score results
        """
        logger.info(f"Running mutation tests for: {source_dir}")
        # TODO: Run mutmut
        return {"mutation_score": 0, "killed": 0, "survived": 0, "timeout": 0}
