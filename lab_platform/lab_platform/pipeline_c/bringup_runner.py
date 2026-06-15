from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lab_platform.config import LabConfig
from lab_platform.pipeline_c.bridge_updater import load_vendor_sdk_version, update_bridge_level


def _topic_device_id(device_id: str) -> str:
    return device_id.replace("-", "_")


def _sensor_qos():
    from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

    return QoSProfile(
        reliability=ReliabilityPolicy.BEST_EFFORT,
        history=HistoryPolicy.KEEP_LAST,
        depth=5,
    )


@dataclass
class CheckResult:
    id: str
    result: str
    detail: str = ""
    latency_ms: float | None = None


@dataclass
class BringupReport:
    run_id: str
    device_id: str
    checks: list[CheckResult] = field(default_factory=list)
    overall: str = "fail"
    bridge_level_after: str = "L0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "device_id": self.device_id,
            "checks": [
                {
                    "id": c.id,
                    "result": c.result,
                    **({"detail": c.detail} if c.detail else {}),
                    **({"latency_ms": c.latency_ms} if c.latency_ms is not None else {}),
                }
                for c in self.checks
            ],
            "overall": self.overall,
            "bridge_level_after": self.bridge_level_after,
        }


class Go2BringupRunner:
    """执行 BU-01..06；需 ROS2 Jazzy + embodied_lab 栈已 launch。"""

    def __init__(self, config: LabConfig, sim: bool = True) -> None:
        self._config = config
        self._sim = sim

    def run(self, run_id: str, device_id: str, run_dir: Path) -> tuple[bool, BringupReport]:
        try:
            import rclpy
            from rclpy.node import Node
            from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
            from sensor_msgs.msg import JointState
            from std_msgs.msg import Empty, Header
            from embodied_lab_msgs.msg import NodeHealth, SafetyState, JointCommand, RunContext
            from embodied_lab_msgs.srv import BridgeSmoke
        except ImportError as e:
            raise RuntimeError(f"ROS2 deps missing: {e}") from e

        report = BringupReport(run_id=run_id, device_id=device_id)
        expected_sdk = load_vendor_sdk_version(self._config, device_id) or (
            "unitree_go2_sim_1.0" if self._sim else "unitree_go2_sdk_1.0"
        )

        if not rclpy.ok():
            rclpy.init()

        topic_ns = _topic_device_id(device_id)
        operator_id = self._config.operator

        class _Checker(Node):
            def __init__(self) -> None:
                super().__init__("bringup_checker")
                self.joint_count = 0
                self.health_seen = False
                self.estop_seen = False
                self.estop_cleared = False
                self.limited_max: float | None = None
                latched = QoSProfile(
                    reliability=ReliabilityPolicy.RELIABLE,
                    durability=DurabilityPolicy.TRANSIENT_LOCAL,
                    history=HistoryPolicy.KEEP_LAST,
                    depth=1,
                )
                self.create_subscription(
                    JointState,
                    f"/perception/{topic_ns}/joint_states",
                    self._on_joint,
                    _sensor_qos(),
                )
                self.create_subscription(NodeHealth, "/system/health", self._on_health, 10)
                self.create_subscription(
                    SafetyState, "/safety/global_state", self._on_safety, latched
                )
                self.create_subscription(
                    JointCommand,
                    f"/internal/{topic_ns}/joint_command_limited",
                    self._on_limited,
                    10,
                )
                self._ctx_pub = self.create_publisher(RunContext, "/system/run_context", latched)
                self._cmd_pub = self.create_publisher(
                    JointCommand, f"/internal/{topic_ns}/joint_command", 10
                )
                self._estop_pub = self.create_publisher(Empty, "/safety/trigger_estop", 10)
                self._clear_pub = self.create_publisher(Empty, "/safety/clear_estop", 10)
                self._smoke = self.create_client(
                    BridgeSmoke, f"/go2_driver_bridge/{topic_ns}/smoke"
                )

            def _on_joint(self, _msg: JointState) -> None:
                self.joint_count += 1

            def _on_health(self, msg: NodeHealth) -> None:
                if msg.node_name == "go2_driver_bridge" and msg.status == 0:
                    self.health_seen = True

            def _on_safety(self, msg: SafetyState) -> None:
                if msg.level >= 2:
                    self.estop_seen = True
                elif msg.level == 0 and self.estop_seen:
                    self.estop_cleared = True

            def _on_limited(self, msg: JointCommand) -> None:
                if msg.q:
                    self.limited_max = max(abs(v) for v in msg.q)

            def publish_run_context(self) -> None:
                msg = RunContext()
                msg.header = Header()
                msg.header.stamp = self.get_clock().now().to_msg()
                msg.run_id = run_id
                msg.run_type = "real_bringup"
                msg.device_ids = [device_id]
                msg.operator_id = operator_id
                self._ctx_pub.publish(msg)

        node = _Checker()
        t0 = time.perf_counter()

        # BU-01: ROS2 域连通（health topic 可见）
        deadline = time.time() + 5.0
        while time.time() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
            if node.health_seen:
                break
        latency = (time.perf_counter() - t0) * 1000
        report.checks.append(
            CheckResult(
                "BU-01",
                "pass" if node.health_seen else "fail",
                "go2_driver_bridge health OK" if node.health_seen else "no health from bridge",
                round(latency, 1),
            )
        )

        # BU-02: Bridge smoke service
        t0 = time.perf_counter()
        smoke_ok = False
        smoke_detail = ""
        if node._smoke.wait_for_service(timeout_sec=5.0):
            req = BridgeSmoke.Request()
            future = node._smoke.call_async(req)
            rclpy.spin_until_future_complete(node, future, timeout_sec=5.0)
            if future.done() and future.result() is not None:
                resp = future.result()
                smoke_ok = resp.ok
                smoke_detail = resp.message
        else:
            smoke_detail = "BridgeSmoke service unavailable"
        report.checks.append(
            CheckResult(
                "BU-02",
                "pass" if smoke_ok else "fail",
                smoke_detail,
                round((time.perf_counter() - t0) * 1000, 1),
            )
        )

        node.publish_run_context()

        # BU-03: joint_states ≥ 50Hz over 5s (expect ~250+ msgs at 100Hz)
        node.joint_count = 0
        t0 = time.perf_counter()
        end = time.time() + 5.0
        while time.time() < end:
            rclpy.spin_once(node, timeout_sec=0.05)
        hz = node.joint_count / max(0.001, time.perf_counter() - t0)
        report.checks.append(
            CheckResult(
                "BU-03",
                "pass" if hz >= 50 else "fail",
                f"joint_states ~{hz:.1f} Hz ({node.joint_count} msgs/5s)",
                round((time.perf_counter() - t0) * 1000, 1),
            )
        )

        # BU-04: SDK version
        sdk_ok = False
        sdk_detail = ""
        if node._smoke.service_is_ready():
            req = BridgeSmoke.Request()
            future = node._smoke.call_async(req)
            rclpy.spin_until_future_complete(node, future, timeout_sec=3.0)
            if future.done() and future.result():
                ver = future.result().sdk_version
                sdk_ok = ver == expected_sdk or (self._sim and "sim" in ver)
                sdk_detail = f"bridge={ver} expected={expected_sdk}"
        report.checks.append(
            CheckResult("BU-04", "pass" if sdk_ok else "fail", sdk_detail)
        )

        # BU-05: ESTOP trigger + clear
        node.estop_seen = False
        node.estop_cleared = False
        node._estop_pub.publish(Empty())
        deadline = time.time() + 3.0
        while time.time() < deadline:
            rclpy.spin_once(node, timeout_sec=0.05)
            if node.estop_seen:
                break
        node._clear_pub.publish(Empty())
        deadline = time.time() + 3.0
        while time.time() < deadline:
            rclpy.spin_once(node, timeout_sec=0.05)
            if node.estop_cleared:
                break
        bu05_ok = node.estop_seen and node.estop_cleared
        report.checks.append(
            CheckResult(
                "BU-05",
                "pass" if bu05_ok else "fail",
                f"estop={node.estop_seen} cleared={node.estop_cleared}",
            )
        )

        # BU-06: Limiter clip
        node.limited_max = None
        over = JointCommand()
        over.header = Header()
        over.header.stamp = node.get_clock().now().to_msg()
        over.device_id = device_id
        over.q = [99.0] * 12
        node._cmd_pub.publish(over)
        deadline = time.time() + 2.0
        while time.time() < deadline and node.limited_max is None:
            rclpy.spin_once(node, timeout_sec=0.05)
        clip_ok = node.limited_max is not None and node.limited_max <= 2.01
        report.checks.append(
            CheckResult(
                "BU-06",
                "pass" if clip_ok else "fail",
                f"limited max |q|={node.limited_max}",
            )
        )

        node.destroy_node()
        all_pass = all(c.result == "pass" for c in report.checks)
        report.overall = "pass" if all_pass else "fail"
        report.bridge_level_after = "L1" if all_pass else "L0"

        results = run_dir / "results"
        results.mkdir(exist_ok=True)
        (results / "bringup_report.json").write_text(
            json.dumps(report.to_dict(), indent=2), encoding="utf-8"
        )
        if all_pass:
            update_bridge_level(self._config, device_id, "L1", run_id)

        return all_pass, report
