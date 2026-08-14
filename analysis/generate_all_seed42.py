"""
analysis/generate_all_seed42.py — Generate agent-level seed=42 data for
all five scenarios, for direct cross-scenario comparison.
"""

from __future__ import annotations

import os

import pandas as pd

from config import params as P
from model.model import AaapsModel

SCENARIOS = ["baseline", "free_market", "universal_ai", "subsidy", "mixed_policy"]


def run_and_save(scenario: str, seed: int = 42, n_students: int = 60) -> None:
    model = AaapsModel(n_students=n_students, scenario=scenario, seed=seed)
    for _ in range(P.TOTAL_STEPS):
        model.step()
    agent_df = model.datacollector.get_agent_vars_dataframe()
    out_dir = os.path.join("outputs", "raw")
    os.makedirs(out_dir, exist_ok=True)
    filename = f"agent_data_{scenario}_seed{seed}.csv"
    path = os.path.join(out_dir, filename)
    agent_df.to_csv(path)
    print(f"[{scenario}] saved: {path} (shape={agent_df.shape})")
