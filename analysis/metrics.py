"""
analysis/metrics.py — Statistical metrics for sensitivity analysis results.

Pure pandas + scipy + numpy.  No Mesa imports.
All functions accept a pandas DataFrame loaded from
``outputs/raw/sensitivity_results.csv`` and return scalars, tuples,
or DataFrames.

Follows CLAUDE.md sections:
  - Data Collection
  - Testing Expectations
  - Key Findings (Emergent Results)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

# =============================================================================
# Baseline reference values (for sensitivity_rank)
# =============================================================================

BASELINE_PARAMS: dict[str, float] = {
    "alpha": 0.008,
    "proc_factor": 30.0,
    "tbf_scale": 1.0,
}

# Column name mapping — the CSV may use slightly different names.
# This dict maps our canonical names to likely CSV column names.
_COL_ALIASES: dict[str, list[str]] = {
    "mean_score": ["mean_score"],
    "gini": ["gini"],
    "deadline_miss_rate": ["deadline_miss_rate"],
    "ai_dependency": ["mean_dependency"],
    "ai_adoption_rate": ["ai_adoption_rate"],
    "n_runs": ["n_runs"],
}


def _resolve_column(df: pd.DataFrame, canonical: str) -> str:
    """Return the first matching column name in *df* for *canonical*."""
    for candidate in _COL_ALIASES.get(canonical, [canonical]):
        if candidate in df.columns:
            return candidate
    # Fallback: try the canonical name directly (may raise later)
    return canonical


# =============================================================================
# Individual metric functions
# =============================================================================


def compute_gini(scores: np.ndarray) -> float:
    """Gini coefficient from array of scores.

    Returns 0.0 if the array is empty or all values are zero.
    Uses the same formula as ``model.model.compute_gini``.
    """
    scores = np.asarray(scores, dtype=float)
    if len(scores) == 0:
        return 0.0

    sorted_scores = np.sort(scores)
    total = sorted_scores.sum()
    if total == 0.0:
        return 0.0

    n = len(sorted_scores)
    # Σ (i+1) * s_i  where i is 0-indexed
    cumsum = np.sum((np.arange(1, n + 1)) * sorted_scores)
    return (2.0 * cumsum) / (n * total) - (n + 1.0) / n


def skewness(scores: np.ndarray) -> float:
    """Pearson skewness via :func:`scipy.stats.skew`.

    Positive skew = right tail; negative = left tail.
    """
    scores_arr = np.asarray(scores, dtype=float)
    if len(scores_arr) < 3:
        return np.nan
    return float(stats.skew(scores_arr))


def excess_kurtosis(scores: np.ndarray) -> float:
    """Excess kurtosis via :func:`scipy.stats.kurtosis` (``fisher=True``).

    Normal distribution → 0.  Leptokurtic (heavy-tailed) → > 0.
    """
    scores_arr = np.asarray(scores, dtype=float)
    if len(scores_arr) < 4:
        return np.nan
    return float(stats.kurtosis(scores_arr, fisher=True))


def ks_test_normality(scores: np.ndarray) -> tuple[float, float]:
    """Kolmogorov-Smirnov test against a normal distribution.

    Standardises *scores* to z-scores first, then runs
    :func:`scipy.stats.kstest` against ``'norm'``.

    Returns
    -------
    (statistic, p_value) : tuple[float, float]
    """
    scores_arr = np.asarray(scores, dtype=float)
    if len(scores_arr) < 3:
        return (np.nan, np.nan)

    # Standardise to z-scores
    mean = scores_arr.mean()
    std = scores_arr.std(ddof=1)
    if std == 0.0:
        # All values identical — degenerate distribution
        return (1.0, 0.0)
    z_scores = (scores_arr - mean) / std

    result = stats.kstest(z_scores, "norm")
    return (float(result.statistic), float(result.pvalue))


def achievement_gap(scores: np.ndarray) -> float:
    """Mean score of top quartile (Q4) minus mean score of bottom quartile (Q1).

    Higher values indicate a wider achievement gap.
    """
    scores_arr = np.asarray(scores, dtype=float)
    if len(scores_arr) < 4:
        return np.nan

    sorted_scores = np.sort(scores_arr)
    n = len(sorted_scores)
    # Quartile boundaries (0-indexed)
    q1_end = n // 4
    q4_start = n - q1_end

    q1_scores = sorted_scores[:q1_end]
    q4_scores = sorted_scores[q4_start:]

    return float(q4_scores.mean() - q1_scores.mean())


# =============================================================================
# Aggregate / summary functions
# =============================================================================


def summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-combination aggregate statistics across seeds.

    Groups by ``['scenario', 'alpha', 'proc_factor', 'tbf_scale']``
    and aggregates all seeds, producing mean and std for each metric.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain at least the group-by columns plus per-run metric
        columns (``mean_score``, ``gini``, ``deadline_miss_rate``,
        ``mean_dependency``, ``ai_adoption_rate``, and a ``seed`` column).

    Returns
    -------
    pd.DataFrame
        With columns:
        * scenario, alpha, proc_factor, tbf_scale
        * mean_score_mean, mean_score_std
        * gini_mean, gini_std
        * miss_rate_mean, miss_rate_std
        * dependency_mean, dependency_std
        * adoption_mean, adoption_std
        * n_runs  (number of seeds aggregated per combo)
    """
    group_cols = ["scenario", "alpha", "proc_factor", "tbf_scale"]

    # Resolve column names
    mscore_col = _resolve_column(df, "mean_score")
    gini_col = _resolve_column(df, "gini")
    miss_col = _resolve_column(df, "deadline_miss_rate")
    dep_col = _resolve_column(df, "ai_dependency")
    adopt_col = _resolve_column(df, "ai_adoption_rate")

    # Build aggregation dict
    agg_dict: dict[str, list[str]] = {
        mscore_col: ["mean", "std"],
        gini_col: ["mean", "std"],
        miss_col: ["mean", "std"],
        dep_col: ["mean", "std"],
        adopt_col: ["mean", "std"],
        "seed": "count",  # n_runs
    }

    grouped = df.groupby(group_cols, dropna=True).agg(agg_dict)

    # Flatten multi-level columns
    grouped.columns = [
        f"{col[0]}_{col[1]}".replace(mscore_col, "mean_score")
        .replace(gini_col, "gini")
        .replace(miss_col, "miss_rate")
        .replace(dep_col, "dependency")
        .replace(adopt_col, "adoption")
        .replace("seed_count", "n_runs")
        for col in grouped.columns
    ]

    result = grouped.reset_index()
    result["n_runs"] = result["n_runs"].astype(int)
    return result


