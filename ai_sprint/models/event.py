"""Event data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Event:
    """
    Message in agent communication queue.

    Status transitions:
    - pending → processing (Agent picks up)
    - processing → done (Successfully handled)
    - processing → failed (Handler error)
    """

    id: str
    agent_id: str
    event_type: str
    payload: dict
    created_at: datetime
    status: str = "pending"  # pending, processing, done, failed
    processed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate status values."""
        valid_statuses = {"pending", "processing", "done", "failed"}
        if self.status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{self.status}'. Must be one of {valid_statuses}"
            )
