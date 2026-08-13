"""
model/agents.py — StudentAgent (v0.3 Networked Redesign).

StudentAgent represents one undergraduate CS student. Implements Mesa 2.x API,
coupled continuous dynamic states (d, c, a_r), interaction attributes,
continuous AI usage intensity u(t), and daily task processing.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import mesa
import numpy as np

from config.params import (
    N_SLOTS_DIVISOR,
    N_SLOTS_BASE,
    W_SCORE_MIN,
    W_SCORE_MAX,
    ALPHA_D,
    DELTA_D,
    BETA_C,
    GAMMA_C,
    RHO_AS,
    LAMBDA_A,
    ETA,
    ETA_SELF,
    KAPPA,
    URGENCY_WEIGHT,
    ASPIRATION_GAP_WEIGHT,
    TOPUP_COST,
    LOW_THRESHOLD,
    TOPUP_AMOUNT,
    AI_MONTHLY_COST,
    AI_MONTHLY_QUOTA,
    AI_QUALITY_BOOST,
    AI_SPEED_BOOST,
    PROCESSING_DIFFICULTY_FACTOR,
    DRAIN_RATE,
    SCORE_CAP,
    TIER_BUDGET_FRACTION,
    SHAREABLE_SEATS,
)

if TYPE_CHECKING:
    from model.tasks import TaskObject


def surprise(
    perceived_difficulty: float,
    actual_difficulty: float,
    task_completed: bool,
    c: float,
) -> float:
    """Compute task surprise signal for calibration error recovery (ODD §7.4)."""
    if task_completed:
        raw_error = abs(perceived_difficulty - actual_difficulty) / max(1.0, actual_difficulty)
        miss_severity = 0.3
    else:
        raw_error = 1.0
        miss_severity = 1.0
    return raw_error * miss_severity * (1.0 - c)


class StudentAgent(mesa.Agent):
    """An undergraduate CS student in AAAPS v0.3."""

    # --- Static Attributes ---
    base_ability: float
    SES: str
    section_id: int
    monthly_budget: float
    N_slots: int
    self_regulation: float
    hobby_pull: float
    w_score: float
    conformity: float
    prosociality: float

    # --- Dynamic State ---
    ai_tier: int
    ai_tier_effective: int
    dependency: float
    calibration_error: float
    retained_ability: float
    ai_legitimacy: float
    aspiration: float
    quota_balance: float
    budget_remaining: float
    slot_queue: list[TaskObject]
    score_total: float
    deadline_miss_count: int
    tasks_completed: int
    miss_by_course: dict[str, int]

    # --- Access Market State ---
    borrowing_from: int | None
    shared_seats_out: int

    # Internal step state
    _ai_used_today: bool
    _u_task_records: list[tuple[float, float]]  # list of (u_t, progress_delta) for daily effort-weighted u(t)
    _surprises_today: list[float]
    _incoming_tasks: list[TaskObject]

    def __init__(
        self,
        unique_id: int,
        model: mesa.Model,
        base_ability: float,
        ses: str,
        section_id: int,
        monthly_budget: float,
        self_regulation: float,
        hobby_pull: float,
        conformity: float,
        prosociality: float,
    ) -> None:
        super().__init__(unique_id, model)

        # Static
        self.base_ability = base_ability
        self.SES = ses
        self.section_id = section_id
        self.monthly_budget = monthly_budget
        self.N_slots = int(self.base_ability / N_SLOTS_DIVISOR) + N_SLOTS_BASE
        self.self_regulation = self_regulation
        self.hobby_pull = hobby_pull
        self.w_score = max(W_SCORE_MIN, min(W_SCORE_MAX, 1.0 - hobby_pull))
        self.conformity = conformity
        self.prosociality = prosociality

        # Initial Dynamic State
        self.ai_tier = 0
        self.ai_tier_effective = 0
        self.dependency = 0.0
        self.calibration_error = 0.0
        self.retained_ability = base_ability
        self.ai_legitimacy = 0.10
        self.aspiration = base_ability
        self.quota_balance = 0.0
        self.budget_remaining = monthly_budget
        self.slot_queue = []
        self.score_total = 0.0
        self.deadline_miss_count = 0
        self.tasks_completed = 0
        self.miss_by_course = {}

        # Access Market State
        self.borrowing_from = None
        self.shared_seats_out = 0

        # Step tracking
        self._ai_used_today = False
        self._u_task_records = []
        self._surprises_today = []
        self._incoming_tasks = []

    # =========================================================================
    # Phase C: Individual Action Step
    # =========================================================================

    def step(self) -> None:
        """Phase C individual action step (Mesa 2.x)."""
        self._ai_used_today = False
        self._u_task_records = []
        self._surprises_today = []

        self._evaluate_slots()
        incoming = getattr(self, "_incoming_tasks", None)
        self._decide_accept_tasks(incoming)
        self._process_tasks()
        self._complete_tasks()
        self._manage_quota()

    def _evaluate_slots(self) -> bool:
        return len(self.slot_queue) < self.N_slots

    def _decide_accept_tasks(self, incoming_tasks: list[TaskObject] | None = None) -> None:
        if not incoming_tasks:
            return
        for task in incoming_tasks:
            if not self._evaluate_slots():
                break
            if task.course_id != 'LIFE':
                self.slot_queue.append(task)
            else:
                accept_prob = self.hobby_pull * (1.0 - 0.5 * self.self_regulation)
                if self.random.random() < accept_prob:
                    self.slot_queue.append(task)

    def _compute_usage_intensity(self, task: TaskObject) -> float:
        """Compute continuous AI usage intensity u(t) in [0, 1] per ODD §7.3."""
        effective_tier = max(self.ai_tier, self.ai_tier_effective)
        
        # 1. Availability check
        if not task.ai_allowed or effective_tier == 0 or self.quota_balance <= 0:
            return 0.0

        # 2. Base propensity: w_score + urgency + aspiration gap
        urgency = 1.0 - (task.deadline_remaining / max(1.0, float(task.deadline_total)))
        aspiration_gap = max(0.0, (self.aspiration - self.retained_ability) / 100.0)
        u_base = float(np.clip(self.w_score + URGENCY_WEIGHT * urgency + ASPIRATION_GAP_WEIGHT * aspiration_gap, 0.0, 1.0))

        # 3. Legitimacy gate: ai_legitimacy^(1 - conformity)
        u_norm = math.pow(max(1e-6, self.ai_legitimacy), 1.0 - self.conformity)

        # 4. Combined intensity
        u_t = float(np.clip(u_base * u_norm, 0.0, 1.0))
        return u_t

    def _process_tasks(self) -> None:
        if not self.slot_queue:
            return

        effective_tier = max(self.ai_tier, self.ai_tier_effective)

        for task in self.slot_queue:
            u_t = self._compute_usage_intensity(task)
            if u_t > 0:
                self._ai_used_today = True

            # Effective intelligence (ODD §7.1)
            eff_boost = AI_SPEED_BOOST[effective_tier] * u_t if task.ai_allowed else 0.0
            effective_intelligence = self.retained_ability + eff_boost

            # Processing time & progress delta (v0.2/ODD §7.1 formulation)
            processing_time = (task.difficulty * PROCESSING_DIFFICULTY_FACTOR) / max(1.0, effective_intelligence)
            progress_delta = 1.0 / max(0.1, processing_time)

            task.processing_progress = min(1.0, task.processing_progress + progress_delta)
            task.deadline_remaining -= 1

            # Store u_t and progress_delta for daily effort-weighted u(t) aggregation
            self._u_task_records.append((u_t, progress_delta))
            task._last_u_t = u_t  # Store for quality multiplier upon completion

            # Quota drainage proportional to intensity u(t)
            if effective_tier > 0 and task.ai_allowed and u_t > 0:
                drain = DRAIN_RATE[effective_tier] * u_t * progress_delta
                self.quota_balance = max(0.0, self.quota_balance - drain)

    def _complete_tasks(self) -> None:
        remaining_queue = []
        effective_tier = max(self.ai_tier, self.ai_tier_effective)

        for task in self.slot_queue:
            if task.processing_progress >= 1.0:
                self.tasks_completed += 1
                
                u_t = getattr(task, '_last_u_t', 0.0)
                quality_mult = 1.0 + AI_QUALITY_BOOST[effective_tier] * u_t * (self.retained_ability / 100.0)
                score = min(SCORE_CAP, task.base_score * quality_mult)
                
                if task.deadline_remaining > 0:
                    self.score_total += max(0.0, score)
                    perceived_diff = task.difficulty * (1.0 - 0.4 * self.calibration_error)
                    s = surprise(perceived_diff, task.difficulty, task_completed=True, c=self.calibration_error)
                    self._surprises_today.append(s)
                else:
                    self.deadline_miss_count += 1
                    self.miss_by_course[task.course_id] = self.miss_by_course.get(task.course_id, 0) + 1
                    perceived_diff = task.difficulty * (1.0 - 0.4 * self.calibration_error)
                    s = surprise(perceived_diff, task.difficulty, task_completed=False, c=self.calibration_error)
                    self._surprises_today.append(s)

            elif task.deadline_remaining <= 0:
                self.deadline_miss_count += 1
                self.miss_by_course[task.course_id] = self.miss_by_course.get(task.course_id, 0) + 1
                perceived_diff = task.difficulty * (1.0 - 0.4 * self.calibration_error)
                s = surprise(perceived_diff, task.difficulty, task_completed=False, c=self.calibration_error)
                self._surprises_today.append(s)

            else:
                remaining_queue.append(task)

        self.slot_queue = remaining_queue

    def _manage_quota(self) -> None:
        if self.ai_tier in (2, 3) and self.quota_balance < LOW_THRESHOLD:
            cost = TOPUP_COST[self.ai_tier]
            if self.budget_remaining >= cost:
                self.budget_remaining -= cost
                self.quota_balance += TOPUP_AMOUNT

    # =========================================================================
    # Phase D: Coupled Continuous State Update
    # =========================================================================

    def update_coupled_dynamics(self) -> None:
        """Solve coupled difference equations for (d, c, a_r) in Phase D.

        Daily u(t) input is computed as the effort-weighted average of u(t)
        across all tasks actively processed by the agent today.
        """
        if self._u_task_records:
            total_weight = sum(w for _, w in self._u_task_records)
            if total_weight > 0:
                daily_u = sum(u * w for u, w in self._u_task_records) / total_weight
            else:
                daily_u = 0.0
        else:
            daily_u = 0.0

        daily_u = float(np.clip(daily_u, 0.0, 1.0))

        # 1. Dependency d
        d_next = self.dependency + ALPHA_D * daily_u * (1.0 - self.dependency) - DELTA_D * (1.0 - daily_u) * self.dependency
        self.dependency = float(np.clip(d_next, 0.0, 1.0))

        # 2. Calibration Error c
        avg_surprise = float(np.mean(self._surprises_today)) if self._surprises_today else 0.0
        c_next = self.calibration_error + BETA_C * self.dependency * (1.0 - self.calibration_error) - GAMMA_C * avg_surprise * self.calibration_error
        self.calibration_error = float(np.clip(c_next, 0.0, 1.0))

        # 3. Retained Ability a_r
        practice = 1.0 - daily_u
        a_next = self.retained_ability + RHO_AS * practice * (self.base_ability - self.retained_ability) - LAMBDA_A * self.dependency * daily_u * self.retained_ability
        self.retained_ability = float(np.clip(a_next, 10.0, self.base_ability))
