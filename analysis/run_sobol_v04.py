"""
analysis/run_sobol_v04.py: Sobol variance decomposition (S1 and ST) for one scenario, v0.4.

Parameter set: outputs/phase2/morris_v04_retained12.csv (Gate 2), bounds from
analysis.run_morris_screening.PROBLEM. Sampler: SALib.sample.sobol (non-deprecated entry point),
calc_second_order=False, scramble=True, so the design has N * (D + 2) points. Every point is run
once per seed in SEEDS and averaged. Outputs per scenario in outputs/phase2/:
  sobol_v04_<scenario>_runs.csv     every run, all metrics, appended chunk by chunk (resumable)
  sobol_v04_<scenario>_indices.csv  S1, ST and bootstrap CIs per metric and parameter
  sobol_v04_<scenario>_manifest.json
Any NaN, failed run or failed sanity check raises, which stops a chained batch (set -e).

Usage: python -m analysis.run_sobol_v04 <free_market|targeted_subsidy> [--N 512] [--seeds 3000]
                                         [--tag smoke]
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from SALib.analyze import sobol as sobol_analyze
from SALib.sample import sobol as sobol_sample

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import config.params as P
from analysis.param_guard import reset_params
from analysis.manifest import network_summary, write_manifest
from analysis.run_morris_screening import PROBLEM as MORRIS_PROBLEM
from analysis.run_production import _compute_metrics, _simulate

OUT = os.path.join(PROJECT_ROOT, "outputs", os.environ.get("AAAPS_OUT", "phase2"))
RETAINED = os.path.join(OUT, "morris_v04_retained12.csv")
SAMPLE_SEED = 20261009
CHUNK = 140  # 10 design points per worker round on 14 workers
METRICS = ["mean_score", "std_score", "gini_score", "mean_dependency", "mean_calibration_error",
           "mean_retained_ability", "deadline_miss_count", "deadline_miss_rate", "ai_adoption_rate",
           "mean_legitimacy", "borrowing_agent_count", "total_shared_seats_lent",
           "relative_ability_decline"]


def build_problem() -> dict:
    names = list(pd.read_csv(RETAINED).parameter)
    idx = [MORRIS_PROBLEM["names"].index(n) for n in names]
    return {"num_vars": len(names), "names": names, "bounds": [MORRIS_PROBLEM["bounds"][i] for i in idx]}


def _job(args):
    scenario, names, vec, pidx, seed = args
    reset_params()
    for n, v in zip(names, vec):
        if n == "SHAREABLE_SEATS_TIER3":
            P.SHAREABLE_SEATS[3] = int(round(float(v)))
        else:
            setattr(P, n, float(v))
    r = _compute_metrics(_simulate(scenario, seed))
    r.update(sample_idx=pidx, seed=seed)
    return r


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario", choices=["free_market", "targeted_subsidy"])
    ap.add_argument("--N", type=int, default=512)
    ap.add_argument("--seeds", default="3000")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    seeds = [int(s) for s in a.seeds.split(",")]
    smoke = a.tag == "smoke"
    stem = f"sobol_v04_{a.scenario}" + (f"_{a.tag}" if a.tag else "")
    runs_path = os.path.join(OUT, stem + "_runs.csv")

    problem = build_problem()
    X = sobol_sample.sample(problem, a.N, calc_second_order=False, scramble=True, seed=SAMPLE_SEED)
    D = problem["num_vars"]
    assert X.shape == (a.N * (D + 2), D), f"unexpected design shape {X.shape}"
    jobs = [(a.scenario, problem["names"], X[i], i, s) for i in range(len(X)) for s in seeds]
    print(f"scenario={a.scenario} D={D} N={a.N} design points={len(X)} seeds={seeds} total runs={len(jobs)}"
          f" est. hours at 0.58 runs/s = {len(jobs) / 0.58 / 3600:.2f}", flush=True)
    print("parameters:", problem["names"], flush=True)

    done = pd.read_csv(runs_path) if os.path.exists(runs_path) else pd.DataFrame()
    n_done = len(done)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=14) as ex:
        for lo in range(n_done, len(jobs), CHUNK):
            chunk = list(ex.map(_job, jobs[lo:lo + CHUNK]))  # raises on any worker error
            pd.DataFrame(chunk).to_csv(runs_path, mode="a", header=not os.path.exists(runs_path), index=False)
            el = time.time() - t0
            fin = lo + len(chunk) - n_done
            print(f"[sobol {a.scenario}] {lo + len(chunk)}/{len(jobs)} {fin / el:.2f} runs/s", flush=True)

    df = pd.read_csv(runs_path)
    assert len(df) == len(jobs), f"runs file has {len(df)} rows, expected {len(jobs)}"
    assert np.isfinite(df[METRICS].to_numpy(dtype=float)).all(), "NaN or inf in metrics"
    Y = df.groupby("sample_idx")[METRICS].mean().sort_index()
    assert list(Y.index) == list(range(len(X))), "missing design points"

    recs = []
    for m in METRICS:
        y = Y[m].values
        if np.var(y) < 1e-12:
            recs += [{"metric": m, "parameter": p, "S1": np.nan, "S1_conf": np.nan, "ST": np.nan,
                      "ST_conf": np.nan, "degenerate": True} for p in problem["names"]]
            print(f"degenerate metric (no variance): {m}")
            continue
        si = sobol_analyze.analyze(problem, y, calc_second_order=False, num_resamples=1000,
                                   conf_level=0.95, seed=SAMPLE_SEED)
        if not smoke:
            s1sum = float(np.sum(si["S1"]))
            assert -0.1 <= s1sum <= 1.15, f"sanity: sum(S1)={s1sum:.3f} for {m}"
            assert np.all(np.array(si["ST"]) >= np.array(si["S1"]) - 3 * np.array(si["ST_conf"]) - 0.05), \
                f"sanity: ST < S1 beyond CI for {m}"
        for i, p in enumerate(problem["names"]):
            recs.append({"metric": m, "parameter": p, "S1": si["S1"][i], "S1_conf": si["S1_conf"][i],
                         "ST": si["ST"][i], "ST_conf": si["ST_conf"][i], "degenerate": False})
    idx = pd.DataFrame(recs)
    idx.to_csv(os.path.join(OUT, stem + "_indices.csv"), index=False)
    write_manifest(os.path.join(OUT, stem + "_manifest.json"), stage="sobol", scenario=a.scenario,
                   seeds=seeds, n_students=P.N_STUDENTS, N=a.N, calc_second_order=False,
                   sampler=f"SALib.sample.sobol scramble=True seed={SAMPLE_SEED}", parameters=problem["names"],
                   bounds=problem["bounds"], total_runs=len(jobs), runs_csv=os.path.abspath(runs_path), network=network_summary(df))
    top = idx[~idx.degenerate].pivot(index="parameter", columns="metric", values="ST")
    print(top.round(3).to_string())


if __name__ == "__main__":
    main()
