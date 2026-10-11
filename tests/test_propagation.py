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


def test_lambda_a_propagates_through_calibration_job():
    """The calibration job sets P.LAMBDA_A in the worker; a reset inside the run path once wiped it silently."""
    from analysis.calibrate_lambda_a import _job
    with ProcessPoolExecutor(max_workers=2) as ex:
        lo, hi = ex.map(_job, [("universal_permanent", 1000, 0.0007), ("universal_permanent", 1000, 0.0059)])
    assert lo["relative_ability_decline"] < hi["relative_ability_decline"], (lo, hi)


def test_lambda_a_propagates_through_morris_and_sobol_jobs():
    import numpy as np
    from analysis.run_morris_screening import PROBLEM, _worker_eval
    from analysis import run_sobol_v04 as sv

    mid = np.array([(lo + hi) / 2 for lo, hi in PROBLEM["bounds"]])
    i = PROBLEM["names"].index("LAMBDA_A")
    lo_v, hi_v = mid.copy(), mid.copy()
    lo_v[i], hi_v[i] = PROBLEM["bounds"][i]
    with ProcessPoolExecutor(max_workers=4) as ex:
        f1 = ex.submit(_worker_eval, (0, lo_v), 1000)
        f2 = ex.submit(_worker_eval, (1, hi_v), 1000)
        f3 = ex.submit(sv._job, ("free_market", ["LAMBDA_A"], [0.0007], 0, 1000))
        f4 = ex.submit(sv._job, ("free_market", ["LAMBDA_A"], [0.0059], 1, 1000))
        m_lo, m_hi, s_lo, s_hi = f1.result()[1], f2.result()[1], f3.result(), f4.result()
    assert m_lo["mean_retained_ability"] > m_hi["mean_retained_ability"], (m_lo, m_hi)
    assert s_lo["mean_retained_ability"] > s_hi["mean_retained_ability"], (s_lo, s_hi)
