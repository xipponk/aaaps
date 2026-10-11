"""Every run record carries the realised network (k_bar, within-section share, attempts)."""
import numpy as np

from analysis.manifest import network_summary
from analysis.param_guard import reset_params
from analysis.run_production import _compute_metrics
from model.model import AaapsModel
import config.params as P


def test_run_metrics_carry_network_fields():
    reset_params()
    m = AaapsModel(n_students=240, scenario="free_market", seed=11)
    for _ in range(3):
        m.step()
    import analysis.run_production as rp
    old = rp.TOTAL_STEPS
    rp.TOTAL_STEPS = 3
    try:
        r = _compute_metrics(m)
    finally:
        rp.TOTAL_STEPS = old
    for k in ("net_attempts", "net_k_bar", "net_within_section_share", "net_disconnected_rejects", "net_kbar_in_range"):
        assert k in r and np.isfinite(r[k]), (k, r.get(k))


def test_network_summary_shape():
    import pandas as pd
    s = network_summary(pd.DataFrame({"net_k_bar": [9.0, 11.0], "net_attempts": [1, 3], "x": [0, 0]}))
    assert s["net_k_bar"]["mean"] == 10.0 and s["net_attempts"]["max"] == 3.0 and "x" not in s
