# AAAPS v0.3 — Implementation Brief (condensed from ODD v0.3)

**Purpose:** Redesign the v0.2 flat/parallel model into a genuine networked ABM,
addressing JASSS desk-rejection critiques. This is a structural rewrite, not a patch.

**Full spec of record:** `ODD_Protocol_AAAPS_v0_3.md` (in this `docs/` folder) — that
document is the authoritative ODD description; this brief is a condensed implementation
view for anything ambiguous below.

---

## 0. What changes vs. the current v0.2 code

| v0.2 (current repo) | v0.3 (target) |
|---|---|
| 60 independent agents, RandomActivation | 240 agents, 6 sections, hybrid schedule (sync social phase + async individual phase) |
| No network | `networkx` social graph: stochastic block model + SES/ability homophily, static topology |
| Hardcoded 3-phase dependency (`dependency_phase` state var) | 3 coupled continuous state vars: `dependency (d)`, `calibration_error (c)`, `retained_ability (a_r)` — phases are derived/clustered post-hoc, NOT state |
| No agent-to-agent interaction | 3 interaction channels: material (AI access sharing), normative (legitimacy diffusion), comparative (aspiration adjustment) |
| Free parameters, no calibration doc | Every param tagged [C]/[K]/[F] in ODD §6, with literature sources |

## 1. New/changed entities (ODD §2)

- `SocialNetwork`: held by the model, `networkx.Graph`, static after init. Agents store
  `unique_id` only (no direct object references — must stay picklable for `joblib`).
- New StudentAgent static attrs: `conformity` (Beta), `prosociality` (Beta), `section_id`.
- New StudentAgent dynamic state: `ai_tier_effective`, `calibration_error (c)`,
  `retained_ability (a_r)` (replaces `effective_ability`), `ai_legitimacy (L)`,
  `aspiration (T)`, `shared_seats_out`, `borrowing_from` (single provider, per Section 10 #4).
- Population: N=240, 6 sections × 40. SES assigned **independent of section** (Section 10 #2).

## 2. Scheduling (ODD §3) — hybrid, two-stage

```
Phase A: environment update (deadlines, task arrival, budget/quota reset)
Phase B: SOCIAL UPDATE — synchronous, computed on a snapshot of t-1 state:
    B1 norm diffusion (legitimacy) -> B2 social comparison (aspiration) -> B3 access market (sharing)
Phase C: individual action — async, self.agents.shuffle().do("step") [Mesa 2.x]
Phase D: coupled state update (d, c, a_r) — solved together, see eqs below
Phase E: data collection
```
Phase B MUST read from an explicit copy of t-1 state, not live agent attributes.

## 3. Core coupled equations (ODD §7.4, resolved Section 10 #5 = Option B)

```python
d_next = d + ALPHA * u * (1 - d) - DELTA_D * (1 - u) * d
c_next = c + BETA * d * (1 - c) - GAMMA * surprise * c
a_next = a_r + RHO * practice * (base_ability - a_r) - LAMBDA * d * u * a_r

def surprise(perceived_difficulty, actual_difficulty, task_completed, c):
    if task_completed:
        raw_error = abs(perceived_difficulty - actual_difficulty) / actual_difficulty
        miss_severity = 0.3
    else:
        raw_error = 1.0
        miss_severity = 1.0
    return raw_error * miss_severity * (1 - c)  # self-serving dampening -> hysteresis
```

## 4. Three interaction submodels (ODD §7.7–7.9)

- **7.7 Access sharing (material):** demand = agents whose desired usage > own quota/tier;
  supply = agents with tier>=2 have `SHAREABLE_SEATS[tier]` seats; match probability =
  `prosociality_i * tie_strength_ij * scarcity_signal`. Under universal free access,
  `scarcity_signal -> 0` (this is the policy-backfire mechanism). Single provider per
  agent (Section 10 #4). Borrowed usage drains the PROVIDER's quota.
- **7.8 Legitimacy diffusion (normative):** `L_next = L + ETA*conformity*(observed_frac - L)
  + ETA_SELF*u*(1-L_next)`, where `observed_frac` is a tie-strength-weighted, noisily
  observed (Bernoulli p_visible) sample of neighbours' AI use.
- **7.9 Aspiration adjustment (comparative):** `T_next = T + KAPPA*(peer_signal - T)`, where
  `peer_signal` is a binned (5 bins), one-semester-lagged, tie-strength-weighted average
  of neighbours' scores.

## 5. Network generation (ODD §5.2)

```
G ~ StochasticBlockModel(sections, p_within, p_between), then rewire for homophily
h_SES, h_ability. Target k_bar = 6-10 (narrowed per literature, ODD §6).
h_SES should be LOW-MODERATE (0.15-0.25 excess same-SES tie prob) — literature review
found ability/section homophily dominates over SES homophily. Reject/regenerate if
disconnected or k_bar out of range. tie_strength ~ Beta(2,2) per edge.
Static topology in main model (rewiring only as a robustness-check variant, Section 10 #1).
```

## 6. Verification checks to implement early (ODD §8) — DO THESE FIRST, before full runs

1. **Zero-interaction check**: set p_within=p_between=0 -> results should reproduce v0.2
   behavior within stochastic bounds. This is the single most important sanity check —
   it proves the new interaction layer is the source of any new behavior.
2. Zero-AI check (S0 scenario) still reproduces ~normal score distribution.
3. Conservation: quota/budget never negative; shared seats never exceed capacity.
4. Network sanity: graph connected, k_bar in target range, homophily achieved as specified.

## 7. Parameters — where they go

ALL new and existing parameters go in `config/params.py`, never hardcoded in model files.
Tag each with a comment noting [C]/[K]/[F] status per ODD §6. Updated values already
decided: `rho_AS ~ 0.30`, `AI_QUALITY_BOOST` anchored to Hedges g=0.533, budget bands
(Bangkok-scaled) low N(4000,700) / mid N(11000,2000) / high N(27000,4000), k_bar target 6-10.
