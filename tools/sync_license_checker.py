"""Distribute the canonical checker to independently copied Docker contexts."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "skipper/check_licenses.py"
TARGETS = (ROOT / "client/check_licenses.py", ROOT / "deploy/local/integration/check_licenses.py")


if __name__ == "__main__":
    for target in TARGETS:
        target.write_bytes(SOURCE.read_bytes())
        print("Updated {}".format(target.relative_to(ROOT)))
