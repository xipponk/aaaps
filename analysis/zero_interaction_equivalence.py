"""
analysis/zero_interaction_equivalence.py: v0.4 zero-interaction vs v0.2 free_market.

PRE-DECLARED BEFORE ANY RUN (committed before the first execution; see git history):
  Units      : per-seed mean over agents of score_total and of deadline_miss_count at step 960,
               100 seeds (0-99) per model, N = 60 agents (the v0.2 size).
  Models     : v0.2 reference (outputs/reference/v02_free_market_final_step_100seeds.csv) and
               v0.4 free_market with zero_interaction_mode=True, default parameters.
  Margin     : equivalence if the mean difference (v0.4 minus v0.2) lies within +-10 percent
               of the v0.2 mean, for each metric.
  Tests      : Welch TOST at alpha = 0.05 (two one-sided tests); the 90 percent bootstrap CI
               of the mean difference (10,000 resamples, rng seed 20261007) must lie inside
               the margin; two-sample KS on the per-seed means is reported as a descriptive
               distribution check, not a decision rule.
  Decision   : equivalent only if BOTH metrics pass TOST. If not, report failure and the
               structural reason. Never call the result "within stochastic bounds" without it.
"""

from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from scipy import stats

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from analysis.manifest import write_manifest
from scenarios.free_market import run as run_free_market

SEEDS = list(range(100))
N = 60
MARGIN = 0.10
ALPHA = 0.05
REF = os.path.join(PROJECT_ROOT, "outputs", "reference", "v02_free_market_final_step_100seeds.csv")
OUT = os.path.join(PROJECT_ROOT, "outputs", "phase2")
METRICS = ["score_total", "deadline_miss_count"]


def _run(seed):
    m = run_free_market(seed=seed, n_students=N, zero_interaction_mode=True)
    df = m.datacollector.get_agent_vars_dataframe().xs(960, level="Step").reset_index()
    df.insert(0, "seed", seed)
    return df


def tost_welch(x, y, margin_abs):
    """TOST on mean(x) - mean(y) with equivalence bounds +-margin_abs; returns p = max(p_lo, p_hi)."""
    d = np.mean(x) - np.mean(y)
    vx, vy = np.var(x, ddof=1) / len(x), np.var(y, ddof=1) / len(y)
    se = np.sqrt(vx + vy)
    dof = (vx + vy) ** 2 / (vx ** 2 / (len(x) - 1) + vy ** 2 / (len(y) - 1))
    p_lo = 1 - stats.t.cdf((d + margin_abs) / se, dof)
    p_hi = stats.t.cdf((d - margin_abs) / se, dof)
    return float(d), float(se), float(max(p_lo, p_hi))


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=14) as ex:
        parts = list(ex.map(_run, SEEDS))
    v04 = pd.concat(parts, ignore_index=True)
    v04_path = os.path.join(OUT, "zero_interaction_v04_N60_final_step.csv")
    v04.to_csv(v04_path, index=False)
    v02 = pd.read_csv(REF)
    print(f"v0.2 REFERENCE: {os.path.abspath(REF)} shape={v02.shape} Step max={v02['step'].max()}")
    print(f"v0.4 ZERO-INT : {os.path.abspath(v04_path)} shape={v04.shape} Step max=960 "
          f"elapsed={time.time() - t0:.0f}s")

    rng = np.random.default_rng(20261007)
    res = {}
    for m in METRICS:
        a = v04.groupby("seed")[m].mean().values
        b = v02.groupby("seed")[m].mean().values
        margin_abs = MARGIN * b.mean()
        d, se, p = tost_welch(a, b, margin_abs)
        boots = np.array([rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(10000)])
        lo, hi = np.percentile(boots, [5, 95])
        ks = stats.ks_2samp(a, b)
        passed = bool(p < ALPHA and lo > -margin_abs and hi < margin_abs)
        res[m] = {"v04_mean": float(a.mean()), "v02_mean": float(b.mean()), "diff": d,
                  "diff_pct_of_v02": 100 * d / float(b.mean()), "margin_abs": float(margin_abs),
                  "tost_p": p, "boot90_ci": [float(lo), float(hi)],
                  "ks_D": float(ks.statistic), "ks_p": float(ks.pvalue), "equivalent": passed}
        print(json.dumps({m: res[m]}, indent=2))
    res["overall_equivalent"] = all(res[m]["equivalent"] for m in METRICS)
    print("OVERALL EQUIVALENT (both metrics):", res["overall_equivalent"])
    with open(os.path.join(OUT, "zero_interaction_equivalence.json"), "w") as f:
        json.dump(res, f, indent=2)
    write_manifest(os.path.join(OUT, "zero_interaction_manifest.json"), stage="zero_interaction",
                   seeds=SEEDS, n_students=N, scenario="free_market", sampler="none",
                   margin=MARGIN, alpha=ALPHA, reference=os.path.abspath(REF))


if __name__ == "__main__":
    main()
