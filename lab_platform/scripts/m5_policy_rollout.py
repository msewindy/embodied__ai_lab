#!/usr/bin/env python3
"""P4：PolicyBackend rollout 入口。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description="CTRL-SIM policy rollout")
    p.add_argument("--device-id", default="franka-01")
    p.add_argument("--domain", type=int, default=43)
    p.add_argument("--template", type=str, default="", help="profile YAML path")
    p.add_argument("--checkpoint", type=str, default="")
    p.add_argument("--backend", type=str, default="lerobot_state")
    p.add_argument("--duration", type=float, default=0.0, help=">0 覆盖 profile")
    p.add_argument("--run-id", default="")
    p.add_argument("--steps-log", type=str, default="")
    args = p.parse_args()

    try:
        from lab_platform.ctrl_sim.policy_rollout import run_policy_rollout
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from lab_platform.ctrl_sim.policy_rollout import run_policy_rollout

    profile = Path(args.template) if args.template else None
    ckpt = Path(args.checkpoint) if args.checkpoint else None
    kwargs: dict = {
        "device_id": args.device_id,
        "domain": args.domain,
        "profile_path": profile,
        "checkpoint": ckpt,
        "backend_name": args.backend,
        "run_id": args.run_id,
        "steps_log": Path(args.steps_log) if args.steps_log else None,
    }
    if args.duration > 0:
        kwargs["duration_s"] = args.duration
    try:
        summary = run_policy_rollout(**kwargs)
    except Exception as e:
        print(f"[rollout] FAIL: {e}", file=sys.stderr)
        return 2
    print(json.dumps({"rollout": summary}, ensure_ascii=False, indent=2))
    return 0 if summary.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
