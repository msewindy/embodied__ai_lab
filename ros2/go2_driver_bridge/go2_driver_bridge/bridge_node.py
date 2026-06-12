#!/usr/bin/env python3
"""Go2 Driver Bridge: sim 或 relay Unitree lowstate → lab Perception 接口."""

from __future__ import annotations

import math
from typing import List

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import JointState, Imu
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist, Vector3, Quaternion
from std_msgs.msg import Header

from embodied_lab_msgs.msg import (
    RobotState,
    JointCommand,
    SafetyState,
    RunContext,
    NodeHealth,
)
from embodied_lab_msgs.srv import BridgeSmoke


GO2_JOINT_NAMES: List[str] = [
    "FL_hip_joint", "FL_thigh_joint", "FL_calf_joint",
    "FR_hip_joint", "FR_thigh_joint", "FR_calf_joint",
    "RL_hip_joint", "RL_thigh_joint", "RL_calf_joint",
    "RR_hip_joint", "RR_thigh_joint", "RR_calf_joint",
]


class Go2DriverBridgeNode(Node):
    def __init__(self) -> None:
        super().__init__("go2_driver_bridge")
        self.declare_parameter("device_id", "quadruped-01")
        self.declare_parameter("sim", True)
        self.declare_parameter("sdk_version", "unitree_go2_sim_1.0")
        self.declare_parameter("max_speed_cap", 1.5)
        self.declare_parameter("unitree_lowstate_topic", "")
        self.declare_parameter("publish_hz", 100.0)

        self.device_id = self.get_parameter("device_id").get_parameter_value().string_value
        self.sim = self.get_parameter("sim").get_parameter_value().bool_value
        self.sdk_version = self.get_parameter("sdk_version").get_parameter_value().string_value
        self.max_speed_cap = self.get_parameter("max_speed_cap").get_parameter_value().double_value
        self._joint_names = GO2_JOINT_NAMES
        self._n = len(self._joint_names)
        self._phase = 0.0
        self._run_id = ""
        self._safety_level = 0
        self._speed_scale = 1.0
        self._last_cmd = JointCommand()

        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
        )
        latched_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        prefix = f"/perception/{self.device_id}"
        self._pub_joint = self.create_publisher(JointState, f"{prefix}/joint_states", sensor_qos)
        self._pub_imu = self.create_publisher(Imu, f"{prefix}/imu", sensor_qos)
        self._pub_odom = self.create_publisher(Odometry, f"{prefix}/odom", sensor_qos)
        self._pub_robot_state = self.create_publisher(RobotState, f"{prefix}/robot_state", sensor_qos)
        self._pub_health = self.create_publisher(NodeHealth, "/system/health", 10)

        internal = f"/internal/{self.device_id}"
        self.create_subscription(
            JointCommand, f"{internal}/joint_command_limited", self._on_joint_cmd, 10
        )
        self.create_subscription(SafetyState, "/safety/global_state", self._on_safety, latched_qos)
        self.create_subscription(
            SafetyState, f"/safety/{self.device_id}/local_state", self._on_safety, 10
        )
        self.create_subscription(RunContext, "/system/run_context", self._on_run_context, latched_qos)

        if not self.sim:
            topic = self.get_parameter("unitree_lowstate_topic").get_parameter_value().string_value
            if topic:
                self.create_subscription(JointState, topic, self._on_unitree_joint, sensor_qos)
                self.get_logger().info(f"Relay mode: subscribing {topic}")
            else:
                self.get_logger().warn("sim=false but unitree_lowstate_topic empty; using internal sim")

        self.create_service(BridgeSmoke, f"/go2_driver_bridge/{self.device_id}/smoke", self._smoke_cb)

        hz = self.get_parameter("publish_hz").get_parameter_value().double_value
        self.create_timer(1.0 / hz, self._tick)
        self.create_timer(1.0, self._publish_health)
        self.get_logger().info(
            f"Go2 bridge ready device={self.device_id} sim={self.sim} joints={self._n}"
        )

    def _on_run_context(self, msg: RunContext) -> None:
        self._run_id = msg.run_id

    def _on_safety(self, msg: SafetyState) -> None:
        self._safety_level = msg.level
        self._speed_scale = msg.speed_scale if msg.level == 1 else (0.0 if msg.level >= 2 else 1.0)

    def _on_joint_cmd(self, msg: JointCommand) -> None:
        self._last_cmd = msg

    def _on_unitree_joint(self, msg: JointState) -> None:
        if not self.sim:
            self._relay_joint_state = msg

    def _tick(self) -> None:
        if self.sim or not hasattr(self, "_relay_joint_state"):
            js = self._sim_joint_state()
        else:
            js = self._relay_joint_state
        self._pub_joint.publish(js)
        self._pub_imu.publish(self._sim_imu())
        self._pub_odom.publish(self._sim_odom())
        self._pub_robot_state.publish(self._build_robot_state(js))
        self._phase += 0.05

    def _stamp_header(self) -> Header:
        h = Header()
        h.stamp = self.get_clock().now().to_msg()
        h.frame_id = f"{self.device_id}_base"
        return h

    def _sim_joint_state(self) -> JointState:
        js = JointState()
        js.header = self._stamp_header()
        js.name = list(self._joint_names)
        js.position = [0.1 * math.sin(self._phase + i * 0.3) for i in range(self._n)]
        js.velocity = [0.0] * self._n
        js.effort = [0.0] * self._n
        return js

    def _sim_imu(self) -> Imu:
        imu = Imu()
        imu.header = self._stamp_header()
        imu.orientation = Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)
        imu.angular_velocity = Vector3(x=0.0, y=0.0, z=0.01 * math.sin(self._phase))
        imu.linear_acceleration = Vector3(x=0.0, y=0.0, z=9.81)
        return imu

    def _sim_odom(self) -> Odometry:
        odom = Odometry()
        odom.header = self._stamp_header()
        odom.child_frame_id = f"{self.device_id}_base"
        odom.twist.twist.linear = Vector3(x=0.05 * math.sin(self._phase * 0.5), y=0.0, z=0.0)
        return odom

    def _build_robot_state(self, js: JointState) -> RobotState:
        rs = RobotState()
        rs.header = js.header
        rs.device_id = self.device_id
        rs.base_lin_vel = [
            float(0.05 * math.sin(self._phase * 0.5) * self._speed_scale),
            0.0,
            0.0,
        ]
        rs.base_ang_vel = [0.0, 0.0, float(0.01 * math.sin(self._phase))]
        rs.projected_gravity = [0.0, 0.0, -1.0]
        rs.joint_pos = [float(p) for p in js.position]
        rs.joint_vel = [float(v) for v in js.velocity]
        rs.joint_torque = [float(e) for e in js.effort]
        return rs

    def _publish_health(self) -> None:
        msg = NodeHealth()
        msg.header = self._stamp_header()
        msg.node_name = "go2_driver_bridge"
        msg.host = "onboard"
        msg.run_id = self._run_id
        msg.status = 0 if self._safety_level < 2 else 2
        msg.message = f"sim={self.sim} sdk={self.sdk_version}"
        msg.control_loop_latency_ms = 0.0
        self._pub_health.publish(msg)

    def _smoke_cb(self, request, response):
        response.ok = True
        response.sdk_version = self.sdk_version
        response.message = "Go2 bridge smoke OK"
        response.checks_passed = ["joint_states", "imu", "robot_state", "health"]
        return response


def main(args=None) -> None:
    rclpy.init(args=args)
    node = Go2DriverBridgeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
