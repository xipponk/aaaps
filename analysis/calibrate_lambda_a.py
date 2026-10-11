"""
analysis/calibrate_lambda_a.py: calibrate LAMBDA_A (v0.4 recovery fix).

Target: relative decline of mean retained ability at step 960 under PERMANENT universal
access (free tier 3, all steps), where relative decline = 1 - mean(a_r) / mean(a_base).
Calibration seeds (1000-1009) are disjoint from production seeds (0-99).

Stages
  grid   : permanent universal access over a LAMBDA_A grid, then log-linear interpolation
           to the 10 / 21 / 35 percent targets.
  verify : all six scenarios at given LAMBDA_A values (one value per candidate).

Usage
  python -m analysis.calibrate_lambda_a grid
  python -m analysis.calibrate_lambda_a verify 0.0031,0.0068,0.0140
"""

from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import config.params as P
from analysis.param_guard import reset_params
from analysis.manifest import network_summary, write_manifest
from analysis.run_production import _run_one

SEEDS = list(range(1000, 1030))
GRID = [0.0007, 0.0012, 0.0016, 0.002, 0.0025, 0.004, 0.0059]
TARGETS = [0.10, 0.21, 0.35]
SCENARIOS6 = ["baseline", "free_market", "mixed_policy", "targeted_subsidy",
              "universal_access", "universal_permanent"]
OUT = os.path.join(PROJECT_ROOT, "outputs", os.environ.get("AAAPS_OUT", "phase1"))


def _job(args):
    scenario, seed, lam = args
    reset_params()
    P.LAMBDA_A = float(lam)
    m = _run_one((scenario, seed))
    m["lambda_a"] = lam
    return m


def _run_jobs(jobs, label):
    t0 = time.time()
    rows = []
    with ProcessPoolExecutor(max_workers=14) as ex:
        futs = [ex.submit(_job, j) for j in jobs]
        for i, f in enumerate(as_completed(futs), 1):
            rows.append(f.result())
            if i % 10 == 0 or i == len(jobs):
                print(f"[{label}] {i}/{len(jobs)} {i / (time.time() - t0):.2f} runs/s", flush=True)
    return pd.DataFrame(rows)


def stage_grid():
    jobs = [("universal_permanent", s, lam) for lam in GRID for s in SEEDS]
    df = _run_jobs(jobs, "grid")
    os.makedirs(OUT, exist_ok=True)
    df.to_csv(os.path.join(OUT, "calib_grid.csv"), index=False)
    g = df.groupby("lambda_a")["relative_ability_decline"].agg(["mean", "std"]).reset_index()
    print(g.to_string(index=False))
    mono = bool(np.all(np.diff(g["mean"].values) > 0))
    print("monotone in lambda_a:", mono)
    for t in TARGETS:
        lam = float(np.exp(np.interp(t, g["mean"].values, np.log(g["lambda_a"].values))))
        print(f"target {t:.2f}: interpolated LAMBDA_A = {lam:.5f}")
    write_manifest(os.path.join(OUT, "calib_grid_manifest.json"), stage="grid", seeds=SEEDS,
                   n_students=P.N_STUDENTS, grid=GRID, scenario="universal_permanent",
                   sampler="log-linear grid", network=network_summary(df))


def stage_verify(lams):
    jobs = [(sc, s, lam) for lam in lams for sc in SCENARIOS6 for s in SEEDS]
    df = _run_jobs(jobs, "verify")
    os.makedirs(OUT, exist_ok=True)
    tag = "_".join(f"{x:g}" for x in lams)
    df.to_csv(os.path.join(OUT, f"calib_verify_{tag}.csv"), index=False)
    cols = ["relative_ability_decline", "mean_dependency", "mean_score", "deadline_miss_count",
            "mean_calibration_error"]
    summ = df.groupby(["lambda_a", "scenario"])[cols].mean().round(4)
    print(summ.to_string())
    write_manifest(os.path.join(OUT, f"calib_verify_{tag}_manifest.json"), stage="verify",
                   seeds=SEEDS, n_students=P.N_STUDENTS, lambdas=lams, scenarios=SCENARIOS6,
                   sampler="none (fixed values)", network=network_summary(df))


if __name__ == "__main__":
    if sys.argv[1] == "grid":
        stage_grid()
    else:
        stage_verify([float(x) for x in sys.argv[2].split(",")])
