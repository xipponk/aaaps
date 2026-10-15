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

## 8. Gate 6: confirmatory results (numbers copied from results_confirmatory.md, no narrative)

Source: results_confirmatory.md (commit b687677), written by analysis/confirmatory_analysis.py, sha256 8908021ded52dcaa934a62b7814907598056607c242ae749c3e520f2f44dbe97 (equal in sha256sum, the file header and the six runner manifests). Seeds 7000-7099, 14,900 runs, pipeline 2026-10-12 to 2026-10-13, no errors. The statement at the top of this file that confirmatory seeds were unused applies to sections 1 to 7 only. Sections 1 to 7 are exploratory; this section 8 is split below. Tables are copied unchanged; csv files are in outputs/v041_conf/results/ (force-added in b687677).

### 8.1 CONFIRMATORY (preregistered rules, A3)

#### Family 1: co-primary tests on E_G(s, k = 0), Holm over two tests, alpha = 0.05
G(baseline) = 14339.5 (mean over 100 seeds). SESOI for E_G = 5% of it = 717.0. Pivot P1.
| scenario | E_G_k0 | relative | p_H0 | TOST_equiv | CI90 | Holm_reject_H0 |
|---|---|---|---|---|---|---|
| universal_permanent | -1042.1 [-1106.0, -979.1] | -0.0727 | 1.0000 | False | [-1096.2, -988.7] | False |
| free_market | -82.6 [-150.6, -16.4] | -0.0058 | 1.0000 | True | [-138.9, -27.0] | False |
H0: E_G(s, 0) <= +SESOI. Rejecting H0 means the gap widening exceeds the SESOI with the benefit made ability-independent.

#### k*, linearity, states and narratives (pre-declared rules of sections 5 to 7)
| scenario | k | E_G | relative | state | label |
|---|---|---|---|---|---|
| free_market | 1.0000 | 231.6 [157.6, 302.2] | 0.0161 | not present at k = 1 | confirmatory-rule |
| free_market | 0.5000 | 89.2 [23.4, 151.9] | 0.0062 | n/a (E_G(s,1) not present) | confirmatory-rule |
| free_market | 0.0000 | -82.6 [-150.6, -16.4] | -0.0058 | n/a (E_G(s,1) not present) | confirmatory-rule |
| free_market | -0.5000 | -243.8 [-314.2, -177.6] | -0.0170 | n/a (E_G(s,1) not present) | confirmatory-rule |
| free_market | -1.0000 | -437.6 [-512.9, -363.3] | -0.0305 | n/a (E_G(s,1) not present) | confirmatory-rule |
| universal_permanent | 1.0000 | 224.5 [165.3, 282.6] | 0.0157 | not present at k = 1 | confirmatory-rule |
| universal_permanent | 0.5000 | -383.3 [-444.7, -322.3] | -0.0267 | n/a (E_G(s,1) not present) | confirmatory-rule |
| universal_permanent | 0.0000 | -1042.1 [-1106.0, -979.1] | -0.0727 | n/a (E_G(s,1) not present) | confirmatory-rule |
| universal_permanent | -0.5000 | -1666.8 [-1735.0, -1601.1] | -0.1162 | n/a (E_G(s,1) not present) | confirmatory-rule |
| universal_permanent | -1.0000 | -2303.2 [-2374.6, -2232.0] | -0.1606 | n/a (E_G(s,1) not present) | confirmatory-rule |

| scenario | k_star | CI95_over_crossing_resamples | share_no_crossing | max_dev_from_line | linearity_flag | label |
|---|---|---|---|---|---|---|
| free_market | 0.240 | [0.053, 0.426] | 0.000 | 26.499 | True | confirmatory-rule |
| mixed_policy | 0.174 | [-0.033, 0.369] | 0.000 | 27.925 | True | exploratory |
| targeted_subsidy | 0.021 | [-0.123, 0.190] | 0.000 | 38.492 | False | exploratory |
| universal_access | 0.449 | [0.384, 0.520] | 0.000 | 27.320 | False | exploratory |
| universal_permanent | 0.815 | [0.770, 0.861] | 0.000 | 24.164 | True | confirmatory-rule |

E_G(s, 1) is NOT present for both co-primary scenarios: per section 5 the claim 'AI widens the gap' is reported as absent in v0.4.1 and the narrative rules are not applied.

