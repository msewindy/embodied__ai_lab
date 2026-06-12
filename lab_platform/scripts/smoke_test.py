#!/usr/bin/env python3
"""TECH-14 冒烟测试：init → demo full → concurrency。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> int:
    print(f"\n>>> {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=cwd)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    data = root / "data"
    import shutil

    if data.exists():
        shutil.rmtree(data)
    lab = "lab"
    steps = [
        [lab, "--data-root", str(data), "init"],
        [lab, "--data-root", str(data), "demo", "full"],
        [lab, "--data-root", str(data), "test", "concurrency"],
    ]
    for step in steps:
        if run(step, root) != 0:
            print("FAILED:", step, file=sys.stderr)
            return 1
    print("\n=== ALL SMOKE TESTS PASSED ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
