"""
analysis/run_a4.py: runner for amendment A4 (post hoc, exploratory channel-ratio sweep and diagnostic D1).
    python -m analysis.run_a4 A4|D1
A4: seeds 8000-8099, levels R0..R6 (quality and speed multipliers), k in {1, 0.5, 0}, free_market and universal_permanent, mode full,
    plus baseline once: 4,300 runs. D1: free_market, k = 1, R3, seeds 8100-8104, local observed-use fraction logged: 5 runs.
Writes outputs/v041_a4/<block>_runs.csv (resumable) and a manifest. Every job starts with reset_params().
"""
from __future__ import annotations

import hashlib
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from analysis.manifest import network_summary, write_manifest  # noqa: E402
from analysis.param_guard import reset_params  # noqa: E402
from analysis.run_production import _compute_metrics  # noqa: E402
import config.params as P  # noqa: E402
from model.model import BENEFIT_LOG_STEPS, AaapsModel  # noqa: E402

OUT = os.path.join(ROOT, "outputs", os.environ.get("AAAPS_A4_OUT", "v041_a4"))
SEEDS = list(range(8000, 8000 + int(os.environ.get("AAAPS_A4_NSEEDS", "100"))))  # smoke tests only; the real runs use 100
D1_SEEDS = list(range(8100, 8105))
SCENARIOS = ["free_market", "universal_permanent"]
KS = [1.0, 0.5, 0.0]
LEVELS = {"R0": (0.0, 1.0), "R1": (0.25, 1.0), "R2": (0.5, 1.0), "R3": (1.0, 1.0), "R4": (1.0, 0.5), "R5": (1.0, 0.25), "R6": (1.0, 0.0)}
SCRIPT_SHA = hashlib.sha256(open(os.path.join(ROOT, "analysis", "a4_analysis.py"), "rb").read()).hexdigest()


def J(block, sc, seed, level="R3", k=1.0, log=False):
    mq, ms = LEVELS[level]
    d = dict(block=block, scenario=sc, seed=seed, level=level, mq=mq, ms=ms, k=k, log=log)
    d["job_id"] = f"{block}|{sc}|{seed}|{level}|{k}"
    return d


def jobs_for(block: str) -> list[dict]:
    if block == "A4":
        jobs = [J("A4", "baseline", s) for s in SEEDS]
        jobs += [J("A4", sc, s, level=lv, k=k) for sc in SCENARIOS for k in KS for lv in LEVELS for s in SEEDS]
    elif block == "D1":
        jobs = [J("D1", "free_market", s, log=True) for s in D1_SEEDS]
    else:
        raise SystemExit(f"unknown block {block}")
    ids = [j["job_id"] for j in jobs]
    assert len(ids) == len(set(ids)), "duplicate job ids"
    return jobs


def run_job(job: dict) -> dict:
    reset_params()
    try:
        sc = job["scenario"]
        P.BENEFIT_ABILITY_SLOPE = float(job["k"])
        P.AI_QUALITY_SCALE = float(job["mq"])
        P.AI_SPEED_SCALE = float(job["ms"])
        if sc == "mixed_policy":
            P.COURSES[2]['ai_allowed'] = False
        model = AaapsModel(n_students=P.N_STUDENTS, scenario=sc, seed=int(job["seed"]), log_local_fraction=bool(job["log"]))
        for a in model.agents:
            wtp = a.monthly_budget * P.TIER_BUDGET_FRACTION[a.SES]
            a.ai_tier = 3 if wtp >= P.AI_MONTHLY_COST[3] else 2 if wtp >= P.AI_MONTHLY_COST[2] else 1
            a.ai_tier_effective = a.ai_tier
        for _ in range(P.TOTAL_STEPS):
            model.step()
        row = _compute_metrics(model)
        df = model.datacollector.get_agent_vars_dataframe().xs(P.TOTAL_STEPS, level="Step").reset_index()
        df = df.sort_values(["base_ability", "AgentID"], kind="mergesort").reset_index(drop=True)
        third = len(df) // 3
        for i, sl in enumerate((slice(0, third), slice(third, 2 * third), slice(2 * third, len(df))), start=1):
            t = df.iloc[sl]
            row[f"score_t{i}"] = float(t.score_total.mean())
            row[f"dep_t{i}"] = float(t.ai_dependency.mean())
        row["G"] = row["score_t3"] - row["score_t1"]
        for s in BENEFIT_LOG_STEPS:
            row[f"g_mean_s{s}"] = float(model.g_log[s])
        row["clip_count"] = int(model.benefit_clip_count)
        row.update(job_id=job["job_id"], block=job["block"], scenario=sc, seed=int(job["seed"]), level=job["level"], mq=job["mq"],
                   ms=job["ms"], k=float(job["k"]), pivot_value=float(model.benefit_pivot))
        if job["log"]:
            L = model.local_log
            os.makedirs(OUT, exist_ok=True)
            np.savez_compressed(os.path.join(OUT, f"D1_seed{job['seed']}.npz"), obs=np.array(L["obs"]), raw=np.array(L["raw"]),
                                glob=np.array(L["glob"]), deg=L["deg"], p_visible=P.P_VISIBLE)
        return row
    finally:
        reset_params()


def main() -> None:
    block = sys.argv[1]
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"{block}_runs.csv")
    jobs = jobs_for(block)
    done = set(pd.read_csv(path).job_id) if os.path.exists(path) else set()
    todo = [j for j in jobs if j["job_id"] not in done]
    print(f"block {block}: {len(jobs)} jobs, {len(done)} done, {len(todo)} to run; output {os.path.abspath(path)}", flush=True)
    t0 = time.time()
    chunk = 140
    with ProcessPoolExecutor(max_workers=14) as ex:
        for lo in range(0, len(todo), chunk):
            rows = list(ex.map(run_job, todo[lo:lo + chunk]))
            pd.DataFrame(rows).to_csv(path, mode="a", header=not os.path.exists(path), index=False)
            n = lo + len(rows)
            print(f"[{block}] {n}/{len(todo)} {n / (time.time() - t0):.2f} runs/s", flush=True)
    df = pd.read_csv(path)
    assert len(df) == len(jobs) and df.job_id.is_unique, f"{len(df)} rows for {len(jobs)} jobs"
    assert np.isfinite(df[["G", "mean_score", "mean_dependency"]].to_numpy(dtype=float)).all(), "non-finite metrics"
    write_manifest(os.path.join(OUT, f"{block}_manifest.json"), stage=f"a4_{block}", seeds=[min(j["seed"] for j in jobs), max(j["seed"] for j in jobs)],
                   n_students=P.N_STUDENTS, n_runs=len(df), sampler="none (paired seeds)", analysis_script_sha256=SCRIPT_SHA,
                   network=network_summary(df))
    print(f"[{block}] DONE {len(df)} rows", flush=True)


if __name__ == "__main__":
    main()
