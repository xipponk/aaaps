# Preregistration: benefit-ability specification study (AAAPS v0.4.1)

Status: written and committed before any run of any k-spec, and before any 100-seed tercile score gap has been
computed from any data. Deviations are logged in the Amendments section with date and commit hash.

## 0. What has already been seen (disclosure)

- v0.4 aggregate outputs only (production_v04, isolation, Morris, Sobol). They contain no per-tercile scores.
- One diagnostic of two runs, seed 0, v0.4 code (baseline and free_market): tercile score gap 14,268 vs 14,054,
  tercile dependency 0.24 / 0.25 / 0.22 (low / mid / high), aspiration equal to 100 for all 240 agents. These were
  looked at; nothing else per tercile has been.
- v0.4 isolation (100 seeds, free_market): dependency full 0.241, no_norms 0.086, no_peer_norms 0.284, none_net
  0.078 (so H_self in section 8 was formed after seeing this and is only confirmatory on the fresh seeds below).

## 1. Code and seeds

- Code under test: v0.4.1 (bug fixes designed in design_v041.md, not yet implemented) plus the benefit
  specifications of section 2. LAMBDA_A is recalibrated once on v0.4.1 to the same target as v0.4 (21% relative
  decline of mean retained ability at step 960, universal_permanent, seeds 1000-1029) and then fixed for every spec.
- Confirmatory seeds: 7000-7099 (100 seeds). Never used before (used so far: 0-99, 1000-1029, 2000-2002, 3000,
  5000-5199). Paired by seed across scenarios, specs and modes (agents are drawn before any scenario logic).
- Runs that error are rerun with the same seed; no run or seed is dropped; no outlier removal. Each runner writes a
  manifest (git hash, params hash, python path and version, seeds, library versions, timestamps).
- The analysis script is committed before the first confirmatory run; its hash is recorded in the manifest.

## 2. Conditions

- Benefit-ability slope k in {1, 0.5, 0, -0.5, -1} on the quality channel (design_benefit_spec.md, B1, with the
  pivot decided in Step 2 and recorded as an amendment before any run). k = 1 is the current rule.
- Scenarios: baseline, free_market, mixed_policy, targeted_subsidy, universal_access, universal_permanent.
- Modes: full, zero_interaction, self_only (aspiration and market off, ETA = 0, ETA_SELF on).
- Channel ablations at k = 1 (quality only, speed only) on free_market and universal_permanent.

## 3. Outcomes (per run, final step 960)

Terciles are by base ability (static), rank-split into 80 / 80 / 80 agents, ties broken by agent id.
- G = mean score of top tercile minus mean score of bottom tercile.
- Effect of a scenario s on G: E_G(s, k) = G(s, k) - G(baseline), paired by seed. Relative form E_G / mean G(baseline).
- Secondary: gini of score; mean_dependency (overall and by tercile); relative_ability_decline by tercile (1 - mean a_r
  / mean a_base inside the tercile); deadline_miss_count mean per agent (overall and by tercile); mean_calibration_error.
  Measured decline is always reported as measured; the 21% calibration target is never reported as a result.

## 4. Smallest effect sizes of interest (SESOI), set from scale and convention, not from data

| Outcome | SESOI | Reason |
|---|---|---|
| E_G | 5% of the baseline gap G(baseline), mean over the same 100 seeds | A shift of one twentieth in the high-low gap is below what any policy argument would rest on; same order as the rounding used to report percentages. Defined as a proportion so it does not depend on the unseen gap size. |
| gini | 0.005 | Half of 0.01, the unit in which national Gini figures are reported. |
| mean_dependency | 0.02 | 2% of the [0,1] scale. |
| relative_ability_decline (tercile) | 0.02 | Two percentage points of relative decline. |
| deadline_miss_count | 0.5 per agent | Half a missed deadline per student over the programme (1 in 2 students). |
| mean_calibration_error | 0.02 | 2% of the [0,1] scale. |

## 5. Estimation and test rules

- All intervals: paired bootstrap over seeds, 10,000 resamples, numpy default_rng(20261016), percentile. 95% CI for
  superiority and reversal statements; 90% CI inside (-SESOI, +SESOI) for equivalence (TOST at alpha = 0.05).
- State of an effect E at a given condition, with E1 the same effect at k = 1 (only defined if the k = 1 effect is
  "present"):
  - present: CI_lo(E) > +SESOI (or CI_hi(E) < -SESOI for a reduction).
  - holds: present and E >= 0.5 * E1.
  - attenuated: present and E < 0.5 * E1.
  - vanished: TOST equivalence to 0 at SESOI.
  - reversed: sign opposite to E1 and the 95% CI beyond the SESOI on that side.
  - indeterminate: none of the above.