#### Interaction clause (section 7 with the A3 decomposition): full - zero = social + individual
social = full - self_only; individual = self_only - zero_interaction. driven: CI95 beyond +/-SESOI; null: CI90 inside (-SESOI, +SESOI); else indeterminate. Pivot P1. Full table for all five scenarios: interaction_decomposition.csv.
| scenario | k | outcome | full_minus_zero | full_minus_zero_class | social | social_class | individual | individual_class | individual_share |
|---|---|---|---|---|---|---|---|---|---|
| free_market | 1.000 | mean_dependency | 0.1521 [0.1498, 0.1544] | driven | -0.0371 [-0.0377, -0.0366] | driven | 0.1892 [0.1867, 0.1918] | driven | 1.244 |
| free_market | 1.000 | gini_score | 0.0033 [0.0029, 0.0037] | null | -0.0021 [-0.0024, -0.0018] | null | 0.0054 [0.0050, 0.0058] | indeterminate | nan |
| free_market | 1.000 | mean_calibration_error | 0.1427 [0.1406, 0.1448] | driven | -0.0111 [-0.0114, -0.0109] | null | 0.1539 [0.1517, 0.1561] | driven | 1.078 |
| free_market | 1.000 | relative_ability_decline | 0.0934 [0.0918, 0.0951] | driven | -0.0400 [-0.0407, -0.0393] | driven | 0.1334 [0.1312, 0.1356] | driven | 1.428 |
| free_market | 1.000 | deadline_miss_count | 1.0809 [0.9767, 1.1870] | driven | -1.5704 [-1.6568, -1.4854] | driven | 2.6513 [2.5160, 2.7917] | driven | 2.453 |
| free_market | 1.000 | G | 349.1800 [290.9388, 405.6861] | null | -202.0097 [-246.6750, -159.4514] | null | 551.1897 [496.6496, 605.9775] | null | nan |
| free_market | 0.000 | mean_dependency | 0.1519 [0.1496, 0.1541] | driven | -0.0374 [-0.0379, -0.0368] | driven | 0.1892 [0.1867, 0.1918] | driven | 1.246 |
| free_market | 0.000 | gini_score | 0.0022 [0.0017, 0.0026] | null | -0.0017 [-0.0020, -0.0014] | null | 0.0038 [0.0034, 0.0042] | null | nan |
| free_market | 0.000 | mean_calibration_error | 0.1426 [0.1405, 0.1447] | driven | -0.0112 [-0.0115, -0.0109] | null | 0.1539 [0.1517, 0.1561] | driven | 1.079 |
| free_market | 0.000 | relative_ability_decline | 0.0934 [0.0917, 0.0950] | driven | -0.0401 [-0.0408, -0.0394] | driven | 0.1334 [0.1312, 0.1356] | driven | 1.429 |
| free_market | 0.000 | deadline_miss_count | 1.0800 [0.9864, 1.1772] | driven | -1.5712 [-1.6604, -1.4832] | driven | 2.6513 [2.5160, 2.7917] | driven | 2.455 |
| free_market | 0.000 | G | 145.9757 [87.0814, 203.8765] | null | -159.0486 [-203.2787, -116.1266] | null | 305.0244 [248.1280, 361.9261] | null | nan |
| universal_permanent | 1.000 | mean_dependency | 0.3397 [0.3383, 0.3412] | driven | -0.0401 [-0.0407, -0.0396] | driven | 0.3798 [0.3784, 0.3813] | driven | 1.118 |
| universal_permanent | 1.000 | gini_score | -0.0025 [-0.0029, -0.0021] | null | -0.0004 [-0.0007, -0.0001] | null | -0.0021 [-0.0025, -0.0016] | null | nan |
| universal_permanent | 1.000 | mean_calibration_error | 0.3722 [0.3707, 0.3736] | driven | -0.0176 [-0.0179, -0.0173] | null | 0.3897 [0.3883, 0.3912] | driven | 1.047 |
| universal_permanent | 1.000 | relative_ability_decline | 0.1886 [0.1871, 0.1900] | driven | -0.0355 [-0.0361, -0.0350] | driven | 0.2241 [0.2223, 0.2259] | driven | 1.188 |
| universal_permanent | 1.000 | deadline_miss_count | 2.5732 [2.4280, 2.7223] | driven | -1.4684 [-1.5516, -1.3860] | driven | 4.0416 [3.8659, 4.2172] | driven | 1.571 |
| universal_permanent | 1.000 | G | 569.5429 [517.0641, 623.1410] | null | -175.9946 [-222.1867, -127.9544] | null | 745.5376 [685.6443, 805.0870] | indeterminate | nan |
| universal_permanent | 0.000 | mean_dependency | 0.3390 [0.3376, 0.3404] | driven | -0.0408 [-0.0414, -0.0403] | driven | 0.3798 [0.3784, 0.3813] | driven | 1.120 |
| universal_permanent | 0.000 | gini_score | -0.0079 [-0.0083, -0.0074] | driven | 0.0004 [0.0002, 0.0007] | null | -0.0083 [-0.0088, -0.0078] | driven | 1.054 |
| universal_permanent | 0.000 | mean_calibration_error | 0.3716 [0.3701, 0.3731] | driven | -0.0181 [-0.0184, -0.0178] | null | 0.3897 [0.3883, 0.3912] | driven | 1.049 |
| universal_permanent | 0.000 | relative_ability_decline | 0.1884 [0.1870, 0.1898] | driven | -0.0357 [-0.0363, -0.0352] | driven | 0.2241 [0.2223, 0.2259] | driven | 1.190 |
| universal_permanent | 0.000 | deadline_miss_count | 2.6114 [2.4716, 2.7533] | driven | -1.4302 [-1.5193, -1.3418] | driven | 4.0416 [3.8659, 4.2172] | driven | 1.548 |
| universal_permanent | 0.000 | G | -314.4999 [-371.8056, -256.6345] | null | -88.0599 [-132.8707, -41.0823] | null | -226.4399 [-287.2138, -165.3707] | null | nan |

#### Family 2: H_self (free_market, k = 1, mean_dependency, alpha = 0.05)
D_full = 0.2311, D_self = 0.2682, D_zero = 0.0790. D_full - D_zero = 0.1521 [0.1498, 0.1544] (beyond SESOI 0.02: True).
S = (D_self - D_zero)/(D_full - D_zero) = 1.244, 95% CI [1.240, 1.248]. Verdict by the preregistered rule: **SUPPORTED**.
Decomposition: individual = 0.1892 [0.1867, 0.1918], social = -0.0371 [-0.0377, -0.0366].

