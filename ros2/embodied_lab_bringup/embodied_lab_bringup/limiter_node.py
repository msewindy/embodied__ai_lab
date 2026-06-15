#!/usr/bin/env python3
"""Limiter：clip 关节指令后转发至 joint_command_limited（BU-06）."""

from __future__ import annotations

import rclpy
from rclpy.node import Node

from embodied_lab_msgs.msg import JointCommand, SafetyState
from go2_driver_bridge.ros_names import topic_device_id


class LimiterNode(Node):
    def __init__(self) -> None:
        super().__init__("limiter_node")
        self.declare_parameter("device_id", "quadruped-01")
        self.declare_parameter("max_joint_pos", 2.0)
        self._device_id = self.get_parameter("device_id").get_parameter_value().string_value
        self._topic_ns = topic_device_id(self._device_id)
        self._max_pos = self.get_parameter("max_joint_pos").get_parameter_value().double_value
        self._last_clip_count = 0
        self._estop = False

        internal = f"/internal/{self._topic_ns}"
        self._pub = self.create_publisher(JointCommand, f"{internal}/joint_command_limited", 10)
        self.create_subscription(JointCommand, f"{internal}/joint_command", self._on_cmd, 10)
        self.create_subscription(SafetyState, "/safety/global_state", self._on_safety, 10)
        self.get_logger().info(f"limiter_node ready device={self._device_id} max_pos={self._max_pos}")

    def _on_safety(self, msg: SafetyState) -> None:
        self._estop = msg.level >= 2

    def _on_cmd(self, msg: JointCommand) -> None:
        out = JointCommand()
        out.header = msg.header
        out.device_id = msg.device_id
        out.mode = msg.mode
        out.q = []
        out.dq = list(msg.dq) if msg.dq else []
        out.tau = list(msg.tau) if msg.tau else []
        out.kp = list(msg.kp) if msg.kp else []
        out.kd = list(msg.kd) if msg.kd else []

        clipped = 0
        if self._estop:
            out.q = [0.0] * len(msg.q)
            out.tau = [0.0] * len(msg.tau) if msg.tau else []
        else:
            for v in msg.q:
                if abs(v) > self._max_pos:
                    out.q.append(max(-self._max_pos, min(self._max_pos, v)))
                    clipped += 1
                else:
                    out.q.append(v)
        self._last_clip_count = clipped
        self._pub.publish(out)

    @property
    def last_clip_count(self) -> int:
        return self._last_clip_count


def main(args=None) -> None:
    rclpy.init(args=args)
    node = LimiterNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
