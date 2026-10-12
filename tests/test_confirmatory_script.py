"""The confirmatory analysis script must run end to end on synthetic data with the real schema."""
import os
import subprocess
import sys
import tempfile

from tests.synth_conf import make

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_script_runs_on_synthetic_data():
    with tempfile.TemporaryDirectory() as d:
        make(d)
        md = os.path.join(d, "out.md")
        env = dict(os.environ, AAAPS_CONF_DIR=d, AAAPS_RESULTS_MD=md)
        r = subprocess.run([sys.executable, "-m", "analysis.confirmatory_analysis"], cwd=ROOT, env=env, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-3000:]
        text = open(md).read()
        for key in ("## CONFIRMATORY", "Family 1", "H_self", "Network sweep corroboration", "## EXPLORATORY", "Narrative by the pre-declared"):
            assert key in text, key
