# findings_v041.md (v0.4.1 working notes, Gate 5; exploratory unless stated)

Code: branch v0.4-recovery-fix, runs made at commit 3e0b2fd plus the later commits listed in git log (pipeline started
2026-10-12 10:40, finished 19:03, no errors). Parameters: LAMBDA_A = 0.00248, RHO_RATIO = 0.5, aspiration option B, SBM generator
with connectivity-only retry. Files: outputs/v041_main/ (untracked), tables and figures in outputs/v041_main/gate5/
(analysis/gate5_analysis.py, reads saved CSVs only, no simulation). All intervals below are paired bootstraps over seeds
(10,000 resamples, rng 20261016). Everything here is exploratory: the confirmatory seeds 7000-7099 have not been used.
v0.4.1 differs from v0.4 in LAMBDA_A, aspiration and the network generator at once, so differences between the two cannot be
attributed to one change, and no attempt is made to do so.

## 1. What v0.4 said and what v0.4.1 shows

| v0.4 claim | v0.4.1 | status |
|---|---|---|
| Removing norms (peer and self reinforcement) lowers dependency by about 64% (0.241 to 0.086) | 0.228 to 0.080 (-0.148, CI -0.151 to -0.146), -65% | holds |
| Removing peer influence alone raises dependency and legitimacy (+0.043, 0.410 to 0.472) | +0.042 (CI 0.042 to 0.043), legitimacy 0.410 to 0.472 | holds |
| Aspiration off: small effect on dependency (-0.019) | -0.0046 (CI -0.0049 to -0.0042); inert by the A2 criterion (inside +/-0.02) | changed (smaller; v0.4 aspiration was saturated at 100) |
| Access market has no population-level effect (dependency 0.0000, score -5) | dependency +0.0000 (CI -0.0003 to 0.0003); score +16.8 (CI +1.9 to +32.0), +0.05% | holds for dependency; score effect now just excludes zero but is tiny |
| none_net equals zero_interaction exactly | identical means in all five outcomes | holds |
| Every scenario has more deadline misses than baseline | +0.79 (free_market), +1.10, +1.53, +1.78, +1.39, all CIs above 0 | holds |
| Gini is not lower than baseline in free_market, mixed, targeted | +0.002 (CI 0.002 to 0.002), +0.002, +0.002 | holds |
| Universal access lowers gini (-0.004 temporary, -0.013 permanent) | -0.002 (CI -0.003 to -0.002), -0.009 (CI -0.010 to -0.009) | holds in sign, weaker |
| Score ordering baseline < mixed < free < targeted < universal temporary < permanent | same ordering (31,477; 32,029; 32,136; 32,343; 33,363; 34,840) | holds |
| Dependency, permanent universal 0.539 | 0.494 | changed (aspiration no longer pushes use up) |
| Legitimacy, universal temporary 0.547 | 0.593 | changed |
| Morris: top 12 are DELTA_D, BETA_C, LAMBDA_A, PROCESSING_DIFFICULTY_FACTOR, ABILITY_STD, ABILITY_MEAN, ETA_SELF, P_VISIBLE, ETA, ALPHA_D, RHO_RATIO, GAMMA_C | same 12 in the same order | holds |
| Morris: ASPIRATION_GAP_WEIGHT borderline (composite 0.303) | 0.145, rank 15 | changed (consistent with the inert aspiration channel) |
| Morris: network parameters at the bottom (0.04 to 0.08) | 0.025 to 0.061 (ranks 17 to 20) | holds, but see limits in section 5 |
| Sobol: parameter leader of each metric | same leader in all 24 metric-scenario pairs | holds |

Nothing in the v0.4 list is dropped. The claims that rested on the aspiration channel (v0.4 dependency effect 0.019,
ASPIRATION_GAP_WEIGHT near the noise threshold) are the ones that weaken.

