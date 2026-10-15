"""
analysis/figures_v41.py: figures for paper v4 (F0 to F9 and appendix FA), built from saved CSVs only. No simulation is run.
    python -m analysis.figures_v41
Writes figures_v41/<name>.png (300 dpi) and .pdf. No figure titles. One colour per scenario in every figure (Okabe-Ito).
Confidence intervals use the shared bootstrap index matrix of the confirmatory analysis, default_rng(20261016).integers(0, 100, (10000, 100)),
or are parsed from the results csv written by the locked analysis scripts (E_G, interaction decomposition, network contrasts, A4 levels).
Provenance of every figure: figures_v41/captions.md.
"""
from __future__ import annotations

import glob
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONF = os.path.join(ROOT, "outputs", "v041_conf")
A4 = os.path.join(ROOT, "outputs", "v041_a4")
MAIN = os.path.join(ROOT, "outputs", "v041_main")
FIG = os.path.join(ROOT, "figures_v41")
NB, NS = 10_000, 100
IDX = np.random.default_rng(20261016).integers(0, NS, size=(NB, NS))

COL = {"baseline": "#555555", "free_market": "#0072B2", "universal_permanent": "#D55E00", "mixed_policy": "#009E73",
       "targeted_subsidy": "#CC79A7", "universal_access": "#E69F00"}
SC5 = ["free_market", "universal_permanent", "mixed_policy", "targeted_subsidy", "universal_access"]
COPRIMARY = ["universal_permanent", "free_market"]
LAB = {"free_market": "free market", "universal_permanent": "universal permanent", "mixed_policy": "mixed policy",
       "targeted_subsidy": "targeted subsidy", "universal_access": "universal access (temporary)"}
plt.rcParams.update({"font.size": 8, "axes.labelsize": 8, "legend.fontsize": 7, "xtick.labelsize": 7, "ytick.labelsize": 7,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.7, "lines.linewidth": 1.2,
                     "pdf.fonttype": 42, "ps.fonttype": 42})


