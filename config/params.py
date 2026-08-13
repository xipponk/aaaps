"""
config/params.py — ALL simulation parameters in one place (v0.3 Networked Redesign).

Never hardcode parameter values in agents.py or model.py.
Import from here instead.

Calibration Tags:
  # [K] Known / empirical literature anchor
  # [C] Calibrated to match domain baseline
  # [F] Fixed / exploratory simulation assumption (to be sensitivity-tested in GSA)
"""

from typing import Final

# =============================================================================
# Population & Sections
# =============================================================================

N_STUDENTS: Final[int] = 240              # [K] 6 sections x 40 students
N_SECTIONS: Final[int] = 6                # [K] CS curriculum sections
STUDENTS_PER_SECTION: Final[int] = 40     # [K] 40 per section

SES_RATIO: Final[dict[str, float]] = {
    'low': 0.30,   # [K] SIT KMUTT demographic baseline
    'mid': 0.50,   # [K]
    'high': 0.20,  # [K]
}

# =============================================================================
# Social Network Topology
# =============================================================================

SBM_P_WITHIN: Final[float] = 0.18         # [C] Intra-section connection probability
SBM_P_BETWEEN: Final[float] = 0.015       # [C] Inter-section connection probability
HOMOPHILY_SES: Final[float] = 0.20        # [K] Low-moderate excess same-SES tie prob per literature
HOMOPHILY_ABILITY: Final[float] = 0.25    # [K] Academic ability homophily
TARGET_K_BAR_RANGE: Final[tuple[float, float]] = (6.0, 10.0)  # [K] Target average degree 6-10
TIE_STRENGTH_BETA_A: Final[float] = 2.0   # [K] Beta(2,2) edge tie strength shape a
TIE_STRENGTH_BETA_B: Final[float] = 2.0   # [K] Beta(2,2) edge tie strength shape b
P_VISIBLE: Final[float] = 0.70            # [K] Noisy observation probability of neighbour AI use

# =============================================================================
# Ability Distribution
# =============================================================================

ABILITY_MEAN: Final[float] = 50.0          # [C]
ABILITY_STD: Final[float] = 15.0           # [C]
ABILITY_CLAMP: Final[tuple[float, float]] = (10.0, 100.0)  # [F]

# =============================================================================
# Self-Regulation & Traits
# =============================================================================

SR_ABILITY_WEIGHT: Final[float] = 0.45     # [K] Correlation with ability
SR_NOISE_WEIGHT: Final[float] = 0.55       # [K]
CONFORMITY_BETA_A: Final[float] = 2.0      # [F] Trait distribution for norm conformity ~ Beta(2,5)
CONFORMITY_BETA_B: Final[float] = 5.0      # [F]
PROSOCIALITY_BETA_A: Final[float] = 2.0   # [F] Trait distribution for prosociality ~ Beta(3,3)
PROSOCIALITY_BETA_B: Final[float] = 2.0   # [F]

# =============================================================================
# Usage Propensity Weights (ODD §7.3)
# =============================================================================

URGENCY_WEIGHT: Final[float] = 0.30       # [F] Weight of task urgency on base usage propensity
ASPIRATION_GAP_WEIGHT: Final[float] = 0.20 # [F] Weight of aspiration gap on base usage propensity

# =============================================================================
# W-Score (willingness to invest in academics)
# =============================================================================

W_SCORE_MIN: Final[float] = 0.2            # [F]
W_SCORE_MAX: Final[float] = 0.95           # [F]

# =============================================================================
# N Slots (concurrent task capacity)
# =============================================================================

N_SLOTS_DIVISOR: Final[float] = 20.0       # [F]
N_SLOTS_BASE: Final[int] = 2               # [F]

# =============================================================================
# Budget (THB/month, Bangkok scaled)
# =============================================================================

BUDGET_PARAMS: Final[dict[str, dict[str, float]]] = {
    'low':  {'mean': 4000.0,  'std': 700.0},    # [K] Re-anchored Bangkok-scaled
    'mid':  {'mean': 11000.0, 'std': 2000.0},   # [K]
    'high': {'mean': 27000.0, 'std': 4000.0},   # [K]
}

# =============================================================================
# AI Pricing, Quota & Access Sharing
# =============================================================================