## 2. LAMBDA_A is a speed parameter, and the saturation is not the clamp
Erosion is LAMBDA_A*d*u*a_r and recovery is rho*(1-u)*(a_base-a_r) with rho = RHO_RATIO*LAMBDA_A (agents.py:327-330). Both
terms are proportional to LAMBDA_A, so at a steady state with fixed d and u it cancels:
a_r/a_base = RHO_RATIO*(1-u) / (d*u + RHO_RATIO*(1-u)). LAMBDA_A sets only how fast that ratio is approached. The 21% decline
is therefore a transient at the 960-day horizon, not a long-run level. The long-run decline the model can produce is about
34.9% (universal_permanent, seeds 1000-1029: 0.3266 at LAMBDA_A 0.008, 0.3418 at 0.012, 0.3478 at 0.02, 0.3489 at 0.04), and it
is fixed by d, u and RHO_RATIO. d and u are endogenous and time-varying, so the formula is a guide to the mechanism, not a
prediction; it was not checked against agent-level data in this analysis. The sensitivity bracket for LAMBDA_A is therefore
10 to 31% (LAMBDA_A 0.0009 to 0.0059; measured 0.1000 and 0.3065). The calibrated 21% (LAMBDA_A 0.00248, measured 0.2104) is
a target, not a result; measured declines are reported per scenario below.
Correction: earlier in this project the flattening of the decline was attributed to retained ability hitting
ABILITY_CLAMP[0]. That was wrong. Share of agents with a_r at the clamp at step 960 in universal_permanent (5 seeds,
outputs/v041_ext/clamp_share.csv): 0.67% at LAMBDA_A 0.0009 (all of them agents whose a_base is itself 10), 0.75% at 0.00248,
1.17% at 0.0059, 0.83% at 0.012.

## 3. Production, 100 seeds per scenario (mean; paired difference vs baseline [95% CI])
| scenario | score | gini | misses | decline | dependency | calib. error | legitimacy |
|---|---|---|---|---|---|---|---|
| baseline | 31,477 | 0.123 | 16.66 | 0 | 0 | 0 | 0 |
| free_market | 32,136 (+659 [635, 682]) | 0.125 (+0.002) | 17.45 (+0.79 [0.69, 0.90]) | 0.103 | 0.228 | 0.372 | 0.410 |
| mixed_policy | 32,029 (+551 [527, 576]) | 0.125 (+0.002) | 17.76 (+1.10 [0.98, 1.20]) | 0.054 | 0.170 | 0.336 | 0.371 |
| targeted_subsidy | 32,343 (+866 [841, 891]) | 0.126 (+0.002) | 18.19 (+1.53 [1.39, 1.67]) | 0.175 | 0.384 | 0.627 | 0.643 |
| universal_access | 33,363 (+1,886 [1,862, 1,909]) | 0.121 (-0.002) | 18.44 (+1.78 [1.62, 1.93]) | 0.173 | 0.364 | 0.834 | 0.593 |
| universal_permanent | 34,840 (+3,363 [3,341, 3,385]) | 0.114 (-0.009) | 18.05 (+1.39 [1.22, 1.56]) | 0.207 | 0.494 | 0.856 | 0.804 |
Full table with every CI: outputs/v041_main/gate5/production_comparison.csv (v0.4 and v0.4.1). Measured declines are not
targets. Score and misses move together: every AI scenario scores higher and misses more deadlines than baseline.

## 4. Interaction isolation (free_market, seeds 0-99, exploratory)
| condition | dependency | legitimacy | calib. error | score | gini |
|---|---|---|---|---|---|
| full | 0.2283 | 0.4103 | 0.3718 | 32,136 | 0.1254 |
| no_norms | 0.0799 | 0.1000 | 0.2339 | 31,818 | 0.1221 |
| no_peer_norms | 0.2705 | 0.4719 | 0.3852 | 32,014 | 0.1280 |
| no_aspiration | 0.2238 | 0.4104 | 0.3690 | 32,129 | 0.1251 |
| no_market | 0.2284 | 0.4103 | 0.3719 | 32,153 | 0.1253 |
| none_net | 0.0778 | 0.1000 | 0.2301 | 31,811 | 0.1220 |
| zero_interaction | 0.0778 | 0.1000 | 0.2301 | 31,811 | 0.1220 |
Paired CIs against full are in outputs/v041_main/gate5/isolation_table.csv.
H_self statistic S = (D_x - D_zero)/(D_full - D_zero), ratio of paired means (EXPLORATORY, seeds 0-99; the confirmatory value
comes only from seeds 7000-7099 and the self_only mode, which does not exist yet). With no_peer_norms as a proxy for
self_only (ETA = 0, ETA_SELF kept, aspiration and market on): S = 1.280 (bootstrap 1.276 to 1.284), D_full - D_zero = +0.151.
S above 1 means peer influence works against dependency. The proxy is not the preregistered statistic.
Caveat that matters for interpretation: the interaction effect on dependency is mostly the rise of legitimacy from its initial
0.10 through ETA_SELF (use raises legitimacy, which raises use). The initial value 0.10 is a literal in agents.py:113, not a
tagged parameter in config/params.py (breaks engineering rule 1) and has never been varied. Part of the H_self result may
therefore be assumption-forced.

