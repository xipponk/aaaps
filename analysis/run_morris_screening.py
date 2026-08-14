"""
analysis/run_morris_screening.py — Morris Elementary Effects Screening (ODD §9 Stage 1).

Runs Morris screening across ALL 23 candidate parameters (Group A-D) on the free_market
scenario, tracking all 12 output metrics. Produces a composite ranking (max across
per-metric normalized mu_star) so a parameter influential on ANY metric is retained.

Uses the fixed parameter-binding codebase (``from config import params as P``) and the
12-metric evaluation identical to run_sobol.py.
"""

from __future__ import annotations

import os
import sys
import time
import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
from SALib.sample import morris as morris_sample
from SALib.analyze import morris as morris_analyze

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scenarios.free_market import run as run_free_market
import config.params as P

# 23 candidate parameters
PROBLEM = {
    'num_vars': 23,
    'names': [
        'ALPHA_D', 'DELTA_D', 'BETA_C', 'GAMMA_C', 'RHO_AS', 'LAMBDA_A',
        'ETA', 'ETA_SELF', 'KAPPA', 'URGENCY_WEIGHT', 'ASPIRATION_GAP_WEIGHT',
        'BORROW_SUBSTITUTION', 'ABILITY_MEAN', 'ABILITY_STD', 'CONFORMITY_BETA_B',
        'PROSOCIALITY_BETA_A', 'SBM_P_WITHIN', 'SBM_P_BETWEEN', 'HOMOPHILY_SES',
        'HOMOPHILY_ABILITY', 'P_VISIBLE', 'SHAREABLE_SEATS_TIER3', 'PROCESSING_DIFFICULTY_FACTOR'
    ],
    'bounds': [
        [0.008, 0.016],   # ALPHA_D
        [0.003, 0.008],   # DELTA_D
        [0.006, 0.015],   # BETA_C
        [0.030, 0.070],   # GAMMA_C
        [0.110, 0.550],   # RHO_AS
        [0.005, 0.012],   # LAMBDA_A
        [0.020, 0.200],   # ETA
        [0.010, 0.100],   # ETA_SELF
        [0.020, 0.250],   # KAPPA
        [0.100, 0.500],   # URGENCY_WEIGHT
        [0.050, 0.400],   # ASPIRATION_GAP_WEIGHT
        [0.300, 0.900],   # BORROW_SUBSTITUTION
        [40.0, 60.0],     # ABILITY_MEAN
        [10.0, 20.0],     # ABILITY_STD
        [2.0, 8.0],       # CONFORMITY_BETA_B
        [1.0, 5.0],       # PROSOCIALITY_BETA_A
        [0.120, 0.250],   # SBM_P_WITHIN
        [0.005, 0.030],   # SBM_P_BETWEEN
        [0.100, 0.350],   # HOMOPHILY_SES
        [0.150, 0.400],   # HOMOPHILY_ABILITY
        [0.400, 0.900],   # P_VISIBLE
        [1.0, 4.0],       # SHAREABLE_SEATS_TIER3
        [20.0, 40.0],     # PROCESSING_DIFFICULTY_FACTOR
    ]
}

# 12 output metrics (identical set to run_sobol.py)
METRICS = [
    'mean_score', 'std_score', 'gini_score', 'mean_dependency',
    'mean_calibration_error', 'mean_retained_ability', 'deadline_miss_count',
    'deadline_miss_rate', 'ai_adoption_rate', 'mean_legitimacy',
    'borrowing_agent_count', 'total_shared_seats_lent',
]


