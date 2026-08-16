"""
analysis/run_sobol.py — Sobol Variance Decomposition (ODD §9 Stage 2).

Executes Sobol GSA across the corrected retained-12 parameter set (from the fixed
Morris screening, 12-metric composite ranking) on the free_market scenario
(N=240, 960 steps, seed=42). Tracks all 12 output metrics, computes S1/ST.
Outputs to outputs/sobol_results.csv and outputs/sobol_raw_evaluations.csv.
"""

from __future__ import annotations

import os
import sys
import time
import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
from SALib.sample import saltelli
from SALib.analyze import sobol

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scenarios.free_market import run as run_free_market
import config.params as P

# Corrected retained-12 (Morris 12-metric composite ranking, fixed codebase)
PROBLEM_12 = {
    'num_vars': 12,
    'names': [
        'ABILITY_MEAN',
        'ABILITY_STD',
        'PROCESSING_DIFFICULTY_FACTOR',
        'DELTA_D',
        'BETA_C',
        'ETA_SELF',
        'PROSOCIALITY_BETA_A',
        'ETA',
        'P_VISIBLE',
        'ALPHA_D',
        'SBM_P_BETWEEN',
        'CONFORMITY_BETA_B',
    ],
    'bounds': [
        [40.0, 60.0],     # ABILITY_MEAN
        [10.0, 20.0],     # ABILITY_STD
        [20.0, 40.0],     # PROCESSING_DIFFICULTY_FACTOR
        [0.003, 0.008],   # DELTA_D
        [0.006, 0.015],   # BETA_C
        [0.010, 0.100],   # ETA_SELF
        [1.0, 5.0],       # PROSOCIALITY_BETA_A
        [0.020, 0.200],   # ETA
        [0.400, 0.900],   # P_VISIBLE
        [0.008, 0.016],   # ALPHA_D
        [0.005, 0.030],   # SBM_P_BETWEEN
        [2.0, 8.0],       # CONFORMITY_BETA_B
    ]
}

METRICS = [
    'mean_score', 'std_score', 'gini_score', 'mean_dependency',
    'mean_calibration_error', 'mean_retained_ability', 'deadline_miss_count',
    'deadline_miss_rate', 'ai_adoption_rate', 'mean_legitimacy',
    'borrowing_agent_count', 'total_shared_seats_lent',
]


def _worker_eval(idx_sample: tuple[int, np.ndarray]) -> tuple[int, dict[str, float]]:
    idx, param_values = idx_sample
    (
        ab_mean, ab_std, proc_factor, delta_d,
        beta_c, eta_self, prosocial_beta_a, eta,
        p_visible, alpha_d, p_between, conf_beta_b
    ) = param_values

    P.ABILITY_MEAN = float(ab_mean)
    P.ABILITY_STD = float(ab_std)
    P.PROCESSING_DIFFICULTY_FACTOR = float(proc_factor)
    P.DELTA_D = float(delta_d)
    P.BETA_C = float(beta_c)
    P.ETA_SELF = float(eta_self)
    P.PROSOCIALITY_BETA_A = float(prosocial_beta_a)
    P.ETA = float(eta)
    P.P_VISIBLE = float(p_visible)
    P.ALPHA_D = float(alpha_d)
    P.SBM_P_BETWEEN = float(p_between)
    P.CONFORMITY_BETA_B = float(conf_beta_b)

    model = run_free_market(seed=42, n_students=240)
    df = model.datacollector.get_agent_vars_dataframe().xs(960, level="Step")

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

    res = {
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
    return idx, res


def run_sobol_analysis():
    print("=" * 79)
    print("Sobol Variance Decomposition (corrected 12-param set)")
    print("=" * 79)

    N = 512
    np.random.seed(42)
    param_samples = saltelli.sample(PROBLEM_12, N=N, calc_second_order=False)
    num_evals = len(param_samples)
    print(f"Generated {num_evals} Saltelli samples (N={N}, D=12, calc_second_order=False).")

    t0 = time.time()
    results_dict = {}
    with ProcessPoolExecutor(max_workers=14) as executor:
        futures = [executor.submit(_worker_eval, (i, s)) for i, s in enumerate(param_samples)]
        completed = 0
        for fut in as_completed(futures):
            idx, res = fut.result()
            results_dict[idx] = res
            completed += 1
            if completed % 500 == 0 or completed == num_evals:
                el = time.time() - t0
                rate = completed / max(1e-6, el)
                rem = (num_evals - completed) / max(1e-6, rate)
                print(f"[{completed}/{num_evals}] ({completed/num_evals*100:.1f}%) "
                      f"speed={rate:.2f}/s est_remaining={rem/60.0:.1f}min")

    elapsed = time.time() - t0
    print(f"[DONE] {num_evals} evals in {elapsed:.1f}s ({elapsed/3600.0:.2f} h).")

    ordered = [results_dict[i] for i in range(num_evals)]
    res_df = pd.DataFrame(ordered)

    out_dir = os.path.join(PROJECT_ROOT, "outputs")
    os.makedirs(out_dir, exist_ok=True)
    res_df.to_csv(os.path.join(out_dir, "sobol_raw_evaluations.csv"), index=False)

    records = []
    for metric in METRICS:
        if res_df[metric].std() == 0.0:
            for i, name in enumerate(PROBLEM_12['names']):
                records.append({'metric': metric, 'parameter': name,
                                'S1': 0.0, 'S1_conf': 0.0, 'ST': 0.0, 'ST_conf': 0.0,
                                'degenerate': True})
            print(f"[skip] {metric}: constant across runs (degenerate)")
            continue
        si = sobol.analyze(PROBLEM_12, res_df[metric].values, calc_second_order=False,
                           print_to_console=False)
        for i, name in enumerate(PROBLEM_12['names']):
            records.append({'metric': metric, 'parameter': name,
                            'S1': float(si['S1'][i]), 'S1_conf': float(si['S1_conf'][i]),
                            'ST': float(si['ST'][i]), 'ST_conf': float(si['ST_conf'][i]),
                            'degenerate': False})

    sobol_df = pd.DataFrame(records)
    sobol_df.to_csv(os.path.join(out_dir, "sobol_results.csv"), index=False)
    print(f"Saved outputs/sobol_results.csv ({len(sobol_df)} rows).")


if __name__ == "__main__":
    run_sobol_analysis()
