#!/usr/bin/env python3
"""发布 /system/run_context（独立 launch 或 lab 外调试时使用）."""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from std_msgs.msg import Header

from embodied_lab_msgs.msg import RunContext


class RunContextNode(Node):
    def __init__(self) -> None:
        super().__init__("run_context_node")
        self.declare_parameter("run_id", "debug_bringup")
        self.declare_parameter("run_type", "real_bringup")
        self.declare_parameter("device_id", "quadruped-01")
        self.declare_parameter("device_ids", [""])
        self.declare_parameter("operator", "p2")
        self.declare_parameter("policy_id", "")
        self.declare_parameter("experiment_plan_id", "")
        self.declare_parameter("task_id", "")
        self.declare_parameter("eval_protocol_id", "")
        self.declare_parameter("scene_id", "")

        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self._pub = self.create_publisher(RunContext, "/system/run_context", qos)
        self.create_timer(1.0, self._publish)
        self.get_logger().info("run_context_node ready")

    def _publish(self) -> None:
        msg = RunContext()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "lab"
        msg.run_id = self.get_parameter("run_id").get_parameter_value().string_value
        msg.run_type = self.get_parameter("run_type").get_parameter_value().string_value
        ids = list(self.get_parameter("device_ids").get_parameter_value().string_array_value)
        ids = [x for x in ids if x]
        if not ids:
            ids = [self.get_parameter("device_id").get_parameter_value().string_value]
        msg.device_ids = ids
        msg.operator_id = self.get_parameter("operator").get_parameter_value().string_value
        msg.policy_id = self.get_parameter("policy_id").get_parameter_value().string_value
        msg.experiment_plan_id = (
            self.get_parameter("experiment_plan_id").get_parameter_value().string_value
        )
        msg.task_id = self.get_parameter("task_id").get_parameter_value().string_value
        msg.eval_protocol_id = (
            self.get_parameter("eval_protocol_id").get_parameter_value().string_value
        )
        msg.scene_id = self.get_parameter("scene_id").get_parameter_value().string_value
        self._pub.publish(msg)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = RunContextNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
