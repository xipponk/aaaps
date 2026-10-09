"""
analysis/network_range_scan.py: graph-only scan of SBM_P_WITHIN x SBM_P_BETWEEN (no simulation).

Builds agents and the network (model constructor, no stepping) with TARGET_K_BAR_RANGE widened to (0, 1e9), so the only
rejection left is disconnection, and records per cell: mean attempts, share of networks that hit the fallback, realized
mean degree and within-section edge share. Used to choose the Morris and network-sweep ranges for v0.4.1.
Seeds 0-9 (graph only; these are not confirmatory seeds). Other network parameters at default.
"""
from __future__ import annotations

import itertools
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from analysis.network_fallback_audit import _audit_one, OUT

PW = [0.04, 0.06, 0.08, 0.10, 0.14, 0.18, 0.25, 0.35, 0.50, 0.70]
PB = [0.002, 0.005, 0.01, 0.015, 0.03, 0.06, 0.12, 0.20]
SEEDS = range(10)


def main() -> None:
    J = [("scan", f"{pw}|{pb}", s, {"SBM_P_WITHIN": pw, "SBM_P_BETWEEN": pb, "TARGET_K_BAR_RANGE": (0.0, 1e9)})
         for pw, pb in itertools.product(PW, PB) for s in SEEDS]
    with ProcessPoolExecutor(max_workers=14) as ex:
        rows = list(ex.map(_audit_one, J, chunksize=2))
    d = pd.DataFrame(rows)
    d[["p_within", "p_between"]] = d.key.str.split("|", expand=True).astype(float)
    d["exp_degree"] = 39 * d.p_within + 200 * d.p_between
    g = d.groupby(["p_within", "p_between"]).agg(exp_degree=("exp_degree", "first"), attempts=("attempts", "mean"),
        disc_per_attempt=("disconnected_rejects", "sum"), n_attempts=("attempts", "sum"), fallback=("fallback", "mean"),
        k_bar=("k_bar", "mean"), within_share=("within_share", "mean")).reset_index()
    g["p_disconnected_per_attempt"] = g.disc_per_attempt / g.n_attempts
    g = g.drop(columns=["disc_per_attempt", "n_attempts"])
    g.to_csv(os.path.join(OUT, "network_range_scan.csv"), index=False)
    print(g.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
