"""Agent-level state hashing for the bitwise regression reference (design_benefit_spec.md, R2(d))."""
from __future__ import annotations

import hashlib

from analysis.param_guard import reset_params
import config.params as P
from model.model import AaapsModel

SCENARIOS = ["baseline", "free_market", "mixed_policy", "targeted_subsidy", "universal_access", "universal_permanent"]
SEEDS = [0, 1, 2, 3, 4]
MODES = ["full", "zero_interaction"]
HASH_STEPS = (1, 120, 240, 480, 720, 960)
FIELDS = ("score_total", "dependency", "calibration_error", "retained_ability", "aspiration", "ai_legitimacy",
          "ai_tier", "ai_tier_effective", "quota_balance", "deadline_miss_count", "tasks_completed")


def _h(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def agent_table_hash(model) -> str:
    parts = []
    for a in sorted(model.agents, key=lambda x: x.unique_id):
        vals = []
        for f in FIELDS:
            v = getattr(a, f)
            vals.append(float(v).hex() if isinstance(v, float) else repr(v))
        parts.append(f"{a.unique_id}:" + ",".join(vals))
    return _h("\n".join(parts))


def run_hashes(args) -> tuple[str, dict]:
    scenario, seed, mode = args[:3]
    overrides = args[3] if len(args) > 3 else {}
    log_local = bool(overrides.get("__log_local__", False))
    reset_params()
    try:
        for key, val in overrides.items():
            if key != "__log_local__":
                setattr(P, key, val)
        if scenario == "mixed_policy":
            P.COURSES[2]['ai_allowed'] = False
        m = AaapsModel(n_students=P.N_STUDENTS, scenario=scenario, seed=seed, zero_interaction_mode=(mode == "zero_interaction"),
                       log_local_fraction=log_local)
        for a in m.agents:
            wtp = a.monthly_budget * P.TIER_BUDGET_FRACTION[a.SES]
            a.ai_tier = 3 if wtp >= P.AI_MONTHLY_COST[3] else 2 if wtp >= P.AI_MONTHLY_COST[2] else 1
            a.ai_tier_effective = a.ai_tier
        out = {
            "random_after_init": _h(repr(m.random.getstate())),
            "edges": _h(repr(sorted(tuple(sorted(e)) for e in m.social_network.edges()))),
        }
        for t in range(1, P.TOTAL_STEPS + 1):
            m.step()
            if t in HASH_STEPS:
                out[f"agents_step_{t}"] = agent_table_hash(m)
        out["random_final"] = _h(repr(m.random.getstate()))
        return f"{scenario}|{seed}|{mode}" + ("|" + ",".join(f"{k}={v}" for k, v in overrides.items()) if overrides else ""), out
    finally:
        reset_params()
