#!/usr/bin/env python3
"""M5：Template MidGoal 播放（APPROACH → RETREAT）。

用法：
  export ROS_DOMAIN_ID=43
  export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
  source /opt/ros/jazzy/setup.bash
  source ~/project/embodied__ai_lab/ros2/install/setup.bash
  python3 lab_platform/scripts/m5_mid_template.py --domain 43
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description="M5 thin Mid template player")
    p.add_argument("--device-id", default="franka-01")
    p.add_argument("--domain", type=int, default=43)
    p.add_argument("--template", type=str, default="", help="YAML MidGoal 模板路径")
    p.add_argument(
        "--scene-yaml",
        type=str,
        default="",
        help="Task Pack scene.yaml（toward / Oracle 必需）",
    )
    p.add_argument("--run-id", default="")
    p.add_argument("--steps-log", type=str, default="", help="写出 mid_steps.json")
    p.add_argument("--eval-log", type=str, default="", help="写出 eval.json（抓放）")
    p.add_argument(
        "--no-oracle-gt",
        action="store_true",
        help="不内嵌发布 GT；需外部 oracle 已在播",
    )
    args = p.parse_args()

    try:
        from lab_platform.ctrl_sim.mid_template import default_template_path, run_mid_template
    except ImportError:
        # 允许直接脚本路径运行
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from lab_platform.ctrl_sim.mid_template import default_template_path, run_mid_template

    tmpl = Path(args.template) if args.template else default_template_path()
    steps_log = Path(args.steps_log) if args.steps_log else None
    eval_log = Path(args.eval_log) if args.eval_log else None
    scene_yaml = Path(args.scene_yaml) if args.scene_yaml else None
    try:
        summary = run_mid_template(
            device_id=args.device_id,
            domain=args.domain,
            template_path=tmpl,
            scene_yaml=scene_yaml,
            run_id=args.run_id,
            steps_log=steps_log,
            eval_log=eval_log,
            publish_oracle_gt=not args.no_oracle_gt,
        )
    except Exception as e:
        print(f"[m5] FAIL: {e}", file=sys.stderr)
        return 2

    print(json.dumps({"m5": summary}, ensure_ascii=False, indent=2))
    return 0 if summary.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
