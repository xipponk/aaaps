# ODD Protocol — AAAPS v0.3

**Model:** AAAPS (AI-Augmented Academic Performance Simulation), v0.3 networked redesign
**Author:** Tuul Triyason, School of Information Technology, KMUTT
**Companion to:** Triyason (2026), "Equal Access, Unequal Benefit: A Networked Agent-Based
Model of AI Tool Access in Higher Education" (JASSS submission)

This document follows the ODD protocol (Grimm et al. 2020, *JASSS* 23(2):7). It is the
specification of record for the v0.3 model and supersedes the v0.2 description. The
executable implementation lives in `config/`, `model/`, `scenarios/`, and `analysis/`;
where this document and the code differ, the code is authoritative.

---

## 1. Purpose and Patterns

### 1.1 Purpose

The model examines how access to generative AI tools interacts with individual cognitive
differences, socioeconomic stratification, and peer social networks to shape student
learning trajectories, academic performance, and capability retention over a four-year
undergraduate program. Its central question is whether equal technological access produces
equal academic benefit.

### 1.2 Emergent patterns the model is designed to reproduce

1. **S-shaped adoption curves** driven by peer social contagion and normative legitimacy
   diffusion.
2. **Emergent access clustering** through informal peer resource sharing that partially
   decouples effective tool access from individual socioeconomic constraints.
3. **Heterogeneous dependency trajectories** — dependency and miscalibration paths diverge
   across student ability and self-regulation profiles rather than moving in lockstep.
4. **The equalization illusion** — equal provision temporarily compresses grade inequality
   while masking latent dependency and capability erosion.

These patterns are emergent outputs, not imposed: they arise from decentralized agent
interactions and the coupled cognitive dynamics described below.

---

## 2. Entities, State Variables, and Scales

### 2.1 Entities

Three entity types: **student agents**, a **social network**, and **academic sections**.

#### Student agents (N = 240)

Each agent is an undergraduate computer-science student progressing through an
eight-semester degree.

**Static attributes (set at initialization, never change):**

| Attribute | Symbol | Distribution / value |
|---|---|---|
| Baseline ability | a_base | N(50, 15), clamped to [10, 100] |
| Socioeconomic status | SES | categorical {low, mid, high}, ratio 0.30 / 0.50 / 0.20 |
| Monthly budget | B | low N(4000,700), mid N(11000,2000), high N(27000,4000) THB |
| Self-regulation | s | generated with ability weight 0.45 and noise weight 0.55 (positive ability correlation) |
| Non-academic time preference ("hobby pull") | h | U(0,1) |
| Conformity trait | conf | Beta(2, 5) |
| Prosociality trait | pros | Beta(2, 2) |
| Willingness to invest in academics | w_score | U(0.2, 0.95) |
| Section membership | section_id | 0..5, 40 per section |

**Dynamic state variables:**

| Variable | Symbol | Range | Meaning |
|---|---|---|---|
| Owned subscription tier | tier | {0,1,2,3} | tier purchased with own budget |
| Effective access tier | tier_eff | {0,1,2,3} | tier after peer borrowing |
| Monthly quota | quota | ≥0 | token bucket of AI usage units |
| AI dependency | d | [0,1] | accumulated reliance on AI |
| Metacognitive calibration error | c | [0,1] | gap between perceived and actual ability |
| Retained ability | a_r | [0, a_base] | independent capability remaining under dependency |
| Perceived legitimacy of AI use | L | [0,1] | normative acceptance of AI |
| Academic score aspiration | T | [0,100] | internal target |
| Borrowing link | borrowing_from | agent id or None | single peer provider |
| Shared seats lent | seats_lent | ≥0 | seats currently lent out |

#### Social network

A static, undirected, weighted graph G = (V, E). Edge weights w_ij ~ Beta(2,2) represent
tie strength. Topology is fixed after initialization (see §5.2).

#### Academic sections

Six sections of 40 students each. Sections are the imposed collective that constrains
within-class peer contact and define the Stochastic Block Model blocks.

### 2.2 Scales

- **Time**: one simulated day per step; 120 days per semester; 8 semesters; **960 steps
  total** (a four-year curriculum).
- **Population**: 240 agents.
- **Space**: none; agents interact through the social network, not a spatial grid.

---

## 3. Process Overview and Scheduling

Each daily step runs five sequential phases:

**Phase A — Environment and quota update.** Deadlines advance and pending coursework tasks
arrive. Every 30 steps (monthly cycle), budgets refresh, quotas reset, and each agent
reconsiders its subscription tier (see §7.5).

**Phase B — Synchronous social interaction.** Computed on a frozen snapshot of step t−1
state, so all agents observe the same information:
1. *Legitimacy diffusion* — L_i updates toward the tie-strength-weighted observed AI use of
   neighbours (§7.7).
