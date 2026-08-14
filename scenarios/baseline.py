"""
scenarios/baseline.py — Baseline scenario runner (v0.3).

No AI access (S0 scenario). Reference baseline.
"""

from __future__ import annotations

import os
import pandas as pd

from config import params as P
from model.model import AaapsModel


def run(
    seed: int = 42,
    save_agents: bool = False,
    n_students: int = P.N_STUDENTS,
    zero_interaction_mode: bool = False,
) -> AaapsModel:
    """Execute a single baseline simulation run."""
    model = AaapsModel(
        n_students=n_students,
        scenario="baseline",
        seed=seed,
        zero_interaction_mode=zero_interaction_mode,
    )

    # Force AI tier to 0 for all agents in baseline
    for a in model.agents:
        a.ai_tier = 0
        a.ai_tier_effective = 0

    for _step in range(P.TOTAL_STEPS):
        model.step()

    return model


if __name__ == "__main__":
    run(seed=42)