- If the effect is not present at k = 1, the claim "AI widens the gap" is reported as absent in v0.4.1 and the narrative
  rules in section 7 are not applied.

## 6. Confirmatory family 1: co-primary tests (Holm, alpha = 0.05, two tests)

For s in {universal_permanent, free_market}, the test is on E_G(s, k = 0), the ability-independent-benefit spec:
- T_s: H0: E_G(s, 0) <= +SESOI versus H1: E_G(s, 0) > +SESOI. p_s = bootstrap proportion of resamples with
  E_G* <= SESOI. Holm: order the two p-values, reject the smaller at alpha/2 and the other at alpha if the first rejected.
- Companion (not part of the family): TOST for E_G(s, 0) within (-SESOI, +SESOI), reported so that "no effect"
  can be asserted only through equivalence.
Rationale: if the gap widening survives removal of the ability-benefit link, it was not built in by that link.

k* (break-even slope): E_G(s, k) is computed on the five grid slopes from the same resample; k* is the value of k where
the linear interpolation between adjacent grid points crosses zero. If the point estimate has no crossing in [-1, 1],
k* is reported as "below -1" or "above 1" with the sign of E_G at the nearest end. CI: for each resample compute k*
(or "none"), report the percentile 95% interval over resamples that cross, and the share of resamples that do not.
Linearity of E_G(k) is checked (max deviation of grid points from the line through k = 1 and k = -1), and if it
exceeds 10% of E_G(1) the check is reported next to k*.

## 7. Pre-declared narratives (numeric, mutually exclusive, applied only if E_G(s, 1) is present for both scenarios)

- N1, circularity confirmed: for both co-primary scenarios, the state of E_G(s, 0) is vanished or reversed.
- N2, robust: for both scenarios, E_G(s, k) is present (CI_lo > SESOI) for every k in {1, 0.5, 0, -0.5}. (k = -1 is
  excluded because a compensatory extreme can legitimately reverse any gap.)
- N3, partly emergent: neither N1 nor N2. This includes "present at k = 0 but lost at some k > -0.5".
Interaction clause, evaluated separately and for each spec k: the outcome Y is called interaction-driven when the
paired difference full minus zero_interaction has a 95% CI beyond +/- SESOI(Y); interaction-null when the 90% CI is inside
(-SESOI, +SESOI). The share ES = (full - zero_interaction) / full is reported only for outcomes that are interaction-driven.

## 8. Confirmatory family 2: H_self (separate, alpha = 0.05)

H_self: the effect of interaction on mean_dependency comes mainly from self-use reinforcement (ETA_SELF), not from peer
norms, aspiration or the market. On free_market, k = 1, with D_full, D_self (self_only), D_zero (zero_interaction):
S = (D_self - D_zero) / (D_full - D_zero), per resample, paired by seed.
- Supported if the 95% CI of S has CI_lo > 0.5 and |D_full - D_zero| is beyond SESOI(dependency).
- Refuted if CI_hi(S) < 0.5 under the same condition.
- Otherwise inconclusive. S > 1 is allowed and means peer influence works against dependency.
Network sweep corroboration (free_market, k = 1, 17 points, conditions full and no_norms): for each of the four
parameters, compute the range over its five levels of mean_dependency in full, paired against the default level.
- Supports H_self: every parameter has all contrasts equivalent to 0 at SESOI(dependency) (TOST, Holm over the 16
  non-default contrasts) in full.
- Contradicts H_self: some parameter has a full contrast with 95% CI beyond 2 * SESOI(dependency) (0.04), meaning
  structure moves dependency materially.
- Otherwise inconclusive. no_norms is expected to be flat in all four, reported as a check on the sweep.

## 9. Exploratory (no multiplicity control, labelled as such in the paper)

Everything else: secondary outcomes by tercile, other scenarios, mixed_policy, targeted_subsidy and universal_access,
channel ablations, self_only for outcomes other than dependency, network-sweep outcomes other than dependency.

## 10. Reporting rules

All k, all scenarios and all outcomes are reported, including those that go against the original v0.4 claims. Seeds,
counts of runs, git hashes and manifests are given with every table. Network realized k_bar and within-section edge
share are reported per run (v0.4.1 writes them to the manifest).

