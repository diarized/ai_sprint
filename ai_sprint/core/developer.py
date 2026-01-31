"""Developer agent - task implementation."""

import sqlite3
from pathlib import Path
from typing import Optional

from ai_sprint.services.state_manager import (
    claim_task_atomic,
    consume_events,
    get_db,
    get_task,
    list_tasks_by_convoy,
    publish_event,
    update_task_status,
)
from ai_sprint.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# T038: Developer agent base (task implementation)
# =============================================================================

class DeveloperAgent:
    """
    Developer agent - implements tasks.

    Responsibilities:
    - Claim tasks from convoy
    - Implement code changes
    - Run local tests
    - Submit for code review
    - Handle rework requests
    """

    def __init__(
        self,
        agent_id: str,
        db_path: str = "~/.ai-sprint/beads.db",
        worktree_path: Optional[Path] = None,
    ):
        """
        Initialize Developer agent.

        Args:
            agent_id: Unique agent identifier (e.g., "dev-001")
            db_path: Path to SQLite database
            worktree_path: Path to git worktree for this agent
        """
        self.agent_id = agent_id
        self.db_path = db_path
        self.worktree_path = worktree_path
        self.current_task_id: Optional[str] = None

    def claim_next_task(self, convoy_id: str) -> Optional[str]:
        """
        Claim the next available task in a convoy.

        Args:
            convoy_id: Convoy to claim from

        Returns:
            Task ID if claimed, None otherwise
        """
        with get_db(self.db_path) as conn:
            tasks = list_tasks_by_convoy(conn, convoy_id, status="todo")

            for task in tasks:
                task_id = task["id"]
                if claim_task_atomic(conn, task_id, self.agent_id):
                    logger.info(f"Claimed task: {task_id}")
                    return task_id

            return None

    def implement_task(self, task_id: str) -> bool:
        """
        Implement a task.

        Args:
            task_id: Task to implement

        Returns:
            True if implementation succeeded
        """
        logger.info(f"Implementing task: {task_id}")

        with get_db(self.db_path) as conn:
            task = get_task(conn, task_id)
            if not task:
                logger.error(f"Task not found: {task_id}")
                return False

            # TODO: Invoke Claude Code for implementation
            logger.warning("Task implementation not implemented - auto-succeeding")

            # Submit for review
            update_task_status(conn, task_id, "in_review")

            # Publish event to CAB
            publish_event(
                conn,
                agent_id="cab",
                event_type="ROUTE_TASK",
                payload={
                    "task_id": task_id,
                    "from_state": "in_progress",
                    "to_state": "in_review",
                },
            )

            return True

    def process_rework_events(self) -> None:
        """Process REWORK_NEEDED events."""
        with get_db(self.db_path) as conn:
            events = consume_events(conn, self.agent_id, limit=10)

            for event in events:
                if event["event_type"] == "REWORK_NEEDED":
                    task_id = event["payload"]["task_id"]
                    reason = event["payload"]["reason"]
                    self.rework_task(task_id, reason)

    def rework_task(self, task_id: str, reason: str) -> None:
        """
        Rework a rejected task.

        Args:
            task_id: Task to rework
            reason: Rejection reason
        """
        logger.info(f"Reworking task {task_id}: {reason}")
        # TODO: Apply fixes based on rejection reason
        logger.warning("Task rework not implemented")

    def recover_state(self) -> Optional[str]:
        """
        Recover state after agent restart.

        Implementation of T066: State recovery after restart.

        Returns:
            Task ID if resuming work, None if starting fresh
        """
        with get_db(self.db_path) as conn:
            # Check for in-progress task assigned to this agent
            cursor = conn.execute(
                """
                SELECT id, status, title
                FROM tasks
                WHERE assignee = ?
                AND status IN ('in_progress', 'in_review', 'in_tests', 'in_docs')
                ORDER BY started_at DESC
                LIMIT 1
                """,
                (self.agent_id,),
            )
            row = cursor.fetchone()

            if row:
                task_id = row[0]
                status = row[1]
                title = row[2]
                logger.info(
                    f"Recovered state: resuming task {task_id} ({title}) in state {status}"
                )
                self.current_task_id = task_id
                return task_id
            else:
                logger.info("No in-progress task found - starting fresh")
                return None

    def resume_work(self, task_id: str) -> bool:
        """
        Resume work on a task after recovery.

        Args:
            task_id: Task to resume

        Returns:
            True if resumed successfully
        """
        with get_db(self.db_path) as conn:
            task = get_task(conn, task_id)
            if not task:
                logger.error(f"Cannot resume - task not found: {task_id}")
                return False

            status = task["status"]
            logger.info(f"Resuming task {task_id} in state {status}")

            # Resume based on current status
            if status == "in_progress":
                # Continue implementation
                return self.implement_task(task_id)
            elif status == "in_review":
                # Wait for CAB review
                logger.info(f"Task {task_id} already in review - waiting")
                return True
            elif status == "in_tests":
                # Wait for testing
                logger.info(f"Task {task_id} already in tests - waiting")
                return True
            elif status == "in_docs":
                # Wait for merge
                logger.info(f"Task {task_id} already in docs - waiting")
                return True
            else:
                logger.warning(f"Unexpected task status {status} for {task_id}")
                return False
