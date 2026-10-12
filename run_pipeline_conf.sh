#!/usr/bin/env bash
# Confirmatory pipeline (preregistration.md A3): tests, blocks K P2 ABL C1 NET L0, then the committed analysis script (once).
# Stops at: a failing test (including the bitwise regression at k = 1 and L0 = 0.10), RuntimeError or Traceback in any log,
# less than 20 GB free disk, uncommitted tracked changes, or another worker set running.
set -euo pipefail
cd /home/tuul/projects/aaaps
export AAAPS_CONF_OUT=v041_conf
PY=.venv/bin/python
LOG=outputs/$AAAPS_CONF_OUT/logs
mkdir -p "$LOG"
say() { echo "[$(date -Is)] $1" | tee -a "$LOG/pipeline.log"; }
disk() { local g; g=$(df -BG --output=avail . | tail -1 | tr -dc 0-9); say "free disk ${g} GB"; [ "$g" -ge 20 ] || { say "STOP: free disk below 20 GB"; exit 6; }; }
guard() { if grep -q -E "RuntimeError|Traceback" "$LOG/$1.log"; then say "STOP: error in $1"; exit 3; fi; say "DONE $1"; }
git diff --quiet && git diff --cached --quiet || { say "STOP: uncommitted tracked changes"; exit 7; }
say "git $(git rev-parse HEAD)"
pgrep -af "analysis\.|tests\." | grep -v -E "pipeline|zsh" && { say "STOP: other worker set running"; exit 2; } || true
disk
say "START tests"; $PY -m tests.run_tests > "$LOG/tests.log" 2>&1 || { say "STOP: tests failed"; exit 1; }; guard tests
for b in K P2 ABL C1 NET L0; do
  disk
  say "START block $b"; $PY -m analysis.run_confirmatory $b > "$LOG/block_$b.log" 2>&1; guard block_$b
done
disk
say "START confirmatory analysis (run once)"; $PY -m analysis.confirmatory_analysis > "$LOG/analysis.log" 2>&1; guard analysis
[ -s results_confirmatory.md ] || { say "STOP: results_confirmatory.md missing"; exit 8; }
say "PIPELINE COMPLETE"