def _worker_eval(idx_sample: tuple[int, np.ndarray]) -> tuple[int, dict[str, float]]:
    idx, param_values = idx_sample
    (
        alpha_d, delta_d, beta_c, gamma_c, rho_as, lambda_a,
        eta, eta_self, kappa, urgency_w, asp_gap_w,
        borrow_sub, ab_mean, ab_std, conf_beta_b,
        prosocial_beta_a, p_within, p_between, h_ses,
        h_ability, p_visible, share_seats_t3, proc_factor
    ) = param_values

    P.ALPHA_D = float(alpha_d)
    P.DELTA_D = float(delta_d)
    P.BETA_C = float(beta_c)
    P.GAMMA_C = float(gamma_c)
    P.RHO_AS = float(rho_as)
    P.LAMBDA_A = float(lambda_a)
    P.ETA = float(eta)
    P.ETA_SELF = float(eta_self)
    P.KAPPA = float(kappa)
    P.URGENCY_WEIGHT = float(urgency_w)
    P.ASPIRATION_GAP_WEIGHT = float(asp_gap_w)
    P.BORROW_SUBSTITUTION = float(borrow_sub)
    P.ABILITY_MEAN = float(ab_mean)
    P.ABILITY_STD = float(ab_std)
    P.CONFORMITY_BETA_B = float(conf_beta_b)
    P.PROSOCIALITY_BETA_A = float(prosocial_beta_a)
    P.SBM_P_WITHIN = float(p_within)
    P.SBM_P_BETWEEN = float(p_between)
    P.HOMOPHILY_SES = float(h_ses)
    P.HOMOPHILY_ABILITY = float(h_ability)
    P.P_VISIBLE = float(p_visible)
    P.SHAREABLE_SEATS[3] = int(round(share_seats_t3))
    P.PROCESSING_DIFFICULTY_FACTOR = float(proc_factor)

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


def run_morris():
    print("=" * 79)
    print("Morris Screening (23 params, 12 metrics, fixed codebase)")
    print("=" * 79)

    r = 20
    param_samples = morris_sample.sample(PROBLEM, N=r, num_levels=4, seed=42)
    num_evals = len(param_samples)
    print(f"Generated {num_evals} samples (r={r}, D={PROBLEM['num_vars']}).")

    t0 = time.time()
    results_dict = {}
    with ProcessPoolExecutor(max_workers=14) as executor:
        futures = [executor.submit(_worker_eval, (i, s)) for i, s in enumerate(param_samples)]
        for fut in as_completed(futures):
            idx, res = fut.result()
            results_dict[idx] = res

    elapsed = time.time() - t0
    print(f"[DONE] {num_evals} evals in {elapsed:.1f}s ({elapsed/60.0:.1f} min).")

    ordered = [results_dict[i] for i in range(num_evals)]
    res_df = pd.DataFrame(ordered)

    # Morris analysis per metric
    analysis = {}
    for metric in METRICS:
        if res_df[metric].std() == 0.0:
            # Degenerate metric: no variance -> zero elementary effects
            analysis[metric] = {'mu_star': np.zeros(PROBLEM['num_vars'])}
            continue
        si = morris_analyze.analyze(PROBLEM, param_samples, res_df[metric].values,
                                    print_to_console=False)
        analysis[metric] = {'mu_star': np.array(si['mu_star']), 'sigma': np.array(si['sigma'])}

    # Build full results table
    records = []
    for i, name in enumerate(PROBLEM['names']):
        rec = {'parameter': name}
        for metric in METRICS:
            rec[f"{metric}_mu_star"] = float(analysis[metric]['mu_star'][i])
            if 'sigma' in analysis[metric]:
                rec[f"{metric}_sigma"] = float(analysis[metric]['sigma'][i])
        records.append(rec)
    morris_df = pd.DataFrame(records)

    out_dir = os.path.join(PROJECT_ROOT, "outputs")
    os.makedirs(out_dir, exist_ok=True)
    morris_df.to_csv(os.path.join(out_dir, "morris_results.csv"), index=False)

    # Composite ranking: normalize mu_star per metric column by its max, take max across metrics
    norm = morris_df[[f"{m}_mu_star" for m in METRICS]].copy()
    for m in METRICS:
        col = f"{m}_mu_star"
        mx = norm[col].abs().max()
        if mx > 0:
            norm[col] = norm[col].abs() / mx
    morris_df['composite_max'] = norm.max(axis=1)
    morris_df = morris_df.sort_values('composite_max', ascending=False).reset_index(drop=True)

    print("\n=== Composite Ranking (max normalized mu_star across 12 metrics) ===")
    print(morris_df[['parameter', 'composite_max']].to_string(index=False))

    morris_df.to_csv(os.path.join(out_dir, "morris_results_ranked.csv"), index=False)
    print(f"\nSaved: outputs/morris_results.csv and outputs/morris_results_ranked.csv")


if __name__ == "__main__":
    run_morris()
