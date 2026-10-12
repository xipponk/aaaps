"""
analysis/run_confirmatory.py: runner for the benefit-ability study (preregistration.md A3). One block per call:
    python -m analysis.run_confirmatory K|P2|ABL|C1|NET|L0
Seeds 7000-7099. Writes outputs/v041_conf/<block>_runs.csv (resumable: finished job_ids are skipped) and a manifest.
Every job starts with reset_params(). Block P2 needs the finished K block (pivot = time-averaged mean a_r/100 of the k = 1 full run).
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

OUT = os.path.join(ROOT, "outputs", os.environ.get("AAAPS_CONF_OUT", "v041_conf"))
SEEDS = list(range(7000, 7000 + int(os.environ.get("AAAPS_CONF_NSEEDS", "100"))))  # smoke tests only; the real runs use 100
AI_SC = ["free_market", "mixed_policy", "targeted_subsidy", "universal_access", "universal_permanent"]
COPRIMARY = ["free_market", "universal_permanent"]
KS = [1.0, 0.5, 0.0, -0.5, -1.0]
MODES = ["full", "self_only", "zero_interaction"]
NET_LEVELS = {"p_within": [0.10, 0.14, 0.25, 0.35], "p_between": [0.005, 0.03, 0.06, 0.12], "h_ses": [0.0, 0.4, 0.6, 0.8],
              "h_ability": [0.0, 0.5, 0.75, 1.0]}
NET_ATTR = {"p_within": "SBM_P_WITHIN", "p_between": "SBM_P_BETWEEN", "h_ses": "HOMOPHILY_SES", "h_ability": "HOMOPHILY_ABILITY"}
DENSITY_POINTS = [(0.282, 0.005), (0.231, 0.015), (0.154, 0.03), (0.077, 0.045)]
SCRIPT_SHA = hashlib.sha256(open(os.path.join(ROOT, "analysis", "confirmatory_analysis.py"), "rb").read()).hexdigest()


def J(block, sc, seed, mode="full", k=1.0, pivot="P1", pivot_value=None, benefit_mode="k", ablation="none", L0=0.10,
      net_label="default", net=None, disabled="none"):
    net = net or {}
    d = dict(block=block, scenario=sc, seed=seed, mode=mode, k=k, pivot=pivot, pivot_value=pivot_value, benefit_mode=benefit_mode,
             ablation=ablation, L0=L0, net_label=net_label, disabled=disabled, net=net)
    d["job_id"] = f"{block}|{sc}|{seed}|{mode}|{k}|{pivot}|{benefit_mode}|{ablation}|{L0}|{net_label}|{disabled}"
    return d


def jobs_for(block: str) -> list[dict]:
    jobs = []
    if block == "K":
        jobs += [J("K", "baseline", s) for s in SEEDS]
        jobs += [J("K", sc, s, mode=m, k=k) for sc in AI_SC for k in KS for m in MODES for s in SEEDS]
    elif block == "P2":
        kf = pd.read_csv(os.path.join(OUT, "K_runs.csv"))
        for sc in COPRIMARY:
            for k in (0.0, -1.0):
                for s in SEEDS:
                    r = kf[(kf.scenario == sc) & (kf.seed == s) & (kf["mode"] == "full") & np.isclose(kf.k, 1.0)]
                    assert len(r) == 1, (sc, s)
                    jobs.append(J("P2", sc, s, k=k, pivot="P2", pivot_value=float(r.xbar_timeavg.iloc[0])))
    elif block == "ABL":
        jobs += [J("ABL", sc, s, mode=m, ablation=ab) for ab in ("quality_only", "speed_only") for sc in COPRIMARY
                 for m in ("full", "zero_interaction") for s in SEEDS]
    elif block == "C1":
        jobs += [J("C1", sc, s, mode=m, benefit_mode="C1") for sc in AI_SC for m in ("full", "zero_interaction") for s in SEEDS]
    elif block == "NET":
        for dis in ("none", "norms"):
            jobs += [J("NET", "free_market", s, net_label="default", disabled=dis) for s in SEEDS]
            for p, lv in NET_LEVELS.items():
                for l in lv:
                    jobs += [J("NET", "free_market", s, net_label=f"{p}={l:g}", net={NET_ATTR[p]: l}, disabled=dis) for s in SEEDS]
            for pw, pb in DENSITY_POINTS:
                jobs += [J("NET", "free_market", s, net_label=f"dens={pw:g}/{pb:g}", net={"SBM_P_WITHIN": pw, "SBM_P_BETWEEN": pb},
                           disabled=dis) for s in SEEDS]
    elif block == "L0":
        jobs += [J("L0", "free_market", s, mode=m, L0=l0) for l0 in (0.05, 0.20, 0.30) for m in MODES for s in SEEDS]
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
        P.BENEFIT_MODE = job["benefit_mode"]
        P.INITIAL_LEGITIMACY = float(job["L0"])
        if job["pivot"] == "P2":
            P.BENEFIT_PIVOT_OVERRIDE = float(job["pivot_value"])
        for attr, v in job["net"].items():
            setattr(P, attr, float(v))
        if job["ablation"] == "quality_only":
            for t in P.AI_SPEED_BOOST:
                P.AI_SPEED_BOOST[t] = 0
        elif job["ablation"] == "speed_only":
            for t in P.AI_QUALITY_BOOST:
                P.AI_QUALITY_BOOST[t] = 0.0
        if sc == "mixed_policy":
            P.COURSES[2]['ai_allowed'] = False
        model = AaapsModel(n_students=P.N_STUDENTS, scenario=sc, seed=int(job["seed"]),
                           zero_interaction_mode=(job["mode"] == "zero_interaction"), self_only_mode=(job["mode"] == "self_only"),
                           disabled_submodels=frozenset({"norms"} if job["disabled"] == "norms" else ()))
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
            row[f"cal_t{i}"] = float(t.calibration_error.mean())
            row[f"decl_t{i}"] = float(1.0 - t.retained_ability.mean() / t.base_ability.mean())
            row[f"miss_t{i}"] = float(t.deadline_miss_count.mean())
        row["G"] = row["score_t3"] - row["score_t1"]
        for s in BENEFIT_LOG_STEPS:
            row[f"g_mean_s{s}"] = float(model.g_log[s])
        row["clip_count"] = int(model.benefit_clip_count)
        row["xbar_timeavg"] = float(model._xbar_sum / P.TOTAL_STEPS)
        row.update(job_id=job["job_id"], block=job["block"], scenario=sc, seed=int(job["seed"]), mode=job["mode"], k=float(job["k"]),
                   pivot=job["pivot"], pivot_value=float(model.benefit_pivot), benefit_mode=job["benefit_mode"],
                   ablation=job["ablation"], L0=float(job["L0"]), net_label=job["net_label"], p_within=P.SBM_P_WITHIN,
                   p_between=P.SBM_P_BETWEEN, h_ses=P.HOMOPHILY_SES, h_ability=P.HOMOPHILY_ABILITY, disabled=job["disabled"])
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
    write_manifest(os.path.join(OUT, f"{block}_manifest.json"), stage=f"confirmatory_{block}", seeds=[SEEDS[0], SEEDS[-1]],
                   n_students=P.N_STUDENTS, n_runs=len(df), sampler="none (paired seeds)",
                   analysis_script_sha256=SCRIPT_SHA, network=network_summary(df))
    print(f"[{block}] DONE {len(df)} rows", flush=True)


if __name__ == "__main__":
    main()
