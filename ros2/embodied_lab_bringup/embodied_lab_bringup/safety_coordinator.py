#!/usr/bin/env python3
"""Safety 协调器：发布 /safety/global_state，支持软件 ESTOP（BU-05）."""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from std_msgs.msg import Header, Empty

from embodied_lab_msgs.msg import SafetyState, RunContext
from go2_driver_bridge.ros_names import topic_device_id


class SafetyCoordinatorNode(Node):
    def __init__(self) -> None:
        super().__init__("safety_coordinator")
        self.declare_parameter("device_id", "quadruped-01")
        self._device_id = self.get_parameter("device_id").get_parameter_value().string_value
        self._topic_ns = topic_device_id(self._device_id)
        self._level = 0
        self._source = "operator"
        self._message = "NORMAL"
        self._run_id = ""
        self._speed_scale = 1.0

        latched = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self._pub_global = self.create_publisher(SafetyState, "/safety/global_state", latched)
        self._pub_local = self.create_publisher(
            SafetyState, f"/safety/{self._topic_ns}/local_state", 10
        )
        self.create_subscription(RunContext, "/system/run_context", self._on_run_context, latched)
        self.create_subscription(Empty, "/safety/trigger_estop", self._on_estop, 10)
        self.create_subscription(Empty, "/safety/clear_estop", self._on_clear, 10)
        self.create_timer(0.5, self._publish)
        self.get_logger().info(f"safety_coordinator ready device={self._device_id}")

    def _on_run_context(self, msg: RunContext) -> None:
        self._run_id = msg.run_id

    def _on_estop(self, _msg: Empty) -> None:
        self._level = 2
        self._source = "software_estop"
        self._message = "ESTOP triggered"
        self._speed_scale = 0.0
        self.get_logger().warn("ESTOP triggered")

    def _on_clear(self, _msg: Empty) -> None:
        self._level = 0
        self._source = "operator"
        self._message = "NORMAL"
        self._speed_scale = 1.0
        self.get_logger().info("ESTOP cleared")

    def _build_state(self, device_id: str) -> SafetyState:
        msg = SafetyState()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.level = self._level
        msg.source = self._source
        msg.message = self._message
        msg.run_id = self._run_id
        msg.device_id = device_id
        msg.speed_scale = self._speed_scale
        return msg

    def _publish(self) -> None:
        self._pub_global.publish(self._build_state(""))
        self._pub_local.publish(self._build_state(self._device_id))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = SafetyCoordinatorNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
