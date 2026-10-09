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

## Step 0 audit: network fallback (Gate 4 partial approval; analysis only, no simulation)

Script: analysis/network_fallback_audit.py (rebuilds agents and network from seed and parameters, no stepping).
Output: outputs/phase2/network_fallback_audit.csv (8,738 rows, 46 networks/s, python = .venv).

Generator (model/network.py): up to max_retries = 50 SBM attempts (line 39). An attempt is rejected if the graph is
disconnected (81-82) or mean degree is outside TARGET_K_BAR_RANGE (84-87); the first accepted attempt is returned
(93). Only after 50 rejections does it silently build an Erdos-Renyi graph with p = 8/(n-1) and no sections
(95-105), with no log, warning or flag.

Counts (fallback / networks):
- production_v04 and isolation, seeds 0-99, default params: 0 / 100. All 6 scenarios share these networks (agents
  and network are built before any scenario logic), so 0 of 600 production runs and 0 of the 500 networked
  isolation runs fell back. The 200 zero_interaction/none_net isolation runs have no network by design, and the
  zero-interaction equivalence runs (N=60) likewise.
- calibration seeds 1000-1029: 0 / 30.
- Morris (design points x seeds 2000-2002): 800 / 1,440 = 55.6%.
- Sobol (same 7,168 points for free_market and targeted_subsidy, seed 3000): 0 / 7,168 (corrected, see below).

Why the expected "half fall back" did not happen: the per-attempt rejection rate at default is about half
(mean 2.17 attempts, 115 k_bar rejections and 2 disconnection rejections over 100 seeds), but 50 consecutive
failures are needed, so default fallback is essentially impossible. The retries do truncate the sample: accepted
networks have k_bar 9.45 to 10.00 (mean 9.83), i.e. the production distribution is conditioned on k_bar <= 10.

Morris: fallback fraction by quintile of SBM_P_WITHIN is 0.26, 0.88, 0.91 (Spearman 0.61 with fallback) and by
SBM_P_BETWEEN 0.37, 0.56, 0.81 (0.36); homophily and ability parameters about 0 to 0.12. By expected degree
39*p_within + 200*p_between: 0% fallback for 7 to 10, 72% for 10 to 11, 100% above 12 (and 40% for 5 to 6, from
disconnection). Fallback networks have within-section edge share 0.17 versus 0.55 for SBM, so in Morris a large
share of the SBM_P_WITHIN and SBM_P_BETWEEN design points did not test those parameters at all: they tested "no
sections". Their low Morris rank (0.04 to 0.08) cannot be read as "network structure does not matter"; the
parameters mostly toggle SBM versus ER, with the toggle point near k_bar = 10.

Sobol (CORRECTED, see note): 0 / 7,168 fell back. The 824 / 7,168 (11.5%) first reported was an artifact of my
audit script: ProcessPoolExecutor workers are reused and the script did not reset config.params between jobs, so
Sobol jobs that followed Morris jobs in the same worker inherited stale Morris network parameters. The Morris
numbers were not affected (every Morris job sets all 22 audited parameters). Fixed by resetting every audited
parameter to its import-time default at the start of each job; first-version output kept as
outputs/phase2/network_fallback_audit_v1_stale_params.csv. The fallback-vs-non-fallback "quasi-experiment" on Sobol
outputs compared an invalid label and is withdrawn.
What actually determines the Sobol networks: seed 3000 gives np.random.default_rng(3000) (model/model.py:109),
independent of model.random. The first SBM draw (network.py:41-43) is identical for every point and has
k_bar about 9.8, so it is accepted on attempt 1 in 7,126 of 7,168 points (99.4%); 42 points need 3 to 8 attempts.
Parameters enter only through agent attributes: SES (network.py:58) and base ability (network.py:69-73), via
ABILITY_STD and ABILITY_MEAN (clamp), which change which edges are rewired and the rng consumption afterwards (SES
draws, budgets, hobby, conformity use fixed numbers of draws because CONFORMITY and PROSOCIALITY betas are not
varied in Sobol). Result: 1,685 distinct edge sets among 7,168 points, accepted k_bar 9.82 to 9.98. Multi-attempt
points concentrate in the middle ABILITY_STD quintile (2.9% vs 0% elsewhere) but the numbers are tiny. So the
Sobol runs use essentially one network realization (plus rewiring variation), one SES/budget draw, and no
fallback. Morris, by contrast, has 518 distinct graphs in 1,440 runs, many being ER fallbacks.

