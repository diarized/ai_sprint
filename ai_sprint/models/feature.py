"""Feature data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Feature:
    """
    Top-level work unit representing a complete feature to implement.

    Status transitions:
    - ready → in_progress (Manager creates convoys)
    - in_progress → done (All convoys complete)
    - in_progress → failed (Unrecoverable error)
    """

    id: str
    name: str
    spec_path: str
    status: str  # ready, in_progress, done, failed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate status values."""
        valid_statuses = {"ready", "in_progress", "done", "failed"}
        if self.status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{self.status}'. Must be one of {valid_statuses}"
            )
