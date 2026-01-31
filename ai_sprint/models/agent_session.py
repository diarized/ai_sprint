"""Agent session data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AgentSession:
    """
    Track active agent processes for health monitoring.

    Status transitions:
    - active → crashed (Process terminated)
    - active → hung (No heartbeat for 5 min)
    - active → stuck (Task timeout)
    - crashed/hung/stuck → active (After restart)
    """

    agent_id: str
    agent_type: str  # manager, cab, refinery, librarian, developer, tester
    status: str  # active, crashed, hung, stuck
    last_heartbeat: datetime
    started_at: datetime
    convoy_id: Optional[str] = None
    current_task: Optional[str] = None
    worktree: Optional[str] = None
    crashed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate agent_type and status values."""
        valid_types = {"manager", "cab", "refinery", "librarian", "developer", "tester"}
        if self.agent_type not in valid_types:
            raise ValueError(
                f"Invalid agent_type '{self.agent_type}'. Must be one of {valid_types}"
            )

        valid_statuses = {"active", "crashed", "hung", "stuck"}
        if self.status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{self.status}'. Must be one of {valid_statuses}"
            )
