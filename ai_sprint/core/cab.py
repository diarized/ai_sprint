"""CAB agent - code review router."""

import sqlite3
from pathlib import Path
from typing import Optional

from ai_sprint.config.settings import Settings
from ai_sprint.services.quality_gates import QualityGateRunner
from ai_sprint.services.state_manager import (
    get_db,
    get_task,
    publish_event,
    update_task_status,
)
from ai_sprint.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# T035: CAB agent base (code review routing)
# =============================================================================

class CABAgent:
    """
    CAB (Change Advisory Board) agent - routes tasks through review.

    Responsibilities:
    - Review code quality (linting, type checking, complexity)
    - Route tasks to testing or back to developer
    - Provide specific rejection feedback
    """

    def __init__(
        self,
        db_path: str = "~/.ai-sprint/beads.db",
        working_dir: Optional[Path] = None,
        settings: Optional[Settings] = None,
    ):
        """
        Initialize CAB agent.

        Args:
            db_path: Path to SQLite database
            working_dir: Directory containing code to review
            settings: Application settings
        """
        self.db_path = db_path
        self.working_dir = working_dir or Path.cwd()
        self.settings = settings or Settings()

    def review_task(self, task_id: str) -> bool:
        """
        Review a task in in_review status.

        Implementation of T078: Integrate quality gates into CAB agent.

        Args:
            task_id: Task to review

        Returns:
            True if approved, False if rejected
        """
        logger.info(f"Reviewing task: {task_id}")

        with get_db(self.db_path) as conn:
            task = get_task(conn, task_id)
            if not task:
                logger.error(f"Task not found: {task_id}")
                return False

            if task["status"] != "in_review":
                logger.error(f"Task {task_id} not in review status")
                return False

            # Run quality gates for review stage
            runner = QualityGateRunner(self.settings, self.working_dir)
            results = runner.run_all_gates(stage="review")

            if runner.all_gates_passed():
                logger.info(f"Task {task_id} passed all quality gates")

                # Approve - route to testing
                update_task_status(conn, task_id, "in_tests")

                # Publish event to Tester
                publish_event(
                    conn,
                    agent_id="tester",
                    event_type="RUN_TESTS",
                    payload={"task_id": task_id},
                )

                return True
            else:
                # Failed quality gates - reject with specific feedback
                failure_message = runner.get_failure_message()
                logger.warning(f"Task {task_id} failed quality gates: {failure_message}")

                self.reject_task(task_id, failure_message)
                return False

    def reject_task(
        self,
        task_id: str,
        reason: str,
    ) -> None:
        """
        Reject a task and send back to developer.

        Args:
            task_id: Task to reject
            reason: Specific rejection reason
        """
        logger.info(f"Rejecting task {task_id}: {reason}")

        with get_db(self.db_path) as conn:
            # Update status back to in_progress
            update_task_status(conn, task_id, "in_progress")

            # Publish rework event to developer
            publish_event(
                conn,
                agent_id="developer",
                event_type="REWORK_NEEDED",
                payload={"task_id": task_id, "reason": reason},
            )
