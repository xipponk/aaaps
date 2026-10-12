"""
analysis/gate5_analysis.py: Gate 5 analysis of the saved v0.4.1 pipeline outputs (no simulation).
Reads outputs/v041_main (v0.4.1) and outputs/phase2 (v0.4); writes tables and figures to outputs/v041_main/gate5/.
All intervals are paired bootstraps over seeds (10,000 resamples, rng 20261016) and are EXPLORATORY here.
"""
from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from SALib.sample import sobol as sobol_sample

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
NEW = os.path.join(ROOT, "outputs", "v041_main")
OLD = os.path.join(ROOT, "outputs", "phase2")
G5 = os.path.join(NEW, "gate5")
os.makedirs(G5, exist_ok=True)
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)
RNG_SEED = 20261016
NBOOT = 10_000


def boot_ci(d: np.ndarray, stat=np.mean) -> tuple[float, float, float]:
    rng = np.random.default_rng(RNG_SEED)
    idx = rng.integers(0, len(d), size=(NBOOT, len(d)))
    b = stat(d[idx], axis=1)
    return float(stat(d)), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def fmt(m, lo, hi, nd=4):
    return f"{m:.{nd}f} [{lo:.{nd}f}, {hi:.{nd}f}]"


# ---------------------------------------------------------------- 1. legitimacy
def legitimacy():
    print("\n===== 1. mean_legitimacy, P_VISIBLE, ETA_SELF =====")
    import analysis.run_sobol_v04 as sv
    os.environ["AAAPS_OUT"] = "v041_main"
    problem = sv.build_problem()
    X = sobol_sample.sample(problem, 512, calc_second_order=False, scramble=True, seed=sv.SAMPLE_SEED)
    Xd = pd.DataFrame(X, columns=problem["names"])
    out = []
    for s in ("free_market", "targeted_subsidy"):
        new = pd.read_csv(os.path.join(NEW, f"sobol_v04_{s}_indices.csv"))
        old = pd.read_csv(os.path.join(OLD, f"sobol_v04_{s}_indices.csv"))
        for p in ("P_VISIBLE", "ETA_SELF", "ETA"):
            for tag, d in (("v0.4", old), ("v0.4.1", new)):
                r = d[(d.metric == "mean_legitimacy") & (d.parameter == p)].iloc[0]
                out.append(dict(scenario=s, parameter=p, version=tag, S1=r.S1, S1_ci=r.S1_conf, ST=r.ST, ST_ci=r.ST_conf))
    t = pd.DataFrame(out)
    t.to_csv(os.path.join(G5, "legitimacy_indices.csv"), index=False)
    print(t.round(3).to_string(index=False))
    fig, ax = plt.subplots(2, 3, figsize=(13, 7))
    for j, s in enumerate(("free_market", "targeted_subsidy")):
        r = pd.read_csv(os.path.join(NEW, f"sobol_v04_{s}_runs.csv")).sort_values("sample_idx")
        assert len(r) == len(Xd)
        y = r.mean_legitimacy.to_numpy()
        b = r.borrowing_agent_count.to_numpy()
        print(f"\n{s}: mean_legitimacy over {len(y)} points: min {y.min():.3f} p5 {np.percentile(y,5):.3f} median {np.median(y):.3f} "
              f"p95 {np.percentile(y,95):.3f} max {y.max():.3f}")
        print(f"  share <= 0.11 (near initial 0.10): {(y<=0.11).mean():.3f}; share >= 0.95: {(y>=0.95).mean():.3f}; "
              f"share within 0.28-0.32: {((y>=0.28)&(y<=0.32)).mean():.3f}; share > 0.3: {(y>0.3).mean():.3f}")
        print(f"  borrowing_agent_count: zero in {(b==0).mean():.3f} of points, median {np.median(b):.1f}, max {b.max():.0f}; "
              f"corr(borrowing, P_VISIBLE) {np.corrcoef(b, Xd.P_VISIBLE)[0,1]:.3f}, corr(borrowing, mean_legitimacy) {np.corrcoef(b, y)[0,1]:.3f}")
        print(f"  corr(mean_legitimacy, P_VISIBLE) {np.corrcoef(y, Xd.P_VISIBLE)[0,1]:.3f}, ETA_SELF {np.corrcoef(y, Xd.ETA_SELF)[0,1]:.3f}, "
              f"ETA {np.corrcoef(y, Xd.ETA)[0,1]:.3f}")
        # borrowing by P_VISIBLE decile
        dec = pd.qcut(Xd.P_VISIBLE, 10, labels=False)
        print("  borrowing_agent_count mean by P_VISIBLE decile:", np.round(pd.Series(b).groupby(dec).mean().values, 1).tolist())
        print("  mean_legitimacy mean by P_VISIBLE decile:", np.round(pd.Series(y).groupby(dec).mean().values, 3).tolist())
        ax[j, 0].hist(y, bins=50); ax[j, 0].set_title(f"{s}: mean_legitimacy"); ax[j, 0].axvline(0.3, c="r", ls=":")
        ax[j, 1].scatter(Xd.P_VISIBLE, y, s=2, alpha=0.4); ax[j, 1].set_xlabel("P_VISIBLE"); ax[j, 1].set_ylabel("mean_legitimacy")
        ax[j, 2].scatter(Xd.P_VISIBLE, b, s=2, alpha=0.4); ax[j, 2].set_xlabel("P_VISIBLE"); ax[j, 2].set_ylabel("borrowing_agent_count")
    fig.tight_layout(); fig.savefig(os.path.join(G5, "legitimacy_distribution.png"), dpi=110); plt.close(fig)


