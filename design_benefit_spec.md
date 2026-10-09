# Design report: benefit-ability specification (v0.4, no model edits, no sweeps run)

Context: JASSS editor's reasons for rejecting v0.3 (circularity of the ability/AI-benefit link,
interaction vs assumption not separable, weak network effects and few seeds). Status: design only,
awaiting Gate 4. Nothing here changes model/, parameters or the paper.

## Part A. What the code does today

### A1. Where ability enters (file:line, HEAD 1c3c1cb)

| # | Channel | Where | Form |
|---|---|---|---|
| 1 | Task capacity | model/agents.py:100 | N_slots = int(a_base/20) + 2 (static, uses base ability) |
| 2 | Life-task acceptance | model/model.py:81, agents.py:162 | SR = 0.34*a_base/100 + 0.55*U; accept prob = hobby*(1 - 0.5*SR) |
| 3 | Processing speed | agents.py:198-203 | EI = a_r + SPEED_BOOST[tier]*u; time = difficulty*30/max(1,EI); progress/day = 1/time |
| 4 | Score quality | agents.py:226-227 | score = min(100, base_score * (1 + QUALITY_BOOST[tier]*u*(a_r/100))) |
| 5 | Usage propensity | agents.py:176-177 | u_base = clip(w + 0.30*urgency + 0.20*max(0,(aspiration - a_r)/100)) |
| 6 | Erosion / recovery | agents.py:327-330 | a_r' = a_r + rho*(1-u)*(a_base-a_r) - LAMBDA_A*d*u*a_r |
| 7 | Network | model/network.py:69-78 | ability homophily rewiring on a_base |

Not ability-linked: willingness w (from hobby), legitimacy, dependency growth (d depends on u only),
calibration error (surprise uses difficulty and c only), budget/tier choice, the market.

### A2. Which links force "high ability benefits more"

- Channel 4 is the forcing link. Absolute AI gain per completed task is base_score*QUALITY_BOOST*u*a_r/100,
  linear in a_r. The cross-derivative d2(score)/d(a_r)d(u) is positive by construction. At tier 3, u=0.7,
  a_r 30 vs 70 the multiplier is 1.105 vs 1.245. The editor's reading is correct for this channel.
- Channel 3 does the opposite. The speed boost is additive and ability-independent in absolute terms
  (progress gain = boost*u/(30*difficulty), same for everyone), so relative to a_r it is larger for low
  ability, and deadline misses happen at the low-ability margin. The model therefore already contains a
  compensatory path, but it only reaches the score through fewer misses and slot turnover, never through
  the task score itself (score does not depend on completion speed).
- Channel 6 is proportional in a_r, so absolute point loss is larger for high ability, relative loss similar.
  Score does not feed back into ability: score_total is read only by the aspiration update (model.py:300).
  So ability dynamics are almost independent of how the benefit is specified (prediction, to be checked).
- Channel 5 is a unit bug, not a design choice. Aspiration moves toward peers' cumulative score_total
  (tens of thousands, model.py:300-305) and is clipped to 100. Diagnostic, one run, seed 0 free_market:
  aspiration at step 960 is exactly 100 for all 240 agents (min=mean=max=100.0). So the gap term is
  (100 - a_r)/100 for everyone, a mild compensatory push on use, and the aspiration submodel carries no
  peer comparison in practice. This also explains the tiny no_aspiration effects in isolation. It should
  be reported as a limitation or fixed before submission (fixing it needs a recalibration decision, so
  not done here).

### A3. Verdict on the circularity critique

Partly correct, and the part that is correct is specific. (1) The score benefit of AI is multiplied by
retained ability, so any statement of the form "AI widens the score gap between high and low ability" is
partly built in. (2) The model is not purely reinforcing: the speed channel is compensatory in relative
terms. (3) The net direction is therefore set by the ratio of two [K]/[C] boosts, QUALITY_BOOST*a_r/100
versus SPEED_BOOST/a_r, which the paper has not tested. (4) Retained ability is not tied to benefit in a
loop: erosion does not depend on score. One-seed diagnostic (seed 0, tercile by base ability, final step):
score gap top minus bottom tercile 14,268 (baseline) vs 14,054 (free_market). One seed, not a result.

## Part B. Specification proposal

### B1. One-parameter family (benefit-ability slope k)

Replace x = a_r/100 in channel 4 by g_k(x) = x + (1 - k)*(m - x), m = P.ABILITY_MEAN/100.

