#!/usr/bin/env python3
"""
run_batch.py — Sensitivity Analysis Entry Point for AAAPS (SER6).

Grid-sweeps three key parameters (ALPHA, PROCESSING_DIFFICULTY_FACTOR, and
TIER_BUDGET_FRACTION scale) across all five scenarios with multiple random
seeds, then saves the resulting metrics as a CSV for downstream analysis.

Designed for a Ryzen 9 / 64 GB Ubuntu machine via joblib parallel execution.

Usage
-----
    python run_batch.py                          # full grid (4,050 runs)
    python run_batch.py --dry-run                # print job count, exit
    python run_batch.py --n-seeds 2 --n-jobs 4   # quick smoke test
    python run_batch.py --scenarios baseline,free_market  # subset of scenarios
"""

from __future__ import annotations

import argparse
import itertools
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.stats import kurtosis, skew

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------

from config.params import TOTAL_STEPS
from model.model import AaapsModel

# ---------------------------------------------------------------------------
# Sensitivity grid constants
# ---------------------------------------------------------------------------

ALPHA_VALUES: list[float] = [0.005, 0.008, 0.012]
PROC_FACTOR_VALUES: list[float] = [20.0, 30.0, 40.0]
TBF_SCALE_VALUES: list[float] = [0.8, 1.0, 1.2]

ALL_SCENARIOS: list[str] = [
    "baseline",
    "free_market",
    "universal_ai",
    "subsidy",
    "mixed_policy",
]

# ---------------------------------------------------------------------------
# Helper: Gini coefficient (standalone, mirrors model.compute_gini)
# ---------------------------------------------------------------------------


def _gini(scores: np.ndarray) -> float:
    """Gini coefficient of a 1-D array of non-negative values."""
    n = len(scores)
    total = scores.sum()
    if n == 0 or total == 0.0:
        return 0.0
    sorted_scores = np.sort(scores)
    cumsum = np.sum((np.arange(1, n + 1) * sorted_scores))
    return (2.0 * cumsum) / (n * total) - (n + 1.0) / n


# ---------------------------------------------------------------------------
# Single-run function (called by joblib)
# ---------------------------------------------------------------------------


def run_one(config: dict) -> dict | None:
    """Execute one simulation run and return a flat dict of output metrics.

    Parameters
    ----------
    config : dict
        Must contain keys: ``alpha``, ``proc_factor``, ``tbf_scale``,
        ``seed``, ``scenario``.

    Returns
    -------
    dict or None
        Flat metrics dict on success; ``None`` if the run raised an
        exception (so the batch can filter out failed runs).
    """
    try:
        # ---- Instantiate model with overrides ----
        model = AaapsModel(
            scenario=config["scenario"],
            seed=config["seed"],
            alpha_override=config["alpha"],
            proc_factor_override=config["proc_factor"],
            tbf_scale_override=config["tbf_scale"],
        )

        # ---- Run full simulation ----
        for _step in range(TOTAL_STEPS):
            model.step()

        # ---- Extract agent-level metrics ----
        score_totals = np.array([a.score_total for a in model.agents])
        dependencies = np.array([a.ai_dependency for a in model.agents])

        mean_score = float(np.mean(score_totals))
        std_score = float(np.std(score_totals))

        # Skewness / kurtosis: guard against degenerate distributions
        score_skew = float(skew(score_totals)) if std_score > 1e-9 else 0.0
        score_kurt = float(kurtosis(score_totals)) if std_score > 1e-9 else 0.0

        gini_coeff = _gini(score_totals)

        ai_adoption_rate = (
            sum(1 for a in model.agents if a.ai_tier > 0) / model.n_students
        )
        mean_dependency = float(np.mean(dependencies))

        total_misses = sum(a.deadline_miss_count for a in model.agents)
        miss_rate = total_misses / max(model.total_tasks_generated, 1)

        # ---- Return flat result dict ----
        return {
            "alpha": config["alpha"],
            "proc_factor": config["proc_factor"],
            "tbf_scale": config["tbf_scale"],
            "seed": config["seed"],
            "scenario": config["scenario"],
            "mean_score": mean_score,
            "std_score": std_score,
            "skewness": score_skew,
            "kurtosis": score_kurt,
            "gini": gini_coeff,
            "ai_adoption_rate": ai_adoption_rate,
            "mean_dependency": mean_dependency,
            "deadline_miss_count": total_misses,
            "deadline_miss_rate": miss_rate,
            "quota_bankruptcies": model.quota_bankruptcy_count,
        }

    except Exception:
        # Let joblib keep going — a single failed run shouldn't kill the batch.
        # The caller filters None entries before saving.
        return None


