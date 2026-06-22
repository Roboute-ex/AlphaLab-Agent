"""Run the repository tests without requiring pytest.

This is a lightweight fallback for constrained demo environments. The tests are
still written so that `python -m pytest` works when pytest is installed.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys


def main() -> None:
    root = pathlib.Path(__file__).resolve().parents[1]
    src_path = str(root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    count = 0
    for path in sorted((root / "tests").glob("test_*.py")):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Cannot load test module: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name in sorted(dir(module)):
            test_fn = getattr(module, name)
            if name.startswith("test_") and callable(test_fn):
                test_fn()
                count += 1
    print(f"executed_tests={count}")


if __name__ == "__main__":
    main()
