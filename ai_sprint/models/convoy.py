"""Convoy data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Convoy:
    """
    Bundle of related tasks (user story) assigned to single developer.

    Status transitions:
    - available → in_progress (Developer claims)
    - available → blocked (Dependencies not met)
    - blocked → available (Dependencies complete)
    - in_progress → done (All tasks complete)
    """

    id: str
    feature_id: str
    story: str
    priority: str
    status: str  # available, in_progress, done, blocked
    files: list[str]
    created_at: datetime
    dependencies: list[str] = field(default_factory=list)
    assignee: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate status values."""
        valid_statuses = {"available", "in_progress", "done", "blocked"}
        if self.status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{self.status}'. Must be one of {valid_statuses}"
            )