## Amendments

### A1 (before any k-spec run; design step 2)
- Pivot for the k family: P1, m = sample mean of a_base at t = 0 per run; g = max(0, k*x + (1-k)*m). P2 (level-matched
  per scenario and seed from the k = 1 run) is a sensitivity analysis for k = 0 and k = -1 in the two co-primary scenarios,
  reported next to the co-primary result. Co-primary tests use P1.
- k > 0 is labelled "reinforcing", never "complementarity". C1 (g_c = m*(1 - c)) is an exploratory spec off the k axis.
- Mean g_k(t) saved at steps 1, 120, ..., 960 for every run; clip engagement counts saved.
- Regression reference is v0.4.1 agent-level hashes, not production_v04.

### A2 (Gate 4b conditions; written before the recalibration runs and before any no_aspiration run on v0.4.1)
- A1 conditions: P1 is primary and P2 is sensitivity. No claim about the ordering of scenarios across k is made without
  P2 for the same k. C1 is exploratory and is interpreted only as E_G within a scenario, never across scenarios.
- Aspiration (v0.4.1, option B restricted to network neighbours): p_i = tie-strength-weighted share of i's neighbours with a
  lower cumulative score than i (ties count one half); target = ABILITY_CLAMP[0] + p_i * (ABILITY_CLAMP[1] - ABILITY_CLAMP[0]);
  aspiration moves toward the target at rate KAPPA and is clipped to ABILITY_CLAMP. The comparison is unit-free (a rank), and
  the map onto the ability scale uses only the existing clamp bounds, so no new parameter and no trait (a_base, a_r) enters
  the target. The aspiration gap is still used only at agents.py:176, in ability points divided by 100.
- Diagnostic seen before this amendment: 3 calibration seeds (1000-1002) x {free_market, universal_permanent}, aspiration
  share within 1 point of a bound, its SD and its correlation with a_base at steps 30, 120, 480, 960. No dependency or
  score effect of aspiration has been looked at.
- Inertness criterion for the aspiration channel, decided on calibration seeds 1000-1029 only, free_market, at the
  recalibrated LAMBDA_A: paired differences (full minus no_aspiration, aspiration frozen at a_base) in mean_dependency and
  in relative_ability_decline over the 30 seeds, bootstrap 10,000 resamples (rng 20261016), 90% interval (equivalent to TOST
  at alpha 0.05). The channel is called inert if both intervals lie inside +/-0.02 (the SESOI for dependency and decline).
  If inert, this is reported at Gate 4c and fallback option C (30-day score rate) is evaluated by the same criterion; the
  choice between B and C is then made by Aj. Tuul, not switched by the code.
- Network sweep: one-at-a-time, 17 points = 1 default + 4 parameters x 4 non-default levels (SBM_P_WITHIN {0.10, 0.14, 0.25,
  0.35}, SBM_P_BETWEEN {0.005, 0.03, 0.06, 0.12}, HOMOPHILY_SES {0, 0.4, 0.6, 0.8}, HOMOPHILY_ABILITY {0, 0.5, 0.75, 1.0}),
  in {full, no_norms}. This is not a 5x5 grid: interactions among network parameters are not tested. A separate
  density-controlled 4-point sweep at expected degree 12 is exploratory.
- Run-time safeguards added to every runner: parameters are reset before each job (reset_params), and the realised network
  (attempts, disconnected rejects, k_bar, within-section share) is written with every run.

### A3 (Gate 5 reply; written and committed before any v0.4.1 confirmatory run; seeds 7000-7099 still unused)
Code state when written: LAMBDA_A = 0.00248, aspiration option B, SBM generator with connectivity-only retry (commits up to 1bf837e).
The benefit family, self_only mode, C1, L0 parameter and the confirmatory runner are NOT implemented at this point; they are
implemented after this amendment and the analysis script are committed.
1. Decomposition of interaction. Wherever the plan speaks of "the effect of interaction" the full minus zero_interaction
   difference is split into social = full - self_only and individual = self_only - zero_interaction, each with its own paired
   CI. self_only = ETA peer term off (no neighbour observation, no random draw for it), ETA_SELF on, aspiration off, market off,
   network built but unused. The interaction clause of section 7 is applied to full - zero_interaction, social and individual
   separately. "Emergent" is claimed only for the social part. Share of the interaction effect that is individual =
   individual / (full - zero), reported only where the full - zero difference is interaction-driven (CI95 beyond SESOI).