#### Network sweep corroboration of H_self (free_market, k = 1, one-at-a-time, 17 points)
| parameter | level | diff | lo95 | hi95 | tost_p | beyond_0p04 | holm_alpha | equivalent_holm |
|---|---|---|---|---|---|---|---|---|
| h_ability | 0.0000 | -0.0003 | -0.0006 | 0.0001 | 0.0000 | False | 0.0125 | True |
| h_ability | 0.5000 | -0.0003 | -0.0006 | 0.0000 | 0.0000 | False | 0.0167 | True |
| h_ability | 0.7500 | 0.0001 | -0.0002 | 0.0006 | 0.0000 | False | 0.0250 | True |
| h_ability | 1.0000 | 0.0003 | -0.0001 | 0.0007 | 0.0000 | False | 0.0500 | True |
| h_ses | 0.0000 | -0.0018 | -0.0022 | -0.0014 | 0.0000 | False | 0.0063 | True |
| h_ses | 0.4000 | 0.0014 | 0.0010 | 0.0018 | 0.0000 | False | 0.0071 | True |
| h_ses | 0.6000 | 0.0030 | 0.0027 | 0.0034 | 0.0000 | False | 0.0083 | True |
| h_ses | 0.8000 | 0.0047 | 0.0043 | 0.0051 | 0.0000 | False | 0.0100 | True |
| p_between | 0.0050 | 0.0000 | -0.0004 | 0.0005 | 0.0000 | False | 0.0042 | True |
| p_between | 0.0300 | -0.0003 | -0.0007 | 0.0001 | 0.0000 | False | 0.0045 | True |
| p_between | 0.0600 | -0.0005 | -0.0009 | -0.0001 | 0.0000 | False | 0.0050 | True |
| p_between | 0.1200 | -0.0006 | -0.0010 | -0.0001 | 0.0000 | False | 0.0056 | True |
| p_within | 0.1000 | 0.0000 | -0.0004 | 0.0004 | 0.0000 | False | 0.0031 | True |
| p_within | 0.1400 | -0.0003 | -0.0007 | 0.0001 | 0.0000 | False | 0.0033 | True |
| p_within | 0.2500 | -0.0002 | -0.0006 | 0.0001 | 0.0000 | False | 0.0036 | True |
| p_within | 0.3500 | -0.0005 | -0.0008 | -0.0001 | 0.0000 | False | 0.0038 | True |
Rule: supports if all 16 contrasts are equivalent to 0 at SESOI 0.02 (TOST, Holm over 16); contradicts if any full contrast has 95% CI beyond +/-0.04. Result: **SUPPORTS H_self** (all equivalent: True; any beyond 0.04: False).

no_norms check (dependency contrasts against the no_norms default point; expected flat):
| parameter | level | diff | lo95 | hi95 |
|---|---|---|---|---|
| p_within | 0.1000 | 0.0002 | 0.0001 | 0.0003 |
| p_within | 0.1400 | 0.0002 | 0.0001 | 0.0003 |
| p_within | 0.2500 | -0.0000 | -0.0001 | 0.0001 |
| p_within | 0.3500 | -0.0001 | -0.0002 | -0.0000 |
| p_between | 0.0050 | 0.0001 | 0.0000 | 0.0002 |
| p_between | 0.0300 | -0.0001 | -0.0001 | 0.0000 |
| p_between | 0.0600 | -0.0001 | -0.0002 | -0.0000 |
| p_between | 0.1200 | -0.0002 | -0.0003 | -0.0001 |
| h_ses | 0.0000 | 0.0001 | -0.0000 | 0.0001 |
| h_ses | 0.4000 | 0.0000 | -0.0001 | 0.0001 |
| h_ses | 0.6000 | -0.0001 | -0.0001 | 0.0000 |
| h_ses | 0.8000 | -0.0001 | -0.0001 | 0.0000 |
| h_ability | 0.0000 | 0.0000 | -0.0000 | 0.0001 |
| h_ability | 0.5000 | 0.0001 | 0.0000 | 0.0002 |
| h_ability | 0.7500 | 0.0002 | 0.0001 | 0.0003 |
| h_ability | 1.0000 | 0.0002 | 0.0001 | 0.0003 |

### 8.2 EXPLORATORY (no multiplicity control)

#### P2 (level-matched pivot) vs P1, E_G, mode full
| scenario | k | E_G_P1 | E_G_P2 | mean_pivot_P2 | mean_pivot_P1 |
|---|---|---|---|---|---|
| universal_permanent | 0.0000 | -1042.1 [-1106.0, -979.1] | -1134.0 [-1193.5, -1075.6] | 0.4485 | 0.5007 |
| universal_permanent | -1.0000 | -2303.2 [-2374.6, -2232.0] | -2467.8 [-2528.4, -2408.5] | 0.4485 | 0.5007 |
| free_market | 0.0000 | -82.6 [-150.6, -16.4] | -87.3 [-155.1, -23.0] | 0.4744 | 0.5007 |
| free_market | -1.0000 | -437.6 [-512.9, -363.3] | -450.0 [-525.0, -375.9] | 0.4744 | 0.5007 |

