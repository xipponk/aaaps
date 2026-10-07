"""
analysis/production_contrasts.py: paired contrasts of each scenario against baseline and
free_market from a production runs CSV (seeds are paired: same seed, same agents).

Usage: python -m analysis.production_contrasts [runs_csv]
Reports mean difference, paired bootstrap 95 percent CI (10,000 resamples, rng seed 7) and
Cohen's dz for deadline_miss_count and gini_score, plus the share of seeds with a positive difference.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT = os.path.join(PROJECT_ROOT, "outputs", "phase2", "production_v04_runs.csv")
OUTCOMES = ["deadline_miss_count", "gini_score"]


def main(path: str) -> None:
    df = pd.read_csv(path)
    print(f"RUNS FILE: {os.path.abspath(path)} shape={df.shape}")
    rng = np.random.default_rng(7)
    rows = []
    for ref in ("baseline", "free_market"):
        r = df[df.scenario == ref].sort_values("seed")
        for sc in df.scenario.unique():
            if sc == ref:
                continue
            x = df[df.scenario == sc].sort_values("seed")
            for o in OUTCOMES:
                d = x[o].values - r[o].values
                b = np.array([rng.choice(d, len(d)).mean() for _ in range(10000)])
                lo, hi = np.percentile(b, [2.5, 97.5])
                rows.append({"vs": ref, "scenario": sc, "outcome": o, "ref_mean": r[o].mean(),
                             "scen_mean": x[o].mean(), "diff": d.mean(), "ci_lo": lo, "ci_hi": hi,
                             "dz": d.mean() / d.std(ddof=1) if d.std(ddof=1) > 0 else np.nan,
                             "share_seeds_positive": float((d > 0).mean())})
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(os.path.dirname(path), os.path.basename(path).replace("_runs.csv", "_contrasts.csv")), index=False)
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT)
