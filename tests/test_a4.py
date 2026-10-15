"""Amendment A4: channel scales, local-fraction logging (must not change any hash), runner schema, analysis script on synthetic data."""
import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from analysis.param_guard import reset_params
import config.params as P
from model.model import AaapsModel
from tests.hashing import run_hashes
from tests.synth_a4 import make

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = json.load(open(os.path.join(ROOT, "tests", "ref_hashes_v041.json")))["hashes"]


def test_scales_bind_and_neutral_values_are_bitwise_and_logging_is_inert():
    base = "free_market|0|full"
    jobs = [("free_market", 0, "full", {"AI_QUALITY_SCALE": 1.0, "AI_SPEED_SCALE": 1.0}),
            ("free_market", 0, "full", {"__log_local__": True}),
            ("free_market", 0, "full", {"AI_QUALITY_SCALE": 0.0}),
            ("free_market", 0, "full", {"AI_SPEED_SCALE": 0.0}),
            ("free_market", 0, "full", {"AI_QUALITY_SCALE": 0.0, "BENEFIT_ABILITY_SLOPE": 0.5}),
            ("free_market", 0, "full", {"AI_QUALITY_SCALE": 0.0, "BENEFIT_ABILITY_SLOPE": 0.0}),
            ("free_market", 0, "full", {"AI_QUALITY_SCALE": 0.0, "AI_SPEED_SCALE": 0.5})]
    with ProcessPoolExecutor(max_workers=len(jobs)) as ex:
        out = dict(ex.map(run_hashes, jobs))
    k = lambda ov: base + "|" + ",".join(f"{a}={b}" for a, b in ov.items())
    assert out[k(jobs[0][3])] == REF[base], "explicit scales 1.0 must reproduce the reference bitwise"
    assert out[k(jobs[1][3])] == REF[base], "logging the local fraction must not change any hash"
    q0, s0 = out[k(jobs[2][3])], out[k(jobs[3][3])]
    assert q0["agents_step_960"] != REF[base]["agents_step_960"], "AI_QUALITY_SCALE = 0 must bind"
    assert s0["agents_step_960"] != REF[base]["agents_step_960"], "AI_SPEED_SCALE = 0 must bind"
    assert q0["agents_step_960"] != s0["agents_step_960"]
    r_k05, r_k0 = out[k(jobs[4][3])], out[k(jobs[5][3])]
    assert q0 == r_k05 == r_k0, "R0 (no quality channel) must not depend on k, bitwise"
    assert out[k(jobs[6][3])]["agents_step_960"] != q0["agents_step_960"], "speed scale must bind when quality is off"


def test_local_log_content():
    reset_params()
    m = AaapsModel(n_students=240, scenario="free_market", seed=5, log_local_fraction=True)
    for a in m.agents:
        wtp = a.monthly_budget * P.TIER_BUDGET_FRACTION[a.SES]
        a.ai_tier = 3 if wtp >= P.AI_MONTHLY_COST[3] else 2 if wtp >= P.AI_MONTHLY_COST[2] else 1
        a.ai_tier_effective = a.ai_tier
    for _ in range(150):
        m.step()
    L = m.local_log
    obs, raw = np.array(L["obs"]), np.array(L["raw"])
    assert obs.shape == (150, 240) and raw.shape == (150, 240) and len(L["glob"]) == 150 and L["deg"].shape == (240,)
    ok = ~np.isnan(obs)
    assert ((obs[ok] >= 0) & (obs[ok] <= 1)).all() and ((raw[ok] >= 0) & (raw[ok] <= 1)).all()
    assert (np.isnan(obs).all(axis=0) == (L["deg"] == 0)).all(), "agents without neighbours are NaN, all others are logged"
    assert (obs[ok] <= raw[ok] + 1e-12).all(), "observed share cannot exceed the raw share"
    assert 0.55 < np.nanmean(obs[100:]) / np.nanmean(raw[100:]) < 0.85, "ratio should be near P_VISIBLE = 0.7"
    off = AaapsModel(n_students=240, scenario="free_market", seed=5)
    assert off.local_log is None
    reset_params()


def test_runner_schema_and_d1_file():
    from analysis import run_a4
    with tempfile.TemporaryDirectory() as d:
        run_a4.OUT = d
        r = run_a4.run_job(run_a4.J("A4", "free_market", 8000, level="R2", k=0.5))
        for c in ("G", "mean_score", "mean_dependency", "g_mean_s960", "clip_count", "scenario", "level", "k", "seed", "job_id"):
            assert c in r, c
        assert r["mq"] == 0.5 and r["ms"] == 1.0 and np.isfinite(r["G"])
        r1 = run_a4.run_job(run_a4.J("D1", "free_market", 8100, log=True))
        z = np.load(os.path.join(d, "D1_seed8100.npz"))
        assert z["obs"].shape == (960, 240) and z["glob"].shape == (960,) and z["raw"].shape == (960, 240)
        assert np.isfinite(r1["G"])
    assert len(run_a4.jobs_for("A4")) == 4300 and len(run_a4.jobs_for("D1")) == 5


def test_a4_script_runs_on_synthetic_data():
    with tempfile.TemporaryDirectory() as d:
        make(d)
        md = os.path.join(d, "out.md")
        env = dict(os.environ, AAAPS_A4_DIR=d, AAAPS_A4_RESULTS_MD=md)
        r = subprocess.run([sys.executable, "-m", "analysis.a4_analysis"], cwd=ROOT, env=env, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-3000:]
        text = open(md).read()
        for key in ("EXPLORATORY", "Ratio thresholds", "k* per level", "D1:", "g_mean_960", "rises through"):
            assert key in text, key
        assert "\u2014" not in text