#### Channel ablations at k = 1 (E_G vs baseline, dependency, decline)
| ablation | scenario | mode | E_G | dependency | decline | score |
|---|---|---|---|---|---|---|
| quality_only | universal_permanent | full | 4474.4 [4395.9, 4555.5] | 0.5423 | 0.2520 | 31830.3878 |
| quality_only | universal_permanent | zero_interaction | 777.7 [738.7, 816.1] | 0.1590 | 0.0209 | 32112.1799 |
| quality_only | free_market | full | 1642.7 [1579.1, 1707.1] | 0.2428 | 0.1170 | 31260.5208 |
| quality_only | free_market | zero_interaction | 286.6 [250.0, 322.5] | 0.0802 | 0.0120 | 31692.4157 |
| speed_only | universal_permanent | full | -1924.6 [-1985.5, -1863.7] | 0.4958 | 0.2075 | 32496.4023 |
| speed_only | universal_permanent | zero_interaction | -962.0 [-1010.8, -914.2] | 0.1554 | 0.0196 | 32108.1288 |
| speed_only | free_market | full | -318.0 [-371.3, -265.2] | 0.2296 | 0.1034 | 31602.6451 |
| speed_only | free_market | zero_interaction | -299.5 [-340.0, -259.1] | 0.0790 | 0.0115 | 31706.0389 |

#### C1 calibration complementarity (E_G vs baseline; mean g_c at step 960)
| scenario | mode | E_G | g_c_960 | score |
|---|---|---|---|---|
| free_market | full | -242.3 [-300.9, -185.1] | 0.3127 | 31852.4115 |
| free_market | zero_interaction | -255.3 [-297.2, -213.8] | 0.3841 | 31822.6392 |
| mixed_policy | full | -131.6 [-185.5, -78.8] | 0.3307 | 31870.0533 |
| mixed_policy | zero_interaction | -131.2 [-181.6, -82.0] | 0.4038 | 31750.1158 |
| targeted_subsidy | full | -282.2 [-347.8, -216.4] | 0.1808 | 31874.1234 |
| targeted_subsidy | zero_interaction | -307.9 [-348.7, -266.5] | 0.3103 | 31932.3779 |
| universal_access | full | -700.9 [-761.5, -642.3] | 0.0826 | 32668.8486 |
| universal_access | zero_interaction | -516.8 [-564.3, -470.0] | 0.2584 | 32220.5997 |
| universal_permanent | full | -1606.6 [-1666.4, -1549.8] | 0.0716 | 33523.7789 |
| universal_permanent | zero_interaction | -805.1 [-854.4, -756.3] | 0.2586 | 32536.0922 |
E_G under C1 is to be read within a scenario only (A1/A2).

#### Sensitivity to the initial legitimacy L0 (free_market, k = 1)
| L0 | D_full | D_self | D_zero | S | S_lo95 | S_hi95 |
|---|---|---|---|---|---|---|
| 0.0500 | 0.2310 | 0.2680 | 0.0529 | 1.2077 | 1.2048 | 1.2106 |
| 0.1000 | 0.2311 | 0.2682 | 0.0790 | 1.2442 | 1.2405 | 1.2480 |
| 0.2000 | 0.2310 | 0.2681 | 0.1172 | 1.3256 | 1.3203 | 1.3312 |
| 0.3000 | 0.2311 | 0.2681 | 0.1466 | 1.4375 | 1.4291 | 1.4461 |

#### Diagnostics
| scenario | k | g_s1 | g_s480 | g_s960 | clip_count | decline |
|---|---|---|---|---|---|---|
| free_market | 1.0000 | 0.5007 | 0.4732 | 0.4482 | 0.0000 | 0.1049 |
| free_market | 0.5000 | 0.5007 | 0.4870 | 0.4744 | 0.0000 | 0.1049 |
| free_market | 0.0000 | 0.5007 | 0.5007 | 0.5007 | 0.0000 | 0.1049 |
| free_market | -0.5000 | 0.5007 | 0.5144 | 0.5269 | 0.0000 | 0.1048 |
| free_market | -1.0000 | 0.5007 | 0.5281 | 0.5533 | 14.7800 | 0.1050 |
| mixed_policy | 1.0000 | 0.5007 | 0.4867 | 0.4732 | 0.0000 | 0.0550 |
| mixed_policy | 0.5000 | 0.5007 | 0.4938 | 0.4869 | 0.0000 | 0.0550 |
| mixed_policy | 0.0000 | 0.5007 | 0.5007 | 0.5007 | 0.0000 | 0.0550 |
| mixed_policy | -0.5000 | 0.5007 | 0.5077 | 0.5145 | 0.0000 | 0.0550 |
| mixed_policy | -1.0000 | 0.5007 | 0.5146 | 0.5282 | 14.9500 | 0.0549 |
| targeted_subsidy | 1.0000 | 0.5007 | 0.4537 | 0.4111 | 0.0000 | 0.1789 |
| targeted_subsidy | 0.5000 | 0.5007 | 0.4772 | 0.4559 | 0.0000 | 0.1789 |
| targeted_subsidy | 0.0000 | 0.5007 | 0.5007 | 0.5007 | 0.0000 | 0.1790 |
| targeted_subsidy | -0.5000 | 0.5007 | 0.5243 | 0.5455 | 0.0000 | 0.1789 |
| targeted_subsidy | -1.0000 | 0.5007 | 0.5479 | 0.5903 | 1.5000 | 0.1790 |
| universal_access | 1.0000 | 0.5007 | 0.4463 | 0.4134 | 0.0000 | 0.1744 |
| universal_access | 0.5000 | 0.5007 | 0.4735 | 0.4571 | 0.0000 | 0.1743 |
| universal_access | 0.0000 | 0.5007 | 0.5007 | 0.5007 | 0.0000 | 0.1745 |
| universal_access | -0.5000 | 0.5007 | 0.5280 | 0.5444 | 0.0000 | 0.1745 |
| universal_access | -1.0000 | 0.5007 | 0.5552 | 0.5880 | 1.3000 | 0.1744 |
| universal_permanent | 1.0000 | 0.5007 | 0.4463 | 0.3965 | 0.0000 | 0.2082 |
| universal_permanent | 0.5000 | 0.5007 | 0.4735 | 0.4486 | 0.0000 | 0.2082 |
| universal_permanent | 0.0000 | 0.5007 | 0.5007 | 0.5007 | 0.0000 | 0.2080 |
| universal_permanent | -0.5000 | 0.5007 | 0.5280 | 0.5528 | 0.0000 | 0.2083 |
| universal_permanent | -1.0000 | 0.5007 | 0.5552 | 0.6049 | 1.3000 | 0.2081 |