def save(fig, name):
    os.makedirs(FIG, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, f"{name}.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("wrote", os.path.join("figures_v41", name))


def ci(d):
    b = d[IDX].mean(axis=1)
    return float(d.mean()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def parse(s):
    """'231.6 [157.6, 302.2]' -> (231.6, 157.6, 302.2)"""
    return tuple(float(x) for x in re.findall(r"-?\d+\.?\d*(?:e-?\d+)?", s)[:3])


def runs(block):
    df = pd.read_csv(os.path.join(CONF, f"{block}_runs.csv"))
    for c, d in (("ablation", "none"), ("disabled", "none"), ("net_label", "default")):
        df[c] = df[c].fillna(d).astype(str)
    return df


def sel(df, **c):
    m = np.ones(len(df), bool)
    for k, v in c.items():
        m &= np.isclose(df[k].astype(float), v) if isinstance(v, float) else (df[k] == v).to_numpy()
    out = df[m].sort_values("seed")
    assert len(out) == NS and out.seed.nunique() == NS, f"selection {c}: {len(out)} rows"
    return out


def tag(ax, text):
    ax.set_title(text, loc="left", fontsize=8, fontweight="bold")


# ---------------------------------------------------------------- F0
def f0():
    p = pd.read_csv(os.path.join(MAIN, "production_v04_runs.csv"))
    base = p[p.scenario == "baseline"].sort_values("seed")
    outs = [("mean_score", "Score gain\n(points)"), ("gini_score", "Change in Gini\nof score"), ("mean_dependency", "Dependency"),
            ("relative_ability_decline", "Relative ability\ndecline"), ("deadline_miss_count", "Deadline misses\n(count)")]
    fig, axs = plt.subplots(1, 5, figsize=(7.4, 2.5), sharey=True)
    for n, (ax, (m, lab)) in enumerate(zip(axs, outs)):
        tag(ax, f"({'abcde'[n]})")
        ax.xaxis.set_major_locator(MaxNLocator(3))
        if m == "gini_score":
            ax.set_xticks([-0.01, 0.0, 0.01], ["-0.01", "0.00", "0.01"])
        for i, sc in enumerate(SC5):
            d = p[p.scenario == sc].sort_values("seed")[m].to_numpy(float) - base[m].to_numpy(float)
            mu, lo, hi = ci(d)
            ax.errorbar(mu, i, xerr=[[mu - lo], [hi - mu]], fmt="o", color=COL[sc], ms=4, capsize=2)
        ax.axvline(0, color="#999999", lw=0.7)
        ax.set_xlabel(lab)
        ax.set_yticks(range(5), [LAB[s] for s in SC5])
        ax.invert_yaxis()
        ax.tick_params(axis="x", labelsize=6.5)
    fig.tight_layout()
    save(fig, "F0_scenario_overview")


# ---------------------------------------------------------------- F1
def f1():
    t = pd.read_csv(os.path.join(CONF, "results", "E_G_states.csv"))
    sesoi = float(pd.read_csv(os.path.join(CONF, "results", "interaction_decomposition.csv")).query("outcome == 'G'").sesoi.iloc[0])
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw=dict(width_ratios=[1, 1]))
    ks_t = pd.read_csv(os.path.join(CONF, "results", "k_star.csv")).set_index("scenario")
    for ax, scs, sub in zip(axs, (COPRIMARY, SC5[2:]), ("(a)", "(b)")):
        for sc in scs:
            r = t[t.scenario == sc].copy()
            v = np.array([parse(s) for s in r.E_G])
            k = r.k.to_numpy(float)
            o = np.argsort(k)
            ax.errorbar(k[o], v[o, 0], yerr=[v[o, 0] - v[o, 1], v[o, 2] - v[o, 0]], color=COL[sc], marker="o", ms=3.5, capsize=2,
                        label=LAB[sc], ls="-" if sc in COPRIMARY else "--")
        ax.axhspan(-sesoi, sesoi, color="#bbbbbb", alpha=0.25, lw=0)
        ax.axhline(0, color="#777777", lw=0.7)
        if ax is axs[0]:
            for sc in COPRIMARY:
                ks, (klo, khi) = float(ks_t.loc[sc, "k_star"]), (float(x) for x in re.findall(r"-?\d+\.\d+", ks_t.loc[sc, "CI95_over_crossing_resamples"]))
                ax.errorbar(ks, 0, xerr=[[ks - klo], [khi - ks]], fmt="D", color=COL[sc], mfc="white", mec=COL[sc], ms=6, capsize=3, lw=1.6, zorder=6,
                            label=f"k* ({LAB[sc]}), 95% CI")
        ax.set_xlabel("Benefit-ability slope k")
        ax.legend(frameon=False, loc="lower right", fontsize=6.5)
        tag(ax, sub)
    axs[0].set_ylabel("E_G = G(AI) - G(baseline) (score points)")
    fig.tight_layout()
    save(fig, "F1_EG_by_k")


# ---------------------------------------------------------------- F2
def f2():
    lv = pd.read_csv(os.path.join(A4, "results", "a4_levels.csv"))
    th = pd.read_csv(os.path.join(A4, "results", "a4_ratio_thresholds.csv"))
    XL = ["R0\nno quality", "R1\n0.25", "R2\n0.5", "R3\n1", "R4\n2", "R5\n4", "R6\nno speed"]
    pos = {"R0": -3.4, "R1": -2, "R2": -1, "R3": 0, "R4": 1, "R5": 2, "R6": 3.4}
    sty = {1.0: ("-", "o", -0.06), 0.5: ("--", "s", 0.0), 0.0: (":", "^", 0.06)}
    sesoi = float(pd.read_csv(os.path.join(CONF, "results", "interaction_decomposition.csv")).query("outcome == 'G'").sesoi.iloc[0])
    rows = [("E_G", "E_G (score points)"), ("score_gain", "Score gain (points)")]
    fig, axs = plt.subplots(2, 2, figsize=(7.2, 5.0), sharex=True)
    for j, sc in enumerate(COPRIMARY):
        for i, (m, ylab) in enumerate(rows):
            ax = axs[i, j]
            for k, (ls, mk, off) in sty.items():
                s = lv[(lv.scenario == sc) & np.isclose(lv.k, k)].copy()
                s["x"] = s.level.map(pos)
                s = s.sort_values("x")
                if m == "g_mean_960":
                    ax.plot(s.x + off, s[m], color=COL[sc], ls=ls, marker=mk, ms=3.5, label=f"k = {k:g}")
                else:
                    v = np.array([parse(x) for x in s[m]])
                    ax.errorbar(s.x + off, v[:, 0], yerr=[v[:, 0] - v[:, 1], v[:, 2] - v[:, 0]], color=COL[sc], ls=ls, marker=mk, ms=3.5,
                                capsize=1.5, label=f"k = {k:g}")
            ax.axvline(0, color="#777777", lw=0.8, ls="-.")
            for xv in (-2.7, 2.7):
                ax.axvline(xv, color="#bbbbbb", lw=0.6)
            if m == "E_G":
                ax.axhline(sesoi, color="#555555", lw=0.7, ls="--")
                ax.axhline(-sesoi, color="#555555", lw=0.7, ls="--")
                ax.axhline(0, color="#999999", lw=0.5)
                for q, yv, mk, kk in (("E_G(k=1) vs +SESOI", sesoi, "D", 1.0), ("E_G(k=0) vs -SESOI", -sesoi, "D", 0.0)):
                    r = th[(th.scenario == sc) & (th.quantity == q)].iloc[0]
                    if "ratio mq/ms" not in str(r.point_estimate):
                        continue
                    est = float(re.search(r"ratio mq/ms = ([\d.]+)", r.point_estimate).group(1))
                    lo, hi = (float(x) for x in re.search(r"ratio \[([\d.]+), ([\d.]+)\]", r.CI95_over_resamples_with_crossing).groups())
                    ax.errorbar(np.log2(est), yv, xerr=[[np.log2(est) - np.log2(lo)], [np.log2(hi) - np.log2(est)]], fmt=mk, color="black",
                                mfc="white", ms=5, capsize=2, zorder=5, label="threshold crossing" if kk == 1.0 else None)
            if j == 0:
                ax.set_ylabel(ylab)
            tag(ax, f"({'abcd'[i * 2 + j]}) {LAB[sc]}")
        axs[1, j].set_xticks([pos[x] for x in pos], XL)
        axs[1, j].set_xlabel("Channel ratio mq/ms (log scale; ends are separate points)")
    axs[0, 0].legend(frameon=False, loc="upper left", bbox_to_anchor=(0.0, 0.88))
    fig.tight_layout()
    save(fig, "F2_ratio_sweep")
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.7), sharex=True)
    for j, sc in enumerate(COPRIMARY):
        ax = axs[j]
        for k, (ls, mk, off) in sty.items():
            s = lv[(lv.scenario == sc) & np.isclose(lv.k, k)].copy()
            s["x"] = s.level.map(pos)
            s = s.sort_values("x")
            ax.plot(s.x + off, s["g_mean_960"], color=COL[sc], ls=ls, marker=mk, ms=3.5, label=f"k = {k:g}")
        ax.axvline(0, color="#777777", lw=0.8, ls="-.")
        for xv in (-2.7, 2.7):
            ax.axvline(xv, color="#bbbbbb", lw=0.6)
        ax.set_xticks([pos[x] for x in pos], XL)
        ax.set_xlabel("Channel ratio mq/ms (log scale; ends are separate points)")
        ax.set_ylabel("g_mean_960" if j == 0 else "")
        tag(ax, f"({'ab'[j]}) {LAB[sc]}")
    axs[0].legend(frameon=False, loc="best")
    fig.tight_layout()
    save(fig, "F2_appendix_pivot")


