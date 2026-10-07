"""
analysis/run_v02_reference.py: regenerate the v0.2 free_market reference data (N=60).

v0.2 lives at git commit a1f980b (branch main). Check it out as a separate worktree and pass
its path; the v0.2 code is imported only inside worker processes (it uses the same package
names, config and model, as v0.4, so it must never share an interpreter with v0.4 imports).

  git worktree add ../aaaps_v02_worktree a1f980b --detach
  python analysis/run_v02_reference.py --v02-root ../aaaps_v02_worktree --seeds 100

Output (repo-relative): outputs/reference/v02_free_market_final_step_<n>seeds.csv, one row
per agent at the last step, plus a manifest. Seed 42 is also compared with an optional saved
ground-truth CSV (--ground-truth).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from importlib import metadata

import numpy as np
import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(args):
    root, seed = args
    sys.path.insert(0, root)
    from scenarios.free_market import run  # v0.2 code
    model = run(seed=seed, n_students=60)
    df = model.datacollector.get_agent_vars_dataframe()
    last = df.index.get_level_values("Step").max()
    out = df.xs(last, level="Step").reset_index()
    out.insert(0, "step", last)
    out.insert(0, "seed", seed)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v02-root", required=True)
    ap.add_argument("--seeds", type=int, default=100)
    ap.add_argument("--ground-truth", default=None)
    a = ap.parse_args()
    root = os.path.abspath(a.v02_root)
    seeds = list(range(a.seeds))
    if 42 not in seeds:
        seeds.append(42)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=14) as ex:
        parts = list(ex.map(_run, [(root, s) for s in seeds]))
    df = pd.concat(parts, ignore_index=True)
    out_dir = os.path.join(REPO_ROOT, "outputs", "reference")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"v02_free_market_final_step_{a.seeds}seeds.csv")
    df.to_csv(path, index=False)
    print(f"OUTPUT: {os.path.abspath(path)}")
    print(f"shape={df.shape} Step max={df['step'].max()} seeds={df['seed'].nunique()} "
          f"elapsed={time.time() - t0:.0f}s")
    v02_hash = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    man = {"v02_git_hash": v02_hash, "seeds": seeds, "n_students": 60, "scenario": "free_market",
           "python_executable": sys.executable, "python_version": sys.version,
           "versions": {p: metadata.version(p) for p in ("mesa", "numpy", "pandas")},
           "written_utc": datetime.now(timezone.utc).isoformat()}
    if a.ground_truth:
        gt = pd.read_csv(a.ground_truth)
        gt_last = gt[gt["Step"] == gt["Step"].max()].sort_values("AgentID")
        me = df[df["seed"] == 42].sort_values("AgentID")
        same = bool(np.allclose(gt_last["score_total"].values, me["score_total"].values))
        print(f"GROUND TRUTH: {os.path.abspath(a.ground_truth)} shape={gt.shape} Step max={gt['Step'].max()}")
        print(f"seed 42 final-step score_total identical to ground truth: {same}")
        man["ground_truth_identical_seed42"] = same
    with open(path.replace(".csv", "_manifest.json"), "w") as f:
        json.dump(man, f, indent=2)


if __name__ == "__main__":
    main()
