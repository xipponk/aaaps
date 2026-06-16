"""
model/model.py — AaapsModel (Mesa 2.x Model subclass).

The world container for the AAAPS simulation.  Creates 60 StudentAgents,
generates course and life tasks each step, applies scenario policies, and
collects data via Mesa's DataCollector.
"""

from __future__ import annotations

import mesa
import numpy as np

from config.params import (
    N_STUDENTS,
    SES_RATIO,
    ABILITY_MEAN,
    ABILITY_STD,
    ABILITY_CLAMP,
    SR_ABILITY_WEIGHT,
    SR_NOISE_WEIGHT,
    BUDGET_PARAMS,
    AI_MONTHLY_QUOTA,
    COURSES,
    LAMBDA_LIFE,
    STEPS_PER_SEMESTER,
    N_SEMESTERS,
    TOTAL_STEPS,
    DIFFICULTY_MULTIPLIER_BASE,
    DIFFICULTY_MULTIPLIER_INCREMENT,
)
from model.agents import StudentAgent
from model.tasks import TaskObject

# ---------------------------------------------------------------------------
# Module-level helper — Gini coefficient
# ---------------------------------------------------------------------------


def compute_gini(model: AaapsModel) -> float:
    """Gini coefficient of score_total across all agents.

    Returns 0.0 when there are no agents or all scores are zero.
    """
    scores = sorted([a.score_total for a in model.agents])
    n = len(scores)
    total = sum(scores)
    if n == 0 or total == 0.0:
        return 0.0
    cumsum = sum((i + 1) * s for i, s in enumerate(scores))
    return (2.0 * cumsum) / (n * total) - (n + 1.0) / n


# ===========================================================================
# AaapsModel
# ===========================================================================


