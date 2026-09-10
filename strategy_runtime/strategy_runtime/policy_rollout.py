"""PolicyBackend rollout：low_state → act → SkillIntent；失败 HOLD。"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import yaml

from strategy_runtime.policy_backend import PolicyAction, PolicyObs, create_backend


def load_rollout_profile(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"invalid profile: {path}")
    return raw


def run_policy_rollout(
    *,
    device_id: str = "franka-01",
    domain: int = 43,
    profile_path: Path | None = None,
    checkpoint: Path | str | None = None,
    backend_name: str = "lerobot_state",
    duration_s: float = 20.0,
    rate_hz: float = 10.0,
    run_id: str = "",
    steps_log: Path | None = None,
    hold_on_miss: bool = True,
) -> dict[str, Any]:
    import os

    os.environ["ROS_DOMAIN_ID"] = str(domain)
    os.environ.setdefault("RMW_IMPLEMENTATION", "rmw_cyclonedds_cpp")

    import rclpy
    from rclpy.node import Node
    from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
    from embodied_lab_msgs.msg import LowStateFeedback, SkillIntent

    cfg: dict[str, Any] = {}
    if profile_path is not None:
        cfg = load_rollout_profile(Path(profile_path))
    backend_name = str(cfg.get("policy_backend") or backend_name)
    ckpt = checkpoint or cfg.get("checkpoint")
    duration_s = float(cfg.get("duration_s") or duration_s)
    rate_hz = float(cfg.get("rate_hz") or rate_hz)
    hold_on_miss = bool(cfg.get("hold_on_miss", hold_on_miss))
    expire_ms = int(cfg.get("expire_ms") or 200)

    backend = create_backend(
        backend_name, checkpoint=ckpt, hold_on_miss=hold_on_miss
    )
    backend.reset({"run_id": run_id, "device_id": device_id})

    ns = device_id.replace("-", "_")
    intent_topic = f"/skill/{ns}/intent"
    low_topic = f"/perception/{ns}/low_state"

    owned = False
    if not rclpy.ok():
        rclpy.init()
        owned = True

    class _Node(Node):
        pass

    node = _Node("m5_policy_rollout")
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

    # wait for state
    t_wait = time.time() + 3.0
    while latest["low"] is None and time.time() < t_wait:
        rclpy.spin_once(node, timeout_sec=0.05)
    if latest["low"] is None:
        backend.close()
        if owned:
            node.destroy_node()
            rclpy.shutdown()
        return {
            "success": False,
            "profile": cfg.get("profile") or "m5_policy_rollout",
            "policy_backend": backend_name,
            "checkpoint": str(ckpt) if ckpt else None,
            "reason": "no low_state",
            "n_pub": 0,
            "n_hold": 0,
        }

    period = 1.0 / max(rate_hz, 0.1)
    t_end = time.time() + max(duration_s, 0.1)
    n_pub = 0
    n_hold = 0
    n_act = 0
    steps: list[dict[str, Any]] = []
    print(
        f"[rollout] backend={backend_name} ckpt={ckpt} "
        f"duration_s={duration_s} rate_hz={rate_hz}",
        flush=True,
    )

    try:
        next_t = time.monotonic()
        while time.time() < t_end:
            rclpy.spin_once(node, timeout_sec=0.02)
            now = time.monotonic()
            if now < next_t:
                continue
            next_t = now + period
            low = latest["low"]
            if low is None:
                n_hold += 1
                _publish_hold(pub, device_id, run_id, expire_ms)
                continue
            obs = PolicyObs(
                q=[float(x) for x in low.q[:7]],
                gripper_width=float(low.gripper_width),
                t=time.time(),
                ee_pose=[float(x) for x in low.ee_pose_actual[:7]],
                run_id=run_id,
            )
            action = backend.act(obs)
            if action.hold:
                n_hold += 1
                _publish_hold(pub, device_id, run_id, expire_ms, reason=action.reason)
                steps.append({"t": obs.t, "hold": True, "reason": action.reason})
            else:
                n_act += 1
                n_pub += 1
                _publish_intent(
                    pub,
                    device_id=device_id,
                    run_id=run_id,
                    action=action,
                    expire_ms=expire_ms,
                )
                if len(steps) < 2000:
                    steps.append(
                        {
                            "t": obs.t,
                            "hold": False,
                            "ee_delta": list(action.ee_delta),
                            "gripper": action.gripper,
                        }
                    )
    finally:
        # 结束发 HOLD，避免悬空 intent
        _publish_hold(pub, device_id, run_id, expire_ms, reason="rollout_end")
        backend.close()
        node.destroy_node()
        if owned:
            try:
                rclpy.shutdown()
            except Exception:
                pass

    summary = {
        "success": n_pub > 0,
        "profile": cfg.get("profile") or "m5_policy_rollout",
        "policy_backend": backend_name,
        "checkpoint": str(ckpt) if ckpt else None,
        "duration_s": duration_s,
        "rate_hz": rate_hz,
        "n_pub": n_pub,
        "n_act": n_act,
        "n_hold": n_hold,
        "skill_mode": "task_space",
    }
    if hasattr(backend, "stats"):
        summary["backend_stats"] = backend.stats()  # type: ignore[attr-defined]
    if steps_log is not None:
        Path(steps_log).parent.mkdir(parents=True, exist_ok=True)
        Path(steps_log).write_text(
            json.dumps({**summary, "steps": steps}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({"rollout": summary}, ensure_ascii=False), flush=True)
    return summary


def _publish_hold(
    pub: Any,
    device_id: str,
    run_id: str,
    expire_ms: int,
    reason: str = "hold",
) -> None:
    from embodied_lab_msgs.msg import SkillIntent

    msg = SkillIntent()
    msg.device_id = device_id
    msg.run_id = run_id
    msg.source = "policy_rollout"
    msg.skill_mode = "hold"
    msg.ee_delta = [0.0] * 6
    msg.gripper = 0.0
    msg.control_mode = 0
    msg.expire_ms = int(expire_ms)
    msg.frame_id = "fr3_link0"
    pub.publish(msg)


def _publish_intent(
    pub: Any,
    *,
    device_id: str,
    run_id: str,
    action: PolicyAction,
    expire_ms: int,
) -> None:
    from embodied_lab_msgs.msg import SkillIntent

    msg = SkillIntent()
    msg.device_id = device_id
    msg.run_id = run_id
    msg.source = "policy_rollout"
    msg.skill_mode = "task_space"
    delta = list(action.ee_delta)[:6]
    while len(delta) < 6:
        delta.append(0.0)
    msg.ee_delta = [float(x) for x in delta]
    msg.gripper = float(action.gripper)
    msg.control_mode = 1
    msg.expire_ms = int(action.expire_ms or expire_ms)
    msg.frame_id = "fr3_link0"
    pub.publish(msg)
