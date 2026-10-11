"""Bitwise regression against the v0.4.1 reference: agent-level state and model.random state must be identical."""
import json
import os
from concurrent.futures import ProcessPoolExecutor

from tests.hashing import MODES, SCENARIOS, SEEDS, run_hashes

REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ref_hashes_v041.json")


def test_hashes_match_reference():
    ref = json.load(open(REF))["hashes"]
    jobs = [(sc, s, m) for sc in SCENARIOS for s in SEEDS for m in MODES]
    with ProcessPoolExecutor(max_workers=14) as ex:
        got = dict(ex.map(run_hashes, jobs))
    bad = sorted(k for k in ref if got.get(k) != ref[k])
    assert not bad, f"{len(bad)} of {len(ref)} runs differ from the reference, first: {bad[:3]}"
