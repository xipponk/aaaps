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

(none yet)

### A1 (before any k-spec run; design step 2)
- Pivot for the k family: P1, m = sample mean of a_base at t = 0 per run; g = max(0, k*x + (1-k)*m). P2 (level-matched
  per scenario and seed from the k = 1 run) is a sensitivity analysis for k = 0 and k = -1 in the two co-primary scenarios,
  reported next to the co-primary result. Co-primary tests use P1.
- k > 0 is labelled "reinforcing", never "complementarity". C1 (g_c = m*(1 - c)) is an exploratory spec off the k axis.
- Mean g_k(t) saved at steps 1, 120, ..., 960 for every run; clip engagement counts saved.
- Regression reference is v0.4.1 agent-level hashes, not production_v04.
