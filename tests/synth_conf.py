"""Synthetic runs with the schema of analysis/run_confirmatory.py, to test analysis/confirmatory_analysis.py before real data exist."""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

SEEDS = list(range(7000, 7100))
AI_SC = ["free_market", "mixed_policy", "targeted_subsidy", "universal_access", "universal_permanent"]
KS = [1.0, 0.5, 0.0, -0.5, -1.0]
NET_LEVELS = {"p_within": [0.10, 0.14, 0.25, 0.35], "p_between": [0.005, 0.03, 0.06, 0.12], "h_ses": [0.0, 0.4, 0.6, 0.8],
              "h_ability": [0.0, 0.5, 0.75, 1.0]}
G_STEPS = (1, 120, 240, 360, 480, 600, 720, 840, 960)


def row(rng, block, sc, seed, mode, k=1.0, pivot="P1", benefit_mode="k", ablation="none", L0=0.10, net_label="default", disabled="none",
        dep=0.2, gap=1000.0):
    r = dict(job_id=f"{block}|{sc}|{seed}|{mode}|{k}|{pivot}|{benefit_mode}|{ablation}|{L0}|{net_label}|{disabled}", block=block,
             scenario=sc, seed=seed, mode=mode, k=k, pivot=pivot, pivot_value=0.5, benefit_mode=benefit_mode, ablation=ablation, L0=L0,
             net_label=net_label, p_within=0.18, p_between=0.015, h_ses=0.2, h_ability=0.25, disabled=disabled)
    base = 7000 + 100 * rng.normal()
    for i, v in enumerate((base, base + 50, base + 100 + gap * 0 + 0)):
        r[f"score_t{i + 1}"] = 30000 + 4000 * i + 100 * rng.normal() + (gap * i / 2 if sc != "baseline" else 0)
        r[f"dep_t{i + 1}"] = dep + 0.01 * rng.normal()
        r[f"cal_t{i + 1}"] = 0.3 + 0.01 * rng.normal()
        r[f"decl_t{i + 1}"] = 0.1 + 0.01 * rng.normal()
        r[f"miss_t{i + 1}"] = 17 + rng.normal()
    r["G"] = r["score_t3"] - r["score_t1"]
    r.update(mean_score=31000 + 100 * rng.normal(), gini_score=0.12 + 0.002 * rng.normal(), mean_dependency=dep + 0.01 * rng.normal(),
             mean_calibration_error=0.3 + 0.01 * rng.normal(), relative_ability_decline=0.1 + 0.005 * rng.normal(),
             deadline_miss_count=17 + 0.3 * rng.normal(), mean_legitimacy=0.4, clip_count=0, xbar_timeavg=0.45,
             net_attempts=1, net_k_bar=10.0, net_within_section_share=0.6)
    for t in G_STEPS:
        r[f"g_mean_s{t}"] = 0.5
    return r


def make(dirpath: str) -> None:
    rng = np.random.default_rng(1)
    os.makedirs(dirpath, exist_ok=True)
    K = [row(rng, "K", "baseline", s, "full", dep=0.0, gap=0.0) for s in SEEDS]
    dep_mode = {"full": 0.23, "self_only": 0.22, "zero_interaction": 0.08}
    for sc in AI_SC:
        for k in KS:
            for mode in ("full", "self_only", "zero_interaction"):
                for s in SEEDS:
                    K.append(row(rng, "K", sc, s, mode, k=k, dep=dep_mode[mode], gap=800.0 * (0.4 + 0.6 * (k + 1) / 2)))
    pd.DataFrame(K).to_csv(os.path.join(dirpath, "K_runs.csv"), index=False)
    P2 = [row(rng, "P2", sc, s, "full", k=k, pivot="P2", gap=800.0 * (0.4 + 0.6 * (k + 1) / 2)) for sc in ("free_market", "universal_permanent")
          for k in (0.0, -1.0) for s in SEEDS]
    pd.DataFrame(P2).to_csv(os.path.join(dirpath, "P2_runs.csv"), index=False)
    ABL = [row(rng, "ABL", sc, s, mode, ablation=ab) for ab in ("quality_only", "speed_only") for sc in ("free_market", "universal_permanent")
           for mode in ("full", "zero_interaction") for s in SEEDS]
    pd.DataFrame(ABL).to_csv(os.path.join(dirpath, "ABL_runs.csv"), index=False)
    C1 = [row(rng, "C1", sc, s, mode, benefit_mode="C1") for sc in AI_SC for mode in ("full", "zero_interaction") for s in SEEDS]
    pd.DataFrame(C1).to_csv(os.path.join(dirpath, "C1_runs.csv"), index=False)
    NET = []
    for dis in ("none", "norms"):
        dep = 0.23 if dis == "none" else 0.08
        for s in SEEDS:
            NET.append(row(rng, "NET", "free_market", s, "full", net_label="default", disabled=dis, dep=dep))
        for p, lv in NET_LEVELS.items():
            for l in lv:
                for s in SEEDS:
                    NET.append(row(rng, "NET", "free_market", s, "full", net_label=f"{p}={l:g}", disabled=dis, dep=dep))
        for lab in ("dens=0.282/0.005", "dens=0.231/0.015", "dens=0.154/0.03", "dens=0.077/0.045"):
            for s in SEEDS:
                NET.append(row(rng, "NET", "free_market", s, "full", net_label=lab, disabled=dis, dep=dep))
    pd.DataFrame(NET).to_csv(os.path.join(dirpath, "NET_runs.csv"), index=False)
    L0 = [row(rng, "L0", "free_market", s, mode, L0=l0, dep=dep_mode[mode]) for l0 in (0.05, 0.20, 0.30)
          for mode in ("full", "self_only", "zero_interaction") for s in SEEDS]
    pd.DataFrame(L0).to_csv(os.path.join(dirpath, "L0_runs.csv"), index=False)
