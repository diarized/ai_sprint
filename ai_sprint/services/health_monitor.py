"""Health monitoring service for agent lifecycle management.

This module implements health monitoring for all agents:
- Heartbeat tracking
- Crash detection (missing process)
- Hung agent detection (no heartbeat for 5 minutes)
- Stuck task detection (exceeding duration limit)
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import psutil

from ai_sprint.config.settings import Settings

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitor agent health and detect failures."""

    def __init__(self, db_path: Path, settings: Settings):
        """Initialize health monitor.

        Args:
            db_path: Path to SQLite database
            settings: Application settings
        """
        self.db_path = db_path
        self.settings = settings
        self.heartbeat_threshold = timedelta(
            seconds=settings.timeouts.agent_heartbeat_seconds
        )
        self.hung_threshold = timedelta(
            seconds=settings.timeouts.agent_hung_seconds
        )
        self.task_timeout = timedelta(
            seconds=settings.timeouts.task_max_duration_seconds
        )

    def record_heartbeat(self, agent_id: str) -> None:
        """Record heartbeat for an agent.

        Args:
            agent_id: Agent identifier (e.g., "dev-001")
        """
        with self._get_db() as conn:
            conn.execute(
                """
                UPDATE agent_sessions
                SET last_heartbeat = ?
                WHERE agent_id = ? AND status = 'active'
                """,
                (datetime.now().isoformat(), agent_id),
            )
            conn.commit()
            logger.debug(f"Heartbeat recorded for {agent_id}")

    def check_crashed_agents(self) -> list[str]:
        """Detect agents with missing processes.

        Returns:
            List of agent IDs for crashed agents
        """
        crashed = []

        with self._get_db() as conn:
            cursor = conn.execute(
                """
                SELECT agent_id, status
                FROM agent_sessions
                WHERE status = 'active'
                """
            )
            active_agents = cursor.fetchall()

        for row in active_agents:
            agent_id = row[0]
            if not self._is_process_running(agent_id):
                crashed.append(agent_id)
                self._mark_crashed(agent_id)
                logger.warning(f"Agent {agent_id} crashed - process not found")

        return crashed

    def check_hung_agents(self) -> list[str]:
        """Detect agents with no heartbeat for 5 minutes.

        Returns:
            List of agent IDs for hung agents
        """
        hung = []
        threshold_time = datetime.now() - self.hung_threshold

        with self._get_db() as conn:
            cursor = conn.execute(
                """
                SELECT agent_id, last_heartbeat
                FROM agent_sessions
                WHERE status = 'active'
                AND last_heartbeat < ?
                """,
                (threshold_time.isoformat(),),
            )
            stale_agents = cursor.fetchall()

        for row in stale_agents:
            agent_id = row[0]
            last_heartbeat = datetime.fromisoformat(row[1])
            elapsed = datetime.now() - last_heartbeat
            hung.append(agent_id)
            self._mark_hung(agent_id)
            logger.warning(
                f"Agent {agent_id} hung - no heartbeat for {elapsed.total_seconds():.0f}s"
            )

        return hung

    def check_stuck_tasks(self) -> list[dict]:
        """Detect tasks exceeding maximum duration.

        Returns:
            List of dicts with task_id, agent_id, duration_seconds
        """
        stuck = []
        threshold_time = datetime.now() - self.task_timeout

        with self._get_db() as conn:
            cursor = conn.execute(
                """
                SELECT t.id, t.assignee, t.started_at
                FROM tasks t
                WHERE t.status IN ('in_progress', 'in_review', 'in_tests', 'in_docs')
                AND t.started_at < ?
                """,
                (threshold_time.isoformat(),),
            )
            long_tasks = cursor.fetchall()

        for row in long_tasks:
            task_id = row[0]
            agent_id = row[1]
            started_at = datetime.fromisoformat(row[2])
            duration = datetime.now() - started_at

            stuck.append(
                {
                    "task_id": task_id,
                    "agent_id": agent_id,
                    "duration_seconds": duration.total_seconds(),
                }
            )

            # Mark agent as stuck
            if agent_id:
                self._mark_stuck(agent_id, task_id)
                logger.warning(
                    f"Task {task_id} stuck on {agent_id} for {duration.total_seconds():.0f}s"
                )

        return stuck

    def get_agent_status(self, agent_id: str) -> Optional[str]:
        """Get current status of an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Status string or None if agent not found
        """
        with self._get_db() as conn:
            cursor = conn.execute(
                "SELECT status FROM agent_sessions WHERE agent_id = ?",
                (agent_id,),
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def _is_process_running(self, agent_id: str) -> bool:
        """Check if agent process is running.

        This checks for tmux sessions matching the agent ID pattern.
        For tmux-based agents, we look for sessions named after the agent.

        Args:
            agent_id: Agent identifier

        Returns:
            True if process found, False otherwise
        """
        try:
            # Check for tmux session with agent name
            import libtmux

            server = libtmux.Server()
            session = server.sessions.get(
                session_name=f"ai-sprint-{agent_id}", default=None
            )
            return session is not None
        except Exception as e:
            logger.error(f"Error checking process for {agent_id}: {e}")
            return False

    def _mark_crashed(self, agent_id: str) -> None:
        """Mark agent as crashed in database."""
        with self._get_db() as conn:
            conn.execute(
                """
                UPDATE agent_sessions
                SET status = 'crashed', crashed_at = ?
                WHERE agent_id = ?
                """,
                (datetime.now().isoformat(), agent_id),
            )
            conn.commit()

    def _mark_hung(self, agent_id: str) -> None:
        """Mark agent as hung in database."""
        with self._get_db() as conn:
            conn.execute(
                """
                UPDATE agent_sessions
                SET status = 'hung'
                WHERE agent_id = ?
                """,
                (agent_id,),
            )
            conn.commit()

    def _mark_stuck(self, agent_id: str, task_id: str) -> None:
        """Mark agent as stuck on a task."""
        with self._get_db() as conn:
            conn.execute(
                """
                UPDATE agent_sessions
                SET status = 'stuck'
                WHERE agent_id = ?
                """,
                (agent_id,),
            )
            conn.commit()

    def _get_db(self) -> sqlite3.Connection:
        """Get database connection with proper settings."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
