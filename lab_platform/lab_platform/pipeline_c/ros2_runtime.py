from __future__ import annotations

import os
from pathlib import Path
from lab_platform.config import LabConfig
from lab_platform.models import RunExecutionResult
from lab_platform.pipeline_c.bringup_runner import Go2BringupRunner
from lab_platform.protocols import IndexClient, RealRuntime
from lab_platform.stubs.real_runtime import StubRealRuntime


def ros2_available() -> bool:
    try:
        import rclpy  # noqa: F401
        return True
    except ImportError:
        return False


class HybridRealRuntime(RealRuntime):
    """ROS 可用且 --ros 时走 Go2BringupRunner，否则 Stub。"""

    def __init__(
        self,
        config: LabConfig,
        index: IndexClient,
        use_ros: bool = False,
        sim: bool = True,
    ) -> None:
        self._stub = StubRealRuntime(config, index)
        self._config = config
        self._use_ros = use_ros and ros2_available()
        self._sim = sim
        self._bringup = Go2BringupRunner(config, sim=sim) if self._use_ros else None

    def bringup(self, run_id: str, device_id: str, run_dir: Path) -> RunExecutionResult:
        if self._bringup is not None:
            try:
                ok, report = self._bringup.run(run_id, device_id, run_dir)
                level = report.bridge_level_after
                print(f"[Go2Bringup] {device_id} → {level} overall={report.overall}")
                return RunExecutionResult(
                    ok,
                    "bringup ok" if ok else "bringup failed",
                    extra={"bridge_level": level, "checks": len(report.checks)},
                )
            except Exception as e:
                print(f"[Go2Bringup] ROS bringup error: {e}")
                if self._use_ros:
                    return RunExecutionResult(
                        False, f"bringup failed: {e}", extra={"bridge_level": "L0"}
                    )
        return self._stub.bringup(run_id, device_id, run_dir)

    def calibrate(
        self, run_id: str, device_id: str, cal_types: list[str], run_dir: Path
    ) -> RunExecutionResult:
        return self._stub.calibrate(run_id, device_id, cal_types, run_dir)

    def collect(self, run_id: str, device_id: str, run_dir: Path) -> RunExecutionResult:
        return self._stub.collect(run_id, device_id, run_dir)

    def deploy(
        self, run_id: str, device_id: str, policy_id: str, run_dir: Path
    ) -> RunExecutionResult:
        return self._stub.deploy(run_id, device_id, policy_id, run_dir)

    def eval_run(
        self,
        run_id: str,
        device_id: str,
        policy_id: str,
        scene_id: str,
        protocol_id: str,
        run_dir: Path,
    ) -> RunExecutionResult:
        return self._stub.eval_run(
            run_id, device_id, policy_id, scene_id, protocol_id, run_dir
        )


class RclpyRos2Bridge:
    """真 ROS2 run_context 发布（Pipeline B/C start/finish）。"""

    def __init__(self) -> None:
        self._node = None
        self._ctx = None

    def _ensure_node(self):
        if self._node is not None:
            return
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
        from embodied_lab_msgs.msg import RunContext
        from std_msgs.msg import Header

        if not rclpy.ok():
            rclpy.init()

        class _CtxNode(Node):
            pass

        node = _CtxNode("lab_run_context")
        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        node._pub = node.create_publisher(RunContext, "/system/run_context", qos)
        node._RunContext = RunContext
        node._Header = Header
        self._node = node

    def publish_run_context(
        self, run_id: str, device_ids: list[str], policy_id: str | None
    ) -> None:
        if not ros2_available():
            from lab_platform.stubs.ros2_bridge import StubRos2Bridge
            StubRos2Bridge().publish_run_context(run_id, device_ids, policy_id)
            return
        self._ensure_node()
        self._ctx = {"run_id": run_id, "device_ids": device_ids, "policy_id": policy_id}
        msg = self._node._RunContext()
        msg.header = self._node._Header()
        msg.header.stamp = self._node.get_clock().now().to_msg()
        msg.run_id = run_id
        msg.run_type = "real_bringup"  # TODO: RunManager 传入真实 run_type
        msg.device_ids = device_ids
        msg.policy_id = policy_id or ""
        msg.operator_id = os.environ.get("LAB_OPERATOR", "p2")
        self._node._pub.publish(msg)
        print(f"[RclpyROS2] run_context → {self._ctx}")

    def clear_run_context(self) -> None:
        if self._node is None:
            if self._ctx:
                print(f"[RclpyROS2] clear run_context (was {self._ctx['run_id']})")
            self._ctx = None
            return
        msg = self._node._RunContext()
        msg.header = self._node._Header()
        msg.header.stamp = self._node.get_clock().now().to_msg()
        msg.run_id = ""
        msg.device_ids = []
        self._node._pub.publish(msg)
        if self._ctx:
            print(f"[RclpyROS2] clear run_context (was {self._ctx['run_id']})")
        self._ctx = None
