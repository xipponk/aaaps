"""
analysis/propagation_audit.py: CLAUDE.md rule 3 propagation audit for all 23 GSA parameters.

Each parameter is set to its lower and upper Morris bound with all others at their defaults,
through the same evaluation function the Morris run uses (analysis.run_morris_screening
._worker_eval, free_market, seed 42, 960 steps). A parameter whose two bounds give outputs
identical to the default in every one of the 12 metrics is reported as DEAD (a bug until shown
otherwise). The default point is run twice to confirm the run is deterministic, so any
difference is caused by the parameter and not by noise.
"""

from __future__ import annotations

import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import config.params as P
from analysis.manifest import write_manifest
from analysis.run_morris_screening import METRICS, PROBLEM, _worker_eval

OUT = os.path.join(PROJECT_ROOT, "outputs", "phase1")


def default_vector() -> np.ndarray:
    d = {n: getattr(P, n, None) for n in PROBLEM["names"]}
    d["SHAREABLE_SEATS_TIER3"] = P.SHAREABLE_SEATS[3]
    d["RHO_RATIO"] = P.RHO_RATIO
    return np.array([float(d[n]) for n in PROBLEM["names"]])


def main() -> None:
    names, bounds = PROBLEM["names"], np.array(PROBLEM["bounds"])
    base = default_vector()
    jobs = [("default_a", base), ("default_b", base)]
    for i, n in enumerate(names):
        for tag, b in (("lo", bounds[i, 0]), ("hi", bounds[i, 1])):
            v = base.copy()
            v[i] = b
            jobs.append((f"{n}|{tag}", v))
    with ProcessPoolExecutor(max_workers=14) as ex:
        futs = [ex.submit(_worker_eval, (k, v)) for k, (_, v) in enumerate(jobs)]
        res = {jobs[k][0]: f.result()[1] for k, f in enumerate(futs)}
    df = pd.DataFrame(res).T
    df.to_csv(os.path.join(OUT, "propagation_audit_raw.csv"))

    det = bool((df.loc["default_a"] == df.loc["default_b"]).all())
    print(f"default point deterministic (two runs identical in all 12 metrics): {det}")
    rows = []
    for n in names:
        d0 = df.loc["default_a"]
        lo, hi = df.loc[f"{n}|lo"], df.loc[f"{n}|hi"]
        changed = [m for m in METRICS if lo[m] != hi[m] or lo[m] != d0[m] or hi[m] != d0[m]]
        scale = (df[METRICS].max() - df[METRICS].min()).replace(0, np.nan)
        spread = ((lo - hi).abs() / scale).max()
        rows.append({"parameter": n, "default": base[names.index(n)], "lo": bounds[names.index(n), 0],
                     "hi": bounds[names.index(n), 1], "n_metrics_changed": len(changed),
                     "max_lo_hi_gap_vs_audit_range": float(spread) if spread == spread else 0.0,
                     "status": "ok" if changed else "DEAD"})
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(OUT, "propagation_audit.csv"), index=False)
    print(out.to_string(index=False))
    print("DEAD parameters:", list(out.loc[out.status == "DEAD", "parameter"]) or "none")
    write_manifest(os.path.join(OUT, "propagation_audit_manifest.json"), stage="propagation_audit",
                   seeds=[42], n_students=P.N_STUDENTS, sampler="one-at-a-time bounds",
                   scenario="free_market", deterministic_default=det)


if __name__ == "__main__":
    main()
