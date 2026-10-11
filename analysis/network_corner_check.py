"""
analysis/network_corner_check.py: graph-only check (no stepping) of connectivity failure at the corners of the Morris
network box under the v0.4.1 generator. Reports the per-attempt disconnect rate and the number of RuntimeErrors
(50 failed attempts) over many seeds. Output: outputs/v041/network_corner_check.csv
"""
from __future__ import annotations

import itertools
import os
import sys
import warnings

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from analysis.param_guard import reset_params  # noqa: E402
import config.params as P  # noqa: E402
from model.model import AaapsModel  # noqa: E402

N_SEEDS = 500


def main() -> None:
    rows = []
    for pw, pb, hs, ha in itertools.product((0.12, 0.25), (0.005, 0.03), (0.10, 0.35), (0.15, 0.40)):
        rej = att = fails = 0
        for seed in range(N_SEEDS):
            reset_params()
            P.SBM_P_WITHIN, P.SBM_P_BETWEEN, P.HOMOPHILY_SES, P.HOMOPHILY_ABILITY = pw, pb, hs, ha
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    m = AaapsModel(n_students=240, scenario="free_market", seed=seed)
                rej += m.network_info["disconnected_rejects"]
                att += m.network_info["attempts"]
            except RuntimeError:
                fails += 1
                rej += 50
                att += 50
        p = rej / att
        rows.append(dict(p_within=pw, p_between=pb, h_ses=hs, h_ability=ha, exp_degree=39 * pw + 200 * pb,
                         per_attempt_disconnect=p, implied_fail_50=p ** 50, runtime_errors=fails, seeds=N_SEEDS))
    reset_params()
    df = pd.DataFrame(rows)
    os.makedirs(os.path.join(ROOT, "outputs", "v041"), exist_ok=True)
    out = os.path.join(ROOT, "outputs", "v041", "network_corner_check.csv")
    df.to_csv(out, index=False)
    print(out, df.shape)
    print(df.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
