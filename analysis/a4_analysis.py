"""
analysis/a4_analysis.py: analysis of amendment A4 (post hoc, exploratory channel-ratio sweep) and diagnostic D1.

Implements preregistration.md A4. Run once on the complete outputs:
    python -m analysis.a4_analysis
Reads outputs/v041_a4/A4_runs.csv and D1_seed*.npz (override the directory with AAAPS_A4_DIR), writes results_a4.md at the repository
root (override with AAAPS_A4_RESULTS_MD) and CSVs to <dir>/results/. It states what the rules give; it does not interpret.
Everything in it is EXPLORATORY. One shared bootstrap index matrix (rng 20261016, 10,000 x n_seeds) is used for every statistic.
"""
from __future__ import annotations

import glob
import hashlib
import os
import subprocess

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.environ.get("AAAPS_A4_DIR", os.path.join(ROOT, "outputs", "v041_a4"))
MD = os.environ.get("AAAPS_A4_RESULTS_MD", os.path.join(ROOT, "results_a4.md"))
RES = os.path.join(DIR, "results")
os.makedirs(RES, exist_ok=True)

NB = 10_000
SESOI_G = 717.0  # E_G SESOI of the confirmatory study (5% of G(baseline) on seeds 7000-7099, results_confirmatory.md), fixed here
SCENARIOS = ["universal_permanent", "free_market"]
KS = [1.0, 0.5, 0.0]
LEVELS = ["R0", "R1", "R2", "R3", "R4", "R5", "R6"]
MQ = {"R0": 0.0, "R1": 0.25, "R2": 0.5, "R3": 1.0, "R4": 1.0, "R5": 1.0, "R6": 1.0}
MS = {"R0": 1.0, "R1": 1.0, "R2": 1.0, "R3": 1.0, "R4": 0.5, "R5": 0.25, "R6": 0.0}
THETA = np.array([MQ[l] / (MQ[l] + MS[l]) for l in LEVELS])  # quality share of the two multipliers, 0 ... 1
LINES: list[str] = []


def w(s: str = "") -> None:
    LINES.append(s)


