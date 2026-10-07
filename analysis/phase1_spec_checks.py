"""
analysis/phase1_spec_checks.py: spec-vs-code checks requested at the start of Phase 1.

(b) Sample correlation of base ability and self-regulation across populations of 240 agents
    (many seeds), against the manuscript value r_AS = 0.30 and the analytic value implied by
    SR_ABILITY_WEIGHT / SR_NOISE_WEIGHT.
(c) Daily usage u and the recovery multiplier: how often the code's `practice` (1 - daily_u)
    equals "the agent actually practised", i.e. share of agent-days with no processed task,
    with tasks but u = 0, and with u > 0 (free_market, one seed, full 960 steps).

Usage: python -m analysis.phase1_spec_checks b | c
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import params as P
from model.model import AaapsModel
from scenarios.free_market import run as run_free_market

OUT = os.path.join(PROJECT_ROOT, "outputs", "phase1")


def check_b(n_seeds: int = 200) -> dict:
    rs = []
    for seed in range(n_seeds):
        m = AaapsModel(n_students=P.N_STUDENTS, scenario="free_market", seed=seed)
        a = np.array([x.base_ability for x in m.agents])
        s = np.array([x.self_regulation for x in m.agents])
        rs.append(float(np.corrcoef(a, s)[0, 1]))
    rs = np.array(rs)
    w_a = P.SR_ABILITY_WEIGHT * P.ABILITY_STD / 100.0
    w_n = P.SR_NOISE_WEIGHT / np.sqrt(12.0)
    res = {
        "n_seeds": n_seeds, "n_agents": P.N_STUDENTS,
        "mean_r": float(rs.mean()), "sd_r": float(rs.std(ddof=1)),
        "p05": float(np.percentile(rs, 5)), "p95": float(np.percentile(rs, 95)),
        "analytic_r_unclipped": float(w_a / np.sqrt(w_a ** 2 + w_n ** 2)),
        "paper_r_AS": 0.30, "code_SR_ABILITY_WEIGHT": P.SR_ABILITY_WEIGHT,
    }
    print(json.dumps(res, indent=2))
    return res


def check_c(seed: int = 7) -> dict:
    """Instrument Phase D inputs without changing the model."""
    from model.agents import StudentAgent
    counts = {"no_task": 0, "task_u0": 0, "task_u_pos": 0}
    orig = StudentAgent.update_coupled_dynamics

    def wrapped(self):
        recs = self._u_task_records
        if not recs:
            counts["no_task"] += 1
        else:
            tw = sum(w for _, w in recs)
            du = sum(u * w for u, w in recs) / tw if tw > 0 else 0.0
            counts["task_u_pos" if du > 0 else "task_u0"] += 1
        return orig(self)

    StudentAgent.update_coupled_dynamics = wrapped
    try:
        run_free_market(seed=seed, n_students=P.N_STUDENTS)
    finally:
        StudentAgent.update_coupled_dynamics = orig
    tot = sum(counts.values())
    res = {"seed": seed, "agent_days": tot, **counts,
           **{f"share_{k}": v / tot for k, v in counts.items()}}
    print(json.dumps(res, indent=2))
    return res


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    which = sys.argv[1]
    res = check_b() if which == "b" else check_c()
    with open(os.path.join(OUT, f"spec_check_{which}.json"), "w") as f:
        json.dump(res, f, indent=2)
