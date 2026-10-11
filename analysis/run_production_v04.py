"""
analysis/run_production_v04.py: v0.4 production runs, 6 scenarios x 100 seeds, N = 240.

Scenarios: baseline, free_market, mixed_policy, targeted_subsidy, universal_access (temporary:
free tier 3 in steps 1-480 only) and universal_permanent (free tier 3 in all steps).

Per run (production_v04_runs.csv): the 12 metrics of analysis.run_production plus gini,
mean_base_ability, relative_ability_decline (MEASURED, not the calibration target),
borrowing_agent_count (borrowers at the last step) and ever_borrowed (agents who borrowed on
any step). Per run and SES x effective tier cell at the last step (production_v04_ses_tier.csv):
agents in the cell, share of all agent-days spent in that cell, and the cell means of score,
retained ability and dependency.
"""

from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import config.params as P
from analysis.param_guard import reset_params
from analysis.manifest import network_summary, write_manifest
from analysis.run_production import _compute_metrics, _simulate

SCENARIOS = ["baseline", "free_market", "mixed_policy", "targeted_subsidy",
             "universal_access", "universal_permanent"]
SEEDS = list(range(100))
OUT = os.path.join(PROJECT_ROOT, "outputs", "phase2")


def _job(args):
    scenario, seed = args
    reset_params()
    model = _simulate(scenario, seed)
    row = _compute_metrics(model)
    allv = model.datacollector.get_agent_vars_dataframe()
    row["ever_borrowed"] = int(allv.groupby(level="AgentID")["borrowing_from"].apply(lambda s: s.notna().any()).sum())
    row.update(scenario=scenario, seed=seed)

    ses_tier = []
    last = allv.xs(P.TOTAL_STEPS, level="Step")
    total_days = len(allv)
    day_counts = allv.groupby(["SES", "ai_tier_effective"]).size()
    for (ses, tier), g in last.groupby(["SES", "ai_tier_effective"]):
        ses_tier.append({"scenario": scenario, "seed": seed, "SES": ses, "tier": int(tier),
                         "n_agents_final": len(g), "share_agent_days": day_counts[(ses, tier)] / total_days,
                         "mean_score": g.score_total.mean(), "mean_retained_ability": g.retained_ability.mean(),
                         "mean_dependency": g.ai_dependency.mean()})
    return row, ses_tier


def main():
    os.makedirs(OUT, exist_ok=True)
    jobs = [(sc, s) for sc in SCENARIOS for s in SEEDS]
    t0, rows, cells = time.time(), [], []
    with ProcessPoolExecutor(max_workers=14) as ex:
        for i, (r, c) in enumerate(ex.map(_job, jobs), 1):
            rows.append(r)
            cells.extend(c)
            if i % 50 == 0 or i == len(jobs):
                print(f"[production] {i}/{len(jobs)} {i / (time.time() - t0):.2f} runs/s", flush=True)
    df, ct = pd.DataFrame(rows), pd.DataFrame(cells)
    p1, p2 = os.path.join(OUT, "production_v04_runs.csv"), os.path.join(OUT, "production_v04_ses_tier.csv")
    df.to_csv(p1, index=False)
    ct.to_csv(p2, index=False)
    print(f"OUTPUT: {os.path.abspath(p1)} shape={df.shape} steps={P.TOTAL_STEPS}")
    print(f"OUTPUT: {os.path.abspath(p2)} shape={ct.shape}")
    cols = ["relative_ability_decline", "mean_score", "gini_score", "mean_dependency",
            "mean_calibration_error", "deadline_miss_count", "mean_legitimacy",
            "borrowing_agent_count", "ever_borrowed"]
    print(df.groupby("scenario")[cols].mean().round(4).to_string())
    write_manifest(os.path.join(OUT, "production_v04_manifest.json"), stage="production",
                   seeds=SEEDS, n_students=P.N_STUDENTS, scenarios=SCENARIOS, sampler="none", network=network_summary(df))


if __name__ == "__main__":
    main()