# ---------------------------------------------------------------- F3
def f3():
    d = pd.read_csv(os.path.join(CONF, "results", "interaction_decomposition.csv"))
    d = d[np.isclose(d.k, 1.0)]
    outs = [("mean_dependency", "\u0394 dependency"), ("mean_calibration_error", "\u0394 calibration error"), ("relative_ability_decline", "\u0394 relative ability decline"),
            ("deadline_miss_count", "\u0394 deadline misses"), ("gini_score", "\u0394 Gini"), ("G", "\u0394 G")]
    fig, axs = plt.subplots(2, 3, figsize=(7.2, 4.6))
    for n, (ax, (o, lab)) in enumerate(zip(axs.ravel(), outs)):
        tag(ax, f"({'abcdef'[n]})")
        r = d[d.outcome == o]
        sesoi = float(r.sesoi.iloc[0])
        for i, sc in enumerate(COPRIMARY):
            q = r[r.scenario == sc].iloc[0]
            for dx, key, hatch in ((-0.19, "individual", None), (0.19, "social", "////")):
                m, lo, hi = parse(q[key])
                ax.bar(i + dx, m, 0.34, color=COL[sc], alpha=1.0 if hatch is None else 0.35, hatch=hatch, edgecolor=COL[sc], lw=0.8)
                ax.errorbar(i + dx, m, yerr=[[m - lo], [hi - m]], color="black", capsize=2, lw=0.8, fmt="none")
            m, lo, hi = parse(q["full_minus_zero"])
            ax.errorbar(i, m, yerr=[[m - lo], [hi - m]], fmt="D", color="black", ms=3.5, capsize=2, lw=0.8)
        ax.axhspan(-sesoi, sesoi, color="#bbbbbb", alpha=0.3, lw=0)
        ax.axhline(0, color="#777777", lw=0.7)
        ax.set_xticks([0, 1], [LAB[s].replace(" ", "\n") for s in COPRIMARY])
        ax.set_xlim(-0.6, 1.6)
        ax.set_ylabel(lab)
    fig.legend(handles=[Patch(fc="#777777", ec="#777777", label="individual"), Patch(fc="#dddddd", ec="#777777", hatch="////", label="social"),
                        plt.Line2D([], [], marker="D", color="black", ls="", ms=3.5, label="full minus zero interaction")],
               frameon=False, loc="upper center", ncol=3, fontsize=7, bbox_to_anchor=(0.5, 1.04))
    fig.tight_layout()
    save(fig, "F3_interaction_decomposition")


