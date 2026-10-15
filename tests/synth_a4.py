"""Synthetic A4 and D1 outputs with the schema of analysis/run_a4.py, to test analysis/a4_analysis.py before real data exist."""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

LEVELS = {"R0": (0.0, 1.0), "R1": (0.25, 1.0), "R2": (0.5, 1.0), "R3": (1.0, 1.0), "R4": (1.0, 0.5), "R5": (1.0, 0.25), "R6": (1.0, 0.0)}


def make(dirpath: str, n_seeds: int = 100) -> None:
    rng = np.random.default_rng(2)
    rows = []
    seeds = range(8000, 8000 + n_seeds)

    def row(sc, s, lv, k, gap):
        return dict(job_id=f"A4|{sc}|{s}|{lv}|{k}", block="A4", scenario=sc, seed=s, level=lv, mq=LEVELS[lv][0], ms=LEVELS[lv][1], k=k,
                    G=14000 + gap + 100 * rng.normal(), mean_score=31000 + gap / 2 + 100 * rng.normal(), mean_dependency=0.3 + 0.01 * rng.normal(),
                    g_mean_s960=0.5, clip_count=0, pivot_value=0.5)

    for s in seeds:
        rows.append(row("baseline", s, "R3", 1.0, 0.0))
        for sc in ("free_market", "universal_permanent"):
            for lv in LEVELS:
                th = LEVELS[lv][0] / (LEVELS[lv][0] + LEVELS[lv][1])
                for k in (1.0, 0.5, 0.0):
                    rows.append(row(sc, s, lv, k, gap=3000 * (th - 0.5) + 1500 * k - 600))
    pd.DataFrame(rows).to_csv(os.path.join(dirpath, "A4_runs.csv"), index=False)
    for s in (8100, 8101):
        deg = rng.integers(0, 20, 240)
        g = np.clip(0.3 + 0.1 * np.sin(np.arange(960) / 50) + 0.01 * rng.normal(size=960), 0, 1)
        raw = np.clip(g[:, None] + 0.1 * rng.normal(size=(960, 240)), 0, 1)
        obs = 0.7 * raw
        np.savez_compressed(os.path.join(dirpath, f"D1_seed{s}.npz"), obs=obs, raw=raw, glob=g, deg=deg, p_visible=0.7)
