"""
analysis/param_guard.py: guard against parameter leakage between jobs in reused worker processes.

ProcessPoolExecutor workers are reused, and the GSA runners set module-level values in
config.params (P.X = v, P.SHAREABLE_SEATS[3] = v, P.COURSES[2]['ai_allowed'] = v). A job that
sets fewer parameters than an earlier job in the same worker, or that dies before restoring, would
silently inherit the earlier values. Every job therefore calls reset_params() first. The defaults
are captured when this module is first imported, which in a worker is before any job has run.
"""

from __future__ import annotations

import copy

from config import params as P

_DEFAULTS = {k: copy.deepcopy(getattr(P, k)) for k in dir(P) if k.isupper()}


def _restore(current, default):
    """Restore mutable containers in place so references held elsewhere stay valid."""
    if isinstance(default, dict) and isinstance(current, dict):
        current.clear()
        for k, v in default.items():
            current[k] = copy.deepcopy(v)
        return current
    if isinstance(default, list) and isinstance(current, list):
        current[:] = copy.deepcopy(default)
        return current
    return copy.deepcopy(default)


def reset_params() -> None:
    """Put every upper-case parameter in config.params back to its file value."""
    for k, default in _DEFAULTS.items():
        setattr(P, k, _restore(getattr(P, k, None), default))
    for k in [k for k in dir(P) if k.isupper() and k not in _DEFAULTS]:
        delattr(P, k)


def leaked_params() -> list[str]:
    """Names whose current value differs from the file value (empty after reset_params)."""
    return sorted(k for k, d in _DEFAULTS.items() if getattr(P, k, None) != d)
