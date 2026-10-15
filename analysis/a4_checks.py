"""
analysis/a4_checks.py: sanity checks for amendment A4 that stop the pipeline when they fail.
    python -m analysis.a4_checks pre    R0 (quality scale 0) at k = 1, 0.5 and 0 must give identical agent-state hashes (bitwise)
    python -m analysis.a4_checks post   in outputs/v041_a4/A4_runs.csv the R0 rows at k = 1, 0.5, 0 must match on every outcome column
Exit code 1 on any mismatch.
"""
from __future__ import annotations

import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def pre() -> int:
    from tests.hashing import run_hashes
    jobs = [(sc, s, "full", {"AI_QUALITY_SCALE": 0.0, "BENEFIT_ABILITY_SLOPE": k}) for sc in ("free_market", "universal_permanent")
            for s in (8000, 8001) for k in (1.0, 0.5, 0.0)]
    with ProcessPoolExecutor(max_workers=12) as ex:
        out = list(ex.map(run_hashes, jobs))
    bad = 0
    for sc in ("free_market", "universal_permanent"):
        for s in (8000, 8001):
            grp = [h for (key, h) in out if key.startswith(f"{sc}|{s}|")]
            same = all(g == grp[0] for g in grp)
            print(f"R0 hash check {sc} seed {s}: {len(grp)} runs, identical: {same}", flush=True)
            bad += 0 if same else 1
    print("R0 PRE-CHECK " + ("PASSED" if not bad else "FAILED"))
    return 1 if bad else 0


def post() -> int:
    df = pd.read_csv(os.path.join(ROOT, "outputs", os.environ.get("AAAPS_A4_OUT", "v041_a4"), "A4_runs.csv"))
    r0 = df[df.level == "R0"]
    skip = {"job_id", "k", "clip_count"} | {c for c in df.columns if c.startswith("g_mean_s")}
    cols = [c for c in df.columns if c not in skip]
    bad = 0
    for (sc, seed), g in r0.groupby(["scenario", "seed"]):
        ref = g[np.isclose(g.k, 1.0)][cols].iloc[0]
        for _, r in g.iterrows():
            if not ref.equals(r[cols]):
                bad += 1
    print(f"R0 post-check: {r0.groupby(['scenario', 'seed']).ngroups} scenario-seed groups, mismatching rows: {bad}")
    print("R0 POST-CHECK " + ("PASSED" if not bad else "FAILED"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(pre() if sys.argv[1] == "pre" else post())