Realised network over all runs with a network (min / mean / max):
| index | net_attempts | net_k_bar | net_within_section_share |
|---|---|---|---|
| min | 1.000 | 6.300 | 0.197 |
| mean | 1.032 | 10.843 | 0.562 |
| max | 7.000 | 32.383 | 0.790 |

Not copied here (in results_confirmatory.md): levels by scenario and k, terciles, density-controlled sweep, full network ranges, no_norms check.

## 9. Gate 7: A4 channel-ratio sweep, D1 diagnostic and replication (all EXPLORATORY; numbers copied from results_a4.md, no narrative)

Source: results_a4.md (commit f7d3e7c), analysis/a4_analysis.py sha256 73b4fd610f13ace59684c8017beeb7cc904e3295fb2f3e4fdf8578a8526c878b (equal in sha256sum
and the file header), runs at git a3f204d, pipeline 2026-10-15 10:33 to 12:52, no errors, R0 hash pre-check and post-check passed. Seeds 8000-8099 (A4)
and 8100-8104 (D1). Amendment A4 in preregistration.md. All of it is post hoc and exploratory.

### 9.1 Replication: R3 (default boost) on seeds 8000-8099 against the confirmatory run on seeds 7000-7099 (no statistical test)
Confirmatory k* uses the grid k in {1, 0.5, 0, -0.5, -1}; the A4 k* uses the grid {1, 0.5, 0} only.
| scenario | quantity | confirmatory, seeds 7000-7099 (results_confirmatory.md) | A4 R3, seeds 8000-8099 (results_a4.md) |
|---|---|---|---|
| free_market | E_G at k = 1 | 231.6 [157.6, 302.2] | 287.9 [227.8, 350.9] |
| free_market | E_G at k = 0 | -82.6 [-150.6, -16.4] | -66.3 [-126.7, -5.0] |
| free_market | k* | 0.240 [0.053, 0.426] | 0.177 [0.038, 0.322] |
| universal_permanent | E_G at k = 1 | 224.5 [165.3, 282.6] | 255.9 [199.7, 315.5] |
| universal_permanent | E_G at k = 0 | -1042.1 [-1106.0, -979.1] | -1005.9 [-1068.9, -940.0] |
| universal_permanent | k* | 0.815 [0.770, 0.861] | 0.813 [0.771, 0.852] |