# ---------------------------------------------------------------- F4
def f4():
    K, L = runs("K"), runs("L0")
    rows = []
    for l0 in (0.05, 0.1, 0.2, 0.3):
        src, kw = (K, {"block": "K", "k": 1.0}) if np.isclose(l0, 0.1) else (L, {"block": "L0"})
        if "block" in kw and kw["block"] == "L0":
            kw = {}
        s = {}
        for mode in ("full", "self_only", "zero_interaction"):
            sub = src[(src.scenario == "free_market") & (src["mode"] == mode) & np.isclose(src.L0.astype(float), l0)]
            if np.isclose(l0, 0.1):
                sub = sub[np.isclose(sub.k, 1.0)]
            sub = sub.sort_values("seed")
            assert len(sub) == NS, (l0, mode, len(sub))
            s[mode] = sub.mean_dependency.to_numpy(float)
        num, den = s["self_only"] - s["zero_interaction"], s["full"] - s["zero_interaction"]
        b = num[IDX].mean(axis=1) / den[IDX].mean(axis=1)
        rows.append((l0, num.mean() / den.mean(), np.percentile(b, 2.5), np.percentile(b, 97.5)))
    t = pd.DataFrame(rows, columns=["L0", "S", "lo", "hi"])
    md = pd.read_csv(os.path.join(CONF, "results", "h_self.csv"))
    assert abs(float(t[np.isclose(t.L0, 0.1)].S.iloc[0]) - float(md.S.iloc[0])) < 1e-9, "S at L0 = 0.1 differs from h_self.csv"
    os.makedirs(FIG, exist_ok=True)
    t.to_csv(os.path.join(FIG, "F4_data_S_by_L0.csv"), index=False)
    fig, ax = plt.subplots(figsize=(3.6, 2.8))
    ax.errorbar(t.L0, t.S, yerr=[t.S - t.lo, t.hi - t.S], color=COL["free_market"], marker="o", ms=4, capsize=2)
    ax.axhline(0.5, color="#555555", ls="--", lw=0.8)
    ax.axhline(1.0, color="#555555", ls=":", lw=0.9)
    ax.text(0.305, 0.5, "S = 0.5 (decision threshold)", ha="right", va="bottom", fontsize=6.5)
    ax.text(0.305, 1.0, "S = 1 (individual part equals the whole)", ha="right", va="top", fontsize=6.5)
    ax.set_ylim(0.3, 1.6)
    ax.set_xticks([0.05, 0.1, 0.2, 0.3])
    ax.set_xlabel("Initial legitimacy L0")
    ax.set_ylabel("S = (D_self - D_zero)/(D_full - D_zero)")
    fig.tight_layout()
    save(fig, "F4_H_self_L0")
    return t


