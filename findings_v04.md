# findings_v04.md (working notes, Phase 1 entries only)

Numbers below come from outputs/phase1/ (CSV, JSON logs and manifests, not tracked by git).
This file is completed in Phase 3.

## Spec-vs-code issues found in Phase 1

1. Recovery vs erosion (manuscript Table 1, as quoted by Aj. Tuul at main_v3_draft.tex:582,
   states rho_as < lambda_a). The v0.3 code had RHO_AS = 0.30 and LAMBDA_A = 0.008, so
   recovery was 37.5 times larger than erosion, the opposite of the stated spec. Spec-vs-code bug.
   Not independently checked here: the .tex lives on faraday.
2. Ability to self-regulation correlation (manuscript Table 1 r_AS = 0.30 at line 578, as
   quoted). Code uses SR_ABILITY_WEIGHT = 0.45 with noise weight 0.55. Measured over 200
   seeds of 240 agents (outputs/phase1/spec_check_b.json): mean r = 0.386, SD 0.053, 5th to
   95th percentile 0.301 to 0.478. Analytic value 0.391. So the code gives about 0.39, not
   0.30 and not 0.45. No ABILITY_SELFREG_CORR parameter exists; the old RHO_AS=0.30 never
   controlled this correlation. RESOLVED at Gate 1: SR_ABILITY_WEIGHT changed to 0.34 so the
   realized r matches the paper's 0.30. Re-measured on 200 new seeds (5000-5199): mean r =
   0.299, SD 0.051 (0.33 gave 0.291). Side effect: mean self-regulation falls from about 0.50
   to about 0.44 because the weights no longer sum to 1; self-regulation only enters the
   acceptance probability of life tasks.
3. Recovery multiplier (manuscript line 519 uses 1 - u(t), as quoted). Code uses
   practice = 1 - daily_u, where daily_u is the effort-weighted mean of per-task u over the
   tasks processed that day (model/agents.py, update_coupled_dynamics). These are the same
   quantity when u(t) means the daily aggregate. Caveat from spec_check_c.json (free_market,
   seed 7, 230,400 agent-days): 5.2 percent of agent-days had no task at all and still count
   as full practice (practice = 1); 66.1 percent had tasks but zero AI use; 28.6 percent had
   AI use. So "practice" means "did not use AI today", and idle days give full recovery.
   LIMITATION (kept on purpose, Gate 1 decision): changing it would need a recalibration of
   LAMBDA_A, so it is not changed without asking.
4. Calibration error (c) is terminal: BETA_C and GAMMA_C change only the calibration error
   metric in the propagation audit, nothing else. c does not feed back into behaviour or score.
5. The retained-ability floor was a literal 10.0 in agents.py. It now reads P.ABILITY_CLAMP[0].
   The aspiration clip in model.py (10.0, 100.0) is still literal (behaviour-neutral, not changed).

## Calibration note (LAMBDA_A)

LAMBDA_A = 0.0020 is a calibrated input, not a result. It was tuned so that relative decline
of mean retained ability at step 960 is 21 percent under permanent universal access (30
seeds, 1000-1029, after the SR fix: 21.0 percent). The 10 and 35 percent values (0.0007 and
0.0059) are a sensitivity bracket, not literature values. Any decline reported in the paper
must be the decline measured in the 100-seed production runs, reported separately.
Anchor for 21 percent: Budzyn et al. 2025 (Lancet Gastroenterol Hepatol 10(10):896-903,
DOI 10.1016/S2468-1253(25)00133-5). The ADR figures (28.4 to 22.4 percent) have only been
seen in secondary sources so far and must be confirmed from the publisher abstract by
Aj. Tuul before they are used as evidence. references.bib on faraday has the wrong volume
and pages for this paper (10(8) 742-751); the Crossref record is 10(10):896-903.

## Phase 2 entries (v0.4 code, LAMBDA_A = 0.0020, RHO_RATIO = 0.5, SR_ABILITY_WEIGHT = 0.34)

### v0.2 reference
Regenerated from git worktree a1f980b with analysis/run_v02_reference.py: 100 seeds x 60 agents
at step 960, outputs/reference/v02_free_market_final_step_100seeds.csv, shape (6000, 14), Step max
960. Seed 42 final-step score_total is identical to the saved GROUNDTRUTH file
(57,600 x 13, Step max 960). Mean over seeds of per-seed mean score 36,053, deadline misses 8.94.

