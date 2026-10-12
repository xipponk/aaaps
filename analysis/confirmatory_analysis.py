"""
analysis/confirmatory_analysis.py: confirmatory and exploratory analysis of the v0.4.1 benefit-ability study.

Implements preregistration.md sections 3 to 8 and amendments A1 to A3. Run once on the complete outputs:
    python -m analysis.confirmatory_analysis
Reads outputs/v041_conf/*_runs.csv (override the directory with AAAPS_CONF_DIR), writes results_confirmatory.md next to the
repository root (override with AAAPS_RESULTS_MD) and CSVs to <dir>/results/. It states what the rules give; it does not interpret.
One shared bootstrap index matrix (rng 20261016, 10,000 x 100) is used for every statistic.
"""
from __future__ import annotations

import glob
import hashlib
import os
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.environ.get("AAAPS_CONF_DIR", os.path.join(ROOT, "outputs", "v041_conf"))
MD = os.environ.get("AAAPS_RESULTS_MD", os.path.join(ROOT, "results_confirmatory.md"))
RES = os.path.join(DIR, "results")
os.makedirs(RES, exist_ok=True)

NB, NS = 10_000, 100
IDX = np.random.default_rng(20261016).integers(0, NS, size=(NB, NS))
KS = [1.0, 0.5, 0.0, -0.5, -1.0]
AI_SC = ["free_market", "mixed_policy", "targeted_subsidy", "universal_access", "universal_permanent"]
COPRIMARY = ["universal_permanent", "free_market"]
SESOI = {"gini_score": 0.005, "mean_dependency": 0.02, "mean_calibration_error": 0.02, "relative_ability_decline": 0.02,
         "deadline_miss_count": 0.5}
OUT_Y = ["mean_dependency", "gini_score", "mean_calibration_error", "relative_ability_decline", "deadline_miss_count"]

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


# ------------------------------------------------------------------ data access
def load() -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(DIR, "*_runs.csv")))
    assert files, f"no *_runs.csv in {DIR}"
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    for c, d in (("ablation", "none"), ("benefit_mode", "k"), ("pivot", "P1"), ("disabled", "none"), ("net_label", "default")):
        df[c] = df[c].fillna(d).astype(str)
    return df


def sel(df: pd.DataFrame, **c) -> pd.DataFrame:
    m = np.ones(len(df), bool)
    for k, v in c.items():
        if isinstance(v, float):
            m &= np.isclose(df[k].astype(float), v)
        else:
            m &= (df[k] == v).to_numpy()
    out = df[m].sort_values("seed")
    assert len(out) == NS and out.seed.nunique() == NS, f"selection {c} has {len(out)} rows"
    return out


def vec(df: pd.DataFrame, col: str, **c) -> np.ndarray:
    return sel(df, **c)[col].to_numpy(dtype=float)


def stats(d: np.ndarray) -> dict:
    b = d[IDX].mean(axis=1)
    return dict(mean=float(d.mean()), lo95=float(np.percentile(b, 2.5)), hi95=float(np.percentile(b, 97.5)),
                lo90=float(np.percentile(b, 5)), hi90=float(np.percentile(b, 95)), boot=b)


def fmt(s: dict, nd: int = 4) -> str:
    return f"{s['mean']:.{nd}f} [{s['lo95']:.{nd}f}, {s['hi95']:.{nd}f}]"


def state(s: dict, e1: float, sesoi: float) -> str:
    """Section 5 state of an effect relative to the k = 1 effect e1 (positive-direction effects)."""
    if s["lo95"] > sesoi:
        return "holds" if s["mean"] >= 0.5 * e1 else "attenuated"
    if s["lo90"] > -sesoi and s["hi90"] < sesoi:
        return "vanished"
    if s["hi95"] < -sesoi:
        return "reversed"
    return "indeterminate"


# ------------------------------------------------------------------ E_G
def g_series(df, sc, k, mode="full", **extra):
    return vec(df, "G", block="K", scenario=sc, k=k, mode=mode, **extra)


def eg_arrays(df):
    base = vec(df, "G", block="K", scenario="baseline", mode="full", k=1.0)
    sesoi = 0.05 * float(base.mean())
    E = {(sc, k): g_series(df, sc, k) - base for sc in AI_SC for k in KS}
    return base, sesoi, E


