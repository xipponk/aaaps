"""
analysis/d1_reference.py (EXPLORATORY, written after Gate 7; reads saved D1 data only, no simulation).
Reference variances of the local fraction that match each definition in model.py:
  raw   X_j ~ Bernoulli(p_t) per neighbour               ref_raw = mean_i p(1-p)/d_i
  obs   X_j ~ Bernoulli(P_VISIBLE * p_t) per neighbour   ref_obs = mean_i q(1-q)/d_i, q = P_VISIBLE * p_t
with d_i the number of neighbours (the denominator of the model is the total tie weight over all neighbours, visible or not) and p_t the
global share of agents with AI use in the snapshot. The model weights neighbours by tie strength ~ Beta(a, b); the D1 files do not hold the
weights, so the weighted references are approximated by the factor sum(w^2)/(sum w)^2 ~ (1 + CV_w^2)/d (CV_w^2 = 1/(a+b+1)... computed below).
Usage: python -m analysis.d1_reference   (writes outputs/v041_a4/results/d1_reference.csv and .md)
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

files = sorted(glob.glob(os.path.join(DIR, "D1_seed*.npz")))
rows = []
per = {k: [] for k in ("p", "var_obs", "var_raw", "ref_obs", "ref_raw")}
for f in files:
    z = np.load(f)
    keep = z["deg"] > 0
    d, g, pv = z["deg"][keep], z["glob"], float(z["p_visible"])
    q = pv * g
    per["p"].append(g)
    per["var_obs"].append(np.nanvar(z["obs"][:, keep], axis=1))
    per["var_raw"].append(np.nanvar(z["raw"][:, keep], axis=1))
    per["ref_obs"].append(np.array([np.mean(x * (1 - x) / d) for x in q]))
    per["ref_raw"].append(np.array([np.mean(x * (1 - x) / d) for x in g]))
A = {k: np.mean(np.array(v), axis=0) for k, v in per.items()}
for lo, hi in [(1 + 120 * i, 120 * (i + 1)) for i in range(8)] + [(1, 960)]:
    s = slice(lo - 1, hi)
    r = {k: A[k][s].mean() for k in A}
    rows.append(dict(steps=f"{lo}-{hi}", p=r["p"], var_raw=r["var_raw"], ref_raw_unweighted=r["ref_raw"], ref_raw_weighted_approx=FACTOR * r["ref_raw"],
                     ratio_raw_to_unweighted=r["var_raw"] / r["ref_raw"], ratio_raw_to_weighted=r["var_raw"] / (FACTOR * r["ref_raw"]),
                     var_obs=r["var_obs"], ref_obs_unweighted=r["ref_obs"], ref_obs_weighted_approx=FACTOR * r["ref_obs"],
                     ratio_obs_to_unweighted=r["var_obs"] / r["ref_obs"], ratio_obs_to_weighted=r["var_obs"] / (FACTOR * r["ref_obs"])))
t = pd.DataFrame(rows)
t.to_csv(os.path.join(DIR, "results", "d1_reference.csv"), index=False)
out = [f"D1 reference variances (EXPLORATORY), seeds {[os.path.basename(f)[7:-4] for f in files]}, P_VISIBLE = {P.P_VISIBLE}, "
       f"tie strength Beta({a}, {b}): mean {mean_w:.3f}, variance {var_w:.4f}, approximate weighting factor 1 + CV^2 = {FACTOR:.3f}.",
       "| " + " | ".join(t.columns) + " |", "|" + "|".join("---" for _ in t.columns) + "|"]
for _, r in t.iterrows():
    out.append("| " + " | ".join(r[c] if isinstance(r[c], str) else f"{r[c]:.5f}" for c in t.columns) + " |")
open(os.path.join(DIR, "results", "d1_reference.md"), "w").write("\n".join(out) + "\n")
print("\n".join(out))
