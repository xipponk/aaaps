"""CLAUDE.md rule 3: KAPPA and ASPIRATION_GAP_WEIGHT must change outputs (not true under the v0.4 saturated aspiration)."""
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from analysis.param_guard import reset_params
import config.params as P
from model.model import AaapsModel

BOUNDS = {"KAPPA": (0.02, 0.25), "ASPIRATION_GAP_WEIGHT": (0.05, 0.40)}


def _run(args):
    name, value, seed = args
    reset_params()
    if name is not None:
        setattr(P, name, value)
    m = AaapsModel(n_students=240, scenario="free_market", seed=seed)
    for a in m.agents:
        wtp = a.monthly_budget * P.TIER_BUDGET_FRACTION[a.SES]
        a.ai_tier = 3 if wtp >= P.AI_MONTHLY_COST[3] else 2 if wtp >= P.AI_MONTHLY_COST[2] else 1
        a.ai_tier_effective = a.ai_tier
    for _ in range(360):
        m.step()
    return (float(np.mean([a.dependency for a in m.agents])), float(np.mean([a.score_total for a in m.agents])))


def test_kappa_and_gap_weight_change_outputs():
    jobs = [(n, v, 1000) for n, (lo, hi) in BOUNDS.items() for v in (lo, hi)]
    with ProcessPoolExecutor(max_workers=4) as ex:
        res = list(ex.map(_run, jobs))
    for i, n in enumerate(BOUNDS):
        lo, hi = res[2 * i], res[2 * i + 1]
        assert lo != hi, f"{n}: identical outputs at both bounds {lo}"