def md_table(df: pd.DataFrame, nd: int = 4) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            cells.append(f"{v:.{nd}f}" if isinstance(v, (float, np.floating)) and np.isfinite(v) else str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def ratio_of(theta: float) -> float:
    return np.inf if theta >= 1.0 else theta / (1.0 - theta)


class Data:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.seeds = sorted(df[df.scenario == "baseline"].seed.unique())
        self.ns = len(self.seeds)
        self.idx = np.random.default_rng(20261016).integers(0, self.ns, size=(NB, self.ns))

    def vec(self, col, scenario, level="R3", k=1.0):
        d = self.df[(self.df.scenario == scenario) & (self.df.level == level) & np.isclose(self.df.k, k)].sort_values("seed")
        assert list(d.seed) == self.seeds, f"selection {scenario} {level} {k}: {len(d)} rows"
        return d[col].to_numpy(dtype=float)

    def boot(self, d):
        return d[self.idx].mean(axis=1)


def ci(b):
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def fmt(m, lo, hi, nd=1):
    return f"{m:.{nd}f} [{lo:.{nd}f}, {hi:.{nd}f}]"


def first_crossing(vals: np.ndarray, c: float):
    """First crossing of level c scanning R0 -> R6 along THETA, linear interpolation. Returns (theta, direction) or None."""
    for i in range(len(vals) - 1):
        a, b = vals[i] - c, vals[i + 1] - c
        if a == 0:
            return float(THETA[i]), "touches"
        if a * b < 0:
            th = THETA[i] + (0 - a) * (THETA[i + 1] - THETA[i]) / (b - a)
            return float(th), ("rises through" if b > a else "falls through")
    return None


def a4(D: Data):
    w("## EXPLORATORY (all of A4, no multiplicity control, post hoc)")
    w()
    base_G = D.vec("G", "baseline")
    base_S = D.vec("mean_score", "baseline")
    w(f"Seeds {D.seeds[0]}-{D.seeds[-1]} ({D.ns} seeds), mode full, pivot P1. G(baseline) = {base_G.mean():.1f}, mean_score(baseline) = "
      f"{base_S.mean():.1f}. E_G = G(scenario, level, k) - G(baseline), paired by seed. SESOI for E_G = {SESOI_G:.1f} (the confirmatory value).")
    w("Levels: quality multiplier mq on AI_QUALITY_BOOST and speed multiplier ms on AI_SPEED_BOOST: "
      + "; ".join(f"{l} = (mq {MQ[l]:g}, ms {MS[l]:g}, ratio mq/ms {ratio_of(THETA[i]):.3g})" for i, l in enumerate(LEVELS)) + ".")
    w("Interpolation axis: theta = mq/(mq + ms) (0, 0.2, 0.333, 0.5, 0.667, 0.8, 1); ratio = mq/ms = theta/(1 - theta).")
    w()
    E = {}
    rows_lv, rows_cross, rows_k, rows_status = [], [], [], []
    for sc in SCENARIOS:
        for k in KS:
            for lv in LEVELS:
                eg = D.vec("G", sc, lv, k) - base_G
                sg = D.vec("mean_score", sc, lv, k) - base_S
                E[(sc, k, lv)] = eg
                be, bs = D.boot(eg), D.boot(sg)
                rows_lv.append(dict(scenario=sc, k=k, level=lv, E_G=fmt(eg.mean(), *ci(be)), score_gain=fmt(sg.mean(), *ci(bs)),
                                    g_mean_960=D.vec("g_mean_s960", sc, lv, k).mean(), mean_dependency=D.vec("mean_dependency", sc, lv, k).mean(),
                                    clip_count=D.vec("clip_count", sc, lv, k).mean(), E_G_vs_SESOI=(
                                        "above" if ci(be)[0] > SESOI_G else "below" if ci(be)[1] < -SESOI_G else "inside")))
    lv_df = pd.DataFrame(rows_lv)
    lv_df.to_csv(os.path.join(RES, "a4_levels.csv"), index=False)
    w("### Levels: E_G, mean score gain vs baseline, g_mean_960 (mean over seeds of mean g_k at step 960)")
    w("E_G_vs_SESOI: CI95 of E_G entirely above +SESOI, entirely below -SESOI, or inside (overlapping).")
    w(md_table(lv_df, 4))
    w()
    # ratio thresholds
    for sc in SCENARIOS:
        for k, c, label in ((1.0, SESOI_G, "E_G(k=1) vs +SESOI"), (0.0, -SESOI_G, "E_G(k=0) vs -SESOI")):
            m = np.array([E[(sc, k, lv)].mean() for lv in LEVELS])
            bm = np.array([D.boot(E[(sc, k, lv)]) for lv in LEVELS])  # levels x NB
            pt = first_crossing(m, c)
            res = [first_crossing(bm[:, j], c) for j in range(NB)]
            th = np.array([r[0] for r in res if r is not None])
            share_none = 1.0 - len(th) / NB
            if pt is None:
                point = "no crossing"
                beyond = ("E_G beyond the threshold at R0 and at every level" if (m > c).all() else
                          "E_G below the threshold at every level" if (m < c).all() else "no crossing")
                if (k == 0.0):
                    beyond = ("E_G(k=0) below -SESOI at every level" if (m < c).all() else "E_G(k=0) above -SESOI at every level" if (m > c).all() else beyond)
                if k == 1.0:
                    beyond = ("E_G(k=1) above +SESOI at every level" if (m > c).all() else "E_G(k=1) below +SESOI at every level" if (m < c).all() else beyond)
                point = f"no crossing ({beyond})"
                cil = "n/a"
            else:
                point = f"{pt[1]} at theta = {pt[0]:.3f}, ratio mq/ms = {ratio_of(pt[0]):.3f}"
                cil = (f"theta [{np.percentile(th, 2.5):.3f}, {np.percentile(th, 97.5):.3f}], ratio [{ratio_of(np.percentile(th, 2.5)):.3f}, "
                       f"{ratio_of(np.percentile(th, 97.5)):.3f}]") if len(th) else "n/a"
            rows_cross.append(dict(scenario=sc, quantity=label, point_estimate=point, CI95_over_resamples_with_crossing=cil,
                                   share_resamples_no_crossing=share_none))
    cr = pd.DataFrame(rows_cross)
    cr.to_csv(os.path.join(RES, "a4_ratio_thresholds.csv"), index=False)
    w("### Ratio thresholds (first crossing scanning R0 to R6, linear interpolation in theta between levels)")
    w("Reported on the point estimates; the CI is over bootstrap resamples that have a crossing, with the share of resamples without one.")
    w(md_table(cr, 3))
    w()
    # k* and linearity per level
    for sc in SCENARIOS:
        for lv in LEVELS:
            e = [E[(sc, k, lv)] for k in KS]
            vals = np.array([x.mean() for x in e])
            bv = np.array([D.boot(x) for x in e])
            def ks_of(v):
                for i in range(len(KS) - 1):
                    a, b = v[i], v[i + 1]
                    if a == 0:
                        return KS[i]
                    if a * b < 0:
                        return KS[i] + (0 - a) * (KS[i + 1] - KS[i]) / (b - a)
                return np.nan
            kp = ks_of(vals)
            kb = np.array([ks_of(bv[:, j]) for j in range(NB)])
            ok = kb[np.isfinite(kb)]
            dev = e[1] - (e[0] + e[2]) / 2.0
            bd = D.boot(dev)
            rows_k.append(dict(scenario=sc, level=lv, E_G_k1=vals[0], E_G_k05=vals[1], E_G_k0=vals[2],
                               k_star=("none in [0,1]" if not np.isfinite(kp) else f"{kp:.3f}"),
                               k_star_CI95=(f"[{np.percentile(ok, 2.5):.3f}, {np.percentile(ok, 97.5):.3f}]" if len(ok) else "n/a"),
                               share_no_crossing=1.0 - len(ok) / NB, midpoint_deviation_E_G_k05=fmt(dev.mean(), *ci(bd), nd=1)))
    kdf = pd.DataFrame(rows_k)
    kdf.to_csv(os.path.join(RES, "a4_kstar.csv"), index=False)
    w("### k* per level from k in {1, 0.5, 0} (scan from k = 1 down) and linearity check")
    w("midpoint_deviation_E_G_k05 = E_G(k=0.5) - (E_G(k=1) + E_G(k=0))/2, mean [CI95]; 0 under exact linearity in k.")
    w(md_table(kdf, 3))
    w()


def d1():
    files = sorted(glob.glob(os.path.join(DIR, "D1_seed*.npz")))
    w("### D1: local observed-use fraction vs global fraction (free_market, k = 1, R3, full)")
    if not files:
        w("No D1 files found.")
        return
    seeds = [int(os.path.basename(f)[7:-4]) for f in files]
    w(f"Seeds {seeds}. Logged per step t and agent i at the point the B1 peer term reads it (snapshot of agent state after step t-1): "
      "obs = tie-strength-weighted share of neighbours whose AI use was observed in the realised draws (the B1 observed_frac); "
      "raw = the same share without the P_VISIBLE draw; global = share of all agents with AI use in the snapshot. Agents without neighbours are excluded. "
      "ref_var_iid = mean over agents of p(1-p)/degree with p the global fraction at that step (unweighted, independent-neighbour reference; a computed reference, not a test).")
    bins = [(1 + 120 * b, 120 * (b + 1)) for b in range(8)]
    acc = {k: [] for k in ("glob", "var_obs", "var_raw", "ref_var_iid", "mad_obs_glob", "mad_raw_glob", "mad_obs_vs_pvis_glob")}
    corr_obs, corr_raw, per_seed = [], [], []
    for f, s in zip(files, seeds):
        z = np.load(f)
        obs, raw, g, deg, pv = z["obs"], z["raw"], z["glob"], z["deg"], float(z["p_visible"])
        keep = deg > 0
        obs, raw = obs[:, keep], raw[:, keep]
        gt = g[:, None]
        vo, vr = np.nanvar(obs, axis=1), np.nanvar(raw, axis=1)
        ref = np.array([np.mean(p * (1 - p) / deg[keep]) for p in g])
        mo, mr, mp = np.nanmean(np.abs(obs - gt), axis=1), np.nanmean(np.abs(raw - gt), axis=1), np.nanmean(np.abs(obs - pv * gt), axis=1)
        for key, arr in zip(acc, (g, vo, vr, ref, mo, mr, mp)):
            acc[key].append(arr)
        def agent_corr(x):
            out = []
            for i in range(x.shape[1]):
                col = x[:, i]
                if np.nanstd(col) > 0 and np.std(g) > 0:
                    out.append(np.corrcoef(col, g)[0, 1])
            return np.array(out)
        co, cr_ = agent_corr(obs), agent_corr(raw)
        corr_obs.append(co)
        corr_raw.append(cr_)
        per_seed.append(dict(seed=str(s), agents=str(int(keep.sum())), mean_global=g.mean(), mean_var_obs=vo.mean(), mean_var_raw=vr.mean(),
                             mean_ref_var_iid=ref.mean(), mean_abs_diff_obs_vs_global=mo.mean(), mean_abs_diff_raw_vs_global=mr.mean(),
                             corr_mean_obs_vs_global_over_time=np.corrcoef(np.nanmean(obs, axis=1), g)[0, 1],
                             mean_agent_corr_obs=co.mean(), mean_agent_corr_raw=cr_.mean()))
    A = {k: np.mean(np.array(v), axis=0) for k, v in acc.items()}  # mean over seeds, per step
    rows = []
    for lo, hi in bins:
        sl = slice(lo - 1, hi)
        rows.append(dict(steps=f"{lo}-{hi}", global_fraction=A["glob"][sl].mean(), var_obs=A["var_obs"][sl].mean(), var_raw=A["var_raw"][sl].mean(),
                         ref_var_iid=A["ref_var_iid"][sl].mean(), mad_obs_vs_global=A["mad_obs_glob"][sl].mean(),
                         mad_raw_vs_global=A["mad_raw_glob"][sl].mean(), mad_obs_vs_Pvisible_x_global=A["mad_obs_vs_pvis_glob"][sl].mean()))
    rows.append(dict(steps="1-960", global_fraction=A["glob"].mean(), var_obs=A["var_obs"].mean(), var_raw=A["var_raw"].mean(),
                     ref_var_iid=A["ref_var_iid"].mean(), mad_obs_vs_global=A["mad_obs_glob"].mean(), mad_raw_vs_global=A["mad_raw_glob"].mean(),
                     mad_obs_vs_Pvisible_x_global=A["mad_obs_vs_pvis_glob"].mean()))
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(RES, "d1_by_period.csv"), index=False)
    w()
    w("Mean over seeds. var = variance across agents at a step, averaged over the steps of the period; mad = mean over agents of |local - global|.")
    w(md_table(t, 5))
    w()
    co, cr_ = np.concatenate(corr_obs), np.concatenate(corr_raw)
    q = lambda x: f"mean {x.mean():.4f}, p05 {np.percentile(x, 5):.4f}, p50 {np.percentile(x, 50):.4f}, p95 {np.percentile(x, 95):.4f} (n agents = {len(x)})"
    w("Correlation over steps 1-960 between an agent's local fraction and the global fraction (agents with constant series excluded):")
    w(f"- observed local fraction: {q(co)}")
    w(f"- raw local fraction: {q(cr_)}")
    ps = pd.DataFrame(per_seed)
    ps.to_csv(os.path.join(RES, "d1_by_seed.csv"), index=False)
    w()
    w("Per seed:")
    w(md_table(ps, 5))
    w()


def main():
    p = os.path.join(DIR, "A4_runs.csv")
    D = Data(pd.read_csv(p))
    sha = hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
    try:
        git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except Exception:
        git = "unknown"
    w("# results_a4.md")
    w()
    w(f"Generated by analysis/a4_analysis.py (sha256 {sha}) at git {git}. Input directory: {DIR}.")
    w(f"Runs in A4_runs.csv: {len(D.df)}. Bootstrap: {NB:,} resamples, one shared index matrix, rng 20261016. Every result in this file is "
      "EXPLORATORY (amendment A4, post hoc). The file states what the rules return and contains no interpretation beyond them.")
    w()
    a4(D)
    d1()
    open(MD, "w").write("\n".join(LINES) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    main()