AI_MONTHLY_COST: Final[dict[int, int]] = {
    0: 0,       # [K] no AI
    1: 0,       # [K] free tier
    2: 600,     # [K] mid tier (THB/month)
    3: 1800,    # [K] premium tier (THB/month)
}

AI_MONTHLY_QUOTA: Final[dict[int, int]] = {
    0: 0,       # [K]
    1: 100,     # [K]
    2: 300,     # [K]
    3: 800,     # [K]
}

SHAREABLE_SEATS: Final[dict[int, int]] = {
    0: 0,       # [K] ODD §5.4
    1: 0,       # [K]
    2: 1,       # [K] Mid tier shares 1 seat
    3: 2,       # [K] Premium tier shares 2 seats
}

# =============================================================================
# AI Speed & Quality Boosts
# =============================================================================

AI_SPEED_BOOST: Final[dict[int, int]] = {
    0: 0,       # [C]
    1: 5,       # [C]
    2: 15,      # [C]
    3: 35,      # [C]
}

AI_QUALITY_BOOST: Final[dict[int, float]] = {
    0: 0.0,     # [K] Anchored to Hedges g=0.533
    1: 0.05,    # [K]
    2: 0.20,    # [K]
    3: 0.50,    # [K]
}

# =============================================================================
# Coupled Dynamics Parameters (ODD §7.4 / §10 #5)
# =============================================================================

ALPHA_D: Final[float] = 0.012             # [C] Dependency growth rate when using AI
DELTA_D: Final[float] = 0.005             # [C] Dependency decay rate when not using AI
BETA_C: Final[float] = 0.010              # [C] Calibration error growth rate with dependency
GAMMA_C: Final[float] = 0.050             # [C] Calibration error recovery rate with surprise
RHO_AS: Final[float] = 0.30               # [K] Practice recovery rate (~0.30 per ODD §6)
LAMBDA_A: Final[float] = 0.008            # [C] Ability erosion rate per AI usage under dependency

# =============================================================================
# Interaction Parameters (ODD §7.7-7.9)
# =============================================================================

ETA: Final[float] = 0.08                  # [F] Norm diffusion rate
ETA_SELF: Final[float] = 0.03             # [F] Self-use legitimacy reinforcement
KAPPA: Final[float] = 0.10                # [F] Aspiration adjustment rate

# =============================================================================
# Processing & Score Formulas
# =============================================================================

PROCESSING_DIFFICULTY_FACTOR: Final[float] = 30.0  # [C]
SCORE_CAP: Final[float] = 100.0                   # [K]

# =============================================================================
# Tier Budget Fraction
# =============================================================================

TIER_BUDGET_FRACTION: Final[dict[str, float]] = {
    'low':  0.05,  # [C]
    'mid':  0.10,  # [C]
    'high': 0.15,  # [C]
}

# =============================================================================
# Quota System (Token Bucket)
# =============================================================================

DRAIN_RATE: Final[dict[int, int]] = {
    0: 0,   # [K] no AI
    1: 1,   # [K] free tier
    2: 3,   # [K] mid tier
    3: 8,   # [K] premium tier
}

TOPUP_COST: Final[dict[int, int]] = {
    2: 200,   # [K] THB per 100 units
    3: 180,   # [K] THB per 100 units
}

LOW_THRESHOLD: Final[float] = 50.0        # [C] trigger top-up when quota < this
TOPUP_AMOUNT: Final[float] = 100.0        # [C] units added per top-up

# =============================================================================
# Simulation Duration
# =============================================================================

STEPS_PER_SEMESTER: Final[int] = 120      # [K] 120 days per semester
N_SEMESTERS: Final[int] = 8               # [K] 4-year curriculum (8 semesters)
TOTAL_STEPS: Final[int] = STEPS_PER_SEMESTER * N_SEMESTERS  # 960

# =============================================================================
# Difficulty Scaling & Course Personalities
# =============================================================================

DIFFICULTY_MULTIPLIER_BASE: Final[float] = 1.0
DIFFICULTY_MULTIPLIER_INCREMENT: Final[float] = 0.08

COURSES: Final[list[dict]] = [
    {
        'id': 'C1',
        'name': 'Theory/Lecture',
        'difficulty_range': (7, 9),
        'ai_allowed': False,
        'assessment': 'exam',
        'lambda_tasks': 0.5 / 7,
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
        'ai_allowed': 'random_50pct',
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

LAMBDA_LIFE: Final[float] = 0.3 / 7  # avg life tasks per day
