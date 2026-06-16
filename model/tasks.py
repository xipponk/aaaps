"""
model/tasks.py — TaskObject dataclass.

TaskObject is a passive data container representing a single academic or life
task assigned to a student.  It is NOT a Mesa Agent — it stores state that
StudentAgent processes during its step() cycle.

C3 "partial" AI is handled at generation time: each C3 task is created with
ai_allowed randomly set to True or False (P=0.5).  The field is always a bool.
"""

from dataclasses import dataclass, field


@dataclass
class TaskObject:
    """A single task in a student's slot queue.

    Attributes
    ----------
    task_id : int
        Unique identifier for this task within the simulation.
    task_type : str
        One of 'academic_assignment', 'quiz', or 'life_task'.
    difficulty : float
        Task difficulty on a 1–10 scale.
    base_score : float
        Raw score value before quality/ability modifiers (difficulty × 10).
    deadline_remaining : int
        Days remaining before the deadline expires (countdown).
    deadline_total : int
        Original deadline length in days, used for urgency calculations.
    ai_allowed : bool
        Whether AI tool use is permitted on this task.
        Always a bool — C3 generates tasks with True/False randomly (P=0.5).
    course_id : str
        Owning course identifier: 'C1'–'C5' for academic tasks, 'LIFE' for
        life tasks.
    processing_progress : float
        Fraction of task processing completed [0.0, 1.0].  Defaults to 0.0.
    """

    task_id: int
    task_type: str
    difficulty: float
    base_score: float
    deadline_remaining: int
    deadline_total: int
    ai_allowed: bool
    course_id: str
    processing_progress: float = field(default=0.0)
