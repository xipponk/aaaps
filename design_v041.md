# Design: v0.4.1 bug fixes (no code changed yet; awaiting Gate 4b)

Scope: (1) aspiration unit bug, (2) network generator, (3) tests, (4) impact and rerun plan. The benefit-ability family
is a separate step on top of v0.4.1 (design_benefit_spec.md). Every number below that came from a run is from v0.4 code.

## 1. Aspiration unit bug

Current rule (model/model.py:295-305): aspiration' = clip(aspiration + KAPPA*(peer_signal - aspiration), 10, 100) with
peer_signal = tie-weighted mean of neighbours' cumulative score_total (tens of thousands by step 960; exceeds 100 within
the first days). Aspiration is on the ability scale (starts at a_base, used in agents.py:176 as (aspiration - a_r)/100),
so it hits the clip within a few steps. Seed 0 free_market: 240 of 240 agents at 100.0 at step 960. Consequences: the
comparison with peers carries no information; the gap term is (100 - a_r)/100 for everyone; v0.4 isolation
"no_aspiration" (small effects) and the Morris/Sobol rank of KAPPA and ASPIRATION_GAP_WEIGHT were measuring a clipped constant.

Three proposed fixes (all keep KAPPA and ASPIRATION_GAP_WEIGHT, none adds a tuned parameter):