def kstar(vals: np.ndarray):
    """Break-even slope from E_G on the grid KS (descending order 1 ... -1), scanning from k = 1 downward."""
    for i in range(len(KS) - 1):
        a, b = vals[i], vals[i + 1]
        if a == 0:
            return KS[i]
        if a * b < 0:
            return KS[i] + (0 - a) * (KS[i + 1] - KS[i]) / (b - a)
    return np.nan


def family1(df):
    base, sesoi, E = eg_arrays(df)
    w("## CONFIRMATORY")
    w()
    w("### Family 1: co-primary tests on E_G(s, k = 0), Holm over two tests, alpha = 0.05")
    w(f"G(baseline) = {base.mean():.1f} (mean over {NS} seeds). SESOI for E_G = 5% of it = {sesoi:.1f}. Pivot P1.")
    rows, ps = [], {}
    for sc in COPRIMARY:
        s = stats(E[(sc, 0.0)])
        p = float((s["boot"] <= sesoi).mean())
        ps[sc] = p
        rows.append(dict(scenario=sc, E_G_k0=fmt(s, 1), relative=s["mean"] / base.mean(), p_H0=p,
                         TOST_equiv=bool(s["lo90"] > -sesoi and s["hi90"] < sesoi), CI90=f"[{s['lo90']:.1f}, {s['hi90']:.1f}]"))
    order = sorted(ps, key=ps.get)
    rej = {order[0]: ps[order[0]] < 0.025}
    rej[order[1]] = rej[order[0]] and ps[order[1]] < 0.05
    for r in rows:
        r["Holm_reject_H0"] = rej[r["scenario"]]
    w(md_table(pd.DataFrame(rows), 4))
    w("H0: E_G(s, 0) <= +SESOI. Rejecting H0 means the gap widening exceeds the SESOI with the benefit made ability-independent.")
    pd.DataFrame(rows).to_csv(os.path.join(RES, "family1.csv"), index=False)

    w()
    w("### k*, linearity, states and narratives (pre-declared rules of sections 5 to 7)")
    st_rows, narr_state = [], {}
    for sc in AI_SC:
        e1 = stats(E[(sc, 1.0)])
        for k in KS:
            s = stats(E[(sc, k)])
            stt = "present at k = 1 (reference)" if k == 1.0 and e1["lo95"] > sesoi else (
                "not present at k = 1" if k == 1.0 else state(s, e1["mean"], sesoi) if e1["lo95"] > sesoi else "n/a (E_G(s,1) not present)")
            narr_state[(sc, k)] = (s, stt)
            st_rows.append(dict(scenario=sc, k=k, E_G=fmt(s, 1), relative=s["mean"] / base.mean(), state=stt,
                                label="confirmatory-rule" if sc in COPRIMARY else "exploratory"))
    sdf = pd.DataFrame(st_rows)
    sdf.to_csv(os.path.join(RES, "E_G_states.csv"), index=False)
    w(md_table(sdf[sdf.scenario.isin(COPRIMARY)], 4))
    kst_rows = []
    for sc in AI_SC:
        mat = np.stack([stats(E[(sc, k)])["boot"] for k in KS], axis=1)       # NB x 5
        pt = np.array([E[(sc, k)].mean() for k in KS])
        ks_pt = kstar(pt)
        kb = np.array([kstar(r) for r in mat])
        crossed = np.isfinite(kb)
        lin = pt[0] + (pt[-1] - pt[0]) * (np.array(KS) - 1.0) / (-2.0)
        dev = float(np.max(np.abs(pt - lin)))
        if np.isfinite(ks_pt):
            kt = f"{ks_pt:.3f}"
        else:
            kt = ("below -1" if pt[-1] > 0 else "above 1") + f" (E_G at nearest end {pt[-1]:.1f})" if (pt > 0).all() or (pt < 0).all() else "none"
        kst_rows.append(dict(scenario=sc, k_star=kt,
                             CI95_over_crossing_resamples=(f"[{np.percentile(kb[crossed], 2.5):.3f}, {np.percentile(kb[crossed], 97.5):.3f}]"
                                                           if crossed.any() else "n/a"),
                             share_no_crossing=float((~crossed).mean()), max_dev_from_line=dev,
                             linearity_flag=bool(dev > 0.10 * abs(pt[0])) if pt[0] != 0 else False,
                             label="confirmatory-rule" if sc in COPRIMARY else "exploratory"))
    kdf = pd.DataFrame(kst_rows)
    kdf.to_csv(os.path.join(RES, "k_star.csv"), index=False)
    w()
    w(md_table(kdf, 3))
    present1 = all(stats(E[(sc, 1.0)])["lo95"] > sesoi for sc in COPRIMARY)
    w()
    if not present1:
        w("E_G(s, 1) is NOT present for both co-primary scenarios: per section 5 the claim 'AI widens the gap' is reported as absent in "
          "v0.4.1 and the narrative rules are not applied.")
        narr = "not applied"
    else:
        n1 = all(narr_state[(sc, 0.0)][1] in ("vanished", "reversed") for sc in COPRIMARY)
        n2 = all(stats(E[(sc, k)])["lo95"] > sesoi for sc in COPRIMARY for k in (1.0, 0.5, 0.0, -0.5))
        narr = "N1 circularity confirmed" if n1 else "N2 robust" if n2 else "N3 partly emergent"
        w(f"Narrative by the pre-declared numeric rules: **{narr}** (N1 test: {n1}; N2 test: {n2}).")
    w()
    return base, sesoi, E