### 9.2 A4 tables
#### Levels: E_G, mean score gain vs baseline, g_mean_960 (mean over seeds of mean g_k at step 960)
E_G_vs_SESOI: CI95 of E_G entirely above +SESOI, entirely below -SESOI, or inside (overlapping).
| scenario | k | level | E_G | score_gain | g_mean_960 | mean_dependency | clip_count | E_G_vs_SESOI |
|---|---|---|---|---|---|---|---|---|
| universal_permanent | 1.0000 | R0 | -1898.1 [-1954.5, -1838.4] | 950.7 [928.7, 972.4] | 0.3963 | 0.4974 | 0.0000 | below |
| universal_permanent | 1.0000 | R1 | -1368.0 [-1422.9, -1310.0] | 1568.4 [1547.4, 1589.9] | 0.3962 | 0.4970 | 0.0000 | below |
| universal_permanent | 1.0000 | R2 | -779.5 [-833.3, -722.8] | 2198.7 [2179.4, 2218.4] | 0.3961 | 0.4966 | 0.0000 | below |
| universal_permanent | 1.0000 | R3 | 255.9 [199.7, 315.5] | 3392.3 [3370.9, 3413.5] | 0.3960 | 0.4963 | 0.0000 | inside |
| universal_permanent | 1.0000 | R4 | 1640.9 [1585.1, 1698.8] | 2317.3 [2297.5, 2336.5] | 0.3858 | 0.5183 | 0.0000 | above |
| universal_permanent | 1.0000 | R5 | 2793.4 [2728.4, 2858.1] | 1513.8 [1488.5, 1539.7] | 0.3801 | 0.5308 | 0.0000 | above |
| universal_permanent | 1.0000 | R6 | 4592.2 [4508.0, 4678.0] | 259.9 [221.4, 298.6] | 0.3738 | 0.5441 | 0.0000 | above |
| universal_permanent | 0.5000 | R0 | -1898.1 [-1954.5, -1838.4] | 950.7 [928.7, 972.4] | 0.4483 | 0.4974 | 0.0000 | below |
| universal_permanent | 0.5000 | R1 | -1512.1 [-1568.0, -1454.8] | 1604.8 [1583.6, 1625.9] | 0.4483 | 0.4969 | 0.0000 | below |
| universal_permanent | 0.5000 | R2 | -1131.1 [-1183.4, -1074.7] | 2248.3 [2228.7, 2267.8] | 0.4482 | 0.4964 | 0.0000 | below |
| universal_permanent | 0.5000 | R3 | -427.9 [-488.4, -364.6] | 3504.6 [3484.0, 3525.6] | 0.4481 | 0.4962 | 0.0000 | inside |
| universal_permanent | 0.5000 | R4 | 1071.7 [1014.8, 1129.5] | 2468.1 [2448.6, 2487.2] | 0.4430 | 0.5180 | 0.0000 | above |
| universal_permanent | 0.5000 | R5 | 2241.6 [2186.6, 2299.0] | 1647.6 [1623.1, 1672.5] | 0.4401 | 0.5307 | 0.0000 | above |
| universal_permanent | 0.5000 | R6 | 4092.1 [4015.5, 4169.2] | 364.4 [324.2, 405.8] | 0.4370 | 0.5440 | 0.0000 | above |
| universal_permanent | 0.0000 | R0 | -1898.1 [-1954.5, -1838.4] | 950.7 [928.7, 972.4] | 0.5003 | 0.4974 | 0.0000 | below |
| universal_permanent | 0.0000 | R1 | -1677.9 [-1737.1, -1615.8] | 1641.1 [1620.6, 1661.2] | 0.5003 | 0.4966 | 0.0000 | below |
| universal_permanent | 0.0000 | R2 | -1455.0 [-1508.4, -1400.3] | 2320.1 [2300.6, 2340.1] | 0.5003 | 0.4965 | 0.0000 | below |
| universal_permanent | 0.0000 | R3 | -1005.9 [-1068.9, -940.0] | 3646.1 [3624.6, 3667.4] | 0.5003 | 0.4958 | 0.0000 | below |
| universal_permanent | 0.0000 | R4 | 448.0 [391.6, 507.6] | 2609.2 [2589.9, 2629.2] | 0.5003 | 0.5179 | 0.0000 | inside |
| universal_permanent | 0.0000 | R5 | 1691.3 [1639.0, 1746.4] | 1778.8 [1753.7, 1803.7] | 0.5003 | 0.5308 | 0.0000 | above |
| universal_permanent | 0.0000 | R6 | 3587.6 [3517.8, 3658.1] | 474.5 [434.6, 514.1] | 0.5003 | 0.5439 | 0.0000 | above |
| free_market | 1.0000 | R0 | -288.7 [-337.3, -239.6] | 36.5 [19.3, 54.3] | 0.4483 | 0.2304 | 0.0000 | inside |
| free_market | 1.0000 | R1 | -167.4 [-218.0, -116.4] | 202.8 [184.9, 220.2] | 0.4481 | 0.2310 | 0.0000 | inside |
| free_market | 1.0000 | R2 | -37.7 [-88.0, 14.8] | 352.9 [331.9, 373.9] | 0.4479 | 0.2311 | 0.0000 | inside |
| free_market | 1.0000 | R3 | 287.9 [227.8, 350.9] | 681.2 [656.8, 706.1] | 0.4475 | 0.2320 | 0.0000 | inside |
| free_market | 1.0000 | R4 | 776.4 [725.1, 828.0] | 313.7 [292.3, 335.5] | 0.4446 | 0.2376 | 0.0000 | above |
| free_market | 1.0000 | R5 | 1177.2 [1124.5, 1231.4] | 51.8 [29.5, 74.4] | 0.4431 | 0.2405 | 0.0000 | above |
| free_market | 1.0000 | R6 | 1662.9 [1600.1, 1726.7] | -296.0 [-324.6, -266.7] | 0.4415 | 0.2436 | 0.0000 | above |
| free_market | 0.5000 | R0 | -288.7 [-337.3, -239.6] | 36.5 [19.3, 54.3] | 0.4743 | 0.2304 | 0.0000 | inside |
| free_market | 0.5000 | R1 | -229.0 [-282.2, -175.8] | 195.2 [177.6, 213.0] | 0.4742 | 0.2309 | 0.0000 | inside |
| free_market | 0.5000 | R2 | -97.3 [-149.5, -42.8] | 378.3 [355.8, 400.4] | 0.4741 | 0.2312 | 0.0000 | inside |
| free_market | 0.5000 | R3 | 121.5 [64.8, 180.8] | 718.0 [693.0, 743.4] | 0.4739 | 0.2317 | 0.0000 | inside |
| free_market | 0.5000 | R4 | 661.0 [606.4, 716.4] | 349.5 [324.8, 374.1] | 0.4725 | 0.2374 | 0.0000 | inside |
| free_market | 0.5000 | R5 | 1032.9 [979.7, 1086.5] | 90.6 [67.8, 115.0] | 0.4717 | 0.2406 | 0.0000 | above |
| free_market | 0.5000 | R6 | 1517.0 [1454.6, 1579.6] | -267.6 [-294.2, -240.2] | 0.4709 | 0.2433 | 0.0000 | above |
| free_market | 0.0000 | R0 | -288.7 [-337.3, -239.6] | 36.5 [19.3, 54.3] | 0.5003 | 0.2304 | 0.0000 | inside |
| free_market | 0.0000 | R1 | -264.9 [-316.7, -212.6] | 208.1 [189.1, 226.6] | 0.5003 | 0.2308 | 0.0000 | inside |
| free_market | 0.0000 | R2 | -199.3 [-253.5, -143.2] | 394.0 [374.7, 413.8] | 0.5003 | 0.2312 | 0.0000 | inside |
| free_market | 0.0000 | R3 | -66.3 [-126.7, -5.0] | 744.5 [720.6, 767.9] | 0.5003 | 0.2318 | 0.0000 | inside |
| free_market | 0.0000 | R4 | 480.1 [425.1, 535.0] | 375.1 [353.5, 396.8] | 0.5003 | 0.2376 | 0.0000 | inside |
| free_market | 0.0000 | R5 | 858.5 [805.4, 912.3] | 119.8 [96.3, 143.6] | 0.5003 | 0.2408 | 0.0000 | above |
| free_market | 0.0000 | R6 | 1403.5 [1343.6, 1464.2] | -235.1 [-261.5, -207.6] | 0.5003 | 0.2435 | 0.0000 | above |

