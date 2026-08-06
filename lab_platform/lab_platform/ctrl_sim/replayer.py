"""M4 A 轨回放：读 low.jsonl 开环重发 SkillIntent，统计 ee 误差。"""

from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _pose_xyz(pose: list[float] | None) -> list[float] | None:
    if not pose or len(pose) < 3:
        return None
    return [float(pose[0]), float(pose[1]), float(pose[2])]


def _dist(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


class TrajectoryReplayer:
    def __init__(
        self,
        *,
        jsonl_path: Path,
        device_id: str = "franka-01",
        domain: int = 43,
        rate: float = 1.0,
        run_id: str = "",
    ) -> None:
        self.jsonl_path = Path(jsonl_path)
        self.device_id = device_id
        self.domain = domain
        self.rate = max(float(rate), 1e-3)
        self.run_id = run_id

    def run(self) -> dict[str, Any]:
        rows = load_jsonl(self.jsonl_path)
        playable = [r for r in rows if r.get("intent") and r.get("low")]
        if not playable:
            return {
                "success": False,
                "message": "no frames with both intent and low in jsonl",
                "num_frames": len(rows),
                "num_played": 0,
            }

        os.environ["ROS_DOMAIN_ID"] = str(self.domain)
        os.environ.setdefault("RMW_IMPLEMENTATION", "rmw_cyclonedds_cpp")

        import rclpy
        from rclpy.node import Node
        from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
        from embodied_lab_msgs.msg import LowStateFeedback, SkillIntent

        owned = False
        if not rclpy.ok():
            rclpy.init()
            owned = True

        ns = self.device_id.replace("-", "_")
        intent_topic = f"/skill/{ns}/intent"
        low_topic = f"/perception/{ns}/low_state"

        class _Node(Node):
            pass

        node = _Node("m4_trajectory_replayer")
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
        latest_low: dict[str, Any] = {"msg": None}

        def _on_low(msg: LowStateFeedback) -> None:
            latest_low["msg"] = msg

        node.create_subscription(LowStateFeedback, low_topic, _on_low, sensor_qos)

        # discovery
        t_end = time.time() + 1.0
        while time.time() < t_end:
            rclpy.spin_once(node, timeout_sec=0.05)

        errors: list[float] = []
        played = 0
        try:
            for i, row in enumerate(playable):
                intent = row["intent"]
                recorded_xyz = _pose_xyz(row["low"].get("ee_pose_actual"))
                msg = SkillIntent()
                msg.header.stamp = node.get_clock().now().to_msg()
                msg.device_id = intent.get("device_id") or self.device_id
                msg.run_id = self.run_id or intent.get("run_id") or ""
                msg.source = "m4_replay"
                msg.skill_mode = intent.get("skill_mode") or "task_space"
                msg.ee_delta = [float(x) for x in intent.get("ee_delta") or [0] * 6]
                while len(msg.ee_delta) < 6:
                    msg.ee_delta.append(0.0)
                msg.gripper = float(intent.get("gripper") or 0.0)
                msg.control_mode = int(intent.get("control_mode") or 1)
                msg.expire_ms = int(intent.get("expire_ms") or 200)
                msg.frame_id = intent.get("frame_id") or "fr3_link0"
                pub.publish(msg)
                played += 1

                # 等一小段再采状态（开环，给 Sim 跟踪时间）
                step_dt = 0.0
                if i + 1 < len(playable):
                    step_dt = max(0.0, float(playable[i + 1]["t"]) - float(row["t"]))
                if step_dt <= 0:
                    step_dt = 0.1
                sleep_s = step_dt / self.rate
                t_wait = time.time() + sleep_s
                while time.time() < t_wait:
                    rclpy.spin_once(node, timeout_sec=0.02)

                low = latest_low["msg"]
                if low is not None and recorded_xyz is not None:
                    actual = _pose_xyz(list(low.ee_pose_actual))
                    if actual is not None:
                        errors.append(_dist(actual, recorded_xyz))
        finally:
            node.destroy_node()
            if owned:
                try:
                    rclpy.shutdown()
                except Exception:
                    pass

        mean_e = sum(errors) / len(errors) if errors else float("nan")
        max_e = max(errors) if errors else float("nan")
        return {
            "success": played > 0,
            "message": "replay completed" if played else "nothing played",
            "num_frames": len(rows),
            "num_played": played,
            "num_error_samples": len(errors),
            "mean_ee_error_m": mean_e,
            "max_ee_error_m": max_e,
            "rate": self.rate,
            "jsonl": str(self.jsonl_path),
        }