# ------------------------------------------------------------------ interaction clause with decomposition
def interaction(df, sesoi_g):
    w("### Interaction clause (section 7 with the A3 decomposition): full - zero = social + individual")
    w("social = full - self_only; individual = self_only - zero_interaction. driven: CI95 beyond +/-SESOI; null: CI90 inside "
      "(-SESOI, +SESOI); else indeterminate. Pivot P1. Full table for all five scenarios: interaction_decomposition.csv.")
    rows = []
    ycols = OUT_Y + ["G"]
    for sc in AI_SC:
        for k in KS:
            for y in ycols:
                se = sesoi_g if y == "G" else SESOI[y]
                f = vec(df, y, block="K", scenario=sc, k=k, mode="full")
                s_ = vec(df, y, block="K", scenario=sc, k=k, mode="self_only")
                z = vec(df, y, block="K", scenario=sc, k=k, mode="zero_interaction")
                r = dict(scenario=sc, k=k, outcome=y, sesoi=se)
                for name, d in (("full_minus_zero", f - z), ("social", f - s_), ("individual", s_ - z)):
                    st = stats(d)
                    cls = "driven" if (st["lo95"] > se or st["hi95"] < -se) else "null" if (st["lo90"] > -se and st["hi90"] < se) else "indeterminate"
                    r[name] = f"{st['mean']:.4f} [{st['lo95']:.4f}, {st['hi95']:.4f}]"
                    r[name + "_class"] = cls
                fz = stats(f - z)
                if r["full_minus_zero_class"] == "driven" and abs(fz["mean"]) > 0:
                    r["individual_share"] = float(((s_ - z).mean()) / (f - z).mean())
                    r["social_share"] = float(((f - s_).mean()) / (f - z).mean())
                rows.append(r)
    d = pd.DataFrame(rows)
    d.to_csv(os.path.join(RES, "interaction_decomposition.csv"), index=False)
    sub = d[d.scenario.isin(COPRIMARY) & d.k.isin([1.0, 0.0])][
        ["scenario", "k", "outcome", "full_minus_zero", "full_minus_zero_class", "social", "social_class", "individual", "individual_class", "individual_share"]]
    w(md_table(sub, 3))
    w()


