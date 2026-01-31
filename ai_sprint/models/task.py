"""Task data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Task:
    """
    Individual work item with acceptance criteria.

    Status transitions:
    - todo → in_progress (Developer claims)
    - in_progress → in_review (Developer submits)
    - in_review → in_tests (CAB approves)
    - in_review → in_progress (CAB rejects)
    - in_tests → in_docs (Tester validates)
    - in_tests → in_progress (Tester rejects)
    - in_docs → done (Refinery merges)
    - in_docs → in_progress (Refinery rejects)
    """

    id: str
    convoy_id: str
    title: str
    description: str
    file_path: str
    status: str  # todo, in_progress, in_review, in_tests, in_docs, done
    priority: str
    acceptance_criteria: list[dict]
    created_at: datetime
    assignee: Optional[str] = None
    validation_results: Optional[dict] = None
    failure_reason: Optional[str] = None
    failure_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate status values."""
        valid_statuses = {"todo", "in_progress", "in_review", "in_tests", "in_docs", "done"}
        if self.status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{self.status}'. Must be one of {valid_statuses}"
            )