def robustness_check(df: pd.DataFrame, metric: str = "gini") -> pd.DataFrame:
    """Compute coefficient of variation (std / mean) per parameter combo.

    Low CV → the finding is robust across seeds.

    Parameters
    ----------
    df : pd.DataFrame
        Raw sensitivity results (one row per seed per combo).
    metric : str
        Which metric column to evaluate (default ``"gini"``).

    Returns
    -------
    pd.DataFrame
        Grouped by ``[scenario, alpha, proc_factor, tbf_scale]`` with
        columns ``cv`` (coefficient of variation) and ``n_runs``,
        sorted by ``cv`` **descending** (least robust first).
    """
    group_cols = ["scenario", "alpha", "proc_factor", "tbf_scale"]
    metric_col = _resolve_column(df, metric)

    grouped = (
        df.groupby(group_cols, dropna=True)
        .agg(
            mean=(metric_col, "mean"),
            std=(metric_col, "std"),
            n_runs=("seed", "count"),
        )
        .reset_index()
    )

    # Avoid division by zero
    grouped["cv"] = grouped["std"] / grouped["mean"].replace(0.0, np.nan)
    grouped["cv"] = grouped["cv"].fillna(0.0)

    return grouped.sort_values("cv", ascending=False).reset_index(drop=True)