# ---------------------------------------------------------------------------
# Job-list builder
# ---------------------------------------------------------------------------


def build_job_list(
    seeds: list[int],
    scenarios: list[str],
    alphas: list[float],
    proc_factors: list[float],
    tbf_scales: list[float],
) -> list[dict]:
    """Cartesian product of (alpha, proc_factor, tbf_scale, seed, scenario)."""
    job_list: list[dict] = []
    for alpha, pf, tbf, seed, scenario in itertools.product(
        alphas, proc_factors, tbf_scales, seeds, scenarios
    ):
        job_list.append(
            {
                "alpha": alpha,
                "proc_factor": pf,
                "tbf_scale": tbf,
                "seed": seed,
                "scenario": scenario,
            }
        )
    return job_list


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="AAAPS Sensitivity Analysis Batch Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  %(prog)s --dry-run\n"
            "  %(prog)s --n-seeds 2 --scenarios baseline,free_market --n-jobs 4\n"
            "  %(prog)s --n-seeds 30  # full 4,050-run grid\n"
        ),
    )
    parser.add_argument(
        "--n-seeds",
        type=int,
        default=30,
        help="Number of random seeds (default: 30).  Use a small value for "
        "quick smoke tests.",
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=-1,
        help="Number of parallel jobs for joblib (default: -1 = all cores).",
    )
    parser.add_argument(
        "--scenarios",
        type=str,
        default=None,
        help="Comma-separated list of scenarios to run (default: all 5).  "
        "Valid: baseline, free_market, universal_ai, subsidy, mixed_policy.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print job count and exit without running simulations.",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    args = parse_args()

    # ---- Seeds ----
    seeds = list(range(args.n_seeds))

    # ---- Scenarios ----
    if args.scenarios is not None:
        scenarios = [s.strip() for s in args.scenarios.split(",")]
        # Validate
        valid = set(ALL_SCENARIOS)
        for s in scenarios:
            if s not in valid:
                print(f"❌ Unknown scenario: '{s}'.  Valid: {sorted(valid)}")
                sys.exit(1)
    else:
        scenarios = list(ALL_SCENARIOS)

    # ---- Build job list ----
    job_list = build_job_list(
        seeds=seeds,
        scenarios=scenarios,
        alphas=ALPHA_VALUES,
        proc_factors=PROC_FACTOR_VALUES,
        tbf_scales=TBF_SCALE_VALUES,
    )

    total_jobs = len(job_list)
    print(f"🔬 Sensitivity grid: {len(ALPHA_VALUES)} α × "
          f"{len(PROC_FACTOR_VALUES)} PF × {len(TBF_SCALE_VALUES)} TBF × "
          f"{len(seeds)} seeds × {len(scenarios)} scenarios = {total_jobs} runs")

    if args.dry_run:
        print(f"✅ Dry run complete.")
        return

    # ---- Output directory ----
    out_dir = Path("outputs/raw")
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- Run in parallel ----
    t_start = time.perf_counter()

    results = Parallel(n_jobs=args.n_jobs, verbose=10)(
        delayed(run_one)(cfg) for cfg in job_list
    )

    # ---- Filter failed runs ----
    valid_results = [r for r in results if r is not None]
    n_failed = len(results) - len(valid_results)
    if n_failed > 0:
        print(f"⚠️  {n_failed} run(s) failed and were dropped.")

    # ---- Save ----
    df = pd.DataFrame(valid_results)
    out_path = out_dir / "sensitivity_results.csv"
    df.to_csv(out_path, index=False)

    elapsed = time.perf_counter() - t_start

    # ---- Summary ----
    print()
    print("✅ Sensitivity analysis complete.")
    print(f"   Total runs: {total_jobs}")
    print(f"   Successful: {len(valid_results)}")
    if n_failed:
        print(f"   Failed:     {n_failed}")
    print(f"   Output:     {out_path.resolve()}")
    print(f"   Elapsed:    {elapsed:.1f} seconds")


if __name__ == "__main__":
    main()