## 5. Morris (23 parameters, r = 20, 3 seeds per design point)
Rank order of the top 12 is unchanged from v0.4. Composite (max over eight metrics of normalised mu*): ranks 1 to 7 all 1.000,
P_VISIBLE 0.893, ETA 0.859, ALPHA_D 0.742, RHO_RATIO 0.688, GAMMA_C 0.441, PROSOCIALITY_BETA_A 0.359, CONFORMITY_BETA_B 0.329,
ASPIRATION_GAP_WEIGHT 0.145, URGENCY_WEIGHT 0.117, HOMOPHILY_SES 0.061, SBM_P_BETWEEN 0.040, HOMOPHILY_ABILITY 0.037,
SBM_P_WITHIN 0.025, BORROW_SUBSTITUTION 0.023, KAPPA 0.018, SHAREABLE_SEATS_TIER3 0.017. mu* and sigma of each parameter on
its top metric, for both versions: outputs/v041_main/gate5/morris_table.csv.
- Network parameters now rank 17 to 20 with no silent fallback (v0.4: 17 to 20 too, values 0.039 to 0.082, from runs where 55.6%
  of design points used the fallback). They remain low. Limit: the composite covers population means and the gini and standard
  deviation of scores, not the tercile gap, so "network does not move the means" is all this shows. The network sweep is the test
  for inequality.
- KAPPA rank 22 (0.018) and ASPIRATION_GAP_WEIGHT rank 15 (0.145): consistent with the inert aspiration channel.
- RHO_RATIO is rank 11 on its own (0.688), so the force rule did not change the set. Ranks 9 to 12 all exceed 0.3 (0.859, 0.742,
  0.688, 0.441). PROSOCIALITY_BETA_A (0.359) and CONFORMITY_BETA_B (0.329) are also above 0.3 but fall outside the top 12 by the
  fixed rule.

## 6. Sobol (N = 512, D = 12, one seed 3000 per design point, 7,168 runs per scenario)
Leader by total-order index, free_market / targeted_subsidy (ST with 95% CI half-width); v0.4 leader identical in every case:
mean_score ABILITY_MEAN 0.566 (0.069) / 0.542; std_score ABILITY_STD 0.434 / 0.442; gini_score ABILITY_MEAN 0.537 / 0.507;
mean_dependency DELTA_D 0.423 (0.054) / 0.480; mean_calibration_error BETA_C 0.594 / 0.611; relative_ability_decline LAMBDA_A
0.470 (0.072) / 0.526 (v0.4: 0.535 / 0.593, both inside the CIs); deadline_miss_count PROCESSING_DIFFICULTY_FACTOR 0.644 / 0.637;
deadline_miss_rate same parameter 0.608 / 0.604; mean_retained_ability ABILITY_MEAN 0.875 / 0.692; mean_legitimacy ETA_SELF
0.361 (0.050) / 0.370.
Sum of first-order indices (interaction share is 1 minus this): 0.96 to 1.00 for score, std, gini, dependency; 0.91 and 0.90 for
decline; 0.90 and 0.88 for deadline metrics. Every S1, ST and CI for every metric and parameter, both versions:
outputs/v041_main/gate5/sobol_all_indices_both_versions.csv; leaders: sobol_leaders.csv.
The borrowing metrics (borrowing_agent_count and total_shared_seats_lent, identical to each other) stay UNRELIABLE: P_VISIBLE
has ST 0.967 in both scenarios (v0.4: 0.953, 1.022) but the sum of S1 is only 0.52 and 0.08, and the linear correlation of
the count with P_VISIBLE is 0.76 and 0.49. They are not used.
mean_legitimacy: ETA_SELF, P_VISIBLE and ETA are within each other's CI (free_market ST 0.361, 0.328, 0.299, half-widths
0.05, 0.04, 0.04); the leader label is not statistically separated. Legitimacy is not a headline outcome.

## 7. Limits and flags
- Sobol uses one seed and one network realisation per design point (plus rewiring variation); indices describe that realisation.
- Aspiration target 10 + 90p maps a neighbour rank linearly onto the ability scale although ability is roughly normal
  (accepted limitation, no change).
- Initial legitimacy 0.10 is a literal in agents.py:113 and untested (section 4).
- Aspiration test thresholds were relaxed after seeing the first diagnostics (design_v041.md section 6.2).
- Budzyn et al. ADR figures are not used; the 21% remains a calibration target.
