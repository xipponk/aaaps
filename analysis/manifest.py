"""
analysis/manifest.py: run manifest writer shared by all v0.4 analysis scripts.

Records git hash (and dirty flag), a hash of every parameter in config.params at call
time, python executable path and version, library versions, seeds, N, sampler and
timestamps, so any saved result can be traced to the code and interpreter that made it.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib import metadata

from config import params as P

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def params_snapshot() -> dict:
    """All upper-case parameters currently set in config.params (reflects overrides)."""
    return {k: getattr(P, k) for k in sorted(dir(P)) if k.isupper()}


def params_hash() -> str:
    blob = json.dumps(params_snapshot(), sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def _version(pkg: str) -> str:
    try:
        return metadata.version(pkg)
    except metadata.PackageNotFoundError:
        return "not installed"


def build_manifest(**extra) -> dict:
    return {
        "git_hash": _git("rev-parse", "HEAD"),
        "git_branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain", "--untracked-files=no")),
        "params_hash": params_hash(),
        "params": params_snapshot(),
        "python_executable": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "versions": {p: _version(p) for p in ("mesa", "numpy", "pandas", "scipy", "networkx", "SALib", "joblib")},
        "written_utc": datetime.now(timezone.utc).isoformat(),
        **extra,
    }


def write_manifest(path: str, **extra) -> dict:
    m = build_manifest(**extra)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        json.dump(m, f, indent=2, default=str)
    return m