- k = 1: g = x + 0.0*(m - x) = x exactly in floating point (bitwise), current spec (reinforcing).
- k = 0: g = m for everyone, ability-independent benefit with the same population-mean level.
- k < 0: compensatory (k = -1: g = 2m - x = 1 - x for m = 0.5, mirror image).
- 0 < k < 1: weaker reinforcement. k > 1 is excluded (g can go negative at low ability without a clip).

The pivot m keeps the average boost at the same level across k, so differences come from the
distribution of the benefit, not its size. Implementation later: parameter BENEFIT_ABILITY_SLOPE = 1.0 [F]
in config/params.py, read as P.BENEFIT_ABILITY_SLOPE at call time (propagation test required).
Regression test (to be written at implementation): with k = 1.0, all 14 metrics for baseline, free_market,
targeted_subsidy, seeds 0-4, equal bit for bit to rows in outputs/phase2/production_v04_runs.csv
(print absolute path, shape, seed max first). Because CSV floats round-trip, equality is exact.

Complementarity: in this family k is exactly the sign of the cross-derivative between ability and AI
use in the quality channel (k > 0 complements, k = 0 additive, k < 0 substitutes). No second parameter is
needed for the main design. Two decomposition specs that need no new parameter: S_q (quality channel only,
SPEED_BOOST = 0) and S_s (speed channel only, QUALITY_BOOST = 0) at k = 1, to show which channel carries the
gap result. These are channel ablations, not tuning.

Main specs: k in {1 (current), 0.5, 0, -0.5, -1}. Decomposition: S_q, S_s.

### B2. LAMBDA_A fixed at 0.0020 in every spec

No recalibration. Report realized relative_ability_decline per spec, per scenario, and per tercile. Since
ability dynamics should be nearly spec-invariant (A2), a large departure would itself be a finding.

### B3. Outcomes and flip rule, declared before any run

Unit: per run, terciles by a_base (static, 80 agents each, rank-split), final step. Scenario effect =
scenario minus baseline, paired by seed, 95% bootstrap CI (10,000 resamples), 100 seeds (0-99).

Outcomes: (i) G = mean score top tercile minus bottom tercile, effect delta_G vs baseline; (ii) gini of
score; (iii) mean_dependency (overall and by tercile); (iv) relative_ability_decline by tercile;
(v) deadline_miss_count (overall and by tercile).

Confirmatory (one): delta_G for free_market minus baseline, as a function of k. Everything else is
exploratory and labelled so. Quantity reported: break-even slope k* where delta_G = 0 (linear interpolation
between grid points, bootstrap CI).

Classification of each v0.4 claim at each k (CI of the effect at that k):
- holds: same sign as at k = 1 and CI excludes 0;
- attenuated: same sign, CI includes 0, or |effect| below half of the k = 1 effect;
- reversed: opposite sign and CI excludes 0.
A conclusion "flips" if it is reversed at any k <= 0.5 (not only at the extreme k = -1). A conclusion is
called emergent only if the full-minus-zero_interaction difference keeps its sign and CI-excluding-0 status
at k = 0 and k = -1.

## Part C. Experiments (not run)

### C6. spec x scenario x {full, zero_interaction}
Scenarios (6): baseline, free_market, mixed_policy, targeted_subsidy, universal_access, universal_permanent.
Baseline has u = 0 so k cannot matter: run once per mode (200 runs) and use it for every spec.
Runs: 5 specs x 5 AI scenarios x 2 modes x 100 seeds = 5,000, plus 200 baseline = 5,200.
Decomposition S_q and S_s on free_market and targeted_subsidy, both modes: 2 x 2 x 2 x 100 = 800.
Total 6,000 runs. At 0.55 to 0.60 runs/s (zero-interaction runs are faster): about 2.8 h; 2.5 h for the
5,200 core part. One tmux worker set, per-agent tercile extraction in a new runner (analysis only).
Emergent share per spec = (full - zero_interaction) / full for each outcome, paired by seed.

Caveat that must be reported: zero_interaction_mode removes all of Phase B, including ETA_SELF (see C8), so
full minus zero_interaction mixes peer diffusion, self-use reinforcement, aspiration and the market. Optional
third mode "self_only" (aspiration and market off, ETA = 0, ETA_SELF kept): +2,500 runs, about 1.2 h. Recommended,
because it separates interaction between agents from a legitimacy feedback that is in effect an individual
assumption.

