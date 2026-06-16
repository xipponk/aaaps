# AAAPS — AI-Augmented Academic Performance Simulation

An Agent-Based Model (ABM) simulating 60 undergraduate CS students over 8 semesters to investigate how differential AI tool access affects academic inequality, performance distributions, and dependency formation.

---

## Research Context

As generative AI tools become ubiquitous in higher education, a critical question arises: **does AI narrow or widen the achievement gap?** This simulation models students with varying socioeconomic status (SES) and innate ability who make rational decisions about adopting AI tools — trading off cost, quality gains, and the accumulating cognitive cost of dependency.

The model tests five policy scenarios (baseline, free-market, universal provision, targeted subsidy, and mixed/course-level bans) to compare outcomes on score distributions, inequality (Gini), and deadline performance.

---

## Key Findings

1. **AI Paradox** — AI users score 3–4% higher on completed tasks but miss 25% more deadlines than non-users. Dependency erosion (Phase 1 effort reduction + Phase 3 capability decay) slows task processing more than the AI speed boost accelerates it.

2. **SES Stratification** — Under a budget-fraction willingness-to-pay rule, high-SES students adopt premium AI (tier 3, 58%), mid-SES students split between free and mid-tier, and low-SES students remain on the free tier. The tier gradient mirrors real-world digital divides.

3. **C3 is the Universal Bottleneck** — 90%+ of all deadline misses occur in the Lab/Practical course (C3: 7-day deadline, difficulty 4–6). No other course generates meaningful deadline pressure.

4. **Universal AI ≈ Free Market** — Providing every student with premium AI for the first four semesters then removing it (universal provision) produces final outcomes indistinguishable from letting the market decide. Students revert to their natural adoption level once the subsidy ends.

5. **Course-Level AI Bans Backfire** — The mixed-policy scenario (banning AI in theory and lab courses) produces the worst outcomes: highest miss rate (1.30%, +63% vs baseline) and the smallest score benefit. Restricting AI where students need it most (C3 labs) increases failure without reducing dependency.

---

## Model Architecture

### Agents

- **60 StudentAgents** — each with static traits (base ability, SES, monthly budget, self-regulation, hobby pull) and dynamic state (AI tier, dependency level, quota balance, task queue, cumulative scores and misses).
- **TaskObject** — passive dataclass representing academic assignments, quizzes, or life tasks with difficulty, deadlines, and AI-permission flags.

### Mechanics

| Mechanic | Description |
|---|---|
| **Task Generation** | Poisson process per course per student per day; 5 courses + life tasks |
| **AI Tier Decision** | Budget-fraction willingness-to-pay: tier cost must be ≤ `TIER_BUDGET_FRACTION[SES] × monthly_budget × w_score` |
| **Processing Time** | `(difficulty × 30) / (effective_ability + AI_SPEED_BOOST[tier])` |
| **Score** | `base_score × (1 + AI_QUALITY_BOOST[tier] × ability_gate)`, capped at 100 |
| **Dependency** | Logistic growth: `Δ = ALPHA × tier × (1 − dep)`, ALPHA = 0.008/day |
| **Phase Effects** | Phase 1 (effort reduction), Phase 2 (miscalibration), Phase 3 (capability erosion) |
| **Quota System** | Token bucket per tier; drain rate scales with tier; top-ups cost THB |

### Scenarios

| Scenario | Description |
|---|---|
| `baseline` | No AI available (control group) |
| `free_market` | Students purchase AI based on SES-dependent willingness to pay |
| `universal_ai` | All students given premium AI free for semesters 1–4, then removed |
| `subsidy` | Only low-SES students given mid-tier AI free |
| `mixed_policy` | C1 (Theory) and C3 (Lab) ban AI; other courses allow |

---

## Installation

Requires Python 3.11+.

```bash
# Clone
git clone <repo-url>
cd aaaps

# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

---

## Usage

### Run a single scenario

```python
from model.model import AaapsModel

model = AaapsModel(n_students=60, scenario="free_market", seed=42)
for _ in range(960):          # 8 semesters × 120 days
    model.step()

# Access results
df = model.datacollector.get_agent_vars_dataframe()
print(df.xs(960, level="Step")["score_total"].describe())
```

### Run all 5 scenarios

```python
from model.model import AaapsModel

for scenario in ["baseline", "free_market", "universal_ai", "subsidy", "mixed_policy"]:
    model = AaapsModel(n_students=60, scenario=scenario, seed=42)
    for _ in range(960):
        model.step()
    # Save or analyse results...
```

Jupyter notebooks for single-run debugging, scenario comparison, and sensitivity analysis are in `notebooks/`.

---

## Project Structure

```
aaaps/
├── README.md
├── CLAUDE.md                  ← Agent instruction file
├── requirements.txt
├── .gitignore
│
├── config/
│   ├── __init__.py
│   └── params.py              ← ALL parameters (no hardcoding elsewhere)
│
├── model/
│   ├── __init__.py
│   ├── model.py               ← AaapsModel (Mesa 2.x Model subclass)
│   ├── agents.py              ← StudentAgent (Mesa 2.x Agent subclass)
│   └── tasks.py               ← TaskObject (passive dataclass)
│
├── scenarios/                 ← Scenario-specific logic (future use)
├── analysis/                  ← Metrics & plotting functions
├── notebooks/                 ← Jupyter notebooks for exploration
│
└── outputs/                   ← Generated CSVs and figures (git-ignored)
    ├── raw/
    └── figures/
```

---

## Citation

```bibtex
@software{aaaps2026,
  author    = {Triyason, Tuul},
  title     = {AAAPS: AI-Augmented Academic Performance Simulation},
  year      = {2026},
  publisher = {King Mongkut's University of Technology Thonburi},
  url       = {<repo-url>},
}
```

---

## Researcher

**Asst. Prof. Dr. Tuul Triyason**  
School of Information Technology  
King Mongkut's University of Technology Thonburi (KMUTT)  
Bangkok, Thailand
