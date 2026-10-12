"""
analysis/clamp_share.py: share of agents whose retained ability sits at ABILITY_CLAMP[0] at step 960, universal_permanent,
for several LAMBDA_A, 5 calibration seeds each. Also the share among agents whose a_base is above the clamp.
Output: outputs/v041_ext/clamp_share.csv
"""
from __future__ import annotations

import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from analysis.param_guard import reset_params  # noqa: E402
from analysis.run_production import _simulate  # noqa: E402
import config.params as P  # noqa: E402

LAMBDAS = [0.0009, 0.00248, 0.0059, 0.012]
SEEDS = list(range(1000, 1005))


def _job(a):
    lam, seed = a
    reset_params()
    P.LAMBDA_A = lam
    m = _simulate("universal_permanent", seed)
    ar = np.array([x.retained_ability for x in m.agents])
    ab = np.array([x.base_ability for x in m.agents])
    lo = P.ABILITY_CLAMP[0]
    at = ar <= lo + 1e-9
    return dict(lambda_a=lam, seed=seed, share_at_clamp=float(at.mean()),
                share_at_clamp_given_abase_above=float(at[ab > lo + 1e-9].mean()) if (ab > lo + 1e-9).any() else 0.0,
                share_abase_at_clamp=float((ab <= lo + 1e-9).mean()), mean_ar_over_abase=float(ar.mean() / ab.mean()),
                min_ar=float(ar.min()))


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=14) as ex:
        df = pd.DataFrame(list(ex.map(_job, [(l, s) for l in LAMBDAS for s in SEEDS])))
    os.makedirs(os.path.join(ROOT, "outputs", "v041_ext"), exist_ok=True)
    out = os.path.join(ROOT, "outputs", "v041_ext", "clamp_share.csv")
    df.to_csv(out, index=False)
    print(out, df.shape)
    print(df.groupby("lambda_a").mean(numeric_only=True).drop(columns="seed").round(4).to_string())
