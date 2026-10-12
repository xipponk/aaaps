#!/usr/bin/env bash
# v0.4.1 pipeline: tests, production, isolation, Morris, retained set, Sobol (free_market then targeted_subsidy, 1 seed).
# Stops at the first failure, RuntimeError, retained set > 14, or clamp share > 10% at the default LAMBDA_A.
set -euo pipefail
cd /home/tuul/projects/aaaps
export AAAPS_OUT=v041_main
PY=.venv/bin/python
LOG=outputs/$AAAPS_OUT/logs
mkdir -p "$LOG"
step() { echo "[$(date -Is)] START $1" | tee -a "$LOG/pipeline.log"; }
guard() { if grep -q -E "RuntimeError|Traceback" "$LOG/$1.log"; then echo "STOP: error in $1" | tee -a "$LOG/pipeline.log"; exit 3; fi; echo "[$(date -Is)] DONE $1" | tee -a "$LOG/pipeline.log"; }
pgrep -af "analysis\.|tests\." | grep -v pipeline | grep -v zsh && { echo "STOP: other worker set running"; exit 2; } || true
python3 - <<'P'
import csv
r=list(csv.DictReader(open("outputs/v041_ext/clamp_share.csv")))
v=[float(x["share_at_clamp"]) for x in r if abs(float(x["lambda_a"])-0.00248)<1e-9]
m=sum(v)/len(v); print("clamp share at default", m)
raise SystemExit(0 if m<=0.10 else 4)
P
step tests;      $PY -m tests.run_tests > "$LOG/tests.log" 2>&1 || { echo "STOP: tests failed" | tee -a "$LOG/pipeline.log"; exit 1; }; guard tests
step production; $PY -m analysis.run_production_v04 > "$LOG/production.log" 2>&1; guard production
step isolation;  $PY -m analysis.run_interaction_isolation > "$LOG/isolation.log" 2>&1; guard isolation
step morris;     $PY -m analysis.run_morris_screening > "$LOG/morris.log" 2>&1; guard morris
step retained;   $PY -m analysis.morris_recompute > "$LOG/retained.log" 2>&1; guard retained
N=$(($(wc -l < outputs/$AAAPS_OUT/morris_v04_retained12.csv) - 1))
echo "retained set size $N" | tee -a "$LOG/pipeline.log"
[ "$N" -le 14 ] || { echo "STOP: retained set > 14" | tee -a "$LOG/pipeline.log"; exit 5; }
step sobol_fm;   $PY -m analysis.run_sobol_v04 free_market --N 512 --seeds 3000 > "$LOG/sobol_free_market.log" 2>&1; guard sobol_free_market
step sobol_ts;   $PY -m analysis.run_sobol_v04 targeted_subsidy --N 512 --seeds 3000 > "$LOG/sobol_targeted_subsidy.log" 2>&1; guard sobol_targeted_subsidy
echo "[$(date -Is)] PIPELINE COMPLETE" | tee -a "$LOG/pipeline.log"