2. H_self (section 8) uses the implemented self_only mode, not the no_peer_norms proxy used in the exploratory Gate 5 reading.
   S = (D_self - D_zero)/(D_full - D_zero) per resample as ratio of resample means. The condition "|D_full - D_zero| beyond SESOI"
   is read as: the 95% CI of D_full - D_zero lies entirely above +0.02 or entirely below -0.02. All bootstrap resamples use ONE
   shared index matrix (numpy default_rng(20261016).integers(0, 100, (10000, 100))) for every condition, scenario and statistic,
   so every contrast is paired and every k-dependent quantity (k*) uses the same resample.
3. Sensitivity to the initial legitimacy L0 (exploratory): L0 in {0.05, 0.10, 0.20, 0.30} x {full, self_only, zero_interaction},
   free_market, k = 1, seeds 7000-7099. L0 = 0.10 reuses the block K rows (identical by the regression test); the other three
   values are run. Reported per L0: D_full, D_self, D_zero, S with CI. L0 is a new tagged parameter INITIAL_LEGITIMACY [F]
   (previously a literal at agents.py:113).
4. Not in the Sobol set: PROSOCIALITY_BETA_A (Morris composite 0.359) and CONFORMITY_BETA_B (0.329) lie above the 0.3 noise
   floor but outside the top 12, by the fixed retained-set rule (top 10 plus forced LAMBDA_A and RHO_RATIO, filled to 12).
   Their Sobol indices do not exist and no statement is made about them beyond the Morris values.
5. Run blocks (all seeds 7000-7099, runner analysis/run_confirmatory.py, outputs/v041_conf/<block>_runs.csv):
   K: k in {1, 0.5, 0, -0.5, -1} x {free_market, mixed_policy, targeted_subsidy, universal_access, universal_permanent} x
   {full, self_only, zero_interaction}, pivot P1 (m = mean a_base/100 at t = 0 in the run), plus baseline once (full, k = 1):
   7,600 runs. P2: k in {0, -1} x {free_market, universal_permanent}, full, pivot m = time average of mean a_r/100 over steps
   1..960 of the k = 1 full run of the same scenario and seed: 400 runs. ABL: quality only (AI_SPEED_BOOST all 0) and speed only
   (AI_QUALITY_BOOST all 0), k = 1, {free_market, universal_permanent}, {full, zero_interaction}: 800 runs. C1: g_c = m*(1 - c),
   five AI scenarios x {full, zero_interaction}: 1,000 runs. NET: free_market, k = 1, one-at-a-time 17 points as in A2 x
   {full, no_norms}: 3,400 runs, plus the density-controlled points (SBM_P_WITHIN, SBM_P_BETWEEN) = (0.282, 0.005), (0.231, 0.015),
   (0.154, 0.03), (0.077, 0.045) x {full, no_norms}: 800 runs. L0: 900 runs. Total 14,900.
6. Per-run outputs written: all production metrics, per-tercile score, dependency, calibration error, relative decline and
   misses, G, mean g_k at steps 1, 120, 240, 360, 480, 600, 720, 840, 960, the clip count, the time-averaged mean a_r/100, the
   pivot used, and the realised network (attempts, k_bar, within-section share).
7. Confirmatory vs exploratory. CONFIRMATORY: the Holm family of section 6, the narratives of section 7 and the interaction
   clause evaluated as in item 1, H_self (section 8) and the network sweep corroboration (section 8). EXPLORATORY: everything
   else (all other scenarios and outcomes, P2, ablations, C1, density-controlled sweep, L0 sensitivity, diagnostics).
