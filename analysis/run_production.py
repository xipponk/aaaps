"""
analysis/run_production.py — Policy-scenario comparison (ODD §5.5, §8 replication).

Runs all 5 scenarios at N=240, 960 steps, 100 seeds each (500 runs total),
collecting the 12 GSA metrics plus scenario/seed identifiers.

Scenarios (ODD §5.5):
  - baseline          : no AI access (S0 reference)
  - free_market       : budget/WTP-based tier purchase, no intervention
  - universal_access  : free premium (tier 3) for everyone, semesters 1-4 only, then withdrawn
  - mixed_policy      : free_market but stricter course AI limits (C1+C3 no AI)
  - targeted_subsidy  : free_market but low-SES students subsidised to min tier 2

Assumption noted: scenario tier policy is enforced via a post-step override (after each
model.step()), so it wins over the monthly _reconsider_ai_tier() in Phase A. On the
monthly-boundary step itself, the agent processes that one step at the monthly re-evaluated
tier before the override re-applies; ~1 step per 30 is affected (~3%), acceptable for the
results table and flagged here for transparency.
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


def _apply_scenario_policy(model: AaapsModel, scenario: str) -> None:
    """Enforce the scenario's AI-access policy on all agents (post-step override)."""
    if scenario == "baseline":
        for a in model.agents:
            a.ai_tier = 0
            a.ai_tier_effective = 0
    elif scenario == "universal_access":
        # Temporary universal access (ODD §5.5): free tier 3 for semesters 1-4
        # (steps 1-480), then withdrawn. From semester 5 (step 481) onward the
        # override stops and agents revert to their own §7.6 budget/WTP tier
        # decisions via _reconsider_ai_tier().
        if model.current_step <= 480:
            for a in model.agents:
                a.ai_tier = 3
                a.ai_tier_effective = 3
        # else: no override — _reconsider_ai_tier() governs from semester 5 onward
    elif scenario == "targeted_subsidy":
        for a in model.agents:
            if a.SES == "low" and a.ai_tier < 2:
                a.ai_tier = 2
                a.ai_tier_effective = 2
    # free_market and mixed_policy: no tier override (budget/WTP-based)


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

    return {
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
    }


def _run_one(scenario_seed: tuple[str, int]) -> dict:
    scenario, seed = scenario_seed

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

        _apply_scenario_policy(model, scenario)

        for _ in range(TOTAL_STEPS):
            model.step()
            _apply_scenario_policy(model, scenario)

        metrics = _compute_metrics(model)
        metrics['scenario'] = scenario
        metrics['seed'] = seed
        return metrics
    finally:
        P.COURSES[2]['ai_allowed'] = saved_c3


def run_production():
    print("=" * 79)
    print("Production scenario comparison: 5 scenarios x 100 seeds = 500 runs")
    print("=" * 79)

    jobs = [(sc, s) for sc in SCENARIOS for s in range(N_SEEDS)]
    print(f"{len(jobs)} jobs. Launching on 14 workers...")

    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=14) as executor:
        futures = [executor.submit(_run_one, j) for j in jobs]
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
