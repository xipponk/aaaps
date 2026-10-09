"""
analysis/seed_convergence.py: how many seeds are enough? (analysis of saved runs, no model runs)

Inputs (saved v0.4 CSVs, 100 seeds, seeds 0-99):
  outputs/phase2/production_v04_runs.csv         6 scenarios
  outputs/phase2/interaction_isolation_runs.csv  free_market, conditions full / no_norms / ...

Pre-declared stability criteria (written before looking at the output):
  Levels   (scenario mean of a metric): stable at n when the median relative 95% CI half-width
           over random size-n subsets is <= 5% of |mean over all 100 seeds|.
  Contrasts (paired difference vs a reference, same seeds): stable at n when, over random size-n
           subsets, the 95% t-CI of the paired mean difference excludes 0 with the same sign as the
           full-sample estimate in >= 95% of subsets ("detection rate"), for contrasts whose
           full-sample CI excludes 0. Contrasts whose full-sample CI includes 0 are reported as
           "null at 100"; for them the median CI half-width is reported instead.
Random subsets: 1000 draws per n without replacement, numpy default_rng(20261009).
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

OUT = os.path.join(PROJECT_ROOT, "outputs", "phase2")
NS = list(range(10, 101, 10))
DRAWS = 1000
RNG = np.random.default_rng(20261009)

LEVEL_METRICS = ["mean_score", "gini_score", "mean_dependency", "deadline_miss_count",
                 "relative_ability_decline", "mean_calibration_error"]
CONTRAST_METRICS = ["mean_score", "gini_score", "mean_dependency", "deadline_miss_count",
                    "relative_ability_decline"]


def _announce(path: str, df: pd.DataFrame, key: str) -> None:
    print(f"[baseline-rule] {os.path.abspath(path)} shape={df.shape} seed max={df['seed'].max()} ({key})")


def _ci_half(x: np.ndarray) -> float:
    n = len(x)
    return float(stats.t.ppf(0.975, n - 1) * x.std(ddof=1) / np.sqrt(n))


def level_curve(x: np.ndarray) -> list[dict]:
    full = x.mean()
    rows = []
    for n in NS:
        hw = [] if n < len(x) else [_ci_half(x)]
        mu = [] if n < len(x) else [x.mean()]
        if n < len(x):
            for _ in range(DRAWS):
                s = x[RNG.choice(len(x), n, replace=False)]
                hw.append(_ci_half(s)); mu.append(s.mean())
        rows.append(dict(n=n, full_mean=full, median_rel_halfwidth=float(np.median(hw) / abs(full)) if full else np.nan,
                         mean_sd_over_subsets=float(np.std(mu)) if n < len(x) else 0.0))
    return rows


def contrast_curve(d: np.ndarray) -> list[dict]:
    full = d.mean()
    full_sig = abs(full) > _ci_half(d)
    rows = []
    for n in NS:
        det, hw = [], []
        reps = [d] if n >= len(d) else [d[RNG.choice(len(d), n, replace=False)] for _ in range(DRAWS)]
        for s in reps:
            h = _ci_half(s); m = s.mean()
            det.append(abs(m) > h and np.sign(m) == np.sign(full)); hw.append(h)
        rows.append(dict(n=n, full_diff=full, full_ci_excludes_0=bool(full_sig),
                         detection_rate=float(np.mean(det)), median_halfwidth=float(np.median(hw))))
    return rows


def first_stable(rows: list[dict], key: str, ok) -> int | None:
    good = [r["n"] for r in rows if ok(r[key])]
    for n in NS:  # smallest n such that all larger n are also ok
        if all(ok(r[key]) for r in rows if r["n"] >= n):
            return n
    return None


def main() -> None:
    prod_path = os.path.join(OUT, "production_v04_runs.csv")
    prod = pd.read_csv(prod_path); _announce(prod_path, prod, "production")
    iso_path = os.path.join(OUT, "interaction_isolation_runs.csv")
    iso = pd.read_csv(iso_path); _announce(iso_path, iso, "isolation")

    lev, con, summary = [], [], []

    for sc, g in prod.groupby("scenario"):
        g = g.sort_values("seed")
        for m in LEVEL_METRICS:
            x = g[m].to_numpy()
            if np.std(x) == 0:
                continue
            rows = level_curve(x)
            for r in rows:
                lev.append(dict(source="production", group=sc, metric=m, **r))
            summary.append(dict(kind="level", source="production", group=sc, metric=m,
                                n_stable=first_stable(rows, "median_rel_halfwidth", lambda v: v <= 0.05)))

    base = prod[prod.scenario == "baseline"].set_index("seed")
    for sc in sorted(set(prod.scenario) - {"baseline"}):
        g = prod[prod.scenario == sc].set_index("seed")
        for m in CONTRAST_METRICS:
            d = (g[m] - base[m]).loc[sorted(g.index)].to_numpy()
            if np.std(d) == 0:
                continue
            rows = contrast_curve(d)
            for r in rows:
                con.append(dict(source="production", contrast=f"{sc} - baseline", metric=m, **r))
            sig = rows[-1]["full_ci_excludes_0"]
            summary.append(dict(kind="contrast", source="production", group=f"{sc} - baseline", metric=m,
                                full_ci_excludes_0=sig,
                                n_stable=first_stable(rows, "detection_rate", lambda v: v >= 0.95) if sig else None,
                                halfwidth_at_100=rows[-1]["median_halfwidth"]))

    full = iso[iso.condition == "full"].set_index("seed")
    for cond in sorted(set(iso.condition) - {"full"}):
        g = iso[iso.condition == cond].set_index("seed")
        for m in CONTRAST_METRICS + ["mean_calibration_error", "mean_legitimacy"]:
            d = (g[m] - full[m]).loc[sorted(g.index)].to_numpy()
            if np.std(d) == 0:
                continue
            rows = contrast_curve(d)
            for r in rows:
                con.append(dict(source="isolation", contrast=f"{cond} - full", metric=m, **r))
            sig = rows[-1]["full_ci_excludes_0"]
            summary.append(dict(kind="contrast", source="isolation", group=f"{cond} - full", metric=m,
                                full_ci_excludes_0=sig,
                                n_stable=first_stable(rows, "detection_rate", lambda v: v >= 0.95) if sig else None,
                                halfwidth_at_100=rows[-1]["median_halfwidth"]))

    pd.DataFrame(lev).to_csv(os.path.join(OUT, "seed_convergence_levels.csv"), index=False)
    pd.DataFrame(con).to_csv(os.path.join(OUT, "seed_convergence_contrasts.csv"), index=False)
    s = pd.DataFrame(summary)
    s.to_csv(os.path.join(OUT, "seed_convergence_summary.csv"), index=False)
    print(s.to_string(index=False))


if __name__ == "__main__":
    main()
