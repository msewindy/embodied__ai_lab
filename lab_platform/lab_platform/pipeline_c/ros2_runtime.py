from __future__ import annotations

from pathlib import Path
from typing import Any

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
                print(f"[Go2Bringup] ROS bringup error: {e}; falling back to stub")
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
    """真 ROS2 `/system/run_context` 发布（TRANSIENT_LOCAL latched）。"""

    def __init__(self) -> None:
        self._node = None
        self._ctx: dict[str, Any] | None = None

    def _ensure_node(self):
        if self._node is not None:
            return
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
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
        # 给 discovery / latched 匹配一点时间
        for _ in range(5):
            rclpy.spin_once(node, timeout_sec=0.05)

    def _spin(self, n: int = 5) -> None:
        if self._node is None:
            return
        import rclpy

        for _ in range(n):
            rclpy.spin_once(self._node, timeout_sec=0.05)

    def publish_run_context(
        self,
        run_id: str,
        device_ids: list[str],
        policy_id: str | None,
        context: dict[str, Any] | None = None,
    ) -> None:
        ctx = dict(context or {})
        ctx.update(
            {
                "run_id": run_id,
                "device_ids": list(device_ids),
                "policy_id": policy_id,
            }
        )
        if not ros2_available():
            from lab_platform.stubs.ros2_bridge import StubRos2Bridge

            StubRos2Bridge().publish_run_context(run_id, device_ids, policy_id, context=ctx)
            return

        self._ensure_node()
        self._ctx = ctx
        msg = self._node._RunContext()
        msg.header = self._node._Header()
        msg.header.stamp = self._node.get_clock().now().to_msg()
        msg.run_id = run_id
        msg.run_type = str(ctx.get("run_type") or "")
        msg.device_ids = list(device_ids)
        msg.policy_id = policy_id or ""
        msg.experiment_plan_id = str(ctx.get("experiment_plan_id") or "")
        msg.operator_id = str(ctx.get("operator_id") or "")
        msg.task_id = str(ctx.get("task_id") or "")
        msg.eval_protocol_id = str(ctx.get("eval_protocol_id") or "")
        msg.scene_id = str(ctx.get("scene_id") or "")
        self._node._pub.publish(msg)
        self._spin(8)
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
        msg.run_type = ""
        msg.device_ids = []
        msg.policy_id = ""
        self._node._pub.publish(msg)
        self._spin(4)
        if self._ctx:
            print(f"[RclpyROS2] clear run_context (was {self._ctx['run_id']})")
        self._ctx = None