#### Ratio thresholds (first crossing scanning R0 to R6, linear interpolation in theta between levels)
Reported on the point estimates; the CI is over bootstrap resamples that have a crossing, with the share of resamples without one.
| scenario | quantity | point_estimate | CI95_over_resamples_with_crossing | share_resamples_no_crossing |
|---|---|---|---|---|
| universal_permanent | E_G(k=1) vs +SESOI | rises through at theta = 0.555, ratio mq/ms = 1.250 | theta [0.549, 0.562], ratio [1.217, 1.281] | 0.000 |
| universal_permanent | E_G(k=0) vs -SESOI | rises through at theta = 0.533, ratio mq/ms = 1.142 | theta [0.526, 0.540], ratio [1.110, 1.172] | 0.000 |
| free_market | E_G(k=1) vs +SESOI | rises through at theta = 0.646, ratio mq/ms = 1.828 | theta [0.629, 0.664], ratio [1.696, 1.975] | 0.000 |
| free_market | E_G(k=0) vs -SESOI | no crossing (E_G(k=0) above -SESOI at every level) | n/a | 1.000 |

#### k* per level from k in {1, 0.5, 0} (scan from k = 1 down) and linearity check
midpoint_deviation_E_G_k05 = E_G(k=0.5) - (E_G(k=1) + E_G(k=0))/2, mean [CI95]; 0 under exact linearity in k.
| scenario | level | E_G_k1 | E_G_k05 | E_G_k0 | k_star | k_star_CI95 | share_no_crossing | midpoint_deviation_E_G_k05 |
|---|---|---|---|---|---|---|---|---|
| universal_permanent | R0 | -1898.084 | -1898.084 | -1898.084 | none in [0,1] | n/a | 1.000 | 0.0 [0.0, 0.0] |
| universal_permanent | R1 | -1367.952 | -1512.138 | -1677.861 | none in [0,1] | n/a | 1.000 | 10.8 [-17.9, 39.8] |
| universal_permanent | R2 | -779.527 | -1131.064 | -1455.047 | none in [0,1] | n/a | 1.000 | -13.8 [-47.9, 19.7] |
| universal_permanent | R3 | 255.937 | -427.893 | -1005.909 | 0.813 | [0.771, 0.852] | 0.000 | -52.9 [-91.4, -15.4] |
| universal_permanent | R4 | 1640.865 | 1071.744 | 448.010 | none in [0,1] | n/a | 1.000 | 27.3 [-9.5, 64.3] |
| universal_permanent | R5 | 2793.367 | 2241.615 | 1691.264 | none in [0,1] | n/a | 1.000 | -0.7 [-37.8, 36.6] |
| universal_permanent | R6 | 4592.211 | 4092.123 | 3587.625 | none in [0,1] | n/a | 1.000 | 2.2 [-29.8, 34.9] |
| free_market | R0 | -288.687 | -288.687 | -288.687 | none in [0,1] | n/a | 1.000 | 0.0 [0.0, 0.0] |
| free_market | R1 | -167.442 | -229.028 | -264.850 | none in [0,1] | n/a | 1.000 | -12.9 [-40.0, 15.0] |
| free_market | R2 | -37.726 | -97.255 | -199.258 | none in [0,1] | [0.694, 0.998] | 0.919 | 21.2 [-7.9, 50.3] |
| free_market | R3 | 287.908 | 121.515 | -66.306 | 0.177 | [0.038, 0.322] | 0.017 | 10.7 [-20.3, 41.2] |
| free_market | R4 | 776.377 | 661.019 | 480.083 | none in [0,1] | n/a | 1.000 | 32.8 [4.3, 62.4] |
| free_market | R5 | 1177.240 | 1032.918 | 858.453 | none in [0,1] | n/a | 1.000 | 15.1 [-12.6, 43.6] |
| free_market | R6 | 1662.883 | 1516.956 | 1403.467 | none in [0,1] | n/a | 1.000 | -16.2 [-42.8, 10.2] |

### 9.3 D1 as generated by a4_analysis.py
The column ref_var_iid in the table below was built as p(1-p)/degree, which matches the raw definition and not the observed one (see 9.4).
#### D1: local observed-use fraction vs global fraction (free_market, k = 1, R3, full)
Seeds [8100, 8101, 8102, 8103, 8104]. Logged per step t and agent i at the point the B1 peer term reads it (snapshot of agent state after step t-1): obs = tie-strength-weighted share of neighbours whose AI use was observed in the realised draws (the B1 observed_frac); raw = the same share without the P_VISIBLE draw; global = share of all agents with AI use in the snapshot. Agents without neighbours are excluded. ref_var_iid = mean over agents of p(1-p)/degree with p the global fraction at that step (unweighted, independent-neighbour reference; a computed reference, not a test).

