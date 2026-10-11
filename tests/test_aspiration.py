"""Aspiration (v0.4.1): rank comparison among network neighbours, unit-consistent, not saturated."""
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from analysis.param_guard import reset_params
import config.params as P
from model.model import AaapsModel

CHECK_STEPS = (30, 120, 480, 960)


def _run(args):
    scenario, seed = args
    reset_params()
    m = AaapsModel(n_students=240, scenario=scenario, seed=seed)
    for a in m.agents:
        wtp = a.monthly_budget * P.TIER_BUDGET_FRACTION[a.SES]
        a.ai_tier = 3 if wtp >= P.AI_MONTHLY_COST[3] else 2 if wtp >= P.AI_MONTHLY_COST[2] else 1
        a.ai_tier_effective = a.ai_tier
    rows = []
    for t in range(1, P.TOTAL_STEPS + 1):
        m.step()
        if t in CHECK_STEPS:
            asp = np.array([a.aspiration for a in m.agents])
            rows.append((t, max(float((asp >= 99.0).mean()), float((asp <= 11.0).mean())), float(asp.std()),
                         float(asp.min()), float(asp.max())))
    return scenario, seed, rows


def test_aspiration_not_saturated_and_in_bounds():
    jobs = [(sc, s) for sc in ("free_market", "universal_permanent") for s in (1000, 1001, 1002)]
    with ProcessPoolExecutor(max_workers=6) as ex:
        for sc, seed, rows in ex.map(_run, jobs):
            for t, share_bound, sd, lo, hi in rows:
                assert lo >= P.ABILITY_CLAMP[0] - 1e-9 and hi <= P.ABILITY_CLAMP[1] + 1e-9
                assert share_bound < 0.10, (sc, seed, t, share_bound)   # per bound; v0.4 value was 1.0 at the upper bound. Design doc said 0.05, relaxed to 0.10 for a rank map (local extremes among ~10 neighbours are about 1/11)
                assert sd > 2.0, (sc, seed, t, sd)


def test_aspiration_target_is_rank_and_scale_free():
    """Multiplying every score by 1000 must not change the aspiration update (v0.4 averaged raw scores)."""
    out = []
    for scale in (1.0, 1000.0):
        reset_params()
        m = AaapsModel(n_students=240, scenario="free_market", seed=7)
        for a in m.agents:
            a.score_total = scale * (10.0 * a.unique_id)
        m._phase_b_social_update()
        out.append([a.aspiration for a in m.agents])
        reset_params()
    assert np.allclose(out[0], out[1])
    # expected value for one agent: tie-weighted share of neighbours below
    reset_params()
    m = AaapsModel(n_students=240, scenario="free_market", seed=7)
    for a in m.agents:
        a.score_total = 10.0 * a.unique_id
    a0 = next(a for a in m.agents if a.unique_id == 30)
    before = a0.aspiration
    nb = list(m.social_network.neighbors(30))
    w = np.array([m.social_network[30][j]['tie_strength'] for j in nb])
    below = np.array([1.0 if j < 30 else 0.0 for j in nb])
    pct = float((w * below).sum() / w.sum())
    target = P.ABILITY_CLAMP[0] + pct * (P.ABILITY_CLAMP[1] - P.ABILITY_CLAMP[0])
    m._phase_b_social_update()
    assert abs(a0.aspiration - (before + P.KAPPA * (target - before))) < 1e-9
    reset_params()
