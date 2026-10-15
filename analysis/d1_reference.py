"""
analysis/d1_reference.py (EXPLORATORY, written after Gate 7; reads saved D1 data only, no simulation).
Reference variances of the local fraction that match each definition in model.py:
  raw   X_j ~ Bernoulli(p_t) per neighbour               ref_raw = mean_i p(1-p)/d_i
  obs   X_j ~ Bernoulli(P_VISIBLE * p_t) per neighbour   ref_obs = mean_i q(1-q)/d_i, q = P_VISIBLE * p_t
with d_i the number of neighbours (the denominator of the model is the total tie weight over all neighbours, visible or not) and p_t the
global share of agents with AI use in the snapshot. The model weights neighbours by tie strength ~ Beta(a, b); the D1 files do not hold the
weights, so the weighted references are approximated by the factor sum(w^2)/(sum w)^2 ~ (1 + CV_w^2)/d (CV_w^2 = 1/(a+b+1)... computed below).

Exact weighting (added after Gate 8, still exploratory): the model of each D1 seed (8100-8104) is CONSTRUCTED again with the D1 settings (free_market,
k = 1, R3; no step is run) to read the tie strengths of the static network, and c_i = sum(w^2)/(sum w)^2 is computed per agent. The reference is then
ref_exact = mean_i q(1-q) c_i (q = p for raw, q = P_VISIBLE * p for obs). The construction is checked against the saved degree vector.
Usage: python -m analysis.d1_reference   (writes outputs/v041_a4/results/d1_reference.csv, d1_reference_steps.csv and .md)
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import config.params as P  # noqa: E402

DIR = os.path.join(ROOT, "outputs", "v041_a4")
a, b = P.TIE_STRENGTH_BETA_A, P.TIE_STRENGTH_BETA_B
mean_w, var_w = a / (a + b), a * b / ((a + b) ** 2 * (a + b + 1))
FACTOR = 1.0 + var_w / mean_w ** 2

from analysis.param_guard import reset_params  # noqa: E402
from model.model import AaapsModel  # noqa: E402


def exact_c(seed, deg_saved):
    """sum(w^2)/(sum w)^2 per agent (sorted by unique_id) from the constructed, never stepped, model."""
    reset_params()
    m = AaapsModel(n_students=P.N_STUDENTS, scenario="free_market", seed=seed)
    G = m.social_network
    order = sorted(G.nodes)
    deg = np.array([G.degree(u) for u in order])
    assert np.array_equal(deg, deg_saved), f"seed {seed}: rebuilt degrees differ from the saved D1 degrees"
    c = np.full(len(order), np.nan)
    for i, u in enumerate(order):
        w = np.array([G[u][v]["tie_strength"] for v in G.neighbors(u)])
        if len(w):
            c[i] = (w ** 2).sum() / w.sum() ** 2
    reset_params()
    return c, deg


files = sorted(glob.glob(os.path.join(DIR, "D1_seed*.npz")))
rows = []
per = {k: [] for k in ("p", "var_obs", "var_raw", "ref_obs", "ref_raw", "ex_obs", "ex_raw")}
CI, DEG = {}, {}
for f in files:
    z = np.load(f)
    seed = int(os.path.basename(f)[7:-4])
    c_all, _ = exact_c(seed, z["deg"])
    CI[seed], DEG[seed] = c_all, z["deg"]
    keep = z["deg"] > 0
    c = c_all[keep]
    d, g, pv = z["deg"][keep], z["glob"], float(z["p_visible"])
    q = pv * g
    per["p"].append(g)
    per["var_obs"].append(np.nanvar(z["obs"][:, keep], axis=1))
    per["var_raw"].append(np.nanvar(z["raw"][:, keep], axis=1))
    per["ref_obs"].append(np.array([np.mean(x * (1 - x) / d) for x in q]))
    per["ref_raw"].append(np.array([np.mean(x * (1 - x) / d) for x in g]))
    per["ex_obs"].append(np.array([np.mean(x * (1 - x) * c) for x in q]))
    per["ex_raw"].append(np.array([np.mean(x * (1 - x) * c) for x in g]))
A = {k: np.mean(np.array(v), axis=0) for k, v in per.items()}
pd.DataFrame(dict(step=np.arange(1, len(A["p"]) + 1), p=A["p"], var_raw=A["var_raw"], ref_raw_exact=A["ex_raw"], ref_raw_unweighted=A["ref_raw"],
                  ratio_raw_to_exact=A["var_raw"] / A["ex_raw"], var_obs=A["var_obs"], ref_obs_exact=A["ex_obs"], ref_obs_unweighted=A["ref_obs"],
                  ratio_obs_to_exact=A["var_obs"] / A["ex_obs"])).to_csv(os.path.join(DIR, "results", "d1_reference_steps.csv"), index=False)
dc = np.concatenate([CI[s_][DEG[s_] > 0] * DEG[s_][DEG[s_] > 0] for s_ in CI])
for lo, hi in [(1 + 120 * i, 120 * (i + 1)) for i in range(8)] + [(1, 960)]:
    s = slice(lo - 1, hi)
    r = {k: A[k][s].mean() for k in A}
    rows.append(dict(steps=f"{lo}-{hi}", p=r["p"], var_raw=r["var_raw"], ref_raw_unweighted=r["ref_raw"], ref_raw_weighted_approx=FACTOR * r["ref_raw"],
                     ratio_raw_to_unweighted=r["var_raw"] / r["ref_raw"], ratio_raw_to_weighted=r["var_raw"] / (FACTOR * r["ref_raw"]),
                     var_obs=r["var_obs"], ref_obs_unweighted=r["ref_obs"], ref_obs_weighted_approx=FACTOR * r["ref_obs"], ref_raw_exact=r["ex_raw"], ref_obs_exact=r["ex_obs"],
                     ratio_raw_to_exact=r["var_raw"] / r["ex_raw"], ratio_obs_to_exact=r["var_obs"] / r["ex_obs"],
                     ratio_obs_to_unweighted=r["var_obs"] / r["ref_obs"], ratio_obs_to_weighted=r["var_obs"] / (FACTOR * r["ref_obs"])))
t = pd.DataFrame(rows)
t.to_csv(os.path.join(DIR, "results", "d1_reference.csv"), index=False)
out = [f"D1 reference variances (EXPLORATORY), seeds {[os.path.basename(f)[7:-4] for f in files]}, P_VISIBLE = {P.P_VISIBLE}, "
       f"tie strength Beta({a}, {b}): mean {mean_w:.3f}, variance {var_w:.4f}, approximate weighting factor 1 + CV^2 = {FACTOR:.3f}; "
       f"exact mean over agents of d_i * sum(w^2)/(sum w)^2 = {dc.mean():.4f} (min {dc.min():.3f}, max {dc.max():.3f}).",
       "| " + " | ".join(t.columns) + " |", "|" + "|".join("---" for _ in t.columns) + "|"]
for _, r in t.iterrows():
    out.append("| " + " | ".join(r[c] if isinstance(r[c], str) else f"{r[c]:.5f}" for c in t.columns) + " |")
open(os.path.join(DIR, "results", "d1_reference.md"), "w").write("\n".join(out) + "\n")
print("\n".join(out))
