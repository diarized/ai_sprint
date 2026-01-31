"""Manager agent - orchestrates feature implementation."""

import sqlite3
import time
from pathlib import Path
from typing import Optional

from ai_sprint.config.settings import Settings
from ai_sprint.services.health_monitor import HealthMonitor
from ai_sprint.services.state_manager import (
    create_convoy,
    get_db,
    increment_task_failure_count,
    list_convoys_by_feature,
    list_features_by_status,
    publish_event,
    update_feature_status,
)
from ai_sprint.services.session_manager import SessionManager, spawn_agent
from ai_sprint.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# T034: Manager agent base (polling, convoy creation, agent spawning)
# =============================================================================

class ManagerAgent:
    """
    Manager agent - orchestrates feature implementation.

    Responsibilities:
    - Poll for ready features
    - Parse tasks.md and create convoys
    - Spawn Developer/Tester agents
    - Monitor agent health
    - Handle agent crashes and restarts
    """

    def __init__(
        self,
        db_path: str = "~/.ai-sprint/beads.db",
        polling_interval: int = 30,
        max_developers: int = 3,
        max_testers: int = 3,
        settings: Optional[Settings] = None,
    ):
        """
        Initialize Manager agent.

        Args:
            db_path: Path to SQLite database
            polling_interval: Seconds between feature polls
            max_developers: Maximum concurrent developer agents
            max_testers: Maximum concurrent tester agents
            settings: Application settings (optional)
        """
        self.db_path = Path(db_path).expanduser()
        self.polling_interval = polling_interval
        self.max_developers = max_developers
        self.max_testers = max_testers
        self.session_manager = SessionManager()
        self.settings = settings or Settings()
        self.health_monitor = HealthMonitor(self.db_path, self.settings)
        self.running = False

    def start(self) -> None:
        """Start Manager agent polling loop."""
        logger.info("Starting Manager agent")
        self.running = True

        try:
            while self.running:
                self._poll_features()
                self._check_agent_health()
                time.sleep(self.polling_interval)
        except KeyboardInterrupt:
            logger.info("Manager agent stopped by user")
        finally:
            self.running = False

    def stop(self) -> None:
        """Stop Manager agent."""
        logger.info("Stopping Manager agent")
        self.running = False

    def _poll_features(self) -> None:
        """Poll for ready features and process them."""
        with get_db(self.db_path) as conn:
            ready_features = list_features_by_status(conn, "ready")

            for feature_row in ready_features:
                feature_id = feature_row["id"]
                logger.info(f"Processing feature: {feature_id}")

                try:
                    # Update feature to in_progress
                    update_feature_status(conn, feature_id, "in_progress")

                    # Create convoys from tasks.md
                    self._create_convoys_from_tasks(conn, feature_row)

                    logger.info(f"Feature {feature_id} convoys created")
                except Exception as e:
                    logger.error(f"Failed to process feature {feature_id}: {e}")
                    update_feature_status(conn, feature_id, "failed")

    def _create_convoys_from_tasks(
        self,
        conn: sqlite3.Connection,
        feature_row: sqlite3.Row,
    ) -> None:
        """
        Parse tasks.md and create convoy records.

        Args:
            conn: Database connection
            feature_row: Feature record
        """
        feature_id = feature_row["id"]
        spec_path = Path(feature_row["spec_path"])
        tasks_file = spec_path / "tasks.md"

        if not tasks_file.exists():
            raise FileNotFoundError(f"tasks.md not found: {tasks_file}")

        # Parse tasks.md and extract convoys
        # TODO: Implement tasks.md parser
        # For now, create a placeholder convoy
        logger.warning("tasks.md parser not implemented - creating placeholder convoy")

        create_convoy(
            conn,
            convoy_id=f"{feature_id}-convoy-1",
            feature_id=feature_id,
            story="Placeholder Story",
            priority="P1",
            files=["placeholder.py"],
            status="available",
        )

    def spawn_developer(
        self,
        agent_id: str,
        convoy_id: str,
        worktree_path: str,
    ) -> None:
        """
        Spawn a Developer agent in tmux session.

        Args:
            agent_id: Unique agent identifier (e.g., "dev-001")
            convoy_id: Convoy to assign
            worktree_path: Path to git worktree
        """
        logger.info(f"Spawning Developer agent: {agent_id} for {convoy_id}")

        # Create tmux session
        session = self.session_manager.create_session(
            session_name=agent_id,
            working_dir=worktree_path,
        )

        # Spawn developer process
        # TODO: Replace with actual Claude Code invocation
        command = f"echo 'Developer {agent_id} working on {convoy_id}'"

        spawn_agent(
            session=session,
            agent_type="developer",
            agent_id=agent_id,
            command=command,
            working_dir=worktree_path,
        )

    def spawn_tester(
        self,
        agent_id: str,
        task_id: str,
        worktree_path: str,
    ) -> None:
        """
        Spawn a Tester agent in tmux session.

        Args:
            agent_id: Unique agent identifier (e.g., "test-001")
            task_id: Task to validate
            worktree_path: Path to git worktree
        """
        logger.info(f"Spawning Tester agent: {agent_id} for {task_id}")

        # Create tmux session
        session = self.session_manager.create_session(
            session_name=agent_id,
            working_dir=worktree_path,
        )

        # Spawn tester process
        # TODO: Replace with actual testing framework invocation
        command = f"echo 'Tester {agent_id} validating {task_id}'"

        spawn_agent(
            session=session,
            agent_type="tester",
            agent_id=agent_id,
            command=command,
            working_dir=worktree_path,
        )

    def _check_agent_health(self) -> None:
        """
        Check health of all active agents.

        Detects crashed, hung, or stuck agents and restarts them.
        Implementation of T062-T064.
        """
        # T062: Crash detection (missing process)
        crashed = self.health_monitor.check_crashed_agents()
        for agent_id in crashed:
            logger.warning(f"Agent {agent_id} crashed - attempting restart")
            self._handle_agent_failure(agent_id, "crashed")

        # T063: Hung agent detection (no heartbeat for 5 minutes)
        hung = self.health_monitor.check_hung_agents()
        for agent_id in hung:
            logger.warning(f"Agent {agent_id} hung - attempting restart")
            self._handle_agent_failure(agent_id, "hung")

        # T064: Stuck task detection (exceeding duration limit)
        stuck_tasks = self.health_monitor.check_stuck_tasks()
        for stuck_info in stuck_tasks:
            agent_id = stuck_info["agent_id"]
            task_id = stuck_info["task_id"]
            duration = stuck_info["duration_seconds"]
            logger.warning(
                f"Task {task_id} stuck on {agent_id} for {duration:.0f}s - attempting restart"
            )
            self._handle_agent_failure(agent_id, "stuck", task_id)

    def _handle_agent_failure(
        self,
        agent_id: str,
        failure_type: str,
        task_id: Optional[str] = None,
    ) -> None:
        """
        Handle agent failure by attempting restart or escalation.

        Implementation of T065-T068.

        Args:
            agent_id: Failed agent identifier
            failure_type: Type of failure (crashed, hung, stuck)
            task_id: Optional task ID if failure is task-specific
        """
        # T067: Track failure count
        if task_id:
            with get_db(self.db_path) as conn:
                failure_count = increment_task_failure_count(
                    conn, task_id, f"Agent {failure_type}"
                )

                # T068: Escalate after 3 failures
                if failure_count >= 3:
                    logger.error(
                        f"Task {task_id} failed {failure_count} times - escalating"
                    )
                    publish_event(
                        conn,
                        agent_id="architect",
                        event_type="ESCALATE_TASK",
                        payload={
                            "task_id": task_id,
                            "failure_count": failure_count,
                            "failure_type": failure_type,
                            "last_agent": agent_id,
                        },
                    )
                    # Mark task as requiring manual intervention
                    conn.execute(
                        """
                        UPDATE tasks
                        SET status = 'todo',
                            assignee = NULL,
                            failure_reason = ?
                        WHERE id = ?
                        """,
                        (
                            f"Escalated after {failure_count} failures ({failure_type})",
                            task_id,
                        ),
                    )
                    conn.commit()
                    return

        # T065: Automatic agent restart
        try:
            self._restart_agent(agent_id)
        except Exception as e:
            logger.error(f"Failed to restart agent {agent_id}: {e}")
            # Publish crash event for monitoring
            with get_db(self.db_path) as conn:
                publish_event(
                    conn,
                    agent_id="manager",
                    event_type="AGENT_RESTART_FAILED",
                    payload={
                        "agent_id": agent_id,
                        "failure_type": failure_type,
                        "task_id": task_id,
                        "error": str(e),
                    },
                )

    def _restart_agent(self, agent_id: str) -> None:
        """
        Restart a crashed or hung agent.

        Implementation of T065-T066.

        Args:
            agent_id: Agent to restart
        """
        logger.info(f"Restarting agent: {agent_id}")

        # Destroy old session
        try:
            self.session_manager.destroy_session(f"ai-sprint-{agent_id}")
        except ValueError:
            pass  # Session already gone

        # T066: State recovery - get agent info from database
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT agent_type, convoy_id, current_task, worktree
                FROM agent_sessions
                WHERE agent_id = ?
                """,
                (agent_id,),
            )
            row = cursor.fetchone()

            if not row:
                logger.error(f"Agent {agent_id} not found in database")
                return

            agent_type = row[0]
            convoy_id = row[1]
            current_task = row[2]
            worktree = row[3]

        # Respawn agent based on type
        if agent_type == "developer":
            if convoy_id and worktree:
                logger.info(
                    f"Respawning Developer {agent_id} with convoy {convoy_id}"
                )
                self.spawn_developer(agent_id, convoy_id, worktree)
            else:
                logger.warning(
                    f"Developer {agent_id} missing convoy or worktree - cannot restart"
                )
        elif agent_type == "tester":
            if current_task and worktree:
                logger.info(f"Respawning Tester {agent_id} with task {current_task}")
                self.spawn_tester(agent_id, current_task, worktree)
            else:
                logger.warning(
                    f"Tester {agent_id} missing task or worktree - cannot restart"
                )
        else:
            logger.warning(f"Unknown agent type {agent_type} for {agent_id}")
