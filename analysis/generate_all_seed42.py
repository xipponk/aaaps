"""
analysis/generate_all_seed42.py — Generate agent-level seed=42 data for
all five scenarios, for direct cross-scenario comparison (used to verify
the F4 SES stratification finding for the manuscript).
"""

from __future__ import annotations

import os

import pandas as pd

from config.params import TOTAL_STEPS
from model.model import AaapsModel

SCENARIOS = ["baseline", "free_market", "universal_ai", "subsidy", "mixed_policy"]


def run_and_save(scenario: str, seed: int = 42, n_students: int = 60) -> None:
    model = AaapsModel(n_students=n_students, scenario=scenario, seed=seed)
    for _ in range(TOTAL_STEPS):
        model.step()

    agent_df: pd.DataFrame = model.datacollector.get_agent_vars_dataframe()
    raw_dir = os.path.join("outputs", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    path = os.path.join(raw_dir, f"agent_data_{scenario}_seed{seed}.csv")
    agent_df.to_csv(path)
    print(f"[{scenario}] saved: {path} (shape={agent_df.shape})")


if __name__ == "__main__":
    for s in SCENARIOS:
        run_and_save(s, seed=42)