class AaapsModel(mesa.Model):
    """Agent-Based Model of 60 undergraduate CS students over 8 semesters.

    Parameters
    ----------
    n_students : int
        Number of students (typically 60).
    scenario : str
        One of 'baseline', 'free_market', 'universal_ai', 'subsidy', or
        'mixed_policy'.
    seed : int | None
        Random seed for reproducibility.
    """

    # ------------------------------------------------------------------
    # Public attributes (set by __init__)
    # ------------------------------------------------------------------

    n_students: int
    scenario: str
    current_semester: int
    current_step: int
    quota_bankruptcy_count: int
    total_tasks_generated: int

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def __init__(
        self,
        n_students: int = N_STUDENTS,
        scenario: str = "free_market",
        seed: int | None = None,
    ) -> None:
        super().__init__(seed=seed)

        # ---- Numpy RNG (seeded from model seed for Poisson draws) ----
        self._np_random = np.random.RandomState(seed)

        # ---- Scenario & counters ----
        self.n_students = n_students
        self.scenario = scenario
        self.current_semester = 1
        self.current_step = 0
        self.quota_bankruptcy_count = 0
        self.total_tasks_generated = 0
        self._next_task_id = 0

        # ---- Create student population ----
        self._create_students()

        # ---- Data collection ----
        self.datacollector = mesa.DataCollector(
            agent_reporters={
                "score_total": lambda a: a.score_total,
                "ai_dependency": lambda a: a.ai_dependency,
                "dependency_phase": lambda a: a.dependency_phase,
                "ai_tier": lambda a: a.ai_tier,
                "quota_balance": lambda a: a.quota_balance,
                "effective_ability": lambda a: a.effective_ability,
                "slots_used": lambda a: len(a.slot_queue),
                "deadline_miss_count": lambda a: a.deadline_miss_count,
                "SES": lambda a: a.SES,
                "base_ability": lambda a: a.base_ability,
                "semester": lambda a: a.model.current_semester,
            },
            model_reporters={
                "mean_score": lambda m: float(
                    np.mean([a.score_total for a in m.agents])
                ),
                "gini_score": compute_gini,
                "ai_adoption_rate": lambda m: (
                    sum(1 for a in m.agents if a.ai_tier > 0) / m.n_students
                ),
                "quota_bankruptcies": lambda m: m.quota_bankruptcy_count,
                "deadline_miss_rate": lambda m: (
                    sum(a.deadline_miss_count for a in m.agents)
                    / max(m.total_tasks_generated, 1)
                ),
            },
        )

    # ------------------------------------------------------------------
    # Student factory
    # ------------------------------------------------------------------

    def _create_students(self) -> None:
        """Create ``n_students`` agents with traits drawn from distributions.

        Uses ``self.random`` (Mesa's seeded RNG) for every random draw.
        """
        # ---- SES assignment (stratified: 30 % low, 50 % mid, 20 % high) ----
        n_low = round(self.n_students * SES_RATIO["low"])
        n_mid = round(self.n_students * SES_RATIO["mid"])
        n_high = self.n_students - n_low - n_mid
        ses_labels = (
            ["low"] * n_low + ["mid"] * n_mid + ["high"] * n_high
        )
        self.random.shuffle(ses_labels)

        for unique_id, ses in enumerate(ses_labels):
            # ---- Base ability: Normal(50, 15) clamped to [10, 100] ----
            base_ability = float(
                self.random.normalvariate(ABILITY_MEAN, ABILITY_STD)
            )
            base_ability = max(ABILITY_CLAMP[0], min(base_ability, ABILITY_CLAMP[1]))

            # ---- Monthly budget: Normal(mean, std) per SES, clamped >= 0 ----
            bp = BUDGET_PARAMS[ses]
            monthly_budget = float(self.random.normalvariate(bp["mean"], bp["std"]))
            monthly_budget = max(monthly_budget, 0.0)

            # ---- Self-regulation: correlated with ability (r ≈ 0.45) ----
            z_ability = (base_ability - ABILITY_MEAN) / ABILITY_STD
            z_noise = float(self.random.normalvariate(0.0, 1.0))
            sr_raw = 0.5 + 0.15 * (
                SR_ABILITY_WEIGHT * z_ability + SR_NOISE_WEIGHT * z_noise
            )
            self_regulation = max(0.0, min(sr_raw, 1.0))

            # ---- Hobby pull: Uniform [0, 1], independent ----
            hobby_pull = float(self.random.uniform(0.0, 1.0))

            # ---- Create agent (auto-registers with self) ----
            StudentAgent(
                unique_id=unique_id,
                model=self,
                base_ability=base_ability,
                ses=ses,
                monthly_budget=monthly_budget,
                self_regulation=self_regulation,
                hobby_pull=hobby_pull,
            )

        # ---- Apply scenario-level initial overrides ----
        if self.scenario == "baseline":
            for agent in self.agents:
                agent.ai_tier = 0
                agent.quota_balance = 0.0

    # ==================================================================
    # Step
    # ==================================================================

    def step(self) -> None:
        """Execute one simulation day (four-phase pipeline).

        Phase A — Model-level: decrement deadlines, generate new tasks,
            apply difficulty scaling, and stage tasks on each agent.
        Phase B — Agent-level: ``self.agents.shuffle().do("step")``.
        Phase C — Bookkeeping: advance ``current_step`` and
            ``current_semester``, apply scenario effects, count
            bankruptcies.
        Phase D — Data: ``self.datacollector.collect(self)``.
        """
        # ---- Phase A: Task generation & deadline maintenance ----
        semester_mult = self._semester_difficulty_multiplier()

        for agent in self.agents:
            # Decrement deadlines on all queued tasks
            for task in agent.slot_queue:
                task.deadline_remaining -= 1

            # Generate new tasks for this student
            incoming = self._generate_tasks(agent, semester_mult)
            agent._incoming_tasks = incoming  # type: ignore[attr-defined]

        # ---- Phase B: Agent step (random order, Mesa 2.x) ----
        self.agents.shuffle().do("step")

        # ---- Phase C: Bookkeeping ----
        self.current_step += 1
        self._steps = self.current_step  # Mesa DataCollector keys on model._steps
        if self.current_step > 0 and self.current_step % STEPS_PER_SEMESTER == 0:
            self.current_semester += 1

        # ---- Monthly cycle (every 30 days) ----
        if self.current_step % 30 == 0:
            for agent in self.agents:
                agent.budget_remaining = agent.monthly_budget
                if agent.ai_tier > 0:
                    agent.quota_balance += AI_MONTHLY_QUOTA[agent.ai_tier]

        self._apply_scenario_effects()

        # Count quota bankruptcies that occurred this step
        for agent in self.agents:
            if agent._quota_bankrupted_this_step:  # type: ignore[attr-defined]
                self.quota_bankruptcy_count += 1
                agent._quota_bankrupted_this_step = False  # type: ignore[attr-defined]

        # ---- Phase D: Collect data ----
        self.datacollector.collect(self)

    # ==================================================================
    # Task generation
    # ==================================================================

    def _generate_tasks(
        self,
        student: StudentAgent,
        semester_multiplier: float,
    ) -> list[TaskObject]:
        """Generate new academic and life tasks for one student.

        Parameters
        ----------
        student : StudentAgent
            The student to generate tasks for.
        semester_multiplier : float
            Difficulty scaling for the current semester.

        Returns
        -------
        list[TaskObject]
            Freshly created tasks ready for acceptance decisions.
        """
        tasks: list[TaskObject] = []

        for course in COURSES:
            # ---- Poisson draw for this course ----
            n_tasks = self._np_random.poisson(course["lambda_tasks"])
            if n_tasks <= 0:
                continue

            for _ in range(n_tasks):
                # ---- Difficulty: uniform in course range × semester ----
                d_min, d_max = course["difficulty_range"]
                difficulty = self.random.uniform(d_min, d_max) * semester_multiplier

                # ---- AI allowed (respect scenario overrides) ----
                ai_allowed = self._resolve_ai_allowed(course)

                # ---- Task type ----
                task_type = (
                    "quiz" if course["assessment"] == "exam"
                    else "academic_assignment"
                )

                deadline = course["deadline_days"]

                tasks.append(
                    TaskObject(
                        task_id=self._next_task_id,
                        task_type=task_type,
                        difficulty=difficulty,
                        base_score=difficulty * 10.0,
                        deadline_remaining=deadline,
                        deadline_total=deadline,
                        ai_allowed=ai_allowed,
                        course_id=course["id"],
                    )
                )
                self._next_task_id += 1

        # ---- Life tasks ----
        n_life = self._np_random.poisson(LAMBDA_LIFE)
        for _ in range(n_life):
            life_diff = self.random.uniform(1.0, 4.0)
            life_deadline = self.random.randint(3, 10)
            tasks.append(
                TaskObject(
                    task_id=self._next_task_id,
                    task_type="life_task",
                    difficulty=life_diff,
                    base_score=life_diff * 10.0,
                    deadline_remaining=life_deadline,
                    deadline_total=life_deadline,
                    ai_allowed=False,
                    course_id="LIFE",
                )
            )
            self._next_task_id += 1

        self.total_tasks_generated += len(tasks)
        return tasks

    # ------------------------------------------------------------------
    # Scenario helpers
    # ------------------------------------------------------------------

    def _resolve_ai_allowed(self, course: dict) -> bool:
        """Return whether AI is allowed for *course* under the current scenario."""
        if self.scenario == "baseline":
            return False

        if self.scenario == "mixed_policy" and course["id"] in ("C1", "C3"):
            return False

        raw = course["ai_allowed"]
        if raw == "random_50pct":
            return self.random.random() < 0.5
        return bool(raw)

    def _apply_scenario_effects(self) -> None:
        """Apply per-agent scenario policies after each step."""
        if self.scenario == "baseline":
            for agent in self.agents:
                agent.ai_tier = 0
                agent.quota_balance = 0.0

        elif self.scenario == "universal_ai":
            # Tier 3 free for semesters 1–4; removed thereafter
            if self.current_semester <= 4:
                for agent in self.agents:
                    agent.ai_tier = 3
            # After semester 4: agents revert to their own decisions
            # (their _decide_ai_tier will handle it in future steps)

        elif self.scenario == "subsidy":
            for agent in self.agents:
                if agent.SES == "low":
                    # Ensure minimum tier 2 (free for low-SES)
                    if agent.ai_tier < 2:
                        agent.ai_tier = 2

        # free_market and mixed_policy: no per-agent override

    def _semester_difficulty_multiplier(self) -> float:
        """Return the difficulty multiplier for the current semester.

        Semester 1 = 1.0×, semester 8 = 1.56×.
        """
        return (
            DIFFICULTY_MULTIPLIER_BASE
            + (self.current_semester - 1) * DIFFICULTY_MULTIPLIER_INCREMENT
        )
