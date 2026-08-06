"""M4 A 轨录制：10Hz 对齐 SkillIntent + LowStateFeedback → low.jsonl。"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Any


DEFAULT_FPS = 10.0


def _f32_list(arr: Any) -> list[float]:
    if arr is None:
        return []
    return [float(x) for x in arr]


def _intent_to_dict(msg: Any) -> dict[str, Any]:
    return {
        "device_id": str(msg.device_id),
        "run_id": str(msg.run_id),
        "source": str(msg.source),
        "skill_mode": str(msg.skill_mode),
        "ee_delta": _f32_list(msg.ee_delta),
        "gripper": float(msg.gripper),
        "control_mode": int(msg.control_mode),
        "expire_ms": int(msg.expire_ms),
        "frame_id": str(msg.frame_id),
    }


def _low_to_dict(msg: Any) -> dict[str, Any]:
    return {
        "device_id": str(msg.device_id),
        "run_id": str(msg.run_id),
        "frame_id": str(msg.frame_id),
        "ee_pose_actual": _f32_list(msg.ee_pose_actual),
        "ee_pose_desired": _f32_list(msg.ee_pose_desired),
        "q": _f32_list(msg.q),
        "dq": _f32_list(msg.dq),
        "gripper_width": float(msg.gripper_width),
        "tracking_error": float(msg.tracking_error),
        "ik_status": str(msg.ik_status),
        "safety_event": str(msg.safety_event),
        "backend": str(msg.backend),
        "latency_ms": float(msg.latency_ms),
    }


class TrajectoryRecorder:
    """在独立线程中 spin，按 record_fps 写 jsonl。"""

    def __init__(
        self,
        *,
        out_path: Path,
        device_id: str = "franka-01",
        domain: int = 43,
        fps: float = DEFAULT_FPS,
        run_id: str = "",
    ) -> None:
        self.out_path = Path(out_path)
        self.device_id = device_id
        self.domain = domain
        self.fps = max(float(fps), 0.1)
        self.run_id = run_id
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._num_frames = 0
        self._error: str | None = None
        self._started_at = 0.0
        self._stopped_at = 0.0

    @property
    def num_frames(self) -> int:
        return self._num_frames

    def start(self) -> None:
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        self._stop.clear()
        self._num_frames = 0
        self._error = None
        self._started_at = time.time()
        self._thread = threading.Thread(target=self._run, name="m4-recorder", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> dict[str, Any]:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None
        self._stopped_at = time.time()
        return self.stats()

    def stats(self) -> dict[str, Any]:
        ns = self.device_id.replace("-", "_")
        return {
            "path": str(self.out_path),
            "record_fps": self.fps,
            "num_frames": self._num_frames,
            "duration_s": max(0.0, self._stopped_at - self._started_at)
            if self._stopped_at
            else max(0.0, time.time() - self._started_at),
            "topics": [
                f"/skill/{ns}/intent",
                f"/perception/{ns}/low_state",
            ],
            "error": self._error,
        }

    def _run(self) -> None:
        os.environ["ROS_DOMAIN_ID"] = str(self.domain)
        os.environ.setdefault("RMW_IMPLEMENTATION", "rmw_cyclonedds_cpp")
        try:
            import rclpy
            from rclpy.node import Node
            from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
            from embodied_lab_msgs.msg import LowStateFeedback, SkillIntent
        except ImportError as e:
            self._error = f"import failed: {e}"
            return

        # 可能已被 RclpyRos2Bridge init；只在未 init 时 init
        owned_ctx = False
        if not rclpy.ok():
            rclpy.init()
            owned_ctx = True

        ns = self.device_id.replace("-", "_")
        intent_topic = f"/skill/{ns}/intent"
        low_topic = f"/perception/{ns}/low_state"

        class _Node(Node):
            pass

        node = _Node("m4_trajectory_recorder")
        intent_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
        )
        latest: dict[str, Any] = {"intent": None, "low": None}

        def _on_intent(msg: SkillIntent) -> None:
            latest["intent"] = msg

        def _on_low(msg: LowStateFeedback) -> None:
            latest["low"] = msg

        node.create_subscription(SkillIntent, intent_topic, _on_intent, intent_qos)
        node.create_subscription(LowStateFeedback, low_topic, _on_low, sensor_qos)

        period = 1.0 / self.fps
        seq = 0
        try:
            with self.out_path.open("w", encoding="utf-8") as fh:
                next_t = time.monotonic()
                while not self._stop.is_set():
                    rclpy.spin_once(node, timeout_sec=0.02)
                    now = time.monotonic()
                    if now < next_t:
                        continue
                    next_t = now + period
                    low = latest["low"]
                    if low is None:
                        continue
                    intent = latest["intent"]
                    row = {
                        "t": time.time(),
                        "seq": seq,
                        "run_id": self.run_id,
                        "intent": _intent_to_dict(intent) if intent is not None else None,
                        "low": _low_to_dict(low),
                    }
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                    fh.flush()
                    seq += 1
                    self._num_frames = seq
        except Exception as e:  # noqa: BLE001 — worker thread boundary
            self._error = str(e)
        finally:
            node.destroy_node()
            if owned_ctx:
                try:
                    rclpy.shutdown()
                except Exception:
                    pass


def main(argv: list[str] | None = None) -> int:
    """子进程入口：录到 SIGINT/SIGTERM 或 --duration。"""
    p = argparse.ArgumentParser(description="M4 CTRL-SIM trajectory recorder")
    p.add_argument("--out", required=True, help="low.jsonl path")
    p.add_argument("--device-id", default="franka-01")
    p.add_argument("--domain", type=int, default=43)
    p.add_argument("--fps", type=float, default=DEFAULT_FPS)
    p.add_argument("--run-id", default="")
    p.add_argument("--duration", type=float, default=0.0, help=">0 则定时停止")
    args = p.parse_args(argv)

    rec = TrajectoryRecorder(
        out_path=Path(args.out),
        device_id=args.device_id,
        domain=args.domain,
        fps=args.fps,
        run_id=args.run_id,
    )

    def _stop(*_a: Any) -> None:
        rec.stop()

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    rec.start()
    print(
        f"[m4-record] writing {args.out} fps={args.fps} device={args.device_id}",
        flush=True,
    )
    try:
        if args.duration > 0:
            time.sleep(args.duration)
            stats = rec.stop()
        else:
            while rec._thread is not None and rec._thread.is_alive():
                time.sleep(0.2)
            stats = rec.stats()
    except KeyboardInterrupt:
        stats = rec.stop()
    print(json.dumps({"record": stats}, ensure_ascii=False), flush=True)
    return 0 if not stats.get("error") else 1


if __name__ == "__main__":
    raise SystemExit(main())
