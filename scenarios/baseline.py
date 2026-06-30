"""
scenarios/baseline.py — Baseline scenario runner.

No AI access in any course. Serves as the reference point against which
all other scenarios are compared.
"""

from __future__ import annotations

import os

import pandas as pd

from config.params import TOTAL_STEPS
from model.model import AaapsModel


def run(
    seed: int = 42,
    save_agents: bool = False,
    n_students: int = 60,
) -> AaapsModel:
    """Execute a single *baseline* simulation run.

    Parameters
    ----------
    seed : int
        Random seed for reproducibility (default 42).
    save_agents : bool
        If ``True``, export the agent-level DataCollector DataFrame to
        ``outputs/raw/agent_data_baseline_seed{seed}.csv``.
    n_students : int
        Number of students (default 60).

    Returns
    -------
    AaapsModel
        The completed model instance.
    """
    model = AaapsModel(
        n_students=n_students,
        scenario="baseline",
        seed=seed,
    )

    for _step in range(TOTAL_STEPS):
        model.step()

    if save_agents:
        agent_df: pd.DataFrame = model.datacollector.get_agent_vars_dataframe()
        raw_dir = _ensure_raw_dir()
        filename = f"agent_data_baseline_seed{seed}.csv"
        path = os.path.join(raw_dir, filename)
        agent_df.to_csv(path)
        print(
            f"[baseline] Agent data saved: {path} "
            f"(shape={agent_df.shape})"
        )

    return model


def _ensure_raw_dir() -> str:
    """Create and return ``outputs/raw/`` (project-relative)."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(project_root, "outputs", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    return raw_dir


# =============================================================================
# CLI invocation
# =============================================================================

if __name__ == "__main__":
    run(seed=42, save_agents=True)
