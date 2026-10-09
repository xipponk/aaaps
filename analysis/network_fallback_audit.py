"""
analysis/network_fallback_audit.py: how often does model/network.py fall back to Erdos-Renyi?

Analysis only: rebuilds the model constructor (agents + network, no stepping, no simulation) for the
(seed, parameter) pairs of each saved experiment and records, per network, the number of SBM attempts,
how many attempts were rejected as disconnected, whether the Erdos-Renyi fallback fired, the realized mean
degree and the within-section share of edges. Detection wraps networkx calls from the audit process only;
model/ is not modified.

Sources: production seeds 0-99 (default params, shared by all 6 scenarios), isolation seeds 0-99, calibration
seeds 1000-1029, Morris design points x seeds 2000-2002 (parameter columns of morris_v04_runs_raw.csv),
Sobol points regenerated with the same sampler and seed as analysis/run_sobol_v04.py (free_market and
targeted_subsidy share the same points and seeds, so one set).
Usage: python -m analysis.network_fallback_audit [smoke]
"""

from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import networkx as nx
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config.params as P
from model import network as netmod
from model.model import AaapsModel

OUT = os.path.join(ROOT, "outputs", "phase2")
PARAM_COLS = ["ALPHA_D", "DELTA_D", "BETA_C", "GAMMA_C", "RHO_RATIO", "LAMBDA_A", "ETA", "ETA_SELF", "KAPPA",
              "URGENCY_WEIGHT", "ASPIRATION_GAP_WEIGHT", "BORROW_SUBSTITUTION", "ABILITY_MEAN", "ABILITY_STD",
              "CONFORMITY_BETA_B", "PROSOCIALITY_BETA_A", "SBM_P_WITHIN", "SBM_P_BETWEEN", "HOMOPHILY_SES",
              "HOMOPHILY_ABILITY", "P_VISIBLE", "PROCESSING_DIFFICULTY_FACTOR"]


DEFAULTS = {c: getattr(P, c) for c in PARAM_COLS + ["TARGET_K_BAR_RANGE"]}  # captured at import, before any worker mutates P


def _audit_one(job: tuple) -> dict:
    source, key, seed, params = job
    # Workers are reused across jobs, so reset every audited parameter before applying this job's values.
    for k, v in DEFAULTS.items():
        setattr(P, k, v)
    for k, v in params.items():
        setattr(P, k, tuple(v) if k == "TARGET_K_BAR_RANGE" else float(v))
    log = {"sbm": 0, "conn": [], "er": 0}
    orig = (nx.stochastic_block_model, nx.is_connected, nx.erdos_renyi_graph)

    def sbm(*a, **k):
        log["sbm"] += 1
        return orig[0](*a, **k)

    def conn(G, *a, **k):
        r = orig[1](G, *a, **k)
        log["conn"].append(bool(r))
        return r

    def er(*a, **k):
        log["er"] += 1
        return orig[2](*a, **k)

    nx.stochastic_block_model, nx.is_connected, nx.erdos_renyi_graph = sbm, conn, er
    try:
        m = AaapsModel(n_students=240, scenario="free_market", seed=int(seed))
    finally:
        nx.stochastic_block_model, nx.is_connected, nx.erdos_renyi_graph = orig
    G = m.social_network
    sec = {a.unique_id: a.section_id for a in m.agents}
    edges = list(G.edges())
    within = float(np.mean([sec[u] == sec[v] for u, v in edges])) if edges else float("nan")
    fb = log["er"] > 0
    import hashlib
    ehash = hashlib.sha1(repr(sorted(tuple(sorted(e)) for e in edges)).encode()).hexdigest()[:12]
    attempts = log["sbm"]
    disc = sum(1 for c in log["conn"][:attempts] if not c)
    return dict(source=source, key=key, seed=seed, attempts=attempts, disconnected_rejects=disc,
                kbar_rejects=(attempts - disc if fb else attempts - 1 - disc), fallback=fb,
                k_bar=2 * len(edges) / 240, within_share=within, edge_hash=ehash)


def jobs(smoke: bool) -> list[tuple]:
    J = []
    for s in range(100):
        J.append(("production_isolation", "default", s, {}))
    for s in range(1000, 1030):
        J.append(("calibration", "default", s, {}))
    mo = pd.read_csv(os.path.join(OUT, "morris_v04_runs_raw.csv"))
    for _, r in mo.iterrows():
        J.append(("morris", int(r.design_idx), int(r.seed), {c: r[c] for c in PARAM_COLS if c in mo.columns}))
    from SALib.sample import sobol as sobol_sample
    from analysis.run_sobol_v04 import build_problem, SAMPLE_SEED
    prob = build_problem()
    X = sobol_sample.sample(prob, 512, calc_second_order=False, scramble=True, seed=SAMPLE_SEED)
    sr = pd.read_csv(os.path.join(OUT, "sobol_v04_free_market_runs.csv"), usecols=["sample_idx", "seed"])
    print("sobol X shape", X.shape, "runs csv", sr.shape, "seeds", sorted(sr.seed.unique()))
    for _, r in sr.iterrows():
        J.append(("sobol", int(r.sample_idx), int(r.seed), dict(zip(prob["names"], X[int(r.sample_idx)]))))
    if smoke:
        J = [j for j in J if j[0] in ("production_isolation", "calibration")][:6] + \
            [j for j in J if j[0] == "morris"][:6] + [j for j in J if j[0] == "sobol"][:4]
    return J


def main() -> None:
    smoke = len(sys.argv) > 1 and sys.argv[1] == "smoke"
    J = jobs(smoke)
    print(f"{len(J)} constructions; python {sys.executable}", flush=True)
    t0 = time.time(); rows = []
    with ProcessPoolExecutor(max_workers=14) as ex:
        for i, r in enumerate(ex.map(_audit_one, J, chunksize=4), 1):
            rows.append(r)
            if i % 200 == 0 or i == len(J):
                print(f"[{i}/{len(J)}] {i/(time.time()-t0):.1f}/s", flush=True)
    df = pd.DataFrame(rows)
    path = os.path.join(OUT, "network_fallback_audit" + ("_smoke" if smoke else "") + ".csv")
    df.to_csv(path, index=False)
    print("wrote", path)
    print(df.groupby("source").agg(n=("fallback", "size"), fallback_rate=("fallback", "mean"),
                                   mean_attempts=("attempts", "mean"), k_bar=("k_bar", "mean")))


if __name__ == "__main__":
    main()
