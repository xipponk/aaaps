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
