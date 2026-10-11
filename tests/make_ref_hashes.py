"""Create tests/ref_hashes_v041.json from the current code (run once on the finished v0.4.1, then commit)."""
import json
import os
import subprocess
from concurrent.futures import ProcessPoolExecutor

from tests.hashing import MODES, SCENARIOS, SEEDS, run_hashes
from analysis.manifest import params_hash

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ref_hashes_v041.json")

if __name__ == "__main__":
    jobs = [(sc, s, m) for sc in SCENARIOS for s in SEEDS for m in MODES]
    with ProcessPoolExecutor(max_workers=14) as ex:
        res = dict(ex.map(run_hashes, jobs))
    meta = {"git_hash_at_creation": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
            "params_hash": params_hash(), "n_runs": len(res)}
    with open(OUT, "w") as f:
        json.dump({"meta": meta, "hashes": res}, f, indent=1, sort_keys=True)
    print(OUT, len(res), meta)
