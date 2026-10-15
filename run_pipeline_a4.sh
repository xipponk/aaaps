#!/usr/bin/env bash
# A4 pipeline (preregistration.md A4): tests, R0 pre-check, block A4, R0 post-check, block D1, then the committed analysis script (once).
# Stops at: a failing test (including the bitwise regression and the logging-inertness test), an R0 mismatch, RuntimeError or Traceback in any
# log, less than 20 GB free disk, uncommitted tracked changes, or another worker set running.
set -euo pipefail
cd /home/tuul/projects/aaaps
export AAAPS_A4_OUT=v041_a4
PY=.venv/bin/python
LOG=outputs/$AAAPS_A4_OUT/logs
mkdir -p "$LOG"
say() { echo "[$(date -Is)] $1" | tee -a "$LOG/pipeline.log"; }
disk() { local g; g=$(df -BG --output=avail . | tail -1 | tr -dc 0-9); say "free disk ${g} GB"; [ "$g" -ge 20 ] || { say "STOP: free disk below 20 GB"; exit 6; }; }
guard() { if grep -q -E "RuntimeError|Traceback" "$LOG/$1.log"; then say "STOP: error in $1"; exit 3; fi; say "DONE $1"; }
git diff --quiet && git diff --cached --quiet || { say "STOP: uncommitted tracked changes"; exit 7; }
say "git $(git rev-parse HEAD)"
pgrep -af "analysis\.|tests\." | grep -v -E "pipeline|zsh" && { say "STOP: other worker set running"; exit 2; } || true
disk
say "START tests"; $PY -m tests.run_tests > "$LOG/tests.log" 2>&1 || { say "STOP: tests failed"; exit 1; }; guard tests
say "START R0 pre-check"; $PY -m analysis.a4_checks pre > "$LOG/precheck.log" 2>&1 || { say "STOP: R0 pre-check failed"; exit 4; }; guard precheck
disk
say "START block A4"; $PY -m analysis.run_a4 A4 > "$LOG/block_A4.log" 2>&1; guard block_A4
say "START R0 post-check"; $PY -m analysis.a4_checks post > "$LOG/postcheck.log" 2>&1 || { say "STOP: R0 post-check failed"; exit 5; }; guard postcheck
disk
say "START block D1"; $PY -m analysis.run_a4 D1 > "$LOG/block_D1.log" 2>&1; guard block_D1
say "START A4 analysis (run once)"; $PY -m analysis.a4_analysis > "$LOG/analysis.log" 2>&1; guard analysis
[ -s results_a4.md ] || { say "STOP: results_a4.md missing"; exit 8; }
say "PIPELINE COMPLETE"
