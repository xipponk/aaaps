"""
analysis/aspiration_inertness.py: inertness criterion of preregistration.md amendment A2.

free_market, calibration seeds 1000-1029, full vs no_aspiration (aspiration frozen at a_base), at the parameters in
config/params.py. Paired differences (full minus no_aspiration) in mean_dependency and relative_ability_decline;
bootstrap over seeds, 10,000 resamples, rng 20261016, 90% interval. Inert if both intervals lie inside +/-0.02.
Outputs: outputs/v041/aspiration_inertness_runs.csv, aspiration_inertness.json, aspiration_inertness_manifest.json
"""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from analysis.manifest import network_summary, write_manifest  # noqa: E402
from analysis.run_interaction_isolation import _job  # noqa: E402
import config.params as P  # noqa: E402

SEEDS = list(range(1000, 1030))
CONDS = ["full", "no_aspiration"]
SESOI = 0.02
OUT = os.path.join(ROOT, "outputs", "v041")


def main() -> None:
    jobs = [(c, s) for c in CONDS for s in SEEDS]
    with ProcessPoolExecutor(max_workers=14) as ex:
        rows = list(ex.map(_job, jobs))
    df = pd.DataFrame(rows)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "aspiration_inertness_runs.csv")
    df.to_csv(path, index=False)
    print(f"OUTPUT: {os.path.abspath(path)} shape={df.shape} steps={P.TOTAL_STEPS} LAMBDA_A={P.LAMBDA_A}")
    wide = {m: df.pivot(index="seed", columns="condition", values=m) for m in ("mean_dependency", "relative_ability_decline")}
    rng = np.random.default_rng(20261016)
    idx = rng.integers(0, len(SEEDS), size=(10_000, len(SEEDS)))
    res = {}
    for m, w in wide.items():
        d = (w["full"] - w["no_aspiration"]).to_numpy()
        boots = d[idx].mean(axis=1)
        lo, hi = np.percentile(boots, [5, 95])
        res[m] = dict(mean_diff=float(d.mean()), ci90_lo=float(lo), ci90_hi=float(hi),
                      inside_sesoi=bool(lo > -SESOI and hi < SESOI),
                      mean_full=float(w["full"].mean()), mean_no_aspiration=float(w["no_aspiration"].mean()))
    res["inert"] = bool(all(res[m]["inside_sesoi"] for m in wide))
    res["sesoi"] = SESOI
    with open(os.path.join(OUT, "aspiration_inertness.json"), "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps(res, indent=2))
    write_manifest(os.path.join(OUT, "aspiration_inertness_manifest.json"), stage="aspiration_inertness",
                   seeds=SEEDS, n_students=P.N_STUDENTS, scenario="free_market", conditions=CONDS,
                   sampler="none (paired seeds); bootstrap rng 20261016, 10000 resamples", network=network_summary(df))


if __name__ == "__main__":
    main()
