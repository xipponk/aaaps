"""
analysis/morris_recompute.py: Gate 2 composite ranking recomputed from the saved Morris runs.

Rule fixed at Gate 2 (before this script was written):
  composite metrics: mean_score, std_score, gini_score, mean_dependency, mean_calibration_error,
    relative_ability_decline, deadline_miss_count, mean_legitimacy
  (ai_adoption_rate, total_shared_seats_lent and borrowing_agent_count are left out of the
  composite and kept as GSA output metrics; relative_ability_decline replaces mean_retained_ability)
  retained set: top 10 of the composite plus LAMBDA_A and RHO_RATIO (forced); if both are
  already in the top 10, fill with ranks 11-12 so that D = 12.

relative_ability_decline = 1 - mean_retained_ability / mean_base_ability. The Morris raw file
has no base ability, so it is rebuilt by constructing each run's model (agents only, no steps)
with the same 23 parameter values and seed. Validation: the rebuild must reproduce
mean_base_ability of known default-parameter runs in production_v04_runs.csv exactly.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
from SALib.analyze import morris as morris_analyze
from SALib.sample import morris as morris_sample

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import config.params as P
from analysis.run_morris_screening import PROBLEM
from model.model import AaapsModel

OUT = os.path.join(PROJECT_ROOT, "outputs", os.environ.get("AAAPS_OUT", "phase2"))
COMPOSITE = ["mean_score", "std_score", "gini_score", "mean_dependency", "mean_calibration_error",
             "relative_ability_decline", "deadline_miss_count", "mean_legitimacy"]
FORCED = ["LAMBDA_A", "RHO_RATIO"]


def set_params(row) -> None:
    for n in PROBLEM["names"]:
        v = float(row[n])
        if n == "SHAREABLE_SEATS_TIER3":
            P.SHAREABLE_SEATS[3] = int(round(v))
        else:
            setattr(P, n, v)


def mean_base(row) -> float:
    set_params(row)
    m = AaapsModel(n_students=240, scenario="free_market", seed=int(row["seed"]))
    return float(np.mean([a.base_ability for a in m.agents]))


def main() -> None:
    raw = pd.read_csv(os.path.join(OUT, "morris_v04_runs_raw.csv"))
    # validation against production defaults
    prod = pd.read_csv(os.path.join(OUT, "production_v04_runs.csv"))
    defaults = {n: (P.SHAREABLE_SEATS[3] if n == "SHAREABLE_SEATS_TIER3" else getattr(P, n)) for n in PROBLEM["names"]}
    ok = True
    for sd in (0, 1, 2):
        row = dict(defaults, seed=sd)
        ref = prod[(prod.scenario == "free_market") & (prod.seed == sd)].mean_base_ability.iloc[0]
        got = mean_base(row)
        print(f"validation seed {sd}: rebuilt {got:.10f} vs production {ref:.10f}")
        ok &= abs(got - ref) < 1e-9
    if not ok:
        sys.exit("VALIDATION FAILED: base-ability rebuild does not match production")
    # reset defaults then rebuild per run
    raw["mean_base_ability"] = [mean_base(r) for _, r in raw.iterrows()]
    raw["relative_ability_decline"] = 1.0 - raw.mean_retained_ability / raw.mean_base_ability
    assert raw.relative_ability_decline.between(-1e-9, 1).all(), "decline outside [0, 1]"
    raw.to_csv(os.path.join(OUT, "morris_v04_runs_raw_with_decline.csv"), index=False)

    # design points: parameters from the first seed row, outputs averaged over seeds
    design = raw.sort_values(["design_idx", "seed"]).groupby("design_idx").first()[PROBLEM["names"]]
    regen = morris_sample.sample(PROBLEM, N=20, num_levels=4, seed=42)
    assert np.allclose(design.values, regen), "raw design points differ from regenerated Morris sample"
    Y = raw.groupby("design_idx")[COMPOSITE].mean().sort_index()
    recs = {}
    for m in COMPOSITE:
        si = morris_analyze.analyze(PROBLEM, regen, Y[m].values, print_to_console=False)
        recs[m] = np.abs(np.array(si["mu_star"]))
    mu = pd.DataFrame(recs, index=PROBLEM["names"])
    norm = mu / mu.max()
    out = mu.add_suffix("_mu_star").join(norm.add_suffix("_norm"))
    out["composite_max"] = norm.max(axis=1)
    out["top_metric"] = norm.idxmax(axis=1)
    out = out.sort_values("composite_max", ascending=False)
    out["rank"] = range(1, len(out) + 1)
    out.to_csv(os.path.join(OUT, "morris_v04_composite_v2.csv"))
    print(out[["rank", "composite_max", "top_metric"]].round(3).to_string())

    ranked = list(out.index)
    keep = ranked[:10]
    for p in FORCED:
        if p not in keep:
            keep.append(p)
    i = 10
    while len(keep) < 12:
        if ranked[i] not in keep:
            keep.append(ranked[i])
        i += 1
    A = ["DELTA_D", "BETA_C", "P_VISIBLE", "PROCESSING_DIFFICULTY_FACTOR", "ABILITY_STD", "ABILITY_MEAN",
         "ETA_SELF", "PROSOCIALITY_BETA_A", "ETA", "ALPHA_D", "GAMMA_C", "CONFORMITY_BETA_B"]
    B = [p for p in A if p not in ("CONFORMITY_BETA_B", "GAMMA_C")] + FORCED
    print("\nRETAINED SET (D=12):")
    for p in keep:
        print(f"  {p:30s} rank {int(out.loc[p, 'rank']):2d}  composite {out.loc[p, 'composite_max']:.3f}"
              f"{'  (forced)' if p in FORCED and int(out.loc[p, 'rank']) > 10 else ''}")
    print("differs from option A by", len(set(keep) - set(A)), "parameters; new:", sorted(set(keep) - set(A)),
          "dropped:", sorted(set(A) - set(keep)))
    print("differs from option B by", len(set(keep) - set(B)), "parameters; new:", sorted(set(keep) - set(B)),
          "dropped:", sorted(set(B) - set(keep)))
    pd.Series(keep).to_csv(os.path.join(OUT, "morris_v04_retained12.csv"), index=False, header=["parameter"])


if __name__ == "__main__":
    main()