def sensitivity_rank(
    df: pd.DataFrame,
    metric: str = "deadline_miss_rate",
) -> pd.DataFrame:
    """One-way sensitivity: rank parameters by their impact on *metric*.

    For each parameter (``alpha``, ``proc_factor``, ``tbf_scale``),
    vary that parameter while holding the other two at their baseline
    values (defined in :data:`BASELINE_PARAMS`).  Computes the range
    ``max(metric_mean) - min(metric_mean)`` across the parameter's
    values (typically 3 each).

    Parameters
    ----------
    df : pd.DataFrame
        Raw sensitivity results (one row per seed per combo).
    metric : str
        Which metric column to rank by (default ``"deadline_miss_rate"``).

    Returns
    -------
    pd.DataFrame
        With columns ``parameter``, ``range``, ``min_val``, ``max_val``,
        sorted by ``range`` **descending** (tornado-chart input).
    """
    metric_col = _resolve_column(df, metric)

    # Pre-compute per-combo metric mean
    group_cols = ["scenario", "alpha", "proc_factor", "tbf_scale"]
    combo_means = df.groupby(group_cols, dropna=True)[metric_col].mean().reset_index()
    combo_means = combo_means.rename(columns={metric_col: "metric_mean"})

    params_to_test = ["alpha", "proc_factor", "tbf_scale"]
    results: list[dict[str, object]] = []

    for param in params_to_test:
        # Build filter: hold the other two at baseline
        other_params = [p for p in params_to_test if p != param]
        mask = pd.Series(True, index=combo_means.index)
        for other in other_params:
            if other in combo_means.columns:
                mask &= np.isclose(
                    combo_means[other].astype(float),
                    float(BASELINE_PARAMS[other]),
                )

        subset = combo_means[mask]
        if subset.empty:
            continue

        # Average across scenarios to isolate this parameter's effect,
        # then compute range across parameter values
        param_means = subset.groupby(param)["metric_mean"].mean()
        vals = param_means
        param_range = float(vals.max() - vals.min())
        results.append(
            {
                "parameter": param,
                "range": param_range,
                "min_val": float(vals.min()),
                "max_val": float(vals.max()),
            }
        )

    # --- Debug: show pivot of mean metric per parameter value ---
    print(f"\n[DEBUG sensitivity_rank] metric={metric}")
    pivot_rows: list[dict[str, object]] = []
    for param in params_to_test:
        other_params = [p for p in params_to_test if p != param]
        mask = pd.Series(True, index=combo_means.index)
        for other in other_params:
            if other in combo_means.columns:
                mask &= np.isclose(
                    combo_means[other].astype(float),
                    float(BASELINE_PARAMS[other]),
                )
        subset = combo_means[mask]
        if subset.empty:
            continue
        param_means = subset.groupby(param)["metric_mean"].mean()
        for val, m in param_means.items():
            pivot_rows.append({"parameter": param, "value": val, "metric_mean": m})
    pivot_df = pd.DataFrame(pivot_rows)
    print(pivot_df.to_string(index=False))
    print()

    result_df = pd.DataFrame(results)
    if result_df.empty:
        return result_df
    return result_df.sort_values("range", ascending=False).reset_index(drop=True)


# =============================================================================
# Smoke test (run with ``python analysis/metrics.py``)
# =============================================================================

if __name__ == "__main__":
    import os
    import sys

    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "outputs", "raw", "sensitivity_results.csv",
    )

    if not os.path.exists(csv_path):
        print(f"[metrics.py] File not found: {csv_path}")
        print("Skipping smoke test — run a sensitivity batch first.\n")
        print("Example: python run_batch.py sensitivity")
        sys.exit(0)

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows from {csv_path}\n")

    # ----- Summary stats -----
    print("=" * 72)
    print("summary_stats() — first 10 rows")
    print("=" * 72)
    summ = summary_stats(df)
    print(summ.head(10).to_string(index=False))
    print()

    # ----- Sensitivity rank: deadline_miss_rate -----
    print("=" * 72)
    print("sensitivity_rank(metric='deadline_miss_rate')")
    print("=" * 72)
    rank_miss = sensitivity_rank(df, metric="deadline_miss_rate")
    print(rank_miss.to_string(index=False))
    print()

    # ----- Sensitivity rank: gini -----
    print("=" * 72)
    print("sensitivity_rank(metric='gini')")
    print("=" * 72)
    rank_gini = sensitivity_rank(df, metric="gini")
    print(rank_gini.to_string(index=False))
    print()

    print("[metrics.py] Smoke test complete.")