# ---------------------------------------------------------------- 2. production
PM = ["mean_score", "gini_score", "deadline_miss_count", "relative_ability_decline", "mean_dependency",
      "mean_calibration_error", "mean_legitimacy"]


def production():
    print("\n===== 2. production v0.4.1 vs v0.4 =====")
    rows = []
    for tag, base in (("v0.4.1", NEW), ("v0.4", OLD)):
        d = pd.read_csv(os.path.join(base, "production_v04_runs.csv"))
        b = d[d.scenario == "baseline"].set_index("seed")
        for sc in d.scenario.unique():
            x = d[d.scenario == sc].set_index("seed")
            for m in PM:
                lvl = x[m].mean()
                if sc == "baseline":
                    rows.append(dict(version=tag, scenario=sc, metric=m, mean=lvl, diff=np.nan, lo=np.nan, hi=np.nan))
                else:
                    dd = (x[m] - b[m]).loc[x.index].to_numpy()
                    mm, lo, hi = boot_ci(dd)
                    rows.append(dict(version=tag, scenario=sc, metric=m, mean=lvl, diff=mm, lo=lo, hi=hi))
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(G5, "production_comparison.csv"), index=False)
    for tag in ("v0.4.1", "v0.4"):
        print(f"\n--- {tag}: mean over 100 seeds, and paired difference vs baseline [95% CI] ---")
        s = t[t.version == tag]
        out = []
        for sc in ["baseline", "free_market", "mixed_policy", "targeted_subsidy", "universal_access", "universal_permanent"]:
            r = {"scenario": sc}
            for m in PM:
                q = s[(s.scenario == sc) & (s.metric == m)].iloc[0]
                nd = 1 if m in ("mean_score",) else 3 if m != "deadline_miss_count" else 2
                r[m] = f"{q['mean']:.{nd}f}" + ("" if sc == "baseline" else f" ({q['diff']:+.{nd}f} [{q['lo']:+.{nd}f},{q['hi']:+.{nd}f}])")
            out.append(r)
        print(pd.DataFrame(out).set_index("scenario").T.to_string())