Mean over seeds. var = variance across agents at a step, averaged over the steps of the period; mad = mean over agents of |local - global|.
| steps | global_fraction | var_obs | var_raw | ref_var_iid | mad_obs_vs_global | mad_raw_vs_global | mad_obs_vs_Pvisible_x_global |
|---|---|---|---|---|---|---|---|
| 1-120 | 0.33997 | 0.02571 | 0.03229 | 0.02560 | 0.15564 | 0.14136 | 0.12688 |
| 121-240 | 0.34549 | 0.02598 | 0.03299 | 0.02603 | 0.15790 | 0.14423 | 0.12860 |
| 241-360 | 0.34970 | 0.02611 | 0.03259 | 0.02618 | 0.15858 | 0.14346 | 0.12893 |
| 361-480 | 0.35160 | 0.02626 | 0.03308 | 0.02625 | 0.15902 | 0.14456 | 0.12913 |
| 481-600 | 0.35464 | 0.02636 | 0.03317 | 0.02635 | 0.15977 | 0.14460 | 0.12958 |
| 601-720 | 0.35631 | 0.02669 | 0.03346 | 0.02641 | 0.16089 | 0.14535 | 0.13022 |
| 721-840 | 0.35794 | 0.02665 | 0.03356 | 0.02646 | 0.16114 | 0.14561 | 0.13016 |
| 841-960 | 0.36037 | 0.02697 | 0.03368 | 0.02654 | 0.16154 | 0.14573 | 0.13110 |
| 1-960 | 0.35200 | 0.02634 | 0.03310 | 0.02623 | 0.15931 | 0.14436 | 0.12933 |

Correlation over steps 1-960 between an agent's local fraction and the global fraction (agents with constant series excluded):
- observed local fraction: mean 0.1457, p05 0.0745, p50 0.1454, p95 0.2154 (n agents = 1177)
- raw local fraction: mean 0.2673, p05 0.1561, p50 0.2683, p95 0.3763 (n agents = 1177)

Per seed:
| seed | agents | mean_global | mean_var_obs | mean_var_raw | mean_ref_var_iid | mean_abs_diff_obs_vs_global | mean_abs_diff_raw_vs_global | corr_mean_obs_vs_global_over_time | mean_agent_corr_obs | mean_agent_corr_raw |
|---|---|---|---|---|---|---|---|---|---|---|
| 8100 | 240 | 0.35628 | 0.02698 | 0.03402 | 0.02677 | 0.16321 | 0.14746 | 0.91096 | 0.14623 | 0.26748 |
| 8101 | 240 | 0.34562 | 0.02781 | 0.03682 | 0.02655 | 0.16232 | 0.15314 | 0.90019 | 0.14348 | 0.26409 |
| 8102 | 240 | 0.36208 | 0.02451 | 0.02921 | 0.02532 | 0.15324 | 0.13496 | 0.90417 | 0.14411 | 0.26608 |
| 8103 | 240 | 0.34663 | 0.02571 | 0.03148 | 0.02564 | 0.15642 | 0.13937 | 0.89629 | 0.14433 | 0.26410 |
| 8104 | 240 | 0.34938 | 0.02668 | 0.03399 | 0.02686 | 0.16136 | 0.14689 | 0.90432 | 0.15033 | 0.27455 |

### 9.4 D1 reference variances matched to each definition (analysis/d1_reference.py, written after Gate 7, reads saved D1 data only)
Definitions in model.py:319-333: observed_frac = sum of tie strengths of neighbours with AI use that passed the P_VISIBLE draw, divided by the total tie strength of all neighbours; raw = the same without the draw.
D1 reference variances (EXPLORATORY), seeds ['8100', '8101', '8102', '8103', '8104'], P_VISIBLE = 0.7, tie strength Beta(2.0, 2.0): mean 0.500, variance 0.0500, approximate weighting factor 1 + CV^2 = 1.200.
| steps | p | var_raw | ref_raw_unweighted | ref_raw_weighted_approx | ratio_raw_to_unweighted | ratio_raw_to_weighted | var_obs | ref_obs_unweighted | ref_obs_weighted_approx | ratio_obs_to_unweighted | ratio_obs_to_weighted |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1-120 | 0.33997 | 0.03229 | 0.02560 | 0.03073 | 1.26116 | 1.05097 | 0.02571 | 0.02077 | 0.02493 | 1.23762 | 1.03135 |
| 121-240 | 0.34549 | 0.03299 | 0.02603 | 0.03123 | 1.26750 | 1.05625 | 0.02598 | 0.02111 | 0.02534 | 1.23029 | 1.02524 |
| 241-360 | 0.34970 | 0.03259 | 0.02618 | 0.03141 | 1.24504 | 1.03754 | 0.02611 | 0.02129 | 0.02555 | 1.22617 | 1.02181 |
| 361-480 | 0.35160 | 0.03308 | 0.02625 | 0.03151 | 1.26013 | 1.05011 | 0.02626 | 0.02138 | 0.02565 | 1.22835 | 1.02362 |
| 481-600 | 0.35464 | 0.03317 | 0.02635 | 0.03163 | 1.25848 | 1.04873 | 0.02636 | 0.02150 | 0.02580 | 1.22598 | 1.02165 |
| 601-720 | 0.35631 | 0.03346 | 0.02641 | 0.03169 | 1.26675 | 1.05563 | 0.02669 | 0.02157 | 0.02588 | 1.23744 | 1.03120 |
| 721-840 | 0.35794 | 0.03356 | 0.02646 | 0.03175 | 1.26812 | 1.05677 | 0.02665 | 0.02163 | 0.02596 | 1.23184 | 1.02654 |
| 841-960 | 0.36037 | 0.03368 | 0.02654 | 0.03185 | 1.26881 | 1.05734 | 0.02697 | 0.02173 | 0.02608 | 1.24093 | 1.03410 |
| 1-960 | 0.35200 | 0.03310 | 0.02623 | 0.03148 | 1.26202 | 1.05168 | 0.02634 | 0.02137 | 0.02565 | 1.23233 | 1.02694 |
