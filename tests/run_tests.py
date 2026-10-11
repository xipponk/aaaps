"""Minimal test runner (no pytest in .venv): python -m tests.run_tests [pattern]"""
import importlib
import pkgutil
import sys
import time
import traceback

import tests


def main(pattern: str = "") -> int:
    failed = 0
    for mod in sorted(m.name for m in pkgutil.iter_modules(tests.__path__) if m.name.startswith("test_")):
        if pattern and pattern not in mod:
            continue
        m = importlib.import_module(f"tests.{mod}")
        for name in sorted(n for n in dir(m) if n.startswith("test_")):
            t0 = time.time()
            try:
                getattr(m, name)()
                print(f"PASS {mod}.{name} ({time.time() - t0:.1f}s)", flush=True)
            except Exception:
                failed += 1
                print(f"FAIL {mod}.{name}", flush=True)
                traceback.print_exc()
    print(f"{'ALL PASSED' if not failed else str(failed) + ' FAILED'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