### Zero-interaction vs v0.2 (pre-declared margin +-10 percent, Welch TOST, 100 seeds, N = 60)
NOT equivalent. Score: v0.4 31,936 vs v0.2 36,053 (difference -11.4 percent, 90 percent
bootstrap CI -4,386 to -3,847, margin +-3,605, TOST p = 0.999, KS D = 0.95). Deadline misses:
16.24 vs 8.94 (+81.7 percent, CI 6.73 to 7.86, margin +-0.89, KS D = 0.88). The earlier paper
phrase "within stochastic bounds" is not supported. Structural differences read from the code
(causes not isolated by an ablation): v0.2 decides AI use per task as a binary choice with the
full tier effect (_decide_ai_tier) and accepts tasks by a self-regulation threshold; v0.4 uses a
continuous intensity u(t) gated by legitimacy, which stays at its initial 0.10 when interaction
is off, and adds coupled dependency, calibration and ability erosion. v0.2 also has phase-based
effort reduction and erosion driven by dependency. An ablation (for example LAMBDA_A = 0,
legitimacy fixed high) would be needed to say which difference drives the gap.

### Interaction isolation (free_market, N = 240, 100 paired seeds, paired bootstrap 95 percent CI)
Effect of removing each submodel, relative to the full model:
- Norm diffusion off: dependency 0.241 to 0.086 (-0.155, CI -0.158 to -0.152); calibration error
  0.380 to 0.246; retained ability 44.98 to 49.36 (+4.37); score 32,265 to 31,852 (-1.3 percent);
  legitimacy 0.41 to 0.10.
- Aspiration adjustment off: dependency -0.019, calibration error -0.011, retained ability +0.69,
  score -17 (-0.05 percent). Small but distinguishable from zero.
- Access market off: no effect (dependency -0.0000, CI -0.0004 to 0.0003; score -5, CI -20 to +9).
- All three off with the network kept, and zero_interaction_mode, give identical means
  (dependency 0.0777, calibration 0.230, retained ability 49.45, score 31,820).
Caveats. (1) "Norms off" freezes legitimacy at its initial 0.10, so it measures the effect of a
low fixed legitimacy as much as the effect of social diffusion. (2) The market only admits
demanders with legitimacy above 0.3, so switching norms off also switches the market off
(0 borrowers in a 60-step smoke test); the three submodels are not independent. (3) The earlier
single-seed isolation numbers (dependency 0.109 to 0.354, D = 0.592) are superseded by these.

### Production, 100 seeds per scenario (measured, not targets)
Relative decline of mean retained ability at step 960 (LAMBDA_A calibrated on permanent
universal access only): baseline 0.0 percent, mixed_policy 5.2, free_market 9.9,
targeted_subsidy 17.1, universal temporary 17.2, universal permanent 20.8.
Mean score: baseline 31,489; mixed 32,103; free_market 32,265; targeted 32,537; universal
temporary 33,642; universal permanent 35,268. Gini: 0.124, 0.125, 0.125, 0.125, 0.120, 0.111.
Dependency: 0.002, 0.182, 0.241, 0.411, 0.376, 0.540. Calibration error: 0.011, 0.347, 0.380,
0.646, 0.865, 0.891. Deadline misses: 16.6, 17.9, 17.3, 18.0, 18.5, 18.2.
Borrowers at the last step: 0, 16.0, 19.7, 22.7, 34.0, 0; ever borrowed: 0.5, 98.7, 114.1,
202.2, 208.6, 199.1. Artifact: the post-step tier override lets agents borrow on the first step
of each month (tiers are re-evaluated in Phase A before the override), which is why universal
permanent shows ever_borrowed = 199 with 0 borrowers at the end, and baseline shows small
nonzero dependency (0.0017).
Files: outputs/phase2/production_v04_runs.csv (600 x 17), production_v04_ses_tier.csv (3,794 x 9).

