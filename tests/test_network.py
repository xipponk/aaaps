"""Network generator (v0.4.1): connectivity-only retry, no silent fallback, realised properties recorded."""

import warnings

from analysis.param_guard import reset_params
import config.params as P
from model.model import AaapsModel

CORNERS = [(0.18, 0.015), (0.12, 0.005), (0.12, 0.03), (0.25, 0.005), (0.25, 0.03)]


def _build(seed, pw, pb):
    reset_params()
    P.SBM_P_WITHIN, P.SBM_P_BETWEEN = pw, pb
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return AaapsModel(n_students=240, scenario="free_market", seed=seed)
    finally:
        reset_params()


def test_connected_sections_and_attempts_recorded():
    import networkx as nx
    for pw, pb in CORNERS:
        for seed in range(20):
            m = _build(seed, pw, pb)
            info = m.network_info
            assert nx.is_connected(m.social_network)
            assert info["generator"] == "sbm" and 1 <= info["attempts"] <= 50
            for k in ("k_bar", "within_section_share", "disconnected_rejects"):
                assert k in info and info[k] == info[k], (k, info)
            assert info["within_section_share"] > 1 / 6 + 0.15, (pw, pb, seed, info)


def test_generator_raises_when_it_cannot_connect():
    try:
        _build(0, 0.02, 0.001)
    except RuntimeError as e:
        assert "no connected stochastic block model" in str(e)
        return
    raise AssertionError("expected RuntimeError, got a graph")


def test_kbar_range_is_warning_not_rejection():
    reset_params()
    P.TARGET_K_BAR_RANGE = (50.0, 60.0)
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            m = AaapsModel(n_students=240, scenario="free_market", seed=3)
        assert m.network_info["attempts"] == 1 and m.network_info["kbar_in_range"] is False
        assert any("outside validation range" in str(x.message) for x in w)
    finally:
        reset_params()


def test_no_erdos_renyi_in_generator_source():
    import inspect
    import model.network as net
    assert "erdos_renyi" not in inspect.getsource(net).replace("Erdos-Renyi fallback", "")
