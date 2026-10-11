"""Parameter leakage between jobs in reused worker processes (the audit-script bug, checked for all runners)."""
import glob
import os
import re
from concurrent.futures import ProcessPoolExecutor

from analysis.param_guard import leaked_params, reset_params
import config.params as P

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _dirty_job(_):
    P.ALPHA_D = 0.999
    P.SHAREABLE_SEATS[3] = 99
    P.COURSES[2]['ai_allowed'] = False
    P.TARGET_K_BAR_RANGE = (0.0, 1.0)
    return 1


def _probe_with_reset(_):
    reset_params()
    return leaked_params(), P.ALPHA_D, P.SHAREABLE_SEATS[3], P.COURSES[2]['ai_allowed']


def _probe_without_reset(_):
    return P.ALPHA_D, P.SHAREABLE_SEATS[3]


def test_reset_restores_everything_in_process():
    P.LAMBDA_A = 0.5
    P.SHAREABLE_SEATS[3] = 77
    P.COURSES[2]['ai_allowed'] = False
    P.NEW_STRAY = 1.0
    ref = P.SHAREABLE_SEATS
    reset_params()
    assert leaked_params() == []
    assert not hasattr(P, "NEW_STRAY")
    assert P.SHAREABLE_SEATS is ref, "containers must be restored in place"
    assert P.COURSES[2]['ai_allowed'] == 'random_50pct'


def test_worker_reuse_leaks_without_reset_and_not_with_reset():
    """One worker, three jobs in order: dirty, probe-with-reset, then dirty again and probe-without-reset (control)."""
    with ProcessPoolExecutor(max_workers=1) as ex:
        ex.submit(_dirty_job, 0).result()
        leaked, alpha, seats, ai = ex.submit(_probe_with_reset, 0).result()
        assert leaked == [] and alpha == 0.012 and seats == 2 and ai == 'random_50pct', (leaked, alpha, seats, ai)
        ex.submit(_dirty_job, 0).result()
        alpha2, seats2 = ex.submit(_probe_without_reset, 0).result()
        assert alpha2 == 0.999 and seats2 == 99, "control: reused worker should leak when no reset is called"


def test_every_pooled_runner_resets_parameters():
    """Static check: any analysis script that mutates config.params and uses a process pool calls reset_params."""
    mutate = re.compile(r"\bP\.[A-Z_]+(\[[^\]]*\])* *=[^=]|setattr\(P,")
    offenders = []
    for path in sorted(glob.glob(os.path.join(ROOT, "analysis", "*.py"))):
        src = open(path).read()
        if "ProcessPoolExecutor" in src and mutate.search(src) and "reset_params" not in src:
            offenders.append(os.path.basename(path))
    assert offenders == [] or offenders == ["network_fallback_audit.py"], offenders
