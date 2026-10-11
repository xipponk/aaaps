"""
analysis/run_production.py: Policy-scenario comparison (ODD §5.5, §8 replication).

Runs all 5 scenarios at N=240, 960 steps, 100 seeds each (500 runs total),
collecting the 12 GSA metrics plus scenario/seed identifiers.

Scenarios (ODD §5.5):
  - baseline          : no AI access (S0 reference)
  - free_market       : budget/WTP-based tier purchase, no intervention
  - universal_access  : free premium (tier 3) for everyone, semesters 1-4 only, then withdrawn
  - mixed_policy      : free_market but stricter course AI limits (C1+C3 no AI)
  - targeted_subsidy  : free_market but low-SES students subsidised to min tier 2

v0.4: the scenario tier policy now lives in AaapsModel._apply_scenario_policy and runs in
Phase A after the monthly tier re-evaluation. In v0.3 it was a post-step override, which let
every agent process (and borrow in) the first step of each month at its re-evaluated tier.
"""

from __future__ import annotations

import os
import sys
import time
import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from model.model import AaapsModel
import config.params as P
from analysis.param_guard import reset_params

SCENARIOS = ["baseline", "free_market", "universal_access", "mixed_policy", "targeted_subsidy"]
N_SEEDS = 100
N_STUDENTS = 240
TOTAL_STEPS = P.TOTAL_STEPS

METRICS = [
    'mean_score', 'std_score', 'gini_score', 'mean_dependency',
    'mean_calibration_error', 'mean_retained_ability', 'deadline_miss_count',
    'deadline_miss_rate', 'ai_adoption_rate', 'mean_legitimacy',
    'borrowing_agent_count', 'total_shared_seats_lent',
]


def _compute_metrics(model: AaapsModel) -> dict[str, float]:
    df = model.datacollector.get_agent_vars_dataframe().xs(TOTAL_STEPS, level="Step")
    scores = df['score_total'].values
    n = len(scores)
    s_sorted = np.sort(scores)
    total = s_sorted.sum()
    if n == 0 or total == 0.0:
        gini = 0.0
    else:
        gini = (2.0 * np.sum((np.arange(n) + 1) * s_sorted)) / (n * total) - (n + 1.0) / n

    total_missed = float(df['deadline_miss_count'].sum())
    total_completed = float(df['tasks_completed'].sum())
    deadline_miss_rate = total_missed / max(1.0, total_missed + total_completed)

    mean_base = float(np.mean(df['base_ability']))
    mean_ar = float(np.mean(df['retained_ability']))
    return {
        'mean_base_ability': mean_base,
        'relative_ability_decline': 1.0 - mean_ar / mean_base,
        'mean_score': float(np.mean(scores)),
        'std_score': float(np.std(scores)),
        'gini_score': float(gini),
        'mean_dependency': float(np.mean(df['ai_dependency'])),
        'mean_calibration_error': float(np.mean(df['calibration_error'])),
        'mean_retained_ability': float(np.mean(df['retained_ability'])),
        'deadline_miss_count': float(np.mean(df['deadline_miss_count'])),
        'deadline_miss_rate': float(deadline_miss_rate),
        'ai_adoption_rate': float(np.mean(df['ai_tier_effective'] >= 1)),
        'mean_legitimacy': float(np.mean(df['ai_legitimacy'])),
        'borrowing_agent_count': float(df['borrowing_from'].notna().sum()),
        'total_shared_seats_lent': float(df['shared_seats_out'].sum()),
        # v0.4.1: realised network, recorded for every run (NaN when the graph is empty)
        'net_attempts': float(model.network_info.get('attempts', np.nan)),
        'net_disconnected_rejects': float(model.network_info.get('disconnected_rejects', np.nan)),
        'net_k_bar': float(model.network_info.get('k_bar', np.nan)),
        'net_within_section_share': float(model.network_info.get('within_section_share', np.nan)),
        'net_kbar_in_range': float(model.network_info.get('kbar_in_range', np.nan)),
    }


def _simulate(scenario: str, seed: int) -> AaapsModel:
    """Run one full simulation for a scenario and seed and return the finished model."""
    saved_c3 = P.COURSES[2]['ai_allowed']
    if scenario == "mixed_policy":
        # Stricter course policy: C3 (Lab/Practical) also disallows AI (C1 already False)
        P.COURSES[2]['ai_allowed'] = False

    try:
        model = AaapsModel(n_students=N_STUDENTS, scenario=scenario, seed=seed)

        # Initial budget/WTP-based tier assignment (free_market default)
        for a in model.agents:
            wtp = a.monthly_budget * P.TIER_BUDGET_FRACTION[a.SES]
            if wtp >= P.AI_MONTHLY_COST[3]:
                a.ai_tier = 3
            elif wtp >= P.AI_MONTHLY_COST[2]:
                a.ai_tier = 2
            else:
                a.ai_tier = 1
            a.ai_tier_effective = a.ai_tier

        # The scenario access policy is enforced inside the model (Phase A, after the monthly
        # tier re-evaluation); see AaapsModel._apply_scenario_policy.
        for _ in range(TOTAL_STEPS):
            model.step()

        return model
    finally:
        P.COURSES[2]['ai_allowed'] = saved_c3


def _run_one(scenario_seed: tuple[str, int]) -> dict:
    scenario, seed = scenario_seed
    reset_params()
    metrics = _compute_metrics(_simulate(scenario, seed))
    metrics['scenario'] = scenario
    metrics['seed'] = seed
    return metrics


def _pool_job(scenario_seed: tuple[str, int]) -> dict:
    """Worker entry for run_production(): clean parameters, then one run."""
    reset_params()
    return _run_one(scenario_seed)


def run_production():
    print("=" * 79)
    print("Production scenario comparison: 5 scenarios x 100 seeds = 500 runs")
    print("=" * 79)

    jobs = [(sc, s) for sc in SCENARIOS for s in range(N_SEEDS)]
    print(f"{len(jobs)} jobs. Launching on 14 workers...")

    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=14) as executor:
        futures = [executor.submit(_pool_job, j) for j in jobs]
        done = 0
        for fut in as_completed(futures):
            results.append(fut.result())
            done += 1
            if done % 50 == 0 or done == len(jobs):
                el = time.time() - t0
                rate = done / max(1e-6, el)
                rem = (len(jobs) - done) / max(1e-6, rate)
                print(f"[{done}/{len(jobs)}] speed={rate:.2f}/s est_remaining={rem/60.0:.1f}min")

    elapsed = time.time() - t0
    print(f"[DONE] {len(jobs)} runs in {elapsed:.1f}s ({elapsed/60.0:.1f} min).")

    df = pd.DataFrame(results)
    out_dir = os.path.join(PROJECT_ROOT, "outputs")
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(os.path.join(out_dir, "production_results.csv"), index=False)
    print(f"Saved outputs/production_results.csv ({len(df)} rows).")

    # Per-scenario summary (mean over seeds)
    summary = df.groupby('scenario')[METRICS].mean()
    summary.to_csv(os.path.join(out_dir, "production_summary.csv"))
    print("\n=== Per-scenario mean (over 100 seeds) ===")
    print(summary[['mean_score', 'gini_score', 'mean_dependency', 'deadline_miss_count',
                   'mean_legitimacy', 'borrowing_agent_count']].round(3).to_string())


if __name__ == "__main__":
    run_production()
