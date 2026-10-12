"""Benefit family, C1, self_only, L0 and the confirmatory runner (preregistration.md A3)."""
import json
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from analysis.param_guard import reset_params
import config.params as P
from model.model import AaapsModel
from tests.hashing import run_hashes

REF = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ref_hashes_v041.json")))["hashes"]


def _model(**kw):
    reset_params()
    for k, v in kw.pop("params", {}).items():
        setattr(P, k, v)
    return AaapsModel(n_students=240, scenario=kw.pop("scenario", "free_market"), seed=kw.pop("seed", 3), **kw)


def test_k1_g_equals_x_bitwise_and_k0_is_pivot():
    m = _model()
    for a in m.agents:
        g, clipped = a.benefit_g()
        assert g == a.retained_ability / 100.0 and not clipped
    m0 = _model(params={"BENEFIT_ABILITY_SLOPE": 0.0})
    assert all(a.benefit_g()[0] == m0.benefit_pivot for a in m0.agents)
    assert abs(m0.benefit_pivot - np.mean([a.base_ability for a in m0.agents]) / 100.0) < 1e-15
    reset_params()


def test_k_minus1_is_mirror_and_clip_is_counted():
    m = _model(params={"BENEFIT_ABILITY_SLOPE": -1.0})
    for a in m.agents:
        g, clipped = a.benefit_g()
        raw = 2 * m.benefit_pivot - a.retained_ability / 100.0
        assert abs(g - max(0.0, raw)) < 1e-12 and (clipped == (raw < 0.0) or abs(raw) < 1e-12)
    reset_params()


def test_pivot_override_and_c1_and_L0():
    m = _model(params={"BENEFIT_PIVOT_OVERRIDE": 0.4, "BENEFIT_MODE": "C1", "INITIAL_LEGITIMACY": 0.25})
    assert m.benefit_pivot == 0.4
    assert all(a.ai_legitimacy == 0.25 for a in m.agents)
    a = next(iter(m.agents))
    a.calibration_error = 0.5
    assert a.benefit_g() == (0.4 * 0.5, False)
    reset_params()


def test_self_only_mode():
    m = _model(self_only_mode=True)
    assert m.disabled_submodels >= {"aspiration", "market"}
    leg0 = [a.ai_legitimacy for a in m.agents]
    for a in m.agents:
        wtp = a.monthly_budget * P.TIER_BUDGET_FRACTION[a.SES]
        a.ai_tier = 3 if wtp >= P.AI_MONTHLY_COST[3] else 2 if wtp >= P.AI_MONTHLY_COST[2] else 1
        a.ai_tier_effective = a.ai_tier
    prev = np.array(leg0)
    for _ in range(60):
        m.step()
        cur = np.array([a.ai_legitimacy for a in m.agents])
        assert (cur >= prev - 1e-12).all(), "self_only legitimacy can only rise"
        prev = cur
    assert prev.max() > 0.1
    assert all(a.aspiration == a.base_ability for a in m.agents)
    assert all(a.borrowing_from is None for a in m.agents)
    try:
        _model(self_only_mode=True, zero_interaction_mode=True)
    except ValueError:
        pass
    else:
        raise AssertionError("self_only and zero_interaction must be exclusive")
    reset_params()


def test_diagnostics_recorded():
    m = _model()
    for _ in range(2):
        m.step()
    assert 1 in m.g_log and 0.0 < m._xbar_sum / 2 < 1.0
    reset_params()


def test_regression_k1_hashes_match_and_k05_differs():
    """Bitwise: k = 1 (default) and L0 = 0.10 reproduce the v0.4.1 reference; k = 0.5 changes scores but not the initial rng state."""
    jobs = [("free_market", 0, "full"), ("universal_permanent", 1, "full"), ("free_market", 2, "zero_interaction"),
            ("targeted_subsidy", 3, "full"), ("free_market", 0, "full", {"BENEFIT_ABILITY_SLOPE": 0.5})]
    with ProcessPoolExecutor(max_workers=5) as ex:
        out = dict(ex.map(run_hashes, jobs))
    for key, got in out.items():
        if "BENEFIT" in key:
            continue
        assert got == REF[key], f"hash mismatch for {key}"
    neg = out["free_market|0|full|BENEFIT_ABILITY_SLOPE=0.5"]
    ref = REF["free_market|0|full"]
    assert neg["random_after_init"] == ref["random_after_init"], "spec parameter changed the rng state at construction"
    assert neg["agents_step_960"] != ref["agents_step_960"], "k = 0.5 must change the final state (parameter binds)"
    assert neg["agents_step_1"] == ref["agents_step_1"], "step 1 precedes any completed task with a different g"


def test_runner_schema_matches_synthetic_schema():
    from analysis.run_confirmatory import J, run_job
    from tests.synth_conf import row
    r = run_job(J("K", "free_market", 7000, mode="self_only", k=0.5))
    synth = set(row(np.random.default_rng(0), "K", "free_market", 7000, "full").keys())
    assert synth <= set(r.keys()), sorted(synth - set(r.keys()))
    assert set(r.keys()) - synth <= {k for k in r if k.startswith("net_") or k in (
        "mean_base_ability", "std_score", "mean_retained_ability", "deadline_miss_rate", "ai_adoption_rate",
        "borrowing_agent_count", "total_shared_seats_lent", "net_disconnected_rejects", "net_kbar_in_range")}, set(r.keys()) - synth
    assert np.isfinite(r["G"]) and r["pivot"] == "P1" and r["mode"] == "self_only"
