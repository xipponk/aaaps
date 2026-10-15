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