# ------------------------------------------------------------------ H_self
def hself(df):
    w("### Family 2: H_self (free_market, k = 1, mean_dependency, alpha = 0.05)")
    f = vec(df, "mean_dependency", block="K", scenario="free_market", k=1.0, mode="full")
    s_ = vec(df, "mean_dependency", block="K", scenario="free_market", k=1.0, mode="self_only")
    z = vec(df, "mean_dependency", block="K", scenario="free_market", k=1.0, mode="zero_interaction")
    num, den = (s_ - z), (f - z)
    bn, bd = num[IDX].mean(axis=1), den[IDX].mean(axis=1)
    S = bn / bd
    S_pt = float(num.mean() / den.mean())
    lo, hi = float(np.percentile(S, 2.5)), float(np.percentile(S, 97.5))
    dst = stats(den)
    beyond = bool(dst["lo95"] > 0.02 or dst["hi95"] < -0.02)
    verdict = "SUPPORTED" if (lo > 0.5 and beyond) else "REFUTED" if (hi < 0.5 and beyond) else "INCONCLUSIVE"
    w(f"D_full = {f.mean():.4f}, D_self = {s_.mean():.4f}, D_zero = {z.mean():.4f}. D_full - D_zero = {fmt(dst)} (beyond SESOI 0.02: {beyond}).")
    w(f"S = (D_self - D_zero)/(D_full - D_zero) = {S_pt:.3f}, 95% CI [{lo:.3f}, {hi:.3f}]. Verdict by the preregistered rule: **{verdict}**.")
    w(f"Decomposition: individual = {fmt(stats(num))}, social = {fmt(stats(f - s_))}.")
    w()
    pd.DataFrame([dict(S=S_pt, lo=lo, hi=hi, D_full=f.mean(), D_self=s_.mean(), D_zero=z.mean(), beyond_sesoi=beyond,
                       verdict=verdict)]).to_csv(os.path.join(RES, "h_self.csv"), index=False)


# ------------------------------------------------------------------ network sweep
LEVELS = {"p_within": ([0.10, 0.14, 0.18, 0.25, 0.35], 0.18), "p_between": ([0.005, 0.015, 0.03, 0.06, 0.12], 0.015),
          "h_ses": ([0.0, 0.2, 0.4, 0.6, 0.8], 0.2), "h_ability": ([0.0, 0.25, 0.5, 0.75, 1.0], 0.25)}


def netsel(df, disabled, param=None, level=None):
    n = df[(df.block == "NET")]
    if param is None:
        return sel(n, scenario="free_market", disabled=disabled, net_label="default")
    return sel(n, scenario="free_market", disabled=disabled, net_label=f"{param}={level:g}")


def network(df):
    w("### Network sweep corroboration of H_self (free_market, k = 1, one-at-a-time, 17 points)")
    base_full = netsel(df, "none").mean_dependency.to_numpy(float)
    rows = []
    for p, (lv, dflt) in LEVELS.items():
        for l in lv:
            if np.isclose(l, dflt):
                continue
            d = netsel(df, "none", p, l).mean_dependency.to_numpy(float) - base_full
            st = stats(d)
            p1, p2 = float((st["boot"] >= 0.02).mean()), float((st["boot"] <= -0.02).mean())
            rows.append(dict(parameter=p, level=l, diff=st["mean"], lo95=st["lo95"], hi95=st["hi95"], tost_p=max(p1, p2),
                             beyond_0p04=bool(st["lo95"] > 0.04 or st["hi95"] < -0.04)))
    t = pd.DataFrame(rows).sort_values("tost_p").reset_index(drop=True)
    m = len(t)
    t["holm_alpha"] = [0.05 / (m - i) for i in range(m)]
    ok, passed = True, []
    for i, r in t.iterrows():
        ok = ok and (r.tost_p < r.holm_alpha)
        passed.append(ok)
    t["equivalent_holm"] = passed
    all_equiv = bool(t.equivalent_holm.all())
    any_beyond = bool(t.beyond_0p04.any())
    verdict = "SUPPORTS H_self" if all_equiv else "CONTRADICTS H_self" if any_beyond else "INCONCLUSIVE"
    t.to_csv(os.path.join(RES, "network_contrasts_full.csv"), index=False)
    w(md_table(t.sort_values(["parameter", "level"]), 4))
    w(f"Rule: supports if all 16 contrasts are equivalent to 0 at SESOI 0.02 (TOST, Holm over 16); contradicts if any full contrast has "
      f"95% CI beyond +/-0.04. Result: **{verdict}** (all equivalent: {all_equiv}; any beyond 0.04: {any_beyond}).")
    nn_base = netsel(df, "norms").mean_dependency.to_numpy(float)
    nn = []
    for p, (lv, dflt) in LEVELS.items():
        for l in lv:
            if np.isclose(l, dflt):
                continue
            st = stats(netsel(df, "norms", p, l).mean_dependency.to_numpy(float) - nn_base)
            nn.append(dict(parameter=p, level=l, diff=st["mean"], lo95=st["lo95"], hi95=st["hi95"]))
    w()
    w("no_norms check (dependency contrasts against the no_norms default point; expected flat):")
    w(md_table(pd.DataFrame(nn), 4))
    w()