### C7. Network sweep (one factor at a time, free_market, spec k = 1)
Important constraint found in network.py:37-98. Default expected degree is 39*0.18 + 200*0.015 = 10.02 (analytic),
sitting at the upper edge of TARGET_K_BAR_RANGE (6,10), and a network is rejected if it is disconnected or out
of range; after 50 failures the code silently falls back to an Erdos-Renyi graph with no sections. So production
networks are conditioned on k_bar <= 10, and any sweep upward in SBM_P_WITHIN or SBM_P_BETWEEN will hit the
fallback unless the range is widened. SBM_P_BETWEEN = 0 is infeasible (never connected). Plan: sweep with
TARGET_K_BAR_RANGE widened to (2, 30) for all points, rerun the default point under that setting (it is not
the production network distribution), log realized k_bar, clustering and a fallback flag per run (post-hoc from
the graph). Wide range is a deliberate departure and must be disclosed.

Levels (5 each, default shared, so 17 unique points):
SBM_P_BETWEEN 0.005, 0.015, 0.03, 0.06, 0.12; SBM_P_WITHIN 0.05, 0.10, 0.18, 0.30, 0.50;
HOMOPHILY_SES 0, 0.2, 0.4, 0.6, 0.8; HOMOPHILY_ABILITY 0, 0.25, 0.5, 0.75, 1.0.
Conditions: full and no_norms. Runs: 17 x 2 x 100 = 3,400, about 1.7 h. Outcomes: mean_dependency, gini,
mean_calibration_error (plus score, misses, legitimacy, saved anyway). Agents are identical across levels for a
given seed (agents are drawn before the network), so comparisons are paired. Optional third condition
no_peer_norms: +1,700 runs, 0.8 h. Read-out: network matters if full varies with the parameter while no_norms
does not.

### C8. no_norms vs ETA_SELF
Confirmed: no_norms skips the whole B1 loop (model/model.py:275), so both the ETA peer term and the ETA_SELF term
(line 291) are off, legitimacy stays at 0.10 (agents.py:113). Because the market needs legitimacy > 0.3
(model.py:329), no_norms also disables the market. no_peer_norms already exists
(analysis/run_interaction_isolation.py:39, ETA = 0, ETA_SELF kept) and was run: dependency +0.043 (CI
0.042 to 0.043), legitimacy +0.062, score -0.24%. Nothing to add. Existing isolation numbers already speak to the
editor's last point: removing interaction changes dependency by -64% but score by -1.3%.

## Part D. Done now (analysis of saved data)

### D9. Seed convergence (analysis/seed_convergence.py, outputs/phase2/seed_convergence_*.csv)
Pre-declared criteria are in the script header (levels: median relative 95% half-width <= 5%; contrasts:
detection rate >= 95% over 1,000 random size-n subsets). Input shapes printed: production (600,17), isolation
(700,16), seed max 99.
- Levels: scenario means of score, gini, dependency, misses, calibration error stable by 10 to 20 seeds;
  relative_ability_decline in free_market and mixed_policy needs 30.
- Paired contrasts vs baseline: all five metrics detected at >= 95% already at n = 10 for score, dependency,
  misses and decline in every scenario; gini needs 10 to 30 (free_market 30, mixed 20, universal 10) and
  targeted_subsidy gini needs 50.
- Isolation: no_norms, no_peer_norms, zero_interaction contrasts detected at 10 to 20 seeds; no_market is null at
  100 for score, dependency, misses, decline, calibration error (half-widths 15 score, 0.0003 dependency),
  its gini difference needs 90.
- Limits: this is paired by seed (shared agents), which is what makes 10 seeds enough. Unpaired comparisons need
  more. It speaks to production and isolation contrasts, not to network parameters (not yet swept). For the
  editor's worry, 100 paired seeds are sufficient for the contrasts reported so far; the weak-effect cases are
  tiny effects (targeted gini +0.0016, no_market gini) and they are the ones needing 50 to 90.

### D10. Figures
figures_v4/fig_morris_composite, fig_sobol_st_free_market, fig_sobol_st_targeted_subsidy (PNG and PDF,
analysis/figures_v4_gsa.py). Unreliable and degenerate Sobol columns are greyed and labelled.
Figure 1 labels and Figure 3 arrows: not done. Their sources are in the manuscript on faraday (no figure source
in this repo). Reading them needs SSH to faraday, so I need Aj. Tuul to choose internal or Tailscale alias
(and to confirm Figure 1 and 3 are conceptual diagrams), or to send me the source files.

## Open decisions for Gate 4
1. Approve k grid {1, 0.5, 0, -0.5, -1} and decomposition specs S_q, S_s.
2. Add the self_only mode (+2,500 runs)?
3. Aspiration unit bug (A2): fix before the spec runs (needs recalibration of LAMBDA_A) or report as limitation?
4. Network sweep with widened TARGET_K_BAR_RANGE: acceptable?
5. Faraday access for Figures 1 and 3.
