"""
analysis/verify_f4.py — Verify F4 (SES Stratification) numbers for the
manuscript: per-scenario Gini, mean score, deadline misses, and AI-tier
distribution by socioeconomic status, all at seed=42 for direct
apples-to-apples comparison across scenarios.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SCENARIOS = ["baseline", "free_market", "universal_ai", "subsidy", "mixed_policy"]


def compute_gini(scores: np.ndarray) -> float:
    """Same formula as model.model.compute_gini."""
    scores = np.sort(np.asarray(scores, dtype=float))
    n = len(scores)
    total = scores.sum()
    if n == 0 or total == 0.0:
        return 0.0
    cumsum = np.sum((np.arange(1, n + 1)) * scores)
    return (2.0 * cumsum) / (n * total) - (n + 1.0) / n


rows = []
for scenario in SCENARIOS:
    df = pd.read_csv(f"outputs/raw/agent_data_{scenario}_seed42.csv")
    last = df[df["Step"] == df["Step"].max()]

    gini = compute_gini(last["score_total"].values)
    mean_score = last["score_total"].mean()
    mean_miss = last["deadline_miss_count"].mean()

    # AI tier by SES
    tier_means = last.groupby("SES")["ai_tier"].mean()
    pct_low_tier2plus = (
        (last[last["SES"] == "low"]["ai_tier"] >= 2).mean() * 100
        if "low" in last["SES"].values else float("nan")
    )
    pct_high_tier3 = (
        (last[last["SES"] == "high"]["ai_tier"] == 3).mean() * 100
        if "high" in last["SES"].values else float("nan")
    )

    rows.append({
        "scenario": scenario,
        "gini": round(gini, 4),
        "mean_score": round(mean_score, 1),
        "mean_deadline_misses": round(mean_miss, 2),
        "low_SES_mean_tier": round(tier_means.get("low", float("nan")), 2),
        "mid_SES_mean_tier": round(tier_means.get("mid", float("nan")), 2),
        "high_SES_mean_tier": round(tier_means.get("high", float("nan")), 2),
        "pct_low_SES_tier2plus": round(pct_low_tier2plus, 1),
        "pct_high_SES_tier3": round(pct_high_tier3, 1),
    })

result = pd.DataFrame(rows)
print(result.to_string(index=False))
result.to_csv("outputs/raw/f4_verification_seed42.csv", index=False)
print()
print("Saved: outputs/raw/f4_verification_seed42.csv")