# ---------------------------------------------------------------- 3. isolation
def isolation():
    print("\n===== 3. isolation (exploratory) =====")
    d = pd.read_csv(os.path.join(NEW, "interaction_isolation_runs.csv"))
    metrics = ["mean_dependency", "mean_legitimacy", "mean_calibration_error", "mean_score", "gini_score"]
    full = d[d.condition == "full"].set_index("seed")
    rows = []
    for c in ["full", "no_norms", "no_peer_norms", "no_aspiration", "no_market", "none_net", "zero_interaction"]:
        x = d[d.condition == c].set_index("seed")
        r = {"condition": c}
        for m in metrics:
            if c == "full":
                r[m] = f"{x[m].mean():.4f}"
            else:
                mm, lo, hi = boot_ci((x[m] - full[m]).loc[x.index].to_numpy())
                r[m] = f"{x[m].mean():.4f} ({mm:+.4f} [{lo:+.4f},{hi:+.4f}])"
        rows.append(r)
    print(pd.DataFrame(rows).set_index("condition").to_string())
    pd.DataFrame(rows).to_csv(os.path.join(G5, "isolation_table.csv"), index=False)
    # S statistics (exploratory). self_only does not exist yet: use no_peer_norms (ETA = 0, aspiration and market on) as proxy
    pv = {c: d[d.condition == c].set_index("seed").mean_dependency for c in d.condition.unique()}
    rng = np.random.default_rng(RNG_SEED)
    idx = rng.integers(0, 100, size=(NBOOT, 100))
    def S(num_c):
        D_full, D_zero, D_n = pv["full"].to_numpy(), pv["zero_interaction"].to_numpy(), pv[num_c].loc[pv["full"].index].to_numpy()
        num, den = (D_n - D_zero), (D_full - D_zero)
        b = num[idx].mean(axis=1) / den[idx].mean(axis=1)
        return num.mean() / den.mean(), np.percentile(b, 2.5), np.percentile(b, 97.5), den.mean()
    print("\nH_self statistic S = (D_x - D_zero) / (D_full - D_zero), ratio of paired means, bootstrap over seeds (EXPLORATORY, seeds 0-99).")
    print("The prereg statistic uses self_only, which is not implemented yet. Proxy and complements:")
    res = []
    for c, note in (("no_peer_norms", "proxy for self_only (ETA=0, ETA_SELF kept, aspiration and market on)"),
                    ("no_norms", "all norms off (complement: 1 - S is the share removed by norms)"),
                    ("none_net", "norms, aspiration, market all off, network kept")):
        s, lo, hi, den = S(c)
        res.append(dict(condition=c, S=s, lo=lo, hi=hi, D_full_minus_D_zero=den, note=note))
        print(f"  {c:14s} S = {s:.3f} [{lo:.3f}, {hi:.3f}]   D_full - D_zero = {den:+.4f}   ({note})")
    pd.DataFrame(res).to_csv(os.path.join(G5, "isolation_S_exploratory.csv"), index=False)


# ---------------------------------------------------------------- 4. Morris
def _morris_stats(base: str, lambda_lo: float) -> dict:
    """mu*, sigma for the 8 composite metrics, recomputed from the saved raw runs (3 seeds averaged per design point)."""
    import copy
    from SALib.analyze import morris as morris_analyze
    from SALib.sample import morris as morris_sample
    from analysis.run_morris_screening import PROBLEM
    pr = copy.deepcopy(PROBLEM)
    pr["bounds"][pr["names"].index("LAMBDA_A")][0] = lambda_lo
    raw = pd.read_csv(os.path.join(base, "morris_v04_runs_raw_with_decline.csv"))
    regen = morris_sample.sample(pr, N=20, num_levels=4, seed=42)
    design = raw.sort_values(["design_idx", "seed"]).groupby("design_idx").first()[pr["names"]]
    assert np.allclose(design.values, regen), "design mismatch"
    comp = ["mean_score", "std_score", "gini_score", "mean_dependency", "mean_calibration_error",
            "relative_ability_decline", "deadline_miss_count", "mean_legitimacy"]
    Y = raw.groupby("design_idx")[comp].mean().sort_index()
    out = {}
    for m in comp:
        si = morris_analyze.analyze(pr, regen, Y[m].values, print_to_console=False)
        out[m] = pd.DataFrame({"mu_star": si["mu_star"], "sigma": si["sigma"]}, index=pr["names"])
    return out