8. Analysis script: analysis/confirmatory_analysis.py. It is committed with this amendment and tested on synthetic data with
   the same schema before the first run. It is run once on the complete outputs and writes results_confirmatory.md and
   outputs/v041_conf/results/*.csv. Its sha256 is written to the runner manifests. If it must be changed after the first
   confirmatory run, the changed version is labelled exploratory and the original output is kept.
9. Pipeline safeguards: the pipeline stops on any failing test (including the bitwise regression at k = 1 and L0 = 0.10), any
   RuntimeError or Traceback, or less than 20 GB free disk.

### A4 (Gate 6 reply; written and committed before any A4 run; seeds 8000-8104 unused; entirely post hoc and exploratory)
Status. A4 is decided after the confirmatory results (results_confirmatory.md, commit b687677) and after the channel ablations
(quality only, speed only, k = 1, seeds 7000-7099) were seen. It has no hypothesis, no Holm family and no confirmatory claim. The
choice of levels and of the direction of the sweep follows from those ablations. Every number it produces is reported as exploratory.
1. Parameters. AI_QUALITY_SCALE (mq) multiplies AI_QUALITY_BOOST and AI_SPEED_SCALE (ms) multiplies AI_SPEED_BOOST, both for all tiers,
   both tagged [F] in config/params.py with default 1.0. At 1.0 the model is bitwise unchanged (tested against tests/ref_hashes_v041.json).
2. Levels (mq, ms; quality-to-speed ratio relative to the default is mq/ms): R0 (0, 1; 0), R1 (0.25, 1; 0.25), R2 (0.5, 1; 0.5), R3 (1, 1; 1,
   default), R4 (1, 0.5; 2), R5 (1, 0.25; 4), R6 (1, 0; infinity). Scaling one channel also changes the total size of the boost, so level
   comparisons are confounded with magnitude; that is why the report carries the mean score gain and g_mean_960 per level.
3. Design. k in {1, 0.5, 0}, scenarios universal_permanent and free_market, mode full, pivot P1, seeds 8000-8099 (100 seeds, never
   used), plus baseline once on the same seeds: 7 x 3 x 2 x 100 + 100 = 4,300 runs. Block A4 of analysis/run_a4.py writes
   outputs/v041_a4/A4_runs.csv. Estimated time 2.2 h at 0.55 runs/s (an estimate, not a measurement).
4. Outcomes and rules (analysis/a4_analysis.py, written and tested on synthetic data before any run, run once). E_G(s, k, level) =
   G(s, k, level) - G(baseline), paired by seed, CI95 from the shared bootstrap index matrix (rng 20261016, 10,000 x 100).
   (a) Ratio thresholds, per scenario: scanning R0 to R6 along theta = mq/(mq + ms), the first level interval in which E_G(k = 1)
   crosses +SESOI (717.0, the confirmatory value) and the first in which E_G(k = 0) crosses -SESOI, by linear interpolation in theta,
   reported as theta and as ratio = theta/(1 - theta), with a bootstrap CI over the resamples that have a crossing and the share of
   resamples without one. If the point estimates have no crossing the report says so and states on which side every level lies.
   (b) Mean score gain against baseline (paired CI) and mean g_k at step 960 (g_mean_960) per scenario, k and level.
   (c) k* per level by interpolation on the grid {1, 0.5, 0}, scanning from k = 1 down, reported only if E_G changes sign in [0, 1]
   ("none in [0,1]" otherwise); linearity in k is reported as E_G(0.5) - (E_G(1) + E_G(0))/2 with CI.
   (d) Sanity check, fatal: R0 (mq = 0) removes the benefit-ability channel, so R0 at k = 1, 0.5 and 0 must be bitwise identical.
   Checked twice by analysis/a4_checks.py: before the block on agent-state hashes (seeds 8000 and 8001, both scenarios, k = 1, 0.5, 0)
   and after the block on every outcome column of the R0 rows. A mismatch stops the pipeline.
5. Diagnostic D1 (exploratory): free_market, k = 1, R3, full, seeds 8100-8104 (5 runs, block D1). New option log_local_fraction records,
   per step and agent, the tie-strength-weighted observed share of neighbours that the B1 peer term reads (model.py, observed_frac),
   the same share without the P_VISIBLE draw, and the global share of agents with AI use in the same snapshot. Logging draws no random
   numbers; a test checks that hashes with logging equal tests/ref_hashes_v041.json. Reported: variance of the local fraction across
   agents (per period of 120 steps and overall) with an independent-neighbour reference p(1 - p)/degree, the per-agent correlation
   over time between local and global fraction (mean and quantiles), and the mean absolute difference between local and global
   fraction over time, also against P_VISIBLE x global. Agents without neighbours are excluded.
6. Pipeline (run_pipeline_a4.sh, tmux): tests (including bitwise regression and the logging-inertness test), R0 pre-check, block A4,
   R0 post-check, block D1, then the analysis script once, writing results_a4.md and outputs/v041_a4/results/*.csv. It stops on a failing
   test, an R0 mismatch, any RuntimeError or Traceback, free disk below 20 GB, uncommitted tracked changes or another worker set.
   After the first A4 run the script is not edited; a changed version is labelled exploratory and the original output is kept.
7. Not claimed: no threshold, k* or ratio from A4 enters the confirmatory claims. Any statement in the paper that uses A4 labels it
   post hoc exploratory and gives the levels and seeds above.
