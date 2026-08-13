"""
test_zero_interaction.py — ODD §8 Zero-Interaction Baseline Verification.

Part A: Compares v0.3 zero-interaction mode (N=60, seed=42) against the
        pre-redesign v0.2 free_market ground truth dataset
        (~/projects/aaaps_main_free_market_seed42_GROUNDTRUTH.csv) for score_total
        and deadline_miss_count.

Part B: Compares v0.3 zero-interaction mode vs. v0.3 full-network mode (N=240, seed=42)
        for continuous coupled state variables (ai_dependency, calibration_error,
        retained_ability).
"""

from __future__ import annotations

import os
import sys
import pandas as pd
import numpy as np
from scipy import stats

from scenarios.free_market import run as run_free_market


def run_verification_suite() -> None:
    print("=================================================================")
    print("AAAPS v0.3 Verification Suite (ODD §8)")
    print("=================================================================\n")

    # -------------------------------------------------------------------------
    # PART A: v0.3 Zero-Interaction vs. v0.2 Ground Truth
    # -------------------------------------------------------------------------
    print("--- PART A: Zero-Interaction v0.3 vs. v0.2 Ground Truth Baseline ---")
    ground_truth_path = "/home/tuul/projects/aaaps_main_free_market_seed42_GROUNDTRUTH.csv"
    
    if not os.path.exists(ground_truth_path):
        print(f"[ERROR] Ground truth file not found at {ground_truth_path}!")
        return

    df_v02 = pd.read_csv(ground_truth_path)
    final_step = df_v02['Step'].max()
    df_v02_final = df_v02[df_v02['Step'] == final_step]
    
    print(f"LOADED GROUND TRUTH FILE: {ground_truth_path}")
    print(f"Shape: {df_v02_final.shape} (Step {final_step}, N={len(df_v02_final)})\n")

    print("Running v0.3 zero-interaction simulation (N=60, seed=42, 960 steps)...")
    model_v03_zero_60 = run_free_market(seed=42, n_students=60, zero_interaction_mode=True)

    v03_df = model_v03_zero_60.datacollector.get_agent_vars_dataframe()
    v03_final = v03_df.xs(960, level="Step") if "Step" in v03_df.index.names else v03_df.tail(60)

    v03_scores = v03_final['score_total'].values
    v03_misses = v03_final['deadline_miss_count'].values

    v02_scores = df_v02_final['score_total'].values
    v02_misses = df_v02_final['deadline_miss_count'].values

    print("\n--- Part A Statistical Metrics ---")
    print("1. score_total:")
    print(f"   v0.2 ground truth mean={np.mean(v02_scores):.2f}, std={np.std(v02_scores):.2f}")
    print(f"   v0.3 zero-int    mean={np.mean(v03_scores):.2f}, std={np.std(v03_scores):.2f}")

    print("\n2. deadline_miss_count:")
    print(f"   v0.2 ground truth mean={np.mean(v02_misses):.2f}, std={np.std(v02_misses):.2f}")
    print(f"   v0.3 zero-int    mean={np.mean(v03_misses):.2f}, std={np.std(v03_misses):.2f}")

    # -------------------------------------------------------------------------
    # PART B: v0.3 Zero-Interaction vs. v0.3 Full-Network (N=240, seed=42)
    # -------------------------------------------------------------------------
    print("\n\n--- PART B: v0.3 Zero-Interaction vs. v0.3 Full-Network Mode ---")
    print("Running v0.3 full-network simulation (N=240, seed=42, 960 steps)...")
    model_v03_net = run_free_market(seed=42, n_students=240, zero_interaction_mode=False)

    print("Running v0.3 zero-interaction simulation (N=240, seed=42, 960 steps)...")
    model_v03_zero_240 = run_free_market(seed=42, n_students=240, zero_interaction_mode=True)

    df_net = model_v03_net.datacollector.get_agent_vars_dataframe().xs(960, level="Step")
    df_zero = model_v03_zero_240.datacollector.get_agent_vars_dataframe().xs(960, level="Step")

    print("\n--- Part B Network Effects on Continuous State Variables ---")
    for var in ["ai_dependency", "calibration_error", "retained_ability"]:
        val_net = df_net[var].values
        val_zero = df_zero[var].values
        ks = stats.ks_2samp(val_net, val_zero)
        print(f"\nMetric: {var}")
        print(f"   Zero-Interaction Mean={np.mean(val_zero):.4f}, Std={np.std(val_zero):.4f}")
        print(f"   Full-Network     Mean={np.mean(val_net):.4f}, Std={np.std(val_net):.4f}")
        print(f"   KS statistic={ks.statistic:.4f}, p-value={ks.pvalue:.4f}")


if __name__ == "__main__":
    run_verification_suite()
