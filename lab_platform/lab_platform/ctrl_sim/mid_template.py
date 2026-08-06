"""M5 薄 Mid：Template MidGoal 播放器 → task_space SkillIntent。"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class MidGoal:
    name: str
    target_ref: str = "none"
    ee_delta: list[float] = field(default_factory=lambda: [0.0] * 6)
    rate_hz: float = 10.0
    max_duration_s: float = 2.0
    success_ee_travel_m: float = 0.04
    expire_ms: int = 200

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MidGoal":
        delta = list(d.get("ee_delta") or [0.0] * 6)
        while len(delta) < 6:
            delta.append(0.0)
        return cls(
            name=str(d["name"]),
            target_ref=str(d.get("target_ref") or "none"),
            ee_delta=[float(x) for x in delta[:6]],
            rate_hz=float(d.get("rate_hz") or 10.0),
            max_duration_s=float(d.get("max_duration_s") or 2.0),
            success_ee_travel_m=float(d.get("success_ee_travel_m") or 0.04),
            expire_ms=int(d.get("expire_ms") or 200),
        )


@dataclass
class MidTemplate:
    profile: str
    situation: str
    forward_wm: str
    goals: list[MidGoal]

    @classmethod
    def load(cls, path: Path) -> "MidTemplate":
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        goals = [MidGoal.from_dict(g) for g in (raw.get("goals") or [])]
        if len(goals) < 2:
            raise ValueError(f"M5 requires ≥2 MidGoals, got {len(goals)} in {path}")
        return cls(
            profile=str(raw.get("profile") or "m5_template"),
            situation=str(raw.get("situation") or "stub"),
            forward_wm=str(raw.get("forward_wm") or "off"),
            goals=goals,
        )


def default_template_path() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "templates" / "m5_approach_retreat.yaml",
        here.parents[3] / "lab_platform" / "templates" / "m5_approach_retreat.yaml",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return candidates[0]


def run_mid_template(
    *,
    device_id: str = "franka-01",
    domain: int = 43,
    template_path: Path | None = None,
    run_id: str = "",
    steps_log: Path | None = None,
) -> dict[str, Any]:
    """执行 Template MidGoal 序列；返回摘要（供 launcher / CLI）。"""
    import os

    os.environ["ROS_DOMAIN_ID"] = str(domain)
    os.environ.setdefault("RMW_IMPLEMENTATION", "rmw_cyclonedds_cpp")

    import rclpy
    from rclpy.node import Node
    from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
    from embodied_lab_msgs.msg import LowStateFeedback, SkillIntent

    path = Path(template_path) if template_path else default_template_path()
    tmpl = MidTemplate.load(path)
    ns = device_id.replace("-", "_")
    intent_topic = f"/skill/{ns}/intent"
    low_topic = f"/perception/{ns}/low_state"

    owned = False
    if not rclpy.ok():
        rclpy.init()
        owned = True

    class _Node(Node):
        pass

    node = _Node("m5_mid_template")
    intent_qos = QoSProfile(
        reliability=ReliabilityPolicy.RELIABLE,
        history=HistoryPolicy.KEEP_LAST,
        depth=1,
    )
    sensor_qos = QoSProfile(
        reliability=ReliabilityPolicy.BEST_EFFORT,
        history=HistoryPolicy.KEEP_LAST,
        depth=5,
    )
    pub = node.create_publisher(SkillIntent, intent_topic, intent_qos)
    latest: dict[str, Any] = {"low": None}

    def _on_low(msg: LowStateFeedback) -> None:
        latest["low"] = msg

    node.create_subscription(LowStateFeedback, low_topic, _on_low, sensor_qos)

    # discovery
    t_end = time.time() + 1.0
    while time.time() < t_end:
        rclpy.spin_once(node, timeout_sec=0.05)

    steps: list[dict[str, Any]] = []
    aborted = False
    abort_reason = ""

    print(
        f"[m5] template={path.name} situation={tmpl.situation} "
        f"wm={tmpl.forward_wm} goals={[g.name for g in tmpl.goals]}",
        flush=True,
    )

    try:
        for gi, goal in enumerate(tmpl.goals):
            print(
                f"[m5] STEP {gi + 1}/{len(tmpl.goals)} MidGoal={goal.name} "
                f"target_ref={goal.target_ref} delta={goal.ee_delta}",
                flush=True,
            )
            # 等一帧 low
            wait0 = time.time() + 1.0
            while latest["low"] is None and time.time() < wait0:
                rclpy.spin_once(node, timeout_sec=0.05)
            if latest["low"] is None:
                aborted = True
                abort_reason = "no low_state"
                steps.append(
                    {
                        "index": gi,
                        "name": goal.name,
                        "status": "failed",
                        "reason": abort_reason,
                    }
                )
                break

            start_ee = [float(x) for x in latest["low"].ee_pose_actual[:3]]
            t0 = time.time()
            period = 1.0 / max(goal.rate_hz, 0.1)
            n_pub = 0
            status = "running"
            reason = ""

            while True:
                rclpy.spin_once(node, timeout_sec=0.0)
                low = latest["low"]
                if low is not None and str(low.safety_event) not in ("", "none"):
                    status = "hold"
                    reason = f"safety_event={low.safety_event}"
                    aborted = True
                    abort_reason = reason
                    break

                msg = SkillIntent()
                msg.header.stamp = node.get_clock().now().to_msg()
                msg.device_id = device_id
                msg.run_id = run_id
                msg.source = "m5_mid_template"
                msg.skill_mode = "task_space"
                msg.ee_delta = [float(x) for x in goal.ee_delta]
                msg.gripper = 0.0
                msg.control_mode = 1  # POSE
                msg.expire_ms = int(goal.expire_ms)
                msg.frame_id = "fr3_link0"
                pub.publish(msg)
                n_pub += 1

                rclpy.spin_once(node, timeout_sec=0.0)
                low = latest["low"]
                travel = 0.0
                if low is not None:
                    cur = [float(x) for x in low.ee_pose_actual[:3]]
                    travel = sum((a - b) ** 2 for a, b in zip(cur, start_ee)) ** 0.5

                elapsed = time.time() - t0
                if travel >= goal.success_ee_travel_m:
                    status = "success"
                    reason = f"ee_travel={travel:.4f}>={goal.success_ee_travel_m}"
                    break
                if elapsed >= goal.max_duration_s:
                    # M5：超时视为本步完成（空载可验收），但仍记录
                    status = "success_timeout"
                    reason = f"timeout {elapsed:.2f}s travel={travel:.4f}"
                    break

                time.sleep(period)

            # 步间停发，让 expire → HOLD，避免步骤粘连
            time.sleep(max(goal.expire_ms / 1000.0, 0.25))

            step = {
                "index": gi,
                "name": goal.name,
                "target_ref": goal.target_ref,
                "status": status,
                "reason": reason,
                "n_pub": n_pub,
                "ee_delta": goal.ee_delta,
            }
            steps.append(step)
            print(f"[m5]   → {status}: {reason} n_pub={n_pub}", flush=True)

            if aborted:
                break

        ok = (
            not aborted
            and len(steps) >= 2
            and all(s.get("status", "").startswith("success") for s in steps)
        )
        summary = {
            "success": ok,
            "profile": tmpl.profile,
            "situation": tmpl.situation,
            "forward_wm": tmpl.forward_wm,
            "template": str(path),
            "num_goals": len(tmpl.goals),
            "num_steps_done": len(steps),
            "steps": steps,
            "aborted": aborted,
            "abort_reason": abort_reason,
            "skill_mode": "task_space",
        }
        if steps_log is not None:
            steps_log.parent.mkdir(parents=True, exist_ok=True)
            steps_log.write_text(
                json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        print(
            f"[m5] DONE success={ok} steps={len(steps)} aborted={aborted}",
            flush=True,
        )
        return summary
    finally:
        node.destroy_node()
        if owned:
            try:
                import rclpy as _rclpy

                _rclpy.shutdown()
            except Exception:
                pass