Consequences to carry into v0.4.1: (1) production and isolation are clean; (2) Morris network-parameter ranks and
the "network parameters are least important" statement are not valid as stated; (3) Sobol is not affected by fallback but varies one network realization;
(4) the network sweep proposed in C7 would hit the same wall unless the range is widened and fallback is made loud.

## Revision 2 (Gate 4 reply, step 2): corrections to the spec family (design only)

Diagnostics below are two single-seed v0.4 runs (seed 0, free_market and universal_permanent; trajectories of mean
a_r and tercile dependency and calibration, no scores) and agent initialisation for seeds 0-99 (no stepping).

### R2(a) Mean preservation and the pivot
g_k = k*x + (1 - k)*m, so the population mean boost is E[g_k] = k*xbar(t) + (1 - k)*m. With a fixed pivot m and
xbar(t) falling under erosion, every k < 1 gives a larger average boost than k = 1, and the excess grows over time.
Diagnostic, seed 0, mean a_r/100 at steps 1, 120, 240, 480, 720, 960:
- free_market: 0.495, 0.492, 0.486, 0.471, 0.457, 0.447 (m = 0.495). At step 960, E[g] is 0.447 (k=1), 0.495 (k=0,
  +10.7%), 0.543 (k=-1, +21%). Time-averaged excess about +5% (k=0) and +10% (k=-1).
- universal_permanent: 0.495, 0.489, 0.476, 0.445, 0.418, 0.396. At step 960: +25% (k=0), +50% (k=-1); time-averaged
  about +12% and +25%.
So the level confound is real and largest where erosion is largest. Why it matters less for E_G: at k = 0 the boost is
the same for every agent, so a level shift raises both terciles by about the same amount and E_G barely moves; it matters
for mean score and gini.
Pivot options:
- P1 (recommended, primary): m = sample mean of a_base at t = 0 in that run (static, per run, known before step 1). Removes
  dependence on the ABILITY_MEAN parameter and on later state; no per-step renormalisation. Level difference remains and
  is reported through a mandatory diagnostic: mean g_k(t) saved at steps 1, 120, ..., 960 for every run of every spec.
- P2 (sensitivity): level-matched constant per (scenario, seed): m = time-average over steps of xbar(t) from that
  scenario and seed's k = 1 run. Makes the time-averaged mean g equal to the k = 1 value for every k. It needs the k = 1 run
  first and uses scenario output to set a spec constant; use only for k = 0 and k = -1 in the two co-primary scenarios.
- P3 (rejected): m = current mean a_r each step, which is a per-step renormalisation and makes k a function of the
  outcome path.
P1 and P2 results are both reported; the preregistered co-primary test uses P1 (amendment A1 in preregistration.md).

### R2(b) Bounds
At k = -1, g = 2m - x is negative when x > 2m. With P1: sample means of a_base over 100 seeds range 47.10 to 51.93
(mean 49.93), so 2m lies between 0.942 and 1.039. Agents with a_base > 2*mean exist in 8 of 100 seeds, at most 1 agent
per seed; worst case g = 2*0.471 - 1.0 = -0.058, i.e. quality multiplier 1 - 0.029 u, a small penalty. With the fixed
pivot 0.5, min g = 0.0 exactly. Proposal: g = max(0, k*x + (1-k)*m) in all specs. Cost to mean preservation: shift of
mean g at most 0.058/240 = 0.0002 (0.05% of m) in the 8 affected seeds, none elsewhere. At k = 1, x >= 0.1 so max(0, x) = x
and the bitwise identity is unchanged. P2 pivots are lower (xbar_avg 0.40 to 0.47), so 2m is 0.8 to 0.94; the clip would
then touch agents above that (normal tail estimate about 0.6% of agents for 2m = 0.88, mean shift about 0.0003). The clip
engagement count (agents, steps) is saved per run so the claim can be checked rather than assumed.