# ---------------------------------------------------------------- F5 and F6
def f56():
    nc = pd.read_csv(os.path.join(CONF, "results", "network_contrasts_full.csv"))
    order = ["p_within", "p_between", "h_ses", "h_ability"]
    nc["o"] = nc.parameter.map({p: i for i, p in enumerate(order)})
    nc = nc.sort_values(["o", "level"]).reset_index(drop=True)
    N = runs("NET")
    N = N[N.scenario == "free_market"]
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.1), gridspec_kw=dict(width_ratios=[1.5, 1]))
    ax = axs[0]
    x, gaps, ticks = [], 0.0, []
    for i, r in nc.iterrows():
        if i > 0 and nc.parameter[i] != nc.parameter[i - 1]:
            gaps += 0.8
        x.append(i + gaps)
    nc["x"] = x
    ax.axhspan(-0.02, 0.02, color="#bbbbbb", alpha=0.3, lw=0)
    ax.axhline(0, color="#777777", lw=0.7)
    ax.errorbar(nc.x, nc["diff"], yerr=[nc["diff"] - nc.lo95, nc.hi95 - nc["diff"]], fmt="o", color=COL["free_market"], ms=3.5, capsize=2)
    ax.set_xticks(nc.x, [f"{l:g}" for l in nc.level], rotation=90)
    for p in order:
        s = nc[nc.parameter == p]
        ax.text(s.x.mean(), -0.2, p, ha="center", va="top", fontsize=7, transform=ax.get_xaxis_transform(), clip_on=False)
    ax.set_ylim(-0.03, 0.03)
    ax.set_ylabel("Change in dependency")
    ax.set_xlabel("")
    tag(ax, "(a)")
    ax = axs[1]
    labs = sorted(N[N.net_label.str.startswith("dens=")].net_label.unique())
    for dis, ls, lab in (("none", "-", "full"), ("norms", "--", "no norms (peer and self)")):
        pts = []
        for lb in labs:
            sub = sel(N, net_label=lb, disabled=dis)
            mu, lo, hi = ci(sub.mean_dependency.to_numpy(float))
            pts.append((sub.net_within_section_share.mean(), mu, lo, hi))
        a = np.array(sorted(pts))
        ax.errorbar(a[:, 0], a[:, 1], yerr=[a[:, 1] - a[:, 2], a[:, 3] - a[:, 1]], color=COL["free_market"], ls=ls, marker="o", ms=3.5, capsize=2, label=lab)
    ax.set_ylim(0, 0.3)
    ax.set_xlabel("Within-section tie share")
    ax.set_ylabel("Dependency")
    ax.legend(frameon=False, loc="center right")
    tag(ax, "(b)")
    fig.tight_layout()
    save(fig, "F5_F6_network_and_density")


# ---------------------------------------------------------------- F7 and F8
NETPAR = {"HOMOPHILY_SES", "HOMOPHILY_ABILITY", "SBM_P_WITHIN", "SBM_P_BETWEEN"}


def f7():
    c = pd.read_csv(os.path.join(MAIN, "morris_v04_composite_v2.csv"), index_col=0).sort_values(["composite_max", "rank"], ascending=[False, True])
    keep = set(pd.read_csv(os.path.join(MAIN, "morris_v04_retained12.csv")).parameter)
    cols = [("mean_score", "mean score"), ("std_score", "std score"), ("gini_score", "Gini"), ("mean_dependency", "dependency"),
            ("mean_calibration_error", "calibration error"), ("relative_ability_decline", "ability decline"),
            ("deadline_miss_count", "deadline misses"), ("mean_legitimacy", "legitimacy")]
    M = c[[f"{m}_norm" for m, _ in cols]].to_numpy(float)
    fig, ax = plt.subplots(figsize=(5.6, 6.0))
    im = ax.imshow(M, cmap="viridis", vmin=0, vmax=1, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=5.5, color="white" if M[i, j] < 0.55 else "black")
    ax.set_xticks(range(len(cols)), [l for _, l in cols], rotation=45, ha="right")
    ax.set_yticks(range(len(c)), [p + (" *" if p in NETPAR else "") + ("  (top 12)" if p in keep else "") for p in c.index], fontsize=6.5)
    for lab, p in zip(ax.get_yticklabels(), c.index):
        if p in NETPAR:
            lab.set_fontweight("bold")
    assert sum(p in keep for p in c.index[:12]) == 12, "top 12 by composite is not the retained set"
    ax.axhline(11.5, color="white", lw=2.0)
    ax.axhline(11.5, color="black", lw=0.8, ls="--")
    fig.colorbar(im, ax=ax, shrink=0.7, label="normalised mu*")
    fig.tight_layout()
    save(fig, "F7_morris")


