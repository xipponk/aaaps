"""
scenarios/free_market.py — Free Market scenario runner (v0.3).

Standard market scenario where students adopt AI based on budget & SES.
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
    """Execute a single free_market simulation run."""
    model = AaapsModel(
        n_students=n_students,
        scenario="free_market",
        seed=seed,
        zero_interaction_mode=zero_interaction_mode,
    )

    # Initial AI tier purchase based on budget & WTP fraction
    for a in model.agents:
        wtp_budget = a.monthly_budget * P.TIER_BUDGET_FRACTION[a.SES]
        if wtp_budget >= P.AI_MONTHLY_COST[3]:
            a.ai_tier = 3
        elif wtp_budget >= P.AI_MONTHLY_COST[2]:
            a.ai_tier = 2
        else:
            a.ai_tier = 1  # Free tier
        a.ai_tier_effective = a.ai_tier

    for _step in range(P.TOTAL_STEPS):
        model.step()

    return model


if __name__ == "__main__":
    run(seed=42)
