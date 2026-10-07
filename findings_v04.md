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
   controlled this correlation. Decision pending: change the paper to about 0.39, or change
   the weights to hit 0.30.
3. Recovery multiplier (manuscript line 519 uses 1 - u(t), as quoted). Code uses
   practice = 1 - daily_u, where daily_u is the effort-weighted mean of per-task u over the
   tasks processed that day (model/agents.py, update_coupled_dynamics). These are the same
   quantity when u(t) means the daily aggregate. Caveat from spec_check_c.json (free_market,
   seed 7, 230,400 agent-days): 5.2 percent of agent-days had no task at all and still count
   as full practice (practice = 1); 66.1 percent had tasks but zero AI use; 28.6 percent had
   AI use. So "practice" means "did not use AI today", and idle days give full recovery.
4. Calibration error (c) is terminal: BETA_C and GAMMA_C change only the calibration error
   metric in the propagation audit, nothing else. c does not feed back into behaviour or score.
5. The retained-ability floor was a literal 10.0 in agents.py. It now reads P.ABILITY_CLAMP[0].
   The aspiration clip in model.py (10.0, 100.0) is still literal (behaviour-neutral, not changed).