### R2(c) Relabelling and a real complementarity
k > 0 in the quality channel is a multiplicative tie between a_r and the AI boost: it is assumption-forced and is called
reinforcing, not complementarity, in all text. k = 0 is ability-independent; k < 0 is compensatory.

Proposed complementarity spec C1 (calibration complementarity, exploratory, off the k axis): quality = 1 + B[tier]*u*g_c,
g_c = m*(1 - c), where c is the agent's own calibration error and m is the P1 pivot. Reading: the AI boost is realised in
proportion to how well the user can judge AI output. Ability enters only through the trajectory of c.
Analytic check at t = 0 in zero_interaction mode:
- c(0) = d(0) = 0 for every agent, so g_c = m for all, identical to the k = 0 spec at t = 0: zero gap effect by equation.
- To first order, d(t) = ALPHA_D*ubar*t and c(t) = BETA_C*ALPHA_D*ubar*t^2/2, so agents are ordered in c by their mean use
  ubar (surprise recovery, GAMMA_C, is second order).
- ubar depends on ability through: (i) urgency (agents with higher a finish tasks sooner and spend fewer days at high
  urgency, so lower u: higher ability, lower ubar); (ii) the aspiration gap term (agents below aspiration use more; zero at
  t = 0 in zero_interaction because aspiration = a_base, and in full mode currently (100 - a_r)/100, favouring low
  ability); (iii) life-task dilution through SR (SR_ABILITY_WEIGHT, r = 0.30; high ability gets fewer life tasks, higher
  ubar), small: from arrival rates (life tasks about 0.018 accepted per day lasting 3 days, academic about 0.76 per day lasting 7 to 45) life tasks are well under 1% of task-days (an estimate, not measured); (iv) legitimacy gate, ability-free in zero_interaction.
  Sign of the net effect is therefore not fixed by the equations alone, but (i) and (ii) both point the same way and (iii)
  is small: higher-ability agents get lower c, so g_c is larger for them, a weak reinforcing gradient that arises from
  behaviour and not from the benefit formula. BETA_C only moves c and no ability-linked parameter enters c directly.
- Consistent with the single-seed diagnostics at step 960 (tercile low / mid / high): free_market d = 0.241 / 0.249 / 0.223,
  c = 0.365 / 0.396 / 0.360; universal_permanent d = 0.553 / 0.533 / 0.502, c = 0.902 / 0.890 / 0.861. Gradient is small
  (about 5 to 9% in the high tercile), so C1 will move E_G far less than the k axis does.
- C1 is not level-matched: at step 960 mean (1 - c) is about 0.62 in free_market and about 0.10 in universal_permanent,
  so C1 mostly measures the cost of miscalibration, and it can reverse the ordering of scenarios by access. It is therefore
  reported as a separate exploratory spec with its mean g_c(t) diagnostic, never mixed into the k interpolation.
Optional C2 (practice): g_d = m*(1 - d), same logic with dependency; not planned unless C1 is informative.
Propagation test required at implementation: BETA_C and GAMMA_C become score-relevant under C1 (they are not today).

### R2(d) Regression test (replaces the CSV-only check)
1. Reference: after the v0.4.1 bug fixes and before adding k, run seeds 0-4 x 6 scenarios x {full, zero_interaction} (60
   runs) and store, per run, sha256 of (i) the agent-level datacollector table at steps 1, 120, 240, 480, 720, 960 (all
   agent variables, bytes) and (ii) model.random.getstate() after construction and after step 960. Stored in
   tests/ref_hashes_v041.json (small, committed); regression reference is v0.4.1, not production_v04.
2. After adding k: with k = 1.0 every hash must be identical. Because k = 1.0 gives (1.0 - k) = 0.0, then x + 0.0*(m - x) = x
   in IEEE arithmetic, and the product order 1 + B*u*g is unchanged, the identity is expected bit for bit.
3. No extra random draw: assert that model.random state after construction is identical for every k (spec parameters are
   read only in agents._complete_tasks, after Phase C scoring, and no rng call is added); and that the final random state
   hash equals the reference at k = 1.
4. The test also runs one k = 0.5 case and asserts it differs from the reference in score columns (a test that the
   parameter binds, per the propagation rule) and is identical in everything not downstream of score (retained ability
   trajectory is identical except through the aspiration path, so this comparison is reported, not asserted).