# ------------------------------------------------------------------ exploratory
def exploratory(df, base, sesoi, E):
    w("## EXPLORATORY (no multiplicity control)")
    w()
    w("### Levels by scenario and k (pivot P1, mode full): means over 100 seeds")
    rows = []
    for sc in ["baseline"] + AI_SC:
        for k in (KS if sc != "baseline" else [1.0]):
            sub = sel(df, block="K", scenario=sc, k=k, mode="full")
            rows.append(dict(scenario=sc, k=k, score=sub.mean_score.mean(), G=sub.G.mean(), gini=sub.gini_score.mean(),
                             dependency=sub.mean_dependency.mean(), calib=sub.mean_calibration_error.mean(),
                             decline=sub.relative_ability_decline.mean(), misses=sub.deadline_miss_count.mean(),
                             g_mean_960=sub.g_mean_s960.mean(), clips=sub.clip_count.mean()))
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(RES, "levels_full.csv"), index=False)
    w(md_table(t, 4))
    w()
    w("### Tercile outcomes at k = 1, mode full (low, mid, high base ability)")
    rows = []
    for sc in ["baseline"] + AI_SC:
        sub = sel(df, block="K", scenario=sc, k=1.0, mode="full")
        rows.append(dict(scenario=sc, **{f"score_t{i}": sub[f"score_t{i}"].mean() for i in (1, 2, 3)},
                         **{f"dep_t{i}": sub[f"dep_t{i}"].mean() for i in (1, 2, 3)},
                         **{f"decl_t{i}": sub[f"decl_t{i}"].mean() for i in (1, 2, 3)}))
    w(md_table(pd.DataFrame(rows), 4))
    w()
    # P2 sensitivity
    w("### P2 (level-matched pivot) vs P1, E_G, mode full")
    rows = []
    for sc in COPRIMARY:
        for k in (0.0, -1.0):
            p1 = stats(E[(sc, k)])
            p2d = vec(df, "G", block="P2", scenario=sc, k=k, mode="full", pivot="P2") - base
            p2 = stats(p2d)
            sub = sel(df, block="P2", scenario=sc, k=k, mode="full", pivot="P2")
            rows.append(dict(scenario=sc, k=k, E_G_P1=fmt(p1, 1), E_G_P2=fmt(p2, 1), mean_pivot_P2=sub.pivot_value.mean(),
                             mean_pivot_P1=sel(df, block="K", scenario=sc, k=k, mode="full").pivot_value.mean()))
    w(md_table(pd.DataFrame(rows), 4))
    w()
    # ablations
    w("### Channel ablations at k = 1 (E_G vs baseline, dependency, decline)")
    rows = []
    for ab in ("quality_only", "speed_only"):
        for sc in COPRIMARY:
            for mode in ("full", "zero_interaction"):
                sub = sel(df, block="ABL", scenario=sc, ablation=ab, mode=mode, k=1.0)
                st = stats(sub.G.to_numpy(float) - base)
                rows.append(dict(ablation=ab, scenario=sc, mode=mode, E_G=fmt(st, 1), dependency=sub.mean_dependency.mean(),
                                 decline=sub.relative_ability_decline.mean(), score=sub.mean_score.mean()))
    w(md_table(pd.DataFrame(rows), 4))
    w()
    # C1
    w("### C1 calibration complementarity (E_G vs baseline; mean g_c at step 960)")
    rows = []
    for sc in AI_SC:
        for mode in ("full", "zero_interaction"):
            sub = sel(df, block="C1", scenario=sc, mode=mode, benefit_mode="C1")
            st = stats(sub.G.to_numpy(float) - base)
            rows.append(dict(scenario=sc, mode=mode, E_G=fmt(st, 1), g_c_960=sub.g_mean_s960.mean(), score=sub.mean_score.mean()))
    w(md_table(pd.DataFrame(rows), 4))
    w("E_G under C1 is to be read within a scenario only (A1/A2).")
    w()
    # density
    w("### Density-controlled network sweep (expected degree 12; free_market, k = 1; dependency, gini, G)")
    rows = []
    dens = df[(df.block == "NET") & df.net_label.str.startswith("dens=")]
    for lab in sorted(dens.net_label.unique()):
        for dis in ("none", "norms"):
            sub = sel(df, block="NET", net_label=lab, disabled=dis, scenario="free_market")
            rows.append(dict(point=lab, condition="full" if dis == "none" else "no_norms", dependency=sub.mean_dependency.mean(),
                             gini=sub.gini_score.mean(), G=sub.G.mean(), within_share=sub.net_within_section_share.mean(),
                             k_bar=sub.net_k_bar.mean()))
    w(md_table(pd.DataFrame(rows), 4))
    w()
    # network sweep non-dependency outcomes
    w("### Network sweep, full: gini and G ranges over levels (mean over seeds)")
    rows = []
    for p, (lv, dflt) in LEVELS.items():
        for l in lv:
            sub = netsel(df, "none") if np.isclose(l, dflt) else netsel(df, "none", p, l)
            rows.append(dict(parameter=p, level=l, dependency=sub.mean_dependency.mean(), gini=sub.gini_score.mean(), G=sub.G.mean(),
                             calib=sub.mean_calibration_error.mean(), within_share=sub.net_within_section_share.mean()))
    w(md_table(pd.DataFrame(rows), 4))
    w()
    # L0
    w("### Sensitivity to the initial legitimacy L0 (free_market, k = 1)")
    rows = []
    for l0 in (0.05, 0.10, 0.20, 0.30):
        if np.isclose(l0, 0.10):
            get = lambda mode: vec(df, "mean_dependency", block="K", scenario="free_market", k=1.0, mode=mode)
        else:
            get = lambda mode, l0=l0: vec(df, "mean_dependency", block="L0", scenario="free_market", L0=l0, mode=mode, k=1.0)
        f, s_, z = get("full"), get("self_only"), get("zero_interaction")
        num, den = s_ - z, f - z
        S = num[IDX].mean(axis=1) / den[IDX].mean(axis=1)
        rows.append(dict(L0=l0, D_full=f.mean(), D_self=s_.mean(), D_zero=z.mean(), S=float(num.mean() / den.mean()),
                         S_lo95=float(np.percentile(S, 2.5)), S_hi95=float(np.percentile(S, 97.5))))
    w(md_table(pd.DataFrame(rows), 4))
    w()
    # diagnostics
    w("### Diagnostics")
    rows = []
    for sc in AI_SC:
        for k in KS:
            sub = sel(df, block="K", scenario=sc, k=k, mode="full")
            rows.append(dict(scenario=sc, k=k, **{f"g_s{t}": sub[f"g_mean_s{t}"].mean() for t in (1, 480, 960)},
                             clip_count=sub.clip_count.mean(), decline=sub.relative_ability_decline.mean()))
    w(md_table(pd.DataFrame(rows), 4))
    net = df[["net_attempts", "net_k_bar", "net_within_section_share"]].describe().loc[["min", "mean", "max"]]
    w()
    w("Realised network over all runs with a network (min / mean / max):")
    w(md_table(net.reset_index(), 3))
    w()


def main():
    df = load()
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    sha = hashlib.sha256(open(__file__, "rb").read()).hexdigest()
    w("# results_confirmatory.md")
    w()
    w(f"Generated by analysis/confirmatory_analysis.py (sha256 {sha}) at git {git}. Input directory: {os.path.abspath(DIR)}.")
    w(f"Runs: {len(df)} rows; by block: {df.block.value_counts().to_dict()}. Seeds {int(df.seed.min())}-{int(df.seed.max())}. "
      "Bootstrap: 10,000 resamples, one shared index matrix, rng 20261016. This file states what the preregistered rules return and "
      "contains no interpretation beyond them.")
    w()
    base, sesoi, E = family1(df)
    interaction(df, sesoi)
    hself(df)
    network(df)
    exploratory(df, base, sesoi, E)
    with open(MD, "w") as f:
        f.write("\n".join(LINES) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    main()
