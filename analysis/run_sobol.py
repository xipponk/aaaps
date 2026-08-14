"""
analysis/run_sobol.py — Sobol Variance Decomposition (ODD §9 Stage 2).

Executes Sobol global sensitivity analysis across the 12 retained parameters from Morris screening
on free_market scenario (N=240, 960 steps, seed=42).
Calculates first-order (S1) and total-effect (ST) sensitivity indices.
Outputs results to outputs/sobol_results.csv.
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

# 12 Retained Parameters from Morris Screening
PROBLEM_12 = {
    'num_vars': 12,
    'names': [
        'ABILITY_MEAN',
        'URGENCY_WEIGHT',
        'PROCESSING_DIFFICULTY_FACTOR',
        'ALPHA_D',
        'RHO_AS',
        'DELTA_D',
        'P_VISIBLE',
        'ETA',
        'BORROW_SUBSTITUTION',
        'LAMBDA_A',
        'BETA_C',
        'ETA_SELF',
    ],
    'bounds': [
        [40.0, 60.0],     # ABILITY_MEAN
        [0.100, 0.500],   # URGENCY_WEIGHT
        [20.0, 40.0],     # PROCESSING_DIFFICULTY_FACTOR
        [0.008, 0.016],   # ALPHA_D
        [0.110, 0.550],   # RHO_AS
        [0.003, 0.008],   # DELTA_D
        [0.400, 0.900],   # P_VISIBLE
        [0.020, 0.200],   # ETA
        [0.300, 0.900],   # BORROW_SUBSTITUTION
        [0.005, 0.012],   # LAMBDA_A
        [0.006, 0.015],   # BETA_C
        [0.010, 0.100],   # ETA_SELF
    ]
}


def _worker_eval(idx_sample: tuple[int, np.ndarray]) -> tuple[int, dict[str, float]]:
    idx, param_values = idx_sample
    (
        ab_mean, urgency_w, proc_factor, alpha_d,
        rho_as, delta_d, p_visible, eta,
        borrow_sub, lambda_a, beta_c, eta_self
    ) = param_values

    # Apply parameter overrides
    P.ABILITY_MEAN = float(ab_mean)
    P.URGENCY_WEIGHT = float(urgency_w)
    P.PROCESSING_DIFFICULTY_FACTOR = float(proc_factor)
    P.ALPHA_D = float(alpha_d)
    P.RHO_AS = float(rho_as)
    P.DELTA_D = float(delta_d)
    P.P_VISIBLE = float(p_visible)
    P.ETA = float(eta)
    P.BORROW_SUBSTITUTION = float(borrow_sub)
    P.LAMBDA_A = float(lambda_a)
    P.BETA_C = float(beta_c)
    P.ETA_SELF = float(eta_self)

    model = run_free_market(seed=42, n_students=240)
    df = model.datacollector.get_agent_vars_dataframe().xs(960, level="Step")

    scores = df['score_total'].values
    n = len(scores)

    # Gini coefficient of score_total
    s_sorted = np.sort(scores)
    total = s_sorted.sum()
    if n == 0 or total == 0.0:
        gini = 0.0
    else:
        cumsum = np.cumsum(s_sorted)
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
    print("=================================================================")
    print("Stage 2: Sobol Variance Decomposition (12 Retained Parameters)")
    print("=================================================================\n")

    # Generate Saltelli Samples (N=512, calc_second_order=False) -> 512 * (12 + 2) = 7,168 runs
    N = 512
    np.random.seed(42)
    param_samples = saltelli.sample(PROBLEM_12, N=N, calc_second_order=False)
    num_evals = len(param_samples)
    print(f"Generated {num_evals} Saltelli parameter samples (N={N}, calc_second_order=False, D=12).")

    t0 = time.time()
    print("Executing ProcessPoolExecutor evaluation across 14 workers on ser6...")

    results_dict = {}
    with ProcessPoolExecutor(max_workers=14) as executor:
        futures = [executor.submit(_worker_eval, (i, sample)) for i, sample in enumerate(param_samples)]
        completed_count = 0
        for future in as_completed(futures):
            idx, res = future.result()
            results_dict[idx] = res
            completed_count += 1
            if completed_count % 500 == 0 or completed_count == num_evals:
                elapsed_soFar = time.time() - t0
                rate = completed_count / max(1e-6, elapsed_soFar)
                remaining = (num_evals - completed_count) / max(1e-6, rate)
                print(f"[{completed_count}/{num_evals}] runs finished ({completed_count/num_evals*100:.1f}%) | "
                      f"Speed: {rate:.2f} runs/s | Est. remaining: {remaining/60.0:.1f} mins")

    elapsed = time.time() - t0
    print(f"\n[COMPLETED] Total evaluation time: {elapsed:.2f} seconds ({elapsed/3600.0:.2f} hours).")

    # Ordered results DataFrame
    ordered_results = [results_dict[i] for i in range(num_evals)]
    res_df = pd.DataFrame(ordered_results)
    
    # Save raw evaluations
    out_dir = os.path.join(PROJECT_ROOT, "outputs")
    os.makedirs(out_dir, exist_ok=True)
    res_df.to_csv(os.path.join(out_dir, "sobol_raw_evaluations.csv"), index=False)

    # Sobol Analysis
    sobol_records = []
    for metric in res_df.columns:
        Y = res_df[metric].values
        si = sobol.analyze(PROBLEM_12, Y, calc_second_order=False, print_to_console=False)
        for i, var_name in enumerate(PROBLEM_12['names']):
            sobol_records.append({
                'metric': metric,
                'parameter': var_name,
                'S1': float(si['S1'][i]),
                'S1_conf': float(si['S1_conf'][i]),
                'ST': float(si['ST'][i]),
                'ST_conf': float(si['ST_conf'][i]),
            })

    sobol_df = pd.DataFrame(sobol_records)
    out_path = os.path.join(out_dir, "sobol_results.csv")
    sobol_df.to_csv(out_path, index=False)
    print(f"Saved Sobol GSA results to: {out_path}")


if __name__ == "__main__":
    run_sobol_analysis()