def f8():
    S = {sc: pd.read_csv(os.path.join(MAIN, f"sobol_v04_{sc}_indices.csv")) for sc in ("free_market", "targeted_subsidy")}
    main = [("mean_score", "Mean score"), ("gini_score", "Gini of score"), ("mean_dependency", "Dependency"), ("relative_ability_decline", "Relative ability decline")]
    order = (S["free_market"][S["free_market"].metric.isin([m for m, _ in main])].groupby("parameter").ST.max().sort_values().index.tolist())
    fig, axs = plt.subplots(2, 4, figsize=(7.4, 5.4), sharey="row")
    for i, sc in enumerate(S):
        for j, (m, lab) in enumerate(main):
            ax = axs[i, j]
            d = S[sc][S[sc].metric == m].set_index("parameter").loc[order].reset_index()
            y = np.arange(len(d))
            ax.barh(y + 0.19, d.ST, 0.36, xerr=d.ST_conf, color=COL[sc], error_kw=dict(lw=0.6, capsize=1))
            ax.barh(y - 0.19, d.S1.clip(lower=0), 0.36, color=COL[sc], alpha=0.35, hatch="////", edgecolor=COL[sc], lw=0.4)
            ax.set_yticks(y, d.parameter, fontsize=6)
            ax.set_xlim(0, 1)
            if i == 1:
                ax.set_xlabel("Index")
            tag(ax, f"({'abcdefgh'[i * 4 + j]}) {lab}")
        axs[i, 0].set_ylabel(LAB[sc] + " (scenario)")
        axs[i, 3].legend(handles=[Patch(fc=COL[sc], label="ST (95% CI)"), Patch(fc=COL[sc], alpha=0.35, hatch="////", ec=COL[sc], label="S1 (clipped at 0)")],
                         frameon=False, loc="lower right", fontsize=6)
    fig.tight_layout()
    save(fig, "F8_sobol_main")
    # appendix: total-order heatmap for the remaining metrics; borrowing and degenerate metrics in grey
    rest = ["std_score", "mean_calibration_error", "mean_retained_ability", "deadline_miss_count", "deadline_miss_rate", "mean_legitimacy",
            "borrowing_agent_count", "total_shared_seats_lent", "ai_adoption_rate"]
    grey = {"borrowing_agent_count", "total_shared_seats_lent", "ai_adoption_rate"}
    params = list(S["free_market"].parameter.unique())
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.6), sharey=True)
    for ax, sc in zip(axs, S):
        M = np.array([[float(S[sc][(S[sc].metric == m) & (S[sc].parameter == p)].ST.iloc[0]) for m in rest] for p in params])
        im_main = ax.imshow(np.where([m not in grey for m in rest], M, np.nan), cmap="viridis", vmin=0, vmax=1, aspect="auto")
        ax.imshow(np.where([m in grey for m in rest], M, np.nan), cmap="Greys", vmin=0, vmax=2.5, aspect="auto", alpha=0.7)
        for iy in range(M.shape[0]):
            for jx in range(M.shape[1]):
                ax.text(jx, iy, "n/a" if np.isnan(M[iy, jx]) else f"{M[iy, jx]:.2f}", ha="center", va="center", fontsize=5, color="white" if (M[iy, jx] < 0.55 and rest[jx] not in grey) else "black")
        ax.set_xticks(range(len(rest)), [m.replace("_", " ") + (" (unreliable)" if m in grey and m != "ai_adoption_rate" else " (degenerate)" if m == "ai_adoption_rate" else "") for m in rest],
                      rotation=60, ha="right", fontsize=6)
        ax.set_yticks(range(len(params)), params, fontsize=6)
        ax.set_xlabel(LAB[sc] + " (scenario)", color=COL[sc])
    fig.colorbar(im_main, ax=axs, shrink=0.8, label="ST")
    save(fig, "F8_appendix_sobol_total_order")


