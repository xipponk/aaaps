"""
model/tasks.py — TaskObject dataclass.

TaskObject is a passive data container representing a single academic or life
task assigned to a student.
"""

from dataclasses import dataclass, field


@dataclass
class TaskObject:
    """A single task in a student's slot queue."""

    task_id: int
    task_type: str
    difficulty: float
    base_score: float
    deadline_remaining: int
    deadline_total: int
    ai_allowed: bool
    course_id: str
    effort_remaining: float = 0.0
    processing_progress: float = field(default=0.0)

    def __post_init__(self) -> None:
        if self.effort_remaining == 0.0:
            self.effort_remaining = self.base_score * 3.0