2. *Aspiration adjustment* — T_i updates toward the tie-strength-weighted average peer
   performance (§7.8).
3. *Access-sharing market* — high-tier suppliers offer seats to eligible demanders (§7.6).

**Phase C — Asynchronous individual task processing.** Agents act in randomized order,
selecting daily effort and usage intensity u(t) and processing pending tasks with effective
capability I_eff (§7.1–7.2).

**Phase D — Coupled dynamic updates.** Dependency d, calibration error c, and retained
ability a_r update per the coupled difference equations (§7.3–7.4).

**Phase E — Data collection.** System- and agent-level variables are recorded.

The hybrid schedule (synchronous social phase, asynchronous individual phase) is a core
design element: social influence is global within a step, while task execution order is
randomized to avoid ordering artefacts.

---

## 4. Design Concepts

**Basic principles.** The model extends an individual-level account of AI adoption and
cognitive offloading with explicit peer interaction, treating students as embedded in
social networks rather than as isolated decision-makers.

**Emergence.** Adoption curves, sharing clusters, and inequality trajectories emerge from
decentralized interaction; none are scripted.

**Adaptation / objectives.** Agents do not optimize a global objective. They satisfice:
tier choice follows a willingness-to-pay threshold, task effort follows urgency and
aspiration-gap pressure, and usage intensity is gated by legitimacy and conformity.

**Learning.** Agents adapt through metacognitive calibration: graded-assignment feedback
updates calibration error, but the update is filtered through an attribution-biased
surprise mechanism (§7.4) that reproduces self-serving attribution and produces hysteresis.

**Sensing.** Agents observe neighbours' AI use only through a noisy channel (probability
P_VISIBLE) and peer performance through a binned, one-semester-lagged signal (§7.8).

**Interaction.** Three channels: material (access sharing), normative (legitimacy
diffusion), comparative (aspiration adjustment). Each is grounded in literature (Lin 2001;
Granovetter 1978; Festinger 1954).

**Stochasticity.** All initial trait assignment, network generation, task arrival, and
matching decisions are stochastic. Each scenario is replicated over 100 independent seeds.

**Collectives.** Formal collectives are the six sections; informal collectives emerge as
access-sharing clusters and peer study cliques.

**Observation.** Metrics are collected at the final step: mean/std of scores, Gini
coefficient, mean dependency, mean calibration error, mean retained ability, deadline
misses, AI adoption rate, mean legitimacy, borrowing count, and shared seats.

---

## 5. Initialization

### 5.1 Population

Ability drawn N(50, 15) clamped to [10, 100]. Self-regulation generated with ability weight
0.45 (positive correlation). SES assigned independent of section (ratios 0.30/0.50/0.20).
Budgets drawn per SES band (Bangkok-scaled undergraduate living allowances).

### 5.2 Social network

A Stochastic Block Model over the six sections with within-section edge probability
p_within = 0.18 and between-section probability p_between = 0.015, followed by
homophily-based rewiring favouring similar ability (h_ability = 0.25) and moderate SES
homophily (h_SES = 0.20). The result is a connected graph with mean degree k_bar in
[6, 10], matching empirical student ego-network bounds. Generation is rejected and
regenerated if the graph is disconnected or k_bar falls outside range.

### 5.3 Scenario configurations

Five policy environments:

1. **Baseline (S0)** — no AI access (tier 0); benchmarks unassisted learning.
2. **Free market (S1)** — unregulated adoption; tier purchase governed by budget and
   willingness to pay.
3. **Universal access (S2)** — free Tier 3 for semesters 1–4 (steps 1–480), then withdrawn
   (steps 481–960 revert to budget/WTP decisions). A permanent variant (full 8 semesters)
   is also run as a robustness benchmark.
4. **Mixed policy (S3)** — market tiers allowed, but AI use prohibited in core foundational
   courses (C1 always, C3 additionally in this scenario).
5. **Targeted subsidy (S4)** — low-SES students subsidized to a minimum of Tier 2 across
   all eight semesters.

Scenario tier policy is enforced via a post-step override that wins over the monthly
`_reconsider_ai_tier()` call; on the monthly-boundary step itself the agent processes one
step at its re-evaluated tier before the override re-applies (~1 step in 30, ≈3%).

---

## 6. Input Data

The model uses no external time-series input. Population statistics and parameter values
are calibrated from published literature and institutional benchmarks (see the parameter
provenance table in the manuscript §3.7). All parameters live in `config/params.py`, tagged
[K] (known/empirical), [C] (calibrated), or [F] (free, resolved by sensitivity analysis).

---

## 7. Submodels

### 7.1 Effective processing capability