# ---------------------------------------------------------------- F9
def f9():
    K, A = runs("K"), runs("ABL")
    base = sel(K, block="K", scenario="baseline", mode="full", k=1.0).G.to_numpy(float)
    fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.9), gridspec_kw=dict(width_ratios=[1, 1, 1.05]))
    sesoi = 0.05 * base.mean()
    for ax, mode, sub in zip(axs[:2], ("full", "zero_interaction"), ("(a)", "(b)")):
        for i, sc in enumerate(COPRIMARY):
            vals = [("both channels", sel(K, block="K", scenario=sc, mode=mode, k=1.0).G.to_numpy(float) - base, None, 1.0),
                    ("quality only", sel(A, scenario=sc, ablation="quality_only", mode=mode, k=1.0).G.to_numpy(float) - base, "////", 0.45),
                    ("speed only", sel(A, scenario=sc, ablation="speed_only", mode=mode, k=1.0).G.to_numpy(float) - base, "....", 0.45)]
            for j, (lab, d, h, al) in enumerate(vals):
                mu, lo, hi = ci(d)
                ax.bar(i * 4 + j, mu, 0.85, color=COL[sc], alpha=al, hatch=h, edgecolor=COL[sc], lw=0.6)
                ax.errorbar(i * 4 + j, mu, yerr=[[mu - lo], [hi - mu]], color="black", capsize=1.5, lw=0.7, fmt="none")
        ax.axhspan(-sesoi, sesoi, color="#bbbbbb", alpha=0.3, lw=0)
        ax.axhline(0, color="#777777", lw=0.7)
        ax.set_xticks([1, 5], [LAB[s].replace(" ", "\n") for s in COPRIMARY])
        ax.set_ylabel("E_G (score points)" if mode == "full" else "")
        tag(ax, sub)
    axs[0].legend(handles=[Patch(fc="#777777", label="both channels"), Patch(fc="#dddddd", ec="#777777", hatch="////", label="quality only"),
                           Patch(fc="#dddddd", ec="#777777", hatch="....", label="speed only")], frameon=False, loc="upper right", fontsize=6)
    ax = axs[2]
    d = pd.read_csv(os.path.join(A4, "results", "d1_reference_steps.csv")).iloc[2:]
    ax.plot(d.step, d.ratio_raw_to_exact.rolling(40, min_periods=1).mean(), color=COL["free_market"], ls="-", label="raw")
    ax.plot(d.step, d.ratio_obs_to_exact.rolling(40, min_periods=1).mean(), color=COL["free_market"], ls="--", label="observed")
    ax.axhline(1.0, color="#777777", lw=0.7)
    ax.set_ylim(0.95, 1.12)
    ax.set_xlabel("Step")
    ax.set_ylabel("Variance / reference (40-step mean)")
    ax.legend(frameon=False, loc="upper right", fontsize=6)
    tag(ax, "(c)")
    fig.tight_layout()
    save(fig, "F9_ablation_and_D1")
    # panels a and b of F9 are F9a, panel c is F9b


# ---------------------------------------------------------------- FA (appendix)
def fa():
    K = runs("K")
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.8))
    ks = [-1.0, -0.5, 0.0, 0.5, 1.0]
    for n, (ax, (m, lab)) in enumerate(zip(axs, (("relative_ability_decline", "Relative ability decline"), ("mean_dependency", "Dependency")))):
        tag(ax, f"({'ab'[n]})")
        for n, sc in enumerate(SC5):
            pts = [ci(sel(K, block="K", scenario=sc, mode="full", k=k)[m].to_numpy(float)) for k in ks]
            a = np.array(pts)
            off = (n - 2) * 0.012
            ax.errorbar(np.array(ks) + off, a[:, 0], yerr=[a[:, 0] - a[:, 1], a[:, 2] - a[:, 0]], color=COL[sc], marker="o", ms=3, capsize=1.5,
                        ls="-" if sc in COPRIMARY else "--", label=LAB[sc])
        ax.set_xlabel("Benefit-ability slope k")
        ax.set_ylabel(lab)
        ax.set_ylim(bottom=0)
    axs[1].legend(frameon=False, loc="lower right", fontsize=6)
    fig.tight_layout()
    save(fig, "FA_k_invariance")


if __name__ == "__main__":
    os.makedirs(FIG, exist_ok=True)
    for f in (f0, f1, f2, f3, f4, f56, f7, f8, f9, fa):
        f()