- A (recommended): relative standing, ability-scaled. Let S_i = score_total_i, Sbar = mean over all agents of score_total
  (r_i = 1 when Sbar = 0). Peer ratio q_i = (tie-weighted mean of neighbours' S_j) / Sbar. Target T_i = a_base_i * q_i.
  aspiration_i' = clip(aspiration_i + KAPPA*(T_i - aspiration_i), P.ABILITY_CLAMP[0], P.ABILITY_CLAMP[1]).
  Reading: an agent whose neighbours score 20% above the population average aspires to 20% above their own base ability.
  Dimensionless, bounded in practice (q about 0.7 to 1.4), starts at a_base (q = 1 at t = 0), no new parameter.
  Weakness: q uses cumulative score, so it varies slowly and reflects neighbours' history; ties to the old quantity.
- B: percentile within section (the reference suggested). For agent i, p_i = fraction of agents in its section whose
  neighbour-weighted peer mean score is below i's peer mean; target T_i = ABILITY_MEAN + ABILITY_STD * Phi^-1(p_i), p clipped
  to [0.01, 0.99]. Strength: scale-free, uses the population ability distribution. Weakness: depends on ABILITY_MEAN/STD
  (ties GSA parameters to the aspiration module) and ignores the agent's own ability, so aspiration can lie far from a_base.
- C: recent score rate. Use daily score gain averaged over the last 30 days instead of cumulative score: rate_j = (S_j(t) -
  S_j(t-30))/30, q_i = weighted neighbour mean rate / mean over all agents of rate, target a_base_i * q_i. Same form as A,
  responds faster, needs a 30-step history (a new window constant, tag [F]).
Choice: A as primary (simplest, parameter-free), C as sensitivity if A turns out inert.

Expected effect on behaviour (v0.4 arithmetic, to be measured, not tuned): the gap term currently adds about
0.2 * 0.55 = 0.11 to u_base for everyone; under A it is 0.2 * max(0, (a_base*q - a_r)/100), roughly 0.2 * 0.05 to 0.10,
so usage and dependency fall, relative decline at the current LAMBDA_A falls, and LAMBDA_A must be recalibrated
(it will rise). The gap term then also depends on ability (a_base*q - a_r), which makes the aspiration path matter for
the ability gradient of use. All isolation conclusions about aspiration must be redone.

## 2. Network generator (model/network.py)

Current: up to 50 SBM attempts; reject on disconnection or k_bar outside TARGET_K_BAR_RANGE (6, 10); after 50 failures a
silent Erdos-Renyi fallback with no sections. Audit (design_benefit_spec.md, step 0): default production and isolation
0 fallback of 100; Morris 800 of 1,440 (55.6%), driven by SBM_P_WITHIN and SBM_P_BETWEEN through expected degree; Sobol 0
of 7,168.

Proposed generator:
1. Retry only on disconnection (max_retries 50 kept).
2. TARGET_K_BAR_RANGE becomes validation only: if realized k_bar is outside the range, emit warnings.warn and set
   G.graph["kbar_in_range"] = False. The range is widened to (2.0, 30.0) so that the default (about 10.0) and the sweeps
   fall inside.
3. If no connected graph after the retries: raise RuntimeError with seed and parameter values. No ER fallback anywhere
   (the fallback code is removed).
4. Record on every graph: G.graph attempts, disconnected_rejects, k_bar, within_section_share, kbar_in_range. Every runner
   (production, isolation, Morris, Sobol, sweeps) writes these four columns per run and the mean and min/max in its manifest.
5. The rng draw order for the first accepted attempt is unchanged, so a network that v0.4 accepted on attempt 1 and that is
   connected is reproduced exactly; networks that v0.4 accepted on later attempts differ (v0.4 skipped attempts for k_bar > 10).

Range scan (graph only, seeds 0-9, outputs/phase2/network_range_scan.csv; per-attempt disconnection probability p_dis,
fallback share, realized k_bar, within-section edge share). With retries on connectivity only:
- Fallback needs p_dis^50: 0.78 gives 4e-6, 0.90 gives 5e-3, 0.97 gives 0.22. Practical rule: keep p_dis <= 0.8 everywhere in
  a sampled box. In the scan p_dis is at most 0.1 for expected degree >= 8.3, about 0.4 at 6.1, about 0.8 at 5, and about 1
  below 4.5 (disconnected almost always).
- Default (0.18, 0.015): expected degree 10.02, p_dis 0, k_bar 10.09, within-share 0.595.
Proposed ranges:
- Morris (rerun on v0.4.1): keep the original elicited bounds SBM_P_WITHIN [0.12, 0.25], SBM_P_BETWEEN [0.005, 0.03]
  (expected degree 5.7 to 15.75, corner (0.12, 0.005) has p_dis between 0.4 and 0.8 so retries are enough). Reason:
  comparability with the Morris design already published in findings; the only change is that the generator no longer
  discards or silently replaces networks. Realized k_bar is saved as a covariate, and the report states that these two
  parameters move density and section structure together.
- Network sweep (approved in principle, 17 points): SBM_P_WITHIN {0.10, 0.14, 0.18, 0.25, 0.35} (expected degree at default
  p_between: 6.9, 8.5, 10.0, 12.8, 16.7; 0.05 and 0.50 from the earlier proposal are dropped: 0.05 is disconnected, 0.50
  is 22.5); SBM_P_BETWEEN {0.005, 0.015, 0.03, 0.06, 0.12} (expected degree at default p_within: 8.0, 10.0, 13.0, 19.0, 31.0,
  all connected); HOMOPHILY_SES {0, 0.2, 0.4, 0.6, 0.8}; HOMOPHILY_ABILITY {0, 0.25, 0.5, 0.75, 1.0} (rewiring keeps the
  edge count, so k_bar does not move; connectivity is checked by the generator).
  Because density moves with p_within and p_between, add a density-controlled pair as a secondary sweep: hold expected degree at
  12 with (p_within, p_between) = (0.282, 0.005), (0.231, 0.015), (0.154, 0.03), (0.077, 0.045). This separates section
  structure from density. 4 points x 2 conditions x 100 seeds = 800 runs, about 0.4 h.

## 3. Tests to add (tests/, run before any batch)

1. Aspiration: run 3 seeds x free_market and universal_permanent; assert at every step after 30 that the share of agents
   with aspiration at either clip bound is below 5%, and that the cross-agent standard deviation of aspiration is above 2
   ability points at step 960. Under v0.4 this test fails (share at 100 is 100%), which is the regression guard.
2. Aspiration scale: assert aspiration - a_base stays within +/-50 at every step and agent.
3. Network sections: for 20 seeds at default and at each corner of the Morris box, assert connected, no fallback (the
   fallback code no longer exists, so assert that attempts <= 50 and graph.graph["attempts"] is present), and within-section
   edge share above the Erdos-Renyi expectation (about 1/6 = 0.167) by at least 0.2.
4. Generator failure: a parameter set that cannot connect (SBM_P_WITHIN 0.02, SBM_P_BETWEEN 0.001) must raise RuntimeError.
5. Manifest: every runner output has k_bar, within_section_share, attempts columns and none is NaN.
6. Propagation test (CLAUDE.md rule 3) for KAPPA and ASPIRATION_GAP_WEIGHT at both bounds: outputs must differ now that
   aspiration is not saturated.
7. Hash regression reference (design_benefit_spec.md, R2(d)) created from the finished v0.4.1.

## 4. Impact and rerun plan (hours at 0.55 to 0.60 runs/s on 14 workers)

Order: implement fixes, tests pass, recalibrate LAMBDA_A, then rerun. Everything model-dependent changes (aspiration touches
dynamics, and the generator changes networks that v0.4 accepted late).
| Step | Runs | Hours |
|---|---|---|
| LAMBDA_A recalibration to 21% (grid 7 values x universal_permanent x 30 seeds, then verify 3 values x 6 scenarios x 30 seeds) | 750 | 0.4 |
| r_AS check (200 seeds, population only) | 0 simulation | < 0.1 |
| production, 6 scenarios x 100 seeds | 600 | 0.3 |
| isolation, 7 conditions x 100 seeds (+ self_only 100) | 800 | 0.4 |
| Morris, 480 design points x 3 seeds | 1,440 | 0.7 |
| Sobol option F (full rerun, 1 seed, 2 scenarios x 7,168) | 14,336 | about 6.9 |
| Sobol option F3 (full rerun, 3 seeds) | 43,008 | about 20.7 (over the 12 h rule) |
| Sobol option P (partial: only points whose network changes under the new generator) | 42 per scenario, 84 | 0.04 |
Option P is valid only if nothing else about the model changed. With the aspiration fix every point changes, so P is not
valid for v0.4.1 and is listed to answer the question, not as a recommendation. (If the aspiration fix were postponed and
only the generator changed, P would be enough: the audit shows 42 of 7,168 points need more than one attempt, all others are
reproduced exactly, and the old Sobol indices would stay valid with those 42 points replaced.) Recommendation: F with 1 seed,
and decide separately whether to use a per-point seed to average over network realizations.
Totals for the recalibration, production, isolation and Morris reruns: about 1.8 h; with Sobol F about 8.7 h.
After Gate 4b, the approved experiments on v0.4.1: k grid with channel ablations 6,000 runs (about 2.8 h), self_only 2,500
(1.2 h), exploratory C1 1,000 (0.5 h), network sweep 3,400 + density-controlled 800 (about 2.0 h).
Regression reference for all of it is the new production v0.4.1, not production_v04; the old findings stay labelled v0.4.

## 6. Gate 4b responses and Gate 4c results (implemented on branch v0.4-recovery-fix)

### 6.1 Step 0: parameter leakage audit of the real runners
Every runner that sets config.params values in a pooled worker was read (file:line of the setting code):
run_morris_screening.py:94-116 (all 23 parameters set in every job), run_sobol_v04.py:56-61 (the same retained subset
in every job), run_sobol.py:77-88 and run_sobol_targeted_subsidy.py:90-101 (the same 12 in every job),
run_interaction_isolation.py:50-57 (saved and restored in try/finally), run_production.py:85-111 (COURSES[2] saved and
restored in try/finally), calibrate_lambda_a.py:46 (LAMBDA_A every job), zero_interaction_equivalence.py:57 (same value
for all jobs of an invocation). In none of them does a job set fewer names than an earlier job in the same worker, so no
run of production, isolation, zero_interaction, calibration, Morris or Sobol was contaminated by a previous job. The bug
was specific to the audit script. Morris has 23 parameters (PROBLEM in run_morris_screening.py:38-61, including
SHAREABLE_SEATS_TIER3); the audit script used 22 because that parameter does not enter the network. The property was
fragile, so all pooled runners now call analysis/param_guard.reset_params() at the start of every job; test_param_guard.py
has a worker-reuse test with a negative control and a static test that every pooled runner calls reset_params.
A regression found and fixed on the way: my first insertion also reset inside run_production._run_one, which wiped the
LAMBDA_A set by the calibration job (first v0.4.1 grid identical at every LAMBDA_A; that output is kept as
calib_grid_INVALID_lambda_wiped.csv). tests now propagate LAMBDA_A through the calibration, Morris and Sobol job paths.

### 6.2 Aspiration: where it is used, and units
Used once: agents.py:176-177, aspiration_gap = max(0, (aspiration - retained_ability)/100), then
u_base = clip(w_score + URGENCY_WEIGHT*urgency + ASPIRATION_GAP_WEIGHT*gap, 0, 1). Both aspiration and retained_ability are
ability points (10 to 100); the division by 100 makes the gap a fraction. The update (model.py B2) must therefore also
produce ability points. v0.4 averaged neighbours' cumulative score_total (tens of thousands of points), so the target was
always above 100 and the aspiration sat at the clip. Option A (a_base * relative score) would put a_base into a social
mechanism, a second ability channel not controlled by k, and is not used. Option B is used with neighbours as the
reference group: p_i is a rank in [0,1], unit-free, and is mapped to points with the existing ABILITY_CLAMP bounds, so
the target carries no a_base or a_r. Ability reaches aspiration only through outcomes (scores), as for any peer comparison.
Observed (3 calibration seeds, 2 scenarios): share within 1 point of a bound 4 to 8% per bound, aspiration SD 24 to 29 points,
corr(aspiration, a_base) 0.5 to 0.76, max |aspiration - a_base| about 59. The design-doc test thresholds (<5% at a bound,
within +/-50 of a_base) were written for option A; they were relaxed to <10% per bound and the +/-50 check was dropped for
B, after seeing these numbers. This is disclosed here and in the Gate 4c report.

### 6.3 Why (1 - c) is about 0.1 in universal_permanent, and what the c equation contains
c update (agents.py:315-317): c' = c + BETA_C*d*(1-c) - GAMMA_C*s*c, with s the day's mean surprise. surprise()
(agents.py:23-40) for a completed task is 0.3*|perceived - actual|/actual*(1-c), and perceived = actual*(1 - 0.4c)
(agents.py:231), so s = 0.12*c*(1-c) on completion days (misses add terms with severity 1). The factor (1-c) multiplies both
the growth and the recovery term, so at balance BETA_C*d = GAMMA_C*0.12*c^2, c* = sqrt(BETA_C*d/(0.12*GAMMA_C)). With
d = 0.50 (v0.4.1 universal_permanent) c* = 0.91; the measured mean is 0.858 (misses and idle days push the other way).
Recovery is quadratic in c, weak when c is small and only large at high c, hence c close to 1 when d is high.
(1-c) is about 0.14 on v0.4.1 (0.86 measured), about 0.10 on v0.4. The equation has no a_base or a_r term and no
SR_ABILITY_WEIGHT (agents.py:315-317). Ability enters only indirectly: through d (daily_u, which has the aspiration gap and the
speed-weighted u records), through task_completed (processing speed uses a_r, agents.py:200-203), and through SR_ABILITY_WEIGHT
into self_regulation (model.py:81) and so into life-task acceptance (agents.py:162), slot load and misses. C1 therefore
works through correlated paths, not a direct ability term.

### 6.4 Generator: corner of the Morris box
outputs/v041/network_corner_check.csv (500 seeds per point, 16 corner points including the homophily extremes, graph only).
Lowest corner (p_within 0.12, p_between 0.005, expected degree 5.68): per-attempt disconnect probability 0.52 to 0.66
(highest with HOMOPHILY_SES 0.35 and HOMOPHILY_ABILITY 0.40), mean attempts about 2 to 3, implied failure after 50 attempts
0.66^50 = 7e-10 per design point, 0 RuntimeErrors in 500 seeds at every point. Over the 480 Morris design points x 3 seeds
the crash probability is below 1e-6. All other corners: per-attempt disconnect below 0.025.

### 6.5 Network sweep size
One-at-a-time, 17 points = default + 4 parameters x 4 other levels (SBM_P_WITHIN, SBM_P_BETWEEN, HOMOPHILY_SES,
HOMOPHILY_ABILITY), in {full, no_norms}: 17 x 2 x 100 = 3,400 runs. Not a 5x5 grid: interactions among network parameters are
not tested, and this is stated in preregistration.md A2.

### 6.6 Recalibration and inertness (seeds 1000-1029, outputs/v041/)
LAMBDA_A grid on universal_permanent: relative decline 0.0806 (0.0007), 0.1264 (0.0012), 0.1572 (0.0016), 0.1834 (0.0020),
0.2111 (0.0025), 0.2681 (0.0040), 0.3065 (0.0059), monotone. Interpolated LAMBDA_A for 21% is 0.00248 (v0.4: 0.0020).
Verified: universal_permanent 0.2104. Aspiration inertness (A2): full minus no_aspiration, free_market, mean_dependency
+0.0048 (90% CI 0.0044 to 0.0053), relative_ability_decline +0.0058 (0.0054 to 0.0062): both inside +/-0.02, so by the
pre-declared criterion the aspiration channel is inert at the default ASPIRATION_GAP_WEIGHT. It is not zero (the
interval excludes zero), it is small. Per A2 the choice between B and C is for Aj. Tuul; C was not implemented or run.

### 6.7 Regression reference
tests/ref_hashes_v041.json: 60 runs (6 scenarios x seeds 0-4 x {full, zero_interaction}), hashes of the agent table at steps 1,
120, 240, 480, 720, 960, of model.random state after construction and at the end, and of the edge set. Reproduced in a second
process pool (tests.test_regression_hashes, 80 s). The reference is for the code without the benefit-ability family; the
family must reproduce these hashes bitwise at k = 1.