### Ablation: zero-interaction with LAMBDA_A = 0 vs v0.2 (exploratory, post hoc, same margin and tests)
Still not equivalent. Score: 31,969 vs 36,053 (-11.3 percent, 90 percent bootstrap CI -4,353 to
-3,816, TOST p = 0.998). Deadline misses 16.18 vs 8.94 (+80.9 percent, CI 6.66 to 7.80, TOST
p = 1.0). Retained ability equals base ability in every agent (max difference 0.0), so the
switch worked. Ability erosion is therefore not what separates v0.4 from v0.2 in the
zero-interaction setting (in the primary run mean relative decline was only 0.95 percent). Other
structural differences (binary vs continuous AI use, legitimacy fixed at 0.10, task acceptance,
v0.2 effort and phase effects) are untested.

### Interaction isolation addendum: what the "norms" switch removes
The no_norms switch skips the whole B1 loop, so it removes BOTH peer diffusion (ETA) and
self-use reinforcement (ETA_SELF). Evidence: mean legitimacy is exactly 0.1000 in every no_norms
run. New condition no_peer_norms (ETA = 0, ETA_SELF kept; 100 paired seeds, free_market,
N = 240) against full: dependency 0.2413 to 0.2841 (+0.0428, CI 0.0423 to 0.0434), calibration
error +0.0119, retained ability -2.24 (CI -2.28 to -2.21), score -77 (-0.24 percent, CI -93 to
-61), legitimacy 0.410 to 0.472. So the large no_norms effect (dependency -64 percent) comes
from removing self-use reinforcement, and removing peer influence alone RAISES dependency and
legitimacy, i.e. with the current parameters peer diffusion pulls legitimacy down.

### Items noted for review (not interpreted until after Gate 3)
Numbers from the 100-seed production run BEFORE the scenario-override fix; recomputed after the
rerun. Paired by seed, bootstrap 95 percent CI (analysis/production_contrasts.py).
(a) Deadline misses are higher than baseline (16.64) in every scenario: free_market +0.67
    (CI 0.58 to 0.76), mixed_policy +1.21 (1.12 to 1.31), targeted_subsidy +1.39 (1.26 to 1.53),
    universal temporary +1.82 (1.68 to 1.96), universal permanent +1.56 (1.39 to 1.73).
    mixed_policy also has more misses than free_market (+0.54, CI 0.43 to 0.65).
(b) Gini is not lower than baseline (0.1236) in free_market (+0.0014, CI 0.0010 to 0.0019),
    mixed_policy (+0.0014, CI 0.0010 to 0.0017) and targeted_subsidy (+0.0012, CI 0.0007 to
    0.0017). targeted_subsidy vs free_market: -0.0003, CI -0.0006 to 0.0001. Only the universal
    scenarios lower gini (temporary -0.0041, permanent -0.0125 vs baseline).
(c) The access market has no population-level effect in free_market: dependency -0.0000
    (CI -0.0004 to 0.0003), calibration error +0.0001, retained ability +0.007 (CI -0.002 to
    0.016), score -5 (CI -20 to +9), 100 paired seeds.

### Morris screening, v0.4 (free_market, 23 parameters, r = 20, 3 seeds averaged per design point)
480 design points x seeds 2000-2002 = 1,440 runs in 40.1 min; manifest records git 035e766 (clean),
.venv python 3.11, SALib 1.5.2; per-seed metrics in outputs/phase2/morris_v04_runs_raw.csv (1,440 x 37).
Composite = max over metrics of column-normalised mu*. Ranking: DELTA_D 1.00, BETA_C 1.00,
P_VISIBLE 1.00, PROCESSING_DIFFICULTY_FACTOR 1.00, ABILITY_STD 1.00, ABILITY_MEAN 1.00, ETA_SELF 1.00,
PROSOCIALITY_BETA_A 0.88, ETA 0.84, ALPHA_D 0.74, GAMMA_C 0.43, CONFORMITY_BETA_B 0.34,
LAMBDA_A 0.32, ASPIRATION_GAP_WEIGHT 0.30, SBM_P_BETWEEN 0.27, RHO_RATIO 0.24, KAPPA 0.24,
BORROW_SUBSTITUTION 0.21, HOMOPHILY_SES 0.20, SBM_P_WITHIN 0.20, SHAREABLE_SEATS_TIER3 0.18,
URGENCY_WEIGHT 0.15, HOMOPHILY_ABILITY 0.14.
Caveats on the ranking itself: ai_adoption_rate is constant (1.0) in free_market, so its mu* is
undefined (NaN) and it carries no information; borrowing_agent_count and total_shared_seats_lent are
identical in every run (duplicate metric); every parameter scores 0.14 to 0.28 on the borrowing
columns, which looks like a noise floor, so composite values below about 0.3 are not
distinguishable from noise; mean_retained_ability is in absolute points and is dominated by
ABILITY_MEAN, which hides LAMBDA_A and RHO_RATIO (a relative-decline metric would not).
v0.3 Sobol set (12 parameters) vs v0.4 top 12: SBM_P_BETWEEN drops out (rank 15, 0.27); GAMMA_C enters
(rank 11). No parameter is dead in the propagation audit, but BETA_C and GAMMA_C only move
calibration error.

