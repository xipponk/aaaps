"""
analysis/verify_quartile_by_scenario.py — Verify whether the Q1 ability
cliff (deadline misses concentrated in the lowest-ability quartile) holds
across all five policy scenarios, using the seed=42 agent-level data
generated for F4 verification.
"""

from __future__ import annotations

import pandas as pd

SCENARIOS = ["baseline", "free_market", "universal_ai", "subsidy", "mixed_policy"]

rows = []
for scenario in SCENARIOS:
    df = pd.read_csv(f"outputs/raw/agent_data_{scenario}_seed42.csv")
    last = df[df["Step"] == df["Step"].max()].copy()

    # Quartile by base_ability (same approach as fig4_miss_by_quartile in plots.py)
    last["ability_quartile"] = pd.qcut(
        last["base_ability"], 4, labels=["Q1", "Q2", "Q3", "Q4"]
    )
    q_summary = last.groupby("ability_quartile", observed=True)["deadline_miss_count"].agg(["mean", "sum"])

    total_misses = last["deadline_miss_count"].sum()
    q1_share = (
        last[last["ability_quartile"] == "Q1"]["deadline_miss_count"].sum() / total_misses * 100
        if total_misses > 0 else float("nan")
    )

    row = {
        "scenario": scenario,
        "Q1_mean": q_summary.loc["Q1", "mean"] if "Q1" in q_summary.index else float("nan"),
        "Q2_mean": q_summary.loc["Q2", "mean"] if "Q2" in q_summary.index else float("nan"),
        "Q3_mean": q_summary.loc["Q3", "mean"] if "Q3" in q_summary.index else float("nan"),
        "Q4_mean": q_summary.loc["Q4", "mean"] if "Q4" in q_summary.index else float("nan"),
        "total_misses": total_misses,
        "Q1_pct_of_total": round(q1_share, 1),
    }
    rows.append(row)

result = pd.DataFrame(rows)
print(result.to_string(index=False))
result.to_csv("outputs/raw/quartile_by_scenario_seed42.csv", index=False)
print()
print("Saved: outputs/raw/quartile_by_scenario_seed42.csv")
