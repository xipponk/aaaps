# Figure captions and provenance (paper v4, not yet in the paper)

All figures: `analysis/figures_v41.py` (reads saved CSVs only, no simulation), PNG 300 dpi and PDF, no titles. One colour per scenario in every figure: free market blue, universal permanent vermillion, mixed policy green, targeted subsidy purple, universal access orange (Okabe-Ito). CI = 95% bootstrap over seeds; shared index matrix `default_rng(20261016).integers(0, 100, (10000, 100))` unless the CI is parsed from a results csv written by a locked analysis script. Figures carry no footer and no panel titles; panel letters (a), (b), ... are at the top left, and everything a footer used to say is in this file. Numbers quoted below are read from the named files. Status words follow `preregistration.md`: confirmatory = seeds 7000-7099 under the A3 rules; exploratory = no multiplicity control.

## F0 Scenario overview (`F0_scenario_overview`)
- Data: `outputs/v041_main/production_v04_runs.csv` (production v0.4.1, k = 1, git c1021d9), difference from baseline paired by seed.
- Seeds: 0-99. Status: exploratory (pre-confirmatory run; the CI is computed by the figure script, not by a locked script).
- Values (mean [CI]): score gain free market 658.9 [635.2, 682.0], universal permanent 3362.9 [3341.3, 3385.2]; change in Gini free market 0.0020 [0.0015, 0.0024], universal permanent -0.0093 [-0.0099, -0.0087]; dependency 0.228 (free market) to 0.494 (universal permanent); decline 0.054 (mixed policy) to 0.207 (universal permanent); misses 0.79 (free market) to 1.78 (universal access).
- Panels: (a) score gain, (b) change in Gini of score, (c) dependency, (d) relative ability decline, (e) deadline misses; each is the difference from the no-AI baseline, paired by seed, 95% bootstrap CI.
- Claim supported: ordering of the five scenarios on the five headline outcomes at the original benefit specification.
- Limits: dependency and decline are defined only with AI use, so the baseline is 0 by construction. Seeds differ from the confirmatory seeds. Universal access is the temporary (first four semesters) policy.

## F1 E_G by k (`F1_EG_by_k`)
- Data: `outputs/v041_conf/results/E_G_states.csv` (from `K_runs.csv`), grey band = SESOI 717.0 (5% of G(baseline) = 14339.5).
- Seeds: 7000-7099. Status: left panel confirmatory (co-primary scenarios, Family 1 and k* rules); right panel exploratory.
- Values: E_G(k=1) free market 231.6 [157.6, 302.2], universal permanent 224.5 [165.3, 282.6]; E_G(k=0) -82.6 [-150.6, -16.4] and -1042.1 [-1106.0, -979.1]; k* 0.240 [0.053, 0.426] and 0.815 [0.770, 0.861] (`k_star.csv`). Holm test of H0 E_G(s,0) <= +SESOI: not rejected in both scenarios (`family1.csv`).
- Panels: (a) co-primary scenarios, with k* (open diamond on the zero line, horizontal bar = 95% CI over crossing resamples, from `k_star.csv`); (b) other scenarios (exploratory). k = 1 original benefit, k = 0 ability independent.
- Claim supported: E_G at k = 1 lies inside the SESOI band in both co-primary scenarios (state "not present at k = 1") and falls as k decreases.
- Limits: five k values only; the k* lines are interpolations of these five points. Scenario labels for the three right-hand scenarios are exploratory.

## F2 Channel-ratio sweep (`F2_ratio_sweep`)
- Data: `outputs/v041_a4/results/a4_levels.csv`, `a4_ratio_thresholds.csv` (from `A4_runs.csv`).
- Seeds: 8000-8099. Status: post hoc exploratory (amendment A4).
- x axis: ratio mq/ms on a log2 scale for R1 to R5 (0.25 to 4); R0 (quality channel removed) and R6 (speed channel removed) are separate end points; dash-dot line = default ratio (R3). Open diamonds = threshold crossings of E_G with +SESOI (k = 1) and -SESOI (k = 0) with CI over resamples. Panels: (a, b) E_G, (c, d) score gain vs baseline, left column universal permanent, right column free market. Dashed horizontal lines: +/- SESOI = 717.0. The row g_mean_960 is in the appendix figure `F2_appendix_pivot` (same axes, k = 1, 0.5, 0).
- Values: crossing of E_G(k=1) with +SESOI at ratio 1.250 [1.217, 1.281] (universal permanent) and 1.828 [1.696, 1.975] (free market); E_G(k=0) crosses -SESOI at 1.142 [1.110, 1.172] (universal permanent); no crossing for free market. R0 is identical across k (checked bitwise).
- Claim supported: the size and sign of E_G depend on the quality to speed ratio; at the default ratio E_G(k=1) is within SESOI.
- Note for reading the x axis: every level other than R3 reduces the combined boost size, so moving along the axis changes both the ratio and the total magnitude of the boost, not the ratio alone (this is why score gain peaks at R3).
- Limits: three k values; thresholds are linear interpolations in theta = mq/(mq+ms) between the seven levels; the ratio is a model scaling of two boost channels, not a measured quantity.

