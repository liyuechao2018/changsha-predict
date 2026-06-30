from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON_FILES = [
    ROOT / "app.py",
    ROOT / "config.py",
    ROOT / "database.py",
    ROOT / "prediction_engine.py",
]


def main() -> int:
    print("Checking Python syntax...")
    for path in PYTHON_FILES:
        py_compile.compile(str(path), doraise=True)
        print(f"  ok {path.relative_to(ROOT)}")

    tests_dir = ROOT / "tests"
    if tests_dir.exists():
        print("Running unit tests...")
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", str(tests_dir)],
            cwd=str(ROOT),
            check=False,
        )
        if result.returncode != 0:
            return result.returncode

    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
