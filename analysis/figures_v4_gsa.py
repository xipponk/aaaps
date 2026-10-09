"""
analysis/figures_v4_gsa.py: v0.4 GSA figures (Morris composite ranking, Sobol ST heatmaps).

Reads saved CSVs only. Writes figures_v4/ (PNG 300 dpi and PDF). Does not touch the v0.3 figures.
Sobol metrics that findings_v04.md marks unreliable (borrowing_agent_count, total_shared_seats_lent)
or degenerate (ai_adoption_rate) are drawn greyed out and labelled, not hidden.
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs", "phase2")
FIG = os.path.join(ROOT, "figures_v4")

METRICS = ["mean_score", "std_score", "gini_score", "deadline_miss_count", "deadline_miss_rate",
           "mean_dependency", "mean_calibration_error", "mean_retained_ability",
           "relative_ability_decline", "mean_legitimacy",
           "borrowing_agent_count", "total_shared_seats_lent", "ai_adoption_rate"]
FLAG = {"borrowing_agent_count": "unreliable", "total_shared_seats_lent": "unreliable", "ai_adoption_rate": "degenerate"}


def _save(fig, name: str) -> None:
    os.makedirs(FIG, exist_ok=True)
    for ext in ("png", "pdf"):
        p = os.path.join(FIG, f"{name}.{ext}")
        fig.savefig(p, dpi=300, bbox_inches="tight")
        print("wrote", os.path.abspath(p))
    plt.close(fig)


def morris_figure() -> None:
    c = pd.read_csv(os.path.join(OUT, "morris_v04_composite_v2.csv"), index_col=0).sort_values("composite_max")
    kept = set(pd.read_csv(os.path.join(OUT, "morris_v04_retained12.csv"))["parameter"])
    fig, ax = plt.subplots(figsize=(7, 7.5))
    colors = ["#1f5f8b" if p in kept else "#b8b8b8" for p in c.index]
    ax.barh(c.index, c["composite_max"], color=colors)
    ax.set_xlabel("Composite Morris score (max over 8 metrics of column-normalised mu*)")
    ax.set_title("Morris screening, v0.4 (r=20, 3 seeds per design point)")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color="#1f5f8b"), plt.Rectangle((0, 0), 1, 1, color="#b8b8b8")],
              labels=["retained for Sobol (D=12)", "screened out"], loc="lower right", frameon=False)
    _save(fig, "fig_morris_composite")


def sobol_figure(scenario: str, tag: str) -> None:
    d = pd.read_csv(os.path.join(OUT, f"sobol_v04_{scenario}_indices.csv"))
    params = list(pd.read_csv(os.path.join(OUT, "morris_v04_retained12.csv"))["parameter"])
    st = d.pivot(index="parameter", columns="metric", values="ST").loc[params, METRICS]
    fig, ax = plt.subplots(figsize=(10, 5.6))
    im = ax.imshow(st.values, cmap="viridis", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(METRICS)))
    ax.set_xticklabels([m + (f"\n({FLAG[m]})" if m in FLAG else "") for m in METRICS], rotation=60, ha="right", fontsize=8)
    ax.set_yticks(range(len(params))); ax.set_yticklabels(params, fontsize=8)
    for i in range(st.shape[0]):
        for j in range(st.shape[1]):
            v = st.values[i, j]
            if v >= 0.05:
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.5, color="white" if v < 0.6 else "black")
    for j, m in enumerate(METRICS):
        if m in FLAG:
            ax.add_patch(plt.Rectangle((j - .5, -.5), 1, len(params), fill=True, color="white", alpha=0.65, lw=0))
    ax.set_title(f"Sobol total-order index ST, {tag} (N=512, 1 seed, 7,168 runs)")
    fig.colorbar(im, ax=ax, label="ST")
    _save(fig, f"fig_sobol_st_{scenario}")


if __name__ == "__main__":
    morris_figure()
    sobol_figure("free_market", "free_market")
    sobol_figure("targeted_subsidy", "targeted_subsidy")