### Production rerun after the scenario-override fix (SUPERSEDES the production numbers and the (a),(b) contrasts above)
Fix: the access policy now runs in Phase A after the monthly tier re-evaluation (commit "fix(model):
scenario access policy runs in Phase A"). In v0.3 and in the first v0.4 production run it was a
post-step override, so every agent processed (and could borrow in) the first step of each month at
its re-evaluated tier. free_market and mixed_policy are bit-identical to the previous run (all 100
seeds); the others changed only slightly. The old files are kept as production_v04_prefix_*.csv.
Checks: baseline dependency is exactly 0.0 in all 100 seeds, baseline ever_borrowed 0, universal
permanent ever_borrowed 0 and borrowers 0 in all seeds.
100 seeds, measured values (decline is MEASURED; 21 percent was only the calibration target for permanent universal):
| scenario | decline | score | gini | dependency | calib. error | misses | legitimacy | borrowers | ever borrowed |
| baseline | 0.0% | 31,477 | 0.1235 | 0.000 | 0.000 | 16.66 | 0.000 | 0.0 | 0.0 |
| mixed_policy | 5.2% | 32,103 | 0.1250 | 0.182 | 0.347 | 17.85 | 0.369 | 16.0 | 98.7 |
| free_market | 9.9% | 32,265 | 0.1250 | 0.241 | 0.380 | 17.31 | 0.410 | 19.7 | 114.1 |
| targeted_subsidy | 17.2% | 32,548 | 0.1246 | 0.411 | 0.646 | 18.00 | 0.641 | 23.7 | 202.3 |
| universal temporary | 17.1% | 33,670 | 0.1191 | 0.376 | 0.864 | 18.52 | 0.547 | 33.4 | 208.5 |
| universal permanent | 20.7% | 35,339 | 0.1105 | 0.539 | 0.891 | 18.26 | 0.801 | 0.0 | 0.0 |
Change versus the previous run (new minus old): baseline score -11.6, gini -0.0002, misses +0.02;
targeted_subsidy score +10.8, misses -0.03; universal temporary score +27.5, misses +0.06;
universal permanent score +70.7, misses +0.06, ever borrowed -199.1; decline changes at most
0.0007. No headline changes.
Recomputed contrasts (paired by seed, bootstrap 95 percent CI):
(a) deadline misses minus baseline (16.66): free_market +0.65 (0.55 to 0.75), mixed_policy +1.19
    (1.09 to 1.30), targeted_subsidy +1.34 (1.20 to 1.49), universal temporary +1.86 (1.72 to
    2.01), universal permanent +1.60 (1.43 to 1.78).
(b) gini minus baseline (0.1235): free_market +0.0016 (0.0011 to 0.0020), mixed_policy +0.0015
    (0.0012 to 0.0018), targeted_subsidy +0.0012 (0.0007 to 0.0017); universal temporary -0.0044,
    universal permanent -0.0130.
(c) unchanged: free_market is identical to the earlier run, so the market null result stands.
No narrative interpretation until after Gate 3.

### Morris recomputed at Gate 2 (outputs/phase2/morris_v04_composite_v2.csv)
Rule fixed before computing: composite over mean_score, std_score, gini_score, mean_dependency,
mean_calibration_error, relative_ability_decline, deadline_miss_count, mean_legitimacy; retained
set = top 10 plus LAMBDA_A and RHO_RATIO forced, filled to D = 12. relative_ability_decline was
rebuilt from the saved runs (mean base ability reproduced exactly for three validation runs).
Ranking: DELTA_D 1.00, BETA_C 1.00, LAMBDA_A 1.00, PROCESSING_DIFFICULTY_FACTOR 1.00, ABILITY_STD 1.00,
ABILITY_MEAN 1.00, ETA_SELF 1.00, P_VISIBLE 0.91, ETA 0.84, ALPHA_D 0.74, RHO_RATIO 0.59, GAMMA_C 0.43,
PROSOCIALITY_BETA_A 0.39, CONFORMITY_BETA_B 0.34, ASPIRATION_GAP_WEIGHT 0.30, URGENCY_WEIGHT 0.09,
SBM_P_BETWEEN 0.08, SBM_P_WITHIN 0.08, HOMOPHILY_SES 0.08, HOMOPHILY_ABILITY 0.04,
BORROW_SUBSTITUTION 0.02, KAPPA 0.02, SHAREABLE_SEATS_TIER3 0.01.
Retained 12: DELTA_D, BETA_C, LAMBDA_A, PROCESSING_DIFFICULTY_FACTOR, ABILITY_STD, ABILITY_MEAN,
ETA_SELF, P_VISIBLE, ETA, ALPHA_D, RHO_RATIO (rank 11, forced), GAMMA_C (rank 12 fill). Differs from
option A by 2 parameters and from option B by 1.
P_VISIBLE and PROSOCIALITY_BETA_A scored high in the first ranking mainly through the borrowing
metrics, which behave like noise (every parameter scored 0.14 to 0.28 there). With borrowing
removed PROSOCIALITY_BETA_A falls from 0.88 to 0.39 (rank 13) and P_VISIBLE stays high (0.91) only
through mean_legitimacy. The network parameters (SBM_P_BETWEEN, SBM_P_WITHIN, HOMOPHILY_SES,
HOMOPHILY_ABILITY) are at the bottom of the table (0.04 to 0.08), together with KAPPA,
BORROW_SUBSTITUTION and SHAREABLE_SEATS_TIER3.

## GSA: Sobol variance decomposition, v0.4 (S1 and ST)
Design: 12 parameters (Gate 2 set), SALib.sample.sobol (scrambled, seed 20261009),
calc_second_order = False, N = 512, so 7,168 design points per scenario, bootstrap CIs with 1,000
resamples (95 percent). Scenarios: free_market and targeted_subsidy, 100 percent of runs completed, no NaN, all
sanity checks passed (sum S1 within [-0.1, 1.15], ST not below S1 beyond CI). Manifests: git 6b18c2a
(clean), .venv python 3.11, SALib 1.5.2. Files: outputs/phase2/sobol_v04_<scenario>_runs.csv
(7,168 rows each), _indices.csv, _manifest.json.
LIMITATION: ONE seed (3000) per design point, not three. Three seeds would take about 10.3 hours per
scenario (20.6 hours in total, above the 12-hour limit set at Gate 2). With one fixed seed the output
is a deterministic function of the parameters, so the indices describe sensitivity of that realisation
(including its fixed random draws), not an average over stochastic replicates. Metrics saved: the
original 12 plus relative_ability_decline. ai_adoption_rate has no variance in free_market and is
reported as degenerate.
Largest bootstrap half-width: 0.12 (S1 and ST, both scenarios); ST values within about 0.1 of each other are not distinguishable.

Total-order indices (ST) of the leading parameters, free_market / targeted_subsidy:
- mean_score: ABILITY_MEAN 0.56 / 0.53, PROCESSING_DIFFICULTY_FACTOR 0.39 / 0.40, ABILITY_STD 0.03 / 0.03,
  LAMBDA_A 0.01 / 0.04. Everything else is below 0.01.
- std_score: ABILITY_STD 0.43 / 0.44, ABILITY_MEAN 0.40 / 0.37, PROCESSING_DIFFICULTY_FACTOR 0.17 / 0.19.
- gini_score: ABILITY_MEAN 0.53 / 0.50, PROCESSING_DIFFICULTY_FACTOR 0.27 / 0.29, ABILITY_STD 0.23 / 0.22.
- deadline_miss_count: PROCESSING_DIFFICULTY_FACTOR 0.64 / 0.63, ABILITY_MEAN 0.32 / 0.23,
  LAMBDA_A 0.04 / 0.12.
- mean_dependency: DELTA_D 0.41 / 0.47, ALPHA_D 0.23 / 0.27, ETA_SELF 0.19 / 0.11, ETA 0.14 / 0.08.
- mean_calibration_error: BETA_C 0.62 / 0.64, GAMMA_C 0.13 / 0.13, DELTA_D 0.11 / 0.11, ALPHA_D 0.09 / 0.10.
- relative_ability_decline: LAMBDA_A 0.54 / 0.59, RHO_RATIO 0.16 / 0.18, ETA_SELF 0.14 / 0.09,
  ETA 0.11 / 0.06; the dependency parameters contribute about 0.03 to 0.04 each.
- mean_legitimacy: ETA_SELF 0.36 / 0.37, P_VISIBLE 0.33 / 0.31, ETA 0.30 / 0.31.
- Interaction share (sum ST minus sum S1) is small for the main metrics (0.01 to 0.2); the exception is
  borrowing_agent_count (sum S1 0.25 and 0.00, sum ST 4.05 and 7.45, with P_VISIBLE ST = 1.02 in
  targeted_subsidy, which is above the theoretical maximum of 1). Those indices are not reliable
  estimates: the metric is a small noisy count and a single seed is used. Do not interpret the
  borrowing and shared-seat indices. They are kept only because Gate 2 asked for them as outputs.
Parameter notes: BETA_C and GAMMA_C influence only mean_calibration_error (ST 0.000 on every other metric).
The two recovery parameters matter for ability only through relative_ability_decline; in the absolute
mean_retained_ability the leading parameter is ABILITY_MEAN (ST 0.85 / 0.63) and LAMBDA_A is 0.08 / 0.22.
The two scenarios rank parameters almost identically for every metric except those involving
ability erosion (LAMBDA_A gains weight in targeted_subsidy: score 0.01 to 0.04, misses 0.04 to 0.12,
decline 0.54 to 0.59) and legitimacy-driven ETA and ETA_SELF (weaker for dependency and decline in
targeted_subsidy). P_VISIBLE and PROSOCIALITY_BETA_A earned high Morris scores mostly through the
borrowing noise (see the Morris section); P_VISIBLE retains a real effect on mean_legitimacy only.
Network parameters (SBM_P_BETWEEN, SBM_P_WITHIN, HOMOPHILY_SES, HOMOPHILY_ABILITY) sit at the bottom of the Morris table and were not in the Sobol set. Narrative interpretation waits for Gate 3.

## v0.4.1 notes (Gate 4c), added 2026-10-12
- Maximum relative decline of mean retained ability the model can produce is about 34.9% (universal_permanent, seeds 1000-1029:
  0.3266 at LAMBDA_A 0.008, 0.3418 at 0.012, 0.3478 at 0.02, 0.3489 at 0.04). The sensitivity bracket for LAMBDA_A is
  therefore 10 to 31% (LAMBDA_A 0.0009 to 0.0059, measured 0.1000 and 0.3065), not 10 to 35%.
- Mechanism of the saturation is the steady state of the ability dynamics, not the ability clamp. Erosion is
  LAMBDA_A*d*u*a_r and recovery is RHO_RATIO*LAMBDA_A*(1-u)*(a_base-a_r): both scale with LAMBDA_A, so at steady state
  LAMBDA_A cancels and a_r/a_base is fixed by d and u (about 0.66 at LAMBDA_A 0.012); LAMBDA_A only sets how fast it is
  approached within 960 days. Share of agents with a_r at ABILITY_CLAMP[0] at step 960 (universal_permanent, 5 seeds,
  outputs/v041_ext/clamp_share.csv): 0.67% at 0.0009 (all of them agents whose a_base is itself 10), 0.75% at 0.00248,
  1.17% at 0.0059, 0.83% at 0.012. An earlier statement in this project that the saturation comes from the clamp was wrong.
- v0.4.1 default LAMBDA_A is 0.00248 (21.04% measured decline, seeds 1000-1029; a calibrated target, not a result).
- Aspiration (option B) is inert at ASPIRATION_GAP_WEIGHT 0.2 by the criterion in preregistration.md A2 (dependency +0.0048,
  decline +0.0058, both inside +/-0.02). Limitation: the target 10 + 90p maps a neighbour rank linearly onto the ability
  scale although ability is roughly normal.
