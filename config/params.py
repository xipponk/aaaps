"""
config/params.py — ALL simulation parameters in one place.

Never hardcode parameter values in agents.py or model.py.
Import from here instead.

Follows CLAUDE.md sections:
  - Initialization Parameters
  - Core Formulas
  - Course Personalities
  - Dependency Phase Effects
  - Quota System
  - AI Tier Upgrade
  - Self-Regulation & Life Task Decision
  - Data Collection
"""

from typing import Final

# =============================================================================
# Population
# =============================================================================

N_STUDENTS: Final[int] = 60

SES_RATIO: Final[dict[str, float]] = {
    'low': 0.30,
    'mid': 0.50,
    'high': 0.20,
}

# =============================================================================
# Ability Distribution
# =============================================================================

ABILITY_MEAN: Final[float] = 50.0
ABILITY_STD: Final[float] = 15.0
ABILITY_CLAMP: Final[tuple[float, float]] = (10.0, 100.0)

# =============================================================================
# Self-Regulation
# =============================================================================

SR_ABILITY_WEIGHT: Final[float] = 0.45
SR_NOISE_WEIGHT: Final[float] = 0.55

# =============================================================================
# W-Score (willingness to invest in academics, inverse of hobby_pull)
# =============================================================================

W_SCORE_MIN: Final[float] = 0.2
W_SCORE_MAX: Final[float] = 0.95

# =============================================================================
# N Slots (concurrent task capacity)
# =============================================================================

N_SLOTS_DIVISOR: Final[float] = 20.0
N_SLOTS_BASE: Final[int] = 2

# =============================================================================
# Budget (THB/month)
# =============================================================================

BUDGET_PARAMS: Final[dict[str, dict[str, float]]] = {
    'low':  {'mean': 3000.0,  'std': 500.0},
    'mid':  {'mean': 8000.0,  'std': 1500.0},
    'high': {'mean': 20000.0, 'std': 3000.0},
}

# =============================================================================
# AI Pricing & Quota
# =============================================================================

AI_MONTHLY_COST: Final[dict[int, int]] = {
    0: 0,       # no AI
    1: 0,       # free tier
    2: 600,     # mid tier (THB/month)
    3: 1800,    # premium tier (THB/month)
}

AI_MONTHLY_QUOTA: Final[dict[int, int]] = {
    0: 0,
    1: 100,
    2: 300,
    3: 800,
}

# =============================================================================
# AI Speed Boost (added to effective_ability when ai_allowed is True)
# =============================================================================

AI_SPEED_BOOST: Final[dict[int, int]] = {
    0: 0,
    1: 5,
    2: 15,
    3: 35,
}

# =============================================================================
# AI Quality Boost (multiplier on score)
# =============================================================================

AI_QUALITY_BOOST: Final[dict[int, float]] = {
    0: 0.0,
    1: 0.05,
    2: 0.20,
    3: 0.50,
}

# =============================================================================
# Processing Time Formula
# =============================================================================

PROCESSING_DIFFICULTY_FACTOR: Final[float] = 30.0

# =============================================================================
# Score Formula
# =============================================================================

SCORE_CAP: Final[float] = 100.0

# =============================================================================
# AI Dependency (Logistic Growth)
# =============================================================================

ALPHA: Final[float] = 0.008  # growth rate per day (slower dependency accumulation)

# =============================================================================
# Tier Budget Fraction (willingness-to-pay by SES)
# =============================================================================

TIER_BUDGET_FRACTION: Final[dict[str, float]] = {
    'low':  0.05,
    'mid':  0.10,
    'high': 0.15,
}

# =============================================================================
# Dependency Phase Thresholds
# =============================================================================

PHASE2_THRESHOLD: Final[float] = 0.4   # ai_dependency >= 0.4 → Phase 2
PHASE3_THRESHOLD: Final[float] = 0.7   # ai_dependency >= 0.7 → Phase 3

# Phase 1 (dependency < 0.4): Effort Reduction
EFFORT_REDUCTION_FACTOR: Final[float] = 0.3

# Phase 2 (0.4 <= dependency < 0.7): Miscalibration
MISCALIBRATION_FACTOR: Final[float] = 0.4

# Phase 3 (dependency >= 0.7): Capability Erosion
EROSION_FACTOR: Final[float] = 0.5

# =============================================================================
# Self-Regulation & Life Task Decision
# =============================================================================

PERCEIVED_SAFETY_FACTOR: Final[float] = 0.3
PANIC_URGENCY_THRESHOLD: Final[float] = 0.85
PANIC_SR_THRESHOLD: Final[float] = 0.6

# =============================================================================
# AI Tier Upgrade Decision
# =============================================================================

BUDGET_SENSITIVITY: Final[dict[str, float]] = {
    'low': 0.5,
    'mid': 1.0,
    'high': 2.0,
}

# =============================================================================
# Quota System (Token Bucket)
# =============================================================================

DRAIN_RATE: Final[dict[int, int]] = {
    0: 0,   # no AI
    1: 1,   # free tier
    2: 3,   # mid tier
    3: 8,   # premium tier
}

TOPUP_COST: Final[dict[int, int]] = {
    2: 200,   # THB per 100 units (mid tier)
    3: 180,   # THB per 100 units (premium tier)
}

LOW_THRESHOLD: Final[float] = 50.0    # trigger top-up when quota < this
TOPUP_AMOUNT: Final[float] = 100.0     # units added per top-up

# =============================================================================
# Simulation Duration
# =============================================================================

STEPS_PER_SEMESTER: Final[int] = 120
N_SEMESTERS: Final[int] = 8
TOTAL_STEPS: Final[int] = STEPS_PER_SEMESTER * N_SEMESTERS  # 960

# =============================================================================
# Difficulty Scaling
# =============================================================================

DIFFICULTY_MULTIPLIER_BASE: Final[float] = 1.0
DIFFICULTY_MULTIPLIER_INCREMENT: Final[float] = 0.08

# =============================================================================
# Course Personalities (5 per semester)
# =============================================================================

COURSES: Final[list[dict]] = [
    {
        'id': 'C1',
        'name': 'Theory/Lecture',
        'difficulty_range': (7, 9),
        'ai_allowed': False,
        'assessment': 'exam',
        'lambda_tasks': 0.5 / 7,      # avg tasks per day
        'deadline_days': 30,
    },
    {
        'id': 'C2',
        'name': 'Programming Project',
        'difficulty_range': (6, 8),
        'ai_allowed': True,
        'assessment': 'project',
        'lambda_tasks': 1.0 / 7,
        'deadline_days': 14,
    },
    {
        'id': 'C3',
        'name': 'Lab/Practical',
        'difficulty_range': (4, 6),
        'ai_allowed': 'random_50pct',   # per-task random: True/False with P=0.5
        'assessment': 'lab',
        'lambda_tasks': 2.0 / 7,
        'deadline_days': 7,
    },
    {
        'id': 'C4',
        'name': 'Easy Elective',
        'difficulty_range': (2, 4),
        'ai_allowed': True,
        'assessment': 'mixed',
        'lambda_tasks': 1.5 / 7,
        'deadline_days': 10,
    },
    {
        'id': 'C5',
        'name': 'Seminar/Research',
        'difficulty_range': (8, 10),
        'ai_allowed': True,
        'assessment': 'report',
        'lambda_tasks': 0.3 / 7,
        'deadline_days': 45,
    },
]

# =============================================================================
# Life Task Generation
# =============================================================================

LAMBDA_LIFE: Final[float] = 0.3 / 7  # avg life tasks per day
