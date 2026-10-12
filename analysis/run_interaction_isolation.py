"""
analysis/run_interaction_isolation.py: run-level interaction isolation, free_market, N = 240.

Conditions (same 100 seeds in every condition, so seeds are paired and agents are identical
within a seed): full; each submodel switched off alone (no_norms = B1, no_aspiration = B2,
no_market = B3); all three off with the network kept (none_net); and zero_interaction_mode
(empty graph, Phase B skipped). Outputs per-run means of dependency, calibration error,
retained ability, score and legitimacy, then paired effects against `full` with bootstrap CIs.
"""

from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import config.params as P
from analysis.param_guard import reset_params
from analysis.manifest import network_summary, write_manifest
from analysis.run_production import _compute_metrics
from scenarios.free_market import run as run_free_market

SEEDS = list(range(100))
CONDITIONS = {
    "full": dict(),
    "no_norms": dict(disabled_submodels=frozenset({"norms"})),
    "no_aspiration": dict(disabled_submodels=frozenset({"aspiration"})),
    "no_market": dict(disabled_submodels=frozenset({"market"})),
    "none_net": dict(disabled_submodels=frozenset({"norms", "aspiration", "market"})),
    "zero_interaction": dict(zero_interaction_mode=True),
    # peer influence only: ETA = 0 removes diffusion, ETA_SELF (self-use reinforcement) stays
    "no_peer_norms": dict(params={"ETA": 0.0}),
}
OUTCOMES = ["mean_dependency", "mean_calibration_error", "mean_retained_ability", "mean_score",
            "mean_legitimacy"]
OUT = os.path.join(PROJECT_ROOT, "outputs", os.environ.get("AAAPS_OUT", "phase2"))


def _job(args):
    cond, seed = args
    kw = dict(CONDITIONS[cond])
    overrides = kw.pop("params", {})
    reset_params()
    try:
        for k, v in overrides.items():
            setattr(P, k, v)
        m = run_free_market(seed=seed, n_students=P.N_STUDENTS, **kw)
    finally:
        reset_params()
    r = _compute_metrics(m)
    r.update(condition=cond, seed=seed)
    return r


def paired_effect(x, y, rng):
    d = x - y
    boots = np.array([rng.choice(d, len(d)).mean() for _ in range(10000)])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    sd = d.std(ddof=1)
    return {"mean_diff": d.mean(), "ci_lo": lo, "ci_hi": hi,
            "cohens_dz": d.mean() / sd if sd > 0 else np.nan,
            "pct_of_full": 100 * d.mean() / y.mean() if y.mean() != 0 else np.nan}


def main():
    """Optional argv: condition names to (re)run; other conditions are kept from the saved CSV."""
    only = sys.argv[1:]
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "interaction_isolation_runs.csv")
    jobs = [(c, s) for c in (only or CONDITIONS) for s in SEEDS]
    t0, rows = time.time(), []
    with ProcessPoolExecutor(max_workers=14) as ex:
        for i, r in enumerate(ex.map(_job, jobs), 1):
            rows.append(r)
            if i % 50 == 0 or i == len(jobs):
                print(f"[isolation] {i}/{len(jobs)} {i / (time.time() - t0):.2f} runs/s", flush=True)
    df = pd.DataFrame(rows)
    if only:
        old = pd.read_csv(path)
        df = pd.concat([old[~old.condition.isin(only)], df], ignore_index=True)
    df.to_csv(path, index=False)
    print(f"OUTPUT: {os.path.abspath(path)} shape={df.shape} steps={P.TOTAL_STEPS}")
    rng = np.random.default_rng(20261008)
    eff = []
    for cond in CONDITIONS:
        if cond == "full":
            continue
        for o in OUTCOMES:
            a = df[df.condition == cond].sort_values("seed")[o].values
            b = df[df.condition == "full"].sort_values("seed")[o].values
            eff.append({"condition": cond, "outcome": o, "full_mean": b.mean(), "cond_mean": a.mean(),
                        **paired_effect(a, b, rng)})
    eff = pd.DataFrame(eff)
    eff.to_csv(os.path.join(OUT, "interaction_isolation_effects.csv"), index=False)
    print(eff.round(4).to_string(index=False))
    write_manifest(os.path.join(OUT, "interaction_isolation_manifest.json"), stage="isolation",
                   seeds=SEEDS, n_students=P.N_STUDENTS, conditions=list(CONDITIONS),
                   scenario="free_market", sampler="none (paired seeds)", network=network_summary(df))


if __name__ == "__main__":
    main()
