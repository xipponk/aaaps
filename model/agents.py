"""
model/agents.py — StudentAgent (Mesa 2.x Agent subclass).

StudentAgent is the ONLY active agent in AAAPS.  Each instance represents one
undergraduate CS student who processes academic and life tasks across 8 semesters,
making AI tool adoption decisions that affect their performance and dependency.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import mesa

from config.params import (
    N_SLOTS_DIVISOR,
    N_SLOTS_BASE,
    W_SCORE_MIN,
    W_SCORE_MAX,
    ALPHA,
    PHASE2_THRESHOLD,
    PHASE3_THRESHOLD,
    EFFORT_REDUCTION_FACTOR,
    MISCALIBRATION_FACTOR,
    EROSION_FACTOR,
    TOPUP_COST,
    LOW_THRESHOLD,
    TOPUP_AMOUNT,
    AI_MONTHLY_COST,
    AI_MONTHLY_QUOTA,
    AI_QUALITY_BOOST,
    AI_SPEED_BOOST,
    PERCEIVED_SAFETY_FACTOR,
    PANIC_URGENCY_THRESHOLD,
    PANIC_SR_THRESHOLD,
    DRAIN_RATE,
    PROCESSING_DIFFICULTY_FACTOR,
    SCORE_CAP,
    TIER_BUDGET_FRACTION,
)

if TYPE_CHECKING:
    from model.tasks import TaskObject


class StudentAgent(mesa.Agent):
    """An undergraduate CS student in the AAAPS simulation.

    Static attributes (set at init, never change) capture SES, innate ability,
    and personality traits.  Dynamic attributes (updated every step) track the
    student's evolving AI relationship, task queue, and cumulative outcomes.
    """

    # ------------------------------------------------------------------
    # Static attributes (set at __init__, never change)
    # ------------------------------------------------------------------

    base_ability: float          # [10–100] drawn from Normal(50, 15)
    SES: str                     # 'low' | 'mid' | 'high'
    monthly_budget: float        # THB/month, f(SES)
    N_slots: int                 # [3–7] concurrent task capacity
    self_regulation: float       # [0–1] correlated with ability (r≈0.45)
    hobby_pull: float            # [0–1] independent draw
    w_score: float               # [0.2–0.95] inverse of hobby_pull

    # ------------------------------------------------------------------
    # Dynamic attributes (updated every step)
    # ------------------------------------------------------------------

    ai_tier: int                 # {0,1,2,3}: 0=none, 1=free, 2=mid, 3=premium
    ai_dependency: float         # [0–1] logistic growth
    dependency_phase: int        # {1,2,3}
    effective_ability: float     # ≤ base_ability always
    self_regulation_eff: float   # reduced by perceived AI safety
    quota_balance: float         # token bucket (AI usage units)
    budget_remaining: float      # THB, resets monthly
    slot_queue: list             # list[TaskObject], max len = N_slots
    score_total: float           # cumulative score
    deadline_miss_count: int     # cumulative deadline misses
    tasks_completed: int         # cumulative tasks completed

    # ------------------------------------------------------------------
    # Phase-effect caches (updated by _update_phase_effects)
    # ------------------------------------------------------------------

    effort_modifier: float               # Phase 1 multiplier on processing effort
    perceived_difficulty_multiplier: float  # Phase 2 multiplier on perceived difficulty

    # ------------------------------------------------------------------
    # Internal step-tracking flags
    # ------------------------------------------------------------------

    _ai_used_today: bool         # set True by _process_tasks when AI is actually used

    def __init__(
        self,
        unique_id: int,
        model: mesa.Model,
        base_ability: float,
        ses: str,
        monthly_budget: float,
        self_regulation: float,
        hobby_pull: float,
    ) -> None:
        """Initialise a StudentAgent with fixed traits and default dynamic state.

        Parameters
        ----------
        unique_id : int
            Unique numeric identifier within the simulation (Mesa 2.x requires
            this as the first argument to Agent).
        model : mesa.Model
            The parent AaapsModel instance.
        base_ability : float
            Innate academic ability [10–100].
        ses : str
            Socio-economic status: 'low', 'mid', or 'high'.
        monthly_budget : float
            Monthly disposable budget in THB.
        self_regulation : float
            Baseline self-regulation [0–1].
        hobby_pull : float
            Propensity to accept life tasks over academic work [0–1].
        """
        super().__init__(unique_id, model)

        # --- Static attributes ---
        self.base_ability = base_ability
        self.SES = ses
        self.monthly_budget = monthly_budget
        self.N_slots = int(self.base_ability / N_SLOTS_DIVISOR) + N_SLOTS_BASE
        self.self_regulation = self_regulation
        self.hobby_pull = hobby_pull
        self.w_score = max(W_SCORE_MIN, min(W_SCORE_MAX, 1.0 - hobby_pull))

        # --- Dynamic attributes (initial defaults) ---
        self.ai_tier = 0
        self.ai_dependency = 0.0
        self.dependency_phase = 1
        self.effective_ability = base_ability
        self.self_regulation_eff = self_regulation
        self.quota_balance = 0.0
        self.budget_remaining = monthly_budget
        self.slot_queue = []
        self.score_total = 0.0
        self.deadline_miss_count = 0
        self.tasks_completed = 0
        self.miss_by_course: dict[str, int] = {}  # per-course miss counter

        # --- Phase-effect caches ---
        self.effort_modifier = 1.0
        self.perceived_difficulty_multiplier = 1.0

        # --- Internal step-tracking ---
        self._ai_used_today = False
        self._quota_bankrupted_this_step = False

    # ==================================================================
    # Step pipeline (called every simulation day)
    # ==================================================================

    def step(self) -> None:
        """Execute the full daily step pipeline in order.

        Reads ``self._incoming_tasks`` (set by the model in Phase A) and
        forwards it to ``_decide_accept_tasks``.  When the attribute is
        missing or ``None`` the call is a no-op.
        """
        self._evaluate_slots()
        incoming = getattr(self, "_incoming_tasks", None)
        self._decide_accept_tasks(incoming)
        # _decide_ai_tier(task) is called per-task from _process_tasks
        self._process_tasks()
        self._complete_tasks()
        self._manage_quota()
        self._update_dependency()
        self._update_phase_effects()

    # ==================================================================
    # Step sub-methods (stubs — logic to be implemented)
    # ==================================================================

    def _evaluate_slots(self) -> bool:
        """Return True if there is at least one free slot in the task queue."""
        return len(self.slot_queue) < self.N_slots

    def _decide_accept_tasks(self, incoming_tasks: list[TaskObject] | None = None) -> None:
        """Accept or reject incoming academic and life tasks.

        Parameters
        ----------
        incoming_tasks : list[TaskObject] or None
            Tasks offered by the model this step.  ``None`` is treated as an
            empty list (keeps ``step()`` compatible before model wiring).
        """
        if incoming_tasks is None:
            incoming_tasks = []

        # ---- Compute urgency from current slot queue ----
        if self.slot_queue:
            urgency = max(
                (1.0 - t.deadline_remaining / t.deadline_total)
                for t in self.slot_queue
            )
        else:
            urgency = 0.0

        # self.self_regulation_eff is maintained by _update_phase_effects()
        # at the end of every step, so it reflects the previous day's state.

        # ---- Acceptance threshold ----
        acceptance_threshold = self.self_regulation_eff * (1.0 - urgency)

        # ---- Panic override: drop existing life tasks ----
        if urgency > PANIC_URGENCY_THRESHOLD and self.self_regulation_eff > PANIC_SR_THRESHOLD:
            self.slot_queue = [
                t for t in self.slot_queue if t.task_type != "life_task"
            ]

        # ---- Process incoming tasks ----
        for task in incoming_tasks:
            if not self._evaluate_slots():
                break  # no free slots left

            if task.task_type == "life_task":
                # Life tasks: accepted when hobby_pull beats the threshold
                if self.hobby_pull > acceptance_threshold:
                    self.slot_queue.append(task)
            else:
                # Academic tasks: always accepted while slots exist
                self.slot_queue.append(task)

    def _decide_ai_tier(self, task: TaskObject) -> int:
        """Choose the best affordable AI tier for a single task.

        Returns 0 immediately if ``task.ai_allowed`` is False.
        Otherwise evaluates tiers 3 → 1 (best-first) using a
        budget-fraction willingness-to-pay rule:

        1. ``AI_MONTHLY_COST[tier]`` must fit within this month's
           remaining budget.
        2. The cost must not exceed the agent's maximum willingness
           to spend:  ``TIER_BUDGET_FRACTION[SES] × monthly_budget
           × w_score``.

        The highest tier that satisfies both conditions wins.
        """
        if not task.ai_allowed:
            return 0

        # Maximum the agent is willing to spend on AI this month
        max_willing = (
            TIER_BUDGET_FRACTION[self.SES]
            * self.monthly_budget
            * self.w_score
        )

        best_tier = 0
        for tier in (3, 2, 1):  # best-first
            cost = AI_MONTHLY_COST[tier]

            # --- affordability check ---
            if cost > self.budget_remaining:
                continue

            # --- willingness-to-pay check ---
            if cost <= max_willing:
                best_tier = tier
                break  # highest affordable tier found

        # ---- Grant initial quota when upgrading to a new tier ----
        if best_tier != self.ai_tier and best_tier > 0:
            self.quota_balance += AI_MONTHLY_QUOTA[best_tier]

        return best_tier

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _expected_topup_cost(self, tier: int) -> float:
        """Estimate additional top-up cost for *tier* this month.

        Returns the cost of one top-up if the tier supports top-ups and
        the current quota balance is below half the tier's monthly
        allocation; otherwise 0.
        """
        if tier not in TOPUP_COST:
            return 0.0
        half_quota = AI_MONTHLY_QUOTA.get(tier, 0) / 2.0
        if self.quota_balance < half_quota:
            return float(TOPUP_COST[tier])
        return 0.0

    def _process_tasks(self) -> None:
        """Advance processing_progress for each task in the slot queue.

        For every task the agent: (1) chooses an AI tier via
        ``_decide_ai_tier``, (2) computes the effective processing speed,
        (3) advances progress by ``1 / processing_time``, (4) drains the
        token-bucket quota, and (5) records whether AI was actually used.

        The chosen tier is stored on the task as ``_ai_tier_used`` so that
        ``_complete_tasks`` can apply the correct quality multiplier.
        """
        for task in self.slot_queue:
            # ---- 1. Decide AI tier for this task ----
            tier = self._decide_ai_tier(task)
            self.ai_tier = tier
            task._ai_tier_used = tier  # type: ignore[attr-defined]

            # ---- 2. Effective intelligence & processing time ----
            effective_intelligence = (
                self.effective_ability
                + AI_SPEED_BOOST[tier] * int(task.ai_allowed)
            )
            processing_time = (
                task.difficulty * PROCESSING_DIFFICULTY_FACTOR
            ) / effective_intelligence

            progress_delta = 1.0 / processing_time

            # ---- 3. Advance progress & clamp ----
            task.processing_progress += progress_delta
            task.processing_progress = min(task.processing_progress, 1.0)

            # ---- 4. Drain quota ----
            if tier > 0 and task.ai_allowed:
                self.quota_balance -= DRAIN_RATE[tier] * progress_delta
                self._ai_used_today = True

                # Quota exhausted mid-stream → tier forced to 0 for remainder
                if self.quota_balance <= 0.0:
                    self.ai_tier = 0
                    self.quota_balance = 0.0
                    self._quota_bankrupted_this_step = True

    def _complete_tasks(self) -> None:
        """Score finished tasks and remove them from the slot queue.

        A task is finished when ``processing_progress >= 1.0``.

        * **On time** (``deadline_remaining > 0``):
            score = base_score × quality_multiplier (capped at SCORE_CAP).
        * **Missed deadline** (``deadline_remaining <= 0``):
            score = 0, ``deadline_miss_count`` incremented.

        In both cases ``tasks_completed`` is incremented.  The quality
        multiplier is computed from the tier that was actually used during
        processing (stored as ``_ai_tier_used`` by ``_process_tasks``).
        """
        completed: list = []  # TaskObject references to remove

        for task in self.slot_queue:
            if task.processing_progress < 1.0:
                continue

            completed.append(task)
            tier_used: int = getattr(task, "_ai_tier_used", 0)

            if task.deadline_remaining > 0:
                # ---- On-time completion ----
                ability_gate = self.effective_ability / 100.0
                quality_multiplier = 1.0 + (
                    AI_QUALITY_BOOST[tier_used] * ability_gate
                )
                score = task.base_score * quality_multiplier
                score = min(score, SCORE_CAP)
                self.score_total += score
            else:
                # ---- Missed deadline ----
                self.deadline_miss_count += 1
                cid = task.course_id
                self.miss_by_course[cid] = self.miss_by_course.get(cid, 0) + 1

            self.tasks_completed += 1

        # Remove completed tasks from the queue
        for task in completed:
            self.slot_queue.remove(task)

    def _manage_quota(self) -> None:
        """Top up AI quota when balance falls below the low threshold.

        Only tiers 2 (mid) and 3 (premium) support top-ups — free tier
        users and no-AI users are skipped.

        A top-up adds ``TOPUP_AMOUNT`` units and deducts the corresponding
        ``TOPUP_COST[ai_tier]`` THB from the monthly budget.

        If quota is fully depleted (≤ 0) the AI tier is forced to 0 to
        prevent further drain until the next top-up cycle.
        """
        # ---- Top-up: low balance, supported tier, sufficient budget ----
        if (
            self.quota_balance < LOW_THRESHOLD
            and self.ai_tier in TOPUP_COST
            and self.budget_remaining > TOPUP_COST[self.ai_tier]
        ):
            self.quota_balance += TOPUP_AMOUNT
            self.budget_remaining -= TOPUP_COST[self.ai_tier]

        # ---- Safety: depleted quota forces tier 0 ----
        if self.quota_balance <= 0.0:
            self.ai_tier = 0
            self.quota_balance = 0.0
            self._quota_bankrupted_this_step = True

        # --- Sanity checks ---
        assert self.quota_balance >= 0.0, (
            f"quota_balance={self.quota_balance} must be >= 0"
        )

    def _update_dependency(self) -> None:
        """Apply logistic growth to ai_dependency based on AI usage.

        Dependency grows only when the agent actively used AI today
        (ai_tier > 0 and at least one task was processed with AI).
        Growth follows:  delta = ALPHA * ai_tier * (1 - ai_dependency).

        The flag ``_ai_used_today`` is reset to False after every step
        so that days without AI usage produce no growth.
        """
        if self.ai_tier > 0 and self._ai_used_today:
            delta = ALPHA * self.ai_tier * (1.0 - self.ai_dependency)
            self.ai_dependency += delta

        # Clamp to valid range
        self.ai_dependency = max(0.0, min(self.ai_dependency, 1.0))

        # Reset for the next step
        self._ai_used_today = False

        # --- Sanity checks ---
        assert 0.0 <= self.ai_dependency <= 1.0, (
            f"ai_dependency={self.ai_dependency} out of [0, 1]"
        )

    def _update_phase_effects(self) -> None:
        """Apply Phase 1/2/3 effects based on current ai_dependency.

        Effects are cumulative — a Phase‑3 agent still experiences Phase‑1
        effort reduction and Phase‑2 miscalibration.

        Phase 1 (dependency < 0.4) — Effort Reduction
            effort_modifier = 1 - EFFORT_REDUCTION_FACTOR * dependency

        Phase 2 (0.4 ≤ dependency < 0.7) — Miscalibration
            perceived_difficulty *= 1 - MISCALIBRATION_FACTOR * (dependency - 0.4)

        Phase 3 (dependency ≥ 0.7) — Capability Erosion
            erosion = EROSION_FACTOR * (dependency - 0.7)
            effective_ability = base_ability * (1 - erosion)
        """
        # ---- Classify phase ----
        if self.ai_dependency < PHASE2_THRESHOLD:
            self.dependency_phase = 1
        elif self.ai_dependency < PHASE3_THRESHOLD:
            self.dependency_phase = 2
        else:
            self.dependency_phase = 3

        # ---- Phase 1: Effort Reduction (always active once dependency > 0) ----
        self.effort_modifier = 1.0 - (EFFORT_REDUCTION_FACTOR * self.ai_dependency)

        # ---- Phase 2: Miscalibration ----
        if self.dependency_phase >= 2:
            excess = self.ai_dependency - PHASE2_THRESHOLD
            self.perceived_difficulty_multiplier = 1.0 - (MISCALIBRATION_FACTOR * excess)
        else:
            self.perceived_difficulty_multiplier = 1.0

        # ---- Phase 3: Capability Erosion ----
        if self.dependency_phase == 3:
            erosion = EROSION_FACTOR * (self.ai_dependency - PHASE3_THRESHOLD)
            self.effective_ability = self.base_ability * (1.0 - erosion)
        else:
            self.effective_ability = self.base_ability

        # effective_ability must NEVER exceed base_ability
        self.effective_ability = min(self.effective_ability, self.base_ability)

        # ---- Self-regulation erosion (continuous, not phase-gated) ----
        perceived_safety = self.ai_dependency * (self.ai_tier / 3.0)
        self.self_regulation_eff = self.self_regulation * (
            1.0 - PERCEIVED_SAFETY_FACTOR * perceived_safety
        )

        # --- Sanity checks ---
        assert self.effective_ability <= self.base_ability, (
            f"effective_ability={self.effective_ability} > "
            f"base_ability={self.base_ability}"
        )
        assert self.effective_ability > 0.0, (
            f"effective_ability={self.effective_ability} must be positive"
        )