## F3 Interaction decomposition (`F3_interaction_decomposition`)
- Data: `outputs/v041_conf/results/interaction_decomposition.csv`, k = 1, mode full against self-only and zero-interaction.
- Seeds: 7000-7099. Status: confirmatory rules (interaction clause, A3), two co-primary scenarios.
- Panels: (a) delta dependency, (b) delta calibration error, (c) delta relative ability decline, (d) delta deadline misses, (e) delta Gini, (f) delta G; each is a difference between modes, paired by seed.
- Bars: individual = self-only minus zero-interaction (solid); social = full minus self-only (hatched, negative); diamond = full minus zero. Grey band = SESOI of each outcome.
- Values (free market, k = 1): dependency individual 0.1892 [0.1867, 0.1918], social -0.0371 [-0.0377, -0.0366], full minus zero 0.1521 [0.1498, 0.1544]; G: individual 551.2 [496.6, 606.0], social -202.0 [-246.7, -159.5].
- Claim supported: for dependency, calibration error, decline and misses the individual part is positive and the social part is negative in both scenarios. Classes in the csv: individual "driven" for these four outcomes; social "driven" for dependency, decline and misses, social calibration error not classed as driven.
- Limits: social is negative, so shares of the total exceed 100% (S = 1.244); do not read the bars as shares. Gini and G are inside SESOI (class null or indeterminate).

## F4 H_self and L0 (`F4_H_self_L0`)
- Data: `K_runs.csv` (L0 = 0.1) and `L0_runs.csv` (L0 = 0.05, 0.2, 0.3), free market, k = 1, mean dependency; `F4_data_S_by_L0.csv`. S at L0 = 0.1 equals `h_self.csv` (asserted).
- Seeds: 7000-7099. Status: L0 = 0.1 confirmatory (H_self SUPPORTED, S = 1.244 [1.240, 1.248]); other L0 values are sensitivity analysis (exploratory).
- Reference lines: S = 0.5 (decision threshold of the preregistered rule) and S = 1.
- Values: S = 1.208, 1.244, 1.326, 1.437 at L0 = 0.05, 0.1, 0.2, 0.3.
- Claim supported: the lower CI limit of S stays above 0.5 and above 1 at all four L0 values.
- Limits: one scenario, one outcome; CIs are narrow and nearly hidden by the markers. S above 1 follows from a negative social part.

## F5 and F6 Network sweep and density control (`F5_F6_network_and_density`)
- Data: panel (a) `network_contrasts_full.csv`; panel (b) `NET_runs.csv` (`dens=` points, `disabled` = none (full) and `norms` (no norms)), free market, k = 1.
- Seeds: 7000-7099. Status: panel (a) confirmatory (corroboration of H_self, all 16 contrasts equivalent to 0 at SESOI 0.02, Holm); panel (b) exploratory.
- Values: largest contrast |difference| in dependency 0.0047; CI range over the 16 contrasts -0.0022 to 0.0051. Panel (b) dependency 0.230 to 0.231 (full) and 0.081 (no norms: peer norms and ETA_SELF both switched off, `disabled_submodels = {norms}`, the `no_norms` condition; this is not the `no_peer_norms` condition with ETA = 0) across within-section shares 0.23 to 0.76 at expected degree 12.
- Panels: (a) one-at-a-time sweep, x axis = level of each network parameter, grey band +/- 0.02 (SESOI for dependency), the default level of each parameter is the reference and is not drawn; (b) density-controlled sweep at expected degree 12, solid = full model, dashed = no norms (peer and self).
- Claim supported: dependency does not change beyond SESOI when network parameters change one at a time, nor when density is held fixed while the within-section share changes.
- Limits: dependency only (gini and G ranges are in `results_confirmatory.md`); one-at-a-time, no interaction between network parameters; a population-mean outcome.

## F7 Morris (`F7_morris`)
- Data: `outputs/v041_main/morris_v04_composite_v2.csv` (normalised mu* per metric, composite) and `morris_v04_retained12.csv`. Provenance checked: manifest `morris_v04_manifest.json` has git hash c1021d9 (v0.4.1), LAMBDA_A = 0.00248 (the v0.4.1 value), seeds 2000-2002, 480 design points. The older v0.4 Morris files with the same base name are in `outputs/phase2/` and are not used.
- Seeds: 2000-2002, free market, 23 parameters, r = 20. Status: exploratory screening.
- Figure: heatmap of normalised mu* (23 parameters by 8 metrics: mean score, std score, Gini, dependency, calibration error, ability decline, deadline misses, legitimacy). Rows are sorted by composite (max over the eight metrics) from high to low. The dashed line after row 12 separates the top 12 (labelled "top 12", retained for Sobol, asserted equal to `morris_v04_retained12.csv`) from the rest. Network parameters are marked with * and bold.
- Values: network parameters rank 17 to 20 (composite 0.025 to 0.061); top 12 retained for Sobol.
- Tie warning: the composite equals 1.0 for 7 parameters (each is the strongest on at least one metric after normalisation), so the order within that group carries no meaning; the row order inside it follows the stored rank only.
- Claim supported: the network parameters are among the least influential on the population-mean metrics.
- Limits: the composite covers means, gini and std of score, not the tercile gap (findings section 5). The file name `morris_v04_*` inside `v041_main` is historical (see `outputs/v041_main/README.md`).