```
I_eff = a_r + AI_SPEED_BOOST[tier_eff] * u(t) * 1{ai_allowed}
```
AI_SPEED_BOOST = {0: 0, 1: 5, 2: 15, 3: 35}. Processing time is
`(task.difficulty × PROCESSING_DIFFICULTY_FACTOR) / max(1, I_eff)`. Score quality carries a
multiplier `1 + AI_QUALITY_BOOST[tier_eff] * u(t) * (a_r / 100)`, with
AI_QUALITY_BOOST = {0: 0.0, 1: 0.05, 2: 0.20, 3: 0.50}, anchored to Hedges' g = 0.533.

### 7.2 Continuous usage intensity

```
u(t) = clamp(u_base * u_avail * L^(1 - conf), 0, 1)
u_base = clamp(w_urgency * urgency + w_asp * gap_asp, 0.1, 1.0)
u_avail = 1{quota > 0 OR tier_eff <= 1}
```

### 7.3 AI dependency accumulation

```
d(t+1) = d + α_d * u * (1 - d) - δ_d * (1 - u) * d
```
α_d = 0.012 (growth), δ_d = 0.005 (decay).

### 7.4 Metacognitive calibration error and retained ability

```
c(t+1) = c + β_c * d * (1 - c) - γ_c * surprise * c
surprise = raw_error * miss_severity * (1 - c)

a_r(t+1) = a_r + ρ_as * (1 - u) * (a_base - a_r) - λ_a * d * u * a_r
```
β_c = 0.010, γ_c = 0.050, ρ_as = 0.30 (recovery), λ_a = 0.008 (erosion).

The `(1 - c)` term in `surprise` dampens corrective feedback as miscalibration grows,
operationalizing self-serving attribution bias (Miller & Ross 1975; Zuckerman 1979). Highly
miscalibrated students attribute failure to external causes, so calibration damage is
self-reinforcing — this is the mechanism that produces cognitive hysteresis under policy
withdrawal.

### 7.5 Tier reconsideration and the borrow-substitution effect

Every 30 steps each agent recomputes willingness to pay:

```
WTP = TIER_BUDGET_FRACTION[SES] * B * w_score
if borrowing_from is not None: WTP *= BORROW_SUBSTITUTION   # < 1
upgrade to tier k if cost[k] <= budget_remaining AND cost[k] <= WTP
```
TIER_BUDGET_FRACTION = {low: 0.05, mid: 0.10, high: 0.15};
AI_MONTHLY_COST = {0:0, 1:0, 2:600, 3:1800}; BORROW_SUBSTITUTION = 0.60 (range 0.30–0.90).

### 7.6 Access-sharing market

Suppliers (tier ≥ 2) offer SHAREABLE_SEATS[tier] seats (tier 2 → 1, tier 3 → 2). Demanders
are agents below tier 3 whose undamped WTP cannot buy the next tier. A demander i matches
an available supplier j with probability:

```
P(match_ij) = prosociality_j * w_ij * (1 - N_{tier>=2, section} / N_section)
```

The final term is the local scarcity signal: under universal free access the fraction of
high-tier students saturates, the signal approaches zero, and the informal sharing market
dissolves. Borrowed usage drains the provider's quota; each borrower has a single provider.

### 7.7 Legitimacy diffusion (normative)

```
L(t+1) = L + η * conf * (observed_frac - L) + η_self * u * (1 - L)
```
observed_frac is a tie-strength-weighted, noisily observed (Bernoulli P_VISIBLE) sample of
neighbours' AI use. η = 0.08, η_self = 0.03.

### 7.8 Aspiration adjustment (comparative)

```
T(t+1) = T + κ * (peer_signal - T)
```
peer_signal is a binned (5 bins), one-semester-lagged, tie-strength-weighted average of
neighbours' scores. κ = 0.10.

---

## 8. Verification

- **Zero-interaction check**: with p_within = p_between = 0 the model reproduces v0.2
  baseline score/deadline mechanics within stochastic bounds, confirming the interaction
  layer is the source of new behavior.
- **Interaction-isolation check**: zero-interaction vs full network shows dependency
  tripling (0.109 → 0.354, KS p < 0.001) and calibration error rising (0.339 → 0.600).
- **Conservation**: quota and budget never negative; shared seats never exceed capacity.
- **Network sanity**: graph connected, k_bar in [6, 10].

## 9. Sensitivity analysis protocol

Two stages (see `analysis/`):
1. **Morris screening** — 23 candidate parameters, r=20 trajectories, composite ranking by
   max-normalized μ* across 12 output metrics.
2. **Sobol variance decomposition** — 12 retained parameters, Saltelli sampling N=512
   (7,168 evaluations), run on both the free_market and targeted_subsidy scenarios.
