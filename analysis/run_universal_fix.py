"""
analysis/run_universal_fix.py — Corrected universal_access re-run (ODD §5.5).

Runs ONLY the universal_access scenario with the temporary-withdrawal policy
(free tier 3 for semesters 1-4, steps 1-480, then withdrawn), N=240, 960 steps,
100 seeds. Saves separately from production_results.csv so the other four
scenarios' data is untouched.
"""

from __future__ import annotations

import os
import sys
import time
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from analysis.run_production import _run_one, METRICS

N_SEEDS = 100
SCENARIO = "universal_access"


def run():
    jobs = [(SCENARIO, s) for s in range(N_SEEDS)]
    print(f"Corrected universal_access: {len(jobs)} seeds, N=240, 960 steps.")

    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=14) as executor:
        futures = [executor.submit(_run_one, j) for j in jobs]
        done = 0
        for fut in as_completed(futures):
            results.append(fut.result())
            done += 1
            if done % 25 == 0 or done == len(jobs):
                el = time.time() - t0
                print(f"[{done}/{len(jobs)}] speed={done/max(1e-6,el):.2f}/s")

    elapsed = time.time() - t0
    print(f"[DONE] {len(jobs)} runs in {elapsed:.1f}s.")

    df = pd.DataFrame(results)
    out_dir = os.path.join(PROJECT_ROOT, "outputs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "universal_access_temporary_results.csv")
    df.to_csv(out_path, index=False)
    print(f"Saved {out_path} ({len(df)} rows).")

    summary = df[METRICS].mean()
    print("\n=== universal_access (temporary) mean over 100 seeds ===")
    print(summary.round(3).to_string())


if __name__ == "__main__":
    run()
