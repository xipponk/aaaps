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
    processing_progress: float = field(default=0.0)
    _last_u_t: float = field(default=0.0)