## F8 Sobol (`F8_sobol_main`, `F8_appendix_sobol_total_order`)
- Data: `outputs/v041_main/sobol_v04_free_market_indices.csv` and `sobol_v04_targeted_subsidy_indices.csv` (N = 512, 12 parameters, seed 3000, 7,168 runs per scenario).
- Status: exploratory. Main figure: mean score, Gini, dependency, decline (ST with 95% CI, S1 clipped at 0). Appendix: heatmap of ST for the other metrics; borrowing metrics and ai_adoption_rate in grey (unreliable and degenerate per findings section 6; ai_adoption_rate has no index).
- Values (free market ST): decline LAMBDA_A 0.470; dependency DELTA_D 0.423 (leader in findings section 6); mean score and Gini led by ABILITY_MEAN; the scenario colour on the main figure is the scenario, not the metric.
- Panels: (a) to (d) free market and (e) to (h) targeted subsidy; columns mean score, Gini of score, dependency, relative ability decline; solid bar = ST with 95% CI, hatched = S1 clipped at 0. Setup: N = 512, 12 parameters, one seed (3000) per design point, v0.4.1 (git c1021d9). The appendix figure has no panel letters.
- Claim supported: which parameters carry the variance of each headline outcome.
- Limits: one seed per design point, so ST includes seed noise; the two scenarios shown are the only ones run for Sobol; legitimacy leader is not statistically separated (findings section 6).

## F9 Channel ablation and D1 diagnostic (`F9_ablation_and_D1`)
- Data: (a, b) `ABL_runs.csv` and `K_runs.csv`, seeds 7000-7099, k = 1, E_G against baseline; status confirmatory-run data, ablation tables are exploratory in `results_confirmatory.md`. (c) `outputs/v041_a4/results/d1_reference_steps.csv` from `analysis/d1_reference.py`, free market, k = 1, R3, seeds 8100-8104, exploratory.
- Panels: (a) full model, (b) zero interaction (E_G against baseline, k = 1, seeds 7000-7099, grey band +/- SESOI = 717.0, 95% bootstrap CI); (c) D1 diagnostic, free market, k = 1, R3, seeds 8100-8104, mean over 5 seeds, reference = independent Bernoulli neighbours with exact tie-strength weights (exploratory).
- Values: quality only, full model, E_G 4474.4 [4395.9, 4555.5] (universal permanent) and 1642.7 [1579.1, 1707.1] (free market); speed only -1924.6 [-1985.5, -1863.7] and -318.0 [-371.3, -265.2]. Panel (c), steps 3-960: variance of the local fraction over the exact reference has mean 1.059 (raw) and 1.034 (observed), range 0.965 to 1.151 and 0.894 to 1.166 before smoothing; 40-step moving mean is plotted.
- Claim supported: the two boost channels have opposite signs on E_G; the observed variance of the local AI-use fraction is close to that of independent neighbours with the same tie weights (ratio about 1.03 to 1.06).
- Limits: (c) uses five seeds of one scenario; the reference assumes independent Bernoulli neighbours with probability p (raw) or 0.7 p (observed), which is a null model, and weights are exact (rebuilt, not stepped networks). Panel (c) is not evidence for or against any mechanism by itself.

## FA Appendix: invariance of decline and dependency to k (`FA_k_invariance`)
- Data: `K_runs.csv`, mode full, five scenarios, five k values; CI by the figure script.
- Seeds: 7000-7099. Status: co-primary scenarios confirmatory data, other three exploratory (dashed). Appendix figure.
- Values: decline varies by at most 0.0004 over k within a scenario (free market 0.1048 to 0.1050; universal permanent 0.2080 to 0.2083); dependency by at most 0.001 (free market 0.2308 to 0.2313).
- Panels: (a) relative ability decline, (b) dependency; solid = co-primary scenarios, dashed = exploratory scenarios.
- What it shows: dependency and decline do not change with k. This follows from the model structure (k enters only the benefit g that converts AI use into score) and is not a finding about students. The figure documents that the k sweep changes the score channel only.
- Limits: it is a check of the implementation and design, not evidence about behaviour.

## F2 appendix pivot (`F2_appendix_pivot`)
- Data: `outputs/v041_a4/results/a4_levels.csv`, column `g_mean_960` (mean benefit g at step 960), k = 1, 0.5, 0. Seeds 8000-8099, post hoc exploratory (A4).
- Panels: (a) universal permanent, (b) free market; same x axis as F2.
- Reading: every level other than R3 reduces the combined boost size, so the x axis changes both the ratio and the magnitude of the boost.
- Limits: g_mean_960 is a model quantity with no CI in the csv, so none is drawn.
