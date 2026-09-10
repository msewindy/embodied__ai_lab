#!/usr/bin/env python3
"""独立发布 scene GT ObjectPose（调试用；正式 run 可由 Mid 内嵌发布）。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--scene-yaml",
        type=str,
        default=str(
            Path(__file__).resolve().parents[2]
            / "tasks/tabletop_pickplace_v0/scene.yaml"
        ),
    )
    p.add_argument("--domain", type=int, default=43)
    p.add_argument("--rate-hz", type=float, default=10.0)
    p.add_argument("--cup-grid-id", type=int, default=None)
    p.add_argument("--duration-s", type=float, default=None)
    args = p.parse_args()

    try:
        from lab_platform.ctrl_sim.oracle_gt import run_oracle_publisher
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from lab_platform.ctrl_sim.oracle_gt import run_oracle_publisher

    run_oracle_publisher(
        scene_yaml=Path(args.scene_yaml),
        domain=args.domain,
        rate_hz=args.rate_hz,
        cup_grid_id=args.cup_grid_id,
        duration_s=args.duration_s,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