def morris():
    print("\n===== 4. Morris =====")
    n = pd.read_csv(os.path.join(NEW, "morris_v04_composite_v2.csv"), index_col=0)
    o = pd.read_csv(os.path.join(OLD, "morris_v04_composite_v2.csv"), index_col=0)
    sn, so = _morris_stats(NEW, 0.0009), _morris_stats(OLD, 0.0007)
    rows = []
    for p in n.index:
        tm = n.loc[p, "top_metric"].replace("_norm", "")
        to = o.loc[p, "top_metric"].replace("_norm", "")
        rows.append(dict(parameter=p, rank_v041=n.loc[p, "rank"], composite_v041=n.loc[p, "composite_max"], top_metric_v041=tm,
                         mu_star_top=sn[tm].loc[p, "mu_star"], sigma_top=sn[tm].loc[p, "sigma"],
                         rank_v04=o.loc[p, "rank"], composite_v04=o.loc[p, "composite_max"], top_metric_v04=to,
                         mu_star_top_v04=so[to].loc[p, "mu_star"], sigma_top_v04=so[to].loc[p, "sigma"]))
    t = pd.DataFrame(rows).sort_values("rank_v041")
    t.to_csv(os.path.join(G5, "morris_table.csv"), index=False)
    print(t.round(3).to_string(index=False))
    print("\nrank 9 to 12 composite (v0.4.1):", n.sort_values("rank").iloc[8:12][["rank", "composite_max"]].round(3).to_dict("index"))
    print("sigma/mu* for ETA_SELF, P_VISIBLE, ETA on mean_dependency (v0.4.1):",
          {p: round(float(sn["mean_dependency"].loc[p, "sigma"] / max(1e-12, sn["mean_dependency"].loc[p, "mu_star"])), 2) for p in ("ETA_SELF", "P_VISIBLE", "ETA")})


# ---------------------------------------------------------------- 5. Sobol
MAIN = ["mean_score", "std_score", "gini_score", "mean_dependency", "mean_calibration_error", "relative_ability_decline",
        "deadline_miss_count", "deadline_miss_rate", "mean_retained_ability", "mean_legitimacy", "borrowing_agent_count",
        "total_shared_seats_lent"]


def sobol():
    print("\n===== 5. Sobol =====")
    allrows = []
    for s in ("free_market", "targeted_subsidy"):
        new = pd.read_csv(os.path.join(NEW, f"sobol_v04_{s}_indices.csv"))
        old = pd.read_csv(os.path.join(OLD, f"sobol_v04_{s}_indices.csv"))
        for m in MAIN:
            a, b = new[new.metric == m], old[old.metric == m]
            if a.degenerate.astype(bool).all():
                allrows.append(dict(scenario=s, metric=m, note="degenerate"))
                continue
            top_a = a.sort_values("ST", ascending=False).iloc[0]
            top_b = b.sort_values("ST", ascending=False).iloc[0]
            second = a.sort_values("ST", ascending=False).iloc[1]
            rel = "UNRELIABLE (borrowing)" if m in ("borrowing_agent_count", "total_shared_seats_lent") else ""
            allrows.append(dict(scenario=s, metric=m, leader_v041=top_a.parameter, S1=top_a.S1, S1_ci=top_a.S1_conf, ST=top_a.ST, ST_ci=top_a.ST_conf,
                                second=second.parameter, second_ST=second.ST, leader_v04=top_b.parameter, ST_v04=top_b.ST, ST_ci_v04=top_b.ST_conf,
                                leader_changed=top_a.parameter != top_b.parameter, sum_S1_v041=a.S1.sum(), sum_S1_v04=b.S1.sum(), note=rel))
    t = pd.DataFrame(allrows)
    t.to_csv(os.path.join(G5, "sobol_leaders.csv"), index=False)
    print(t.round(3).to_string(index=False))
    # full index tables with CI for every parameter and metric
    full = []
    for s in ("free_market", "targeted_subsidy"):
        for tag, base in (("v0.4.1", NEW), ("v0.4", OLD)):
            d = pd.read_csv(os.path.join(base, f"sobol_v04_{s}_indices.csv"))
            d.insert(0, "version", tag); d.insert(0, "scenario", s)
            full.append(d)
    pd.concat(full).to_csv(os.path.join(G5, "sobol_all_indices_both_versions.csv"), index=False)
    # dependency: which of ETA_SELF, ETA, P_VISIBLE matter (relevant to H_self)
    for s in ("free_market", "targeted_subsidy"):
        d = pd.read_csv(os.path.join(NEW, f"sobol_v04_{s}_indices.csv"))
        d = d[d.metric == "mean_dependency"].set_index("parameter")
        print(f"\n{s} mean_dependency v0.4.1 ST (CI) for norm parameters:",
              {p: f"{d.loc[p,'ST']:.3f} ({d.loc[p,'ST_conf']:.3f})" for p in ("ETA_SELF", "ETA", "P_VISIBLE")})


if __name__ == "__main__":
    which = sys.argv[1:] or ["legitimacy", "production", "isolation", "morris", "sobol"]
    for w in which:
        globals()[w]()
