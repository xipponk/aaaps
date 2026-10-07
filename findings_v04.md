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
