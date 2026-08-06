#!/usr/bin/env python3
"""FR3 CTRL-SIM Low bridge（TECH-02 ↔ Isaac 官方 JointStates）。

物理侧约定（选项 A · 优先）：
  - Isaac Sim 加载官方 FR3 USD，启用 ``isaacsim.ros2.bridge``
  - 按 NVIDIA 教程搭 JointStates OmniGraph：
    https://docs.isaacsim.omniverse.nvidia.com/6.0.0/ros2_tutorials/tutorial_ros2_manipulation.html
  - 本节点订阅官方 ``/joint_states``，发布官方 ``/joint_command``
    （消息形态对齐 IsaacSim-ros_workspaces ``isaac_tutorials/ros2_publisher.py``）

实验室契约侧：
  - sub ``/skill/{device}/intent`` (SkillIntent, task_space)
  - pub ``/perception/{device}/low_state`` (LowStateFeedback)
  - expire_ms 超时 → HOLD（保持最后 joint 指令）

真机期（Phase-2）应改挂 franka_ros2 官方控制器
（如 cartesian_impedance / joint_impedance_with_ik），本包仅作 CTRL-SIM 适配。
"""

from __future__ import annotations

import time
from typing import List, Optional

import numpy as np
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import JointState
from std_msgs.msg import Header

from embodied_lab_msgs.msg import LowStateFeedback, SkillIntent
from franka_sim_bridge.fr3_kinematics import (
    Q_HOME,
    apply_ee_delta,
    fk_tcp,
    pose7_from_T,
)
from franka_sim_bridge.ros_names import topic_device_id

# Isaac Sim FR3 资产常见关节名（与 Content Browser FrankaFR3 对齐；可被参数覆盖）
DEFAULT_ARM_JOINTS = [
    "fr3_joint1",
    "fr3_joint2",
    "fr3_joint3",
    "fr3_joint4",
    "fr3_joint5",
    "fr3_joint6",
    "fr3_joint7",
]
DEFAULT_FINGER_JOINTS = ["fr3_finger_joint1", "fr3_finger_joint2"]

# gripper∈[0,1] → 单指开口半宽（m）；全开约 0.04/指 → 总宽 0.08（数据契约）
GRIPPER_WIDTH_OPEN = 0.080


class FrankaSimBridgeNode(Node):
    def __init__(self) -> None:
        super().__init__("franka_sim_bridge")
        self.declare_parameter("device_id", "franka-01")
        self.declare_parameter("backend", "isaac_sim")
        self.declare_parameter("joint_states_topic", "/joint_states")
        self.declare_parameter("joint_command_topic", "/joint_command")
        self.declare_parameter("control_hz", 50.0)
        self.declare_parameter("default_expire_ms", 200)
        self.declare_parameter("max_ee_delta_m", 0.08)
        self.declare_parameter("max_ee_delta_rad", 0.25)
        self.declare_parameter("frame_id", "fr3_link0")
        self.declare_parameter("arm_joint_names", DEFAULT_ARM_JOINTS)
        self.declare_parameter("finger_joint_names", DEFAULT_FINGER_JOINTS)
        self.declare_parameter("hold_on_expire", True)

        self.device_id = self.get_parameter("device_id").get_parameter_value().string_value
        self.backend = self.get_parameter("backend").get_parameter_value().string_value
        self.frame_id = self.get_parameter("frame_id").get_parameter_value().string_value
        self.default_expire_ms = int(
            self.get_parameter("default_expire_ms").get_parameter_value().integer_value
        )
        self.max_ee_delta_m = float(
            self.get_parameter("max_ee_delta_m").get_parameter_value().double_value
        )
        self.max_ee_delta_rad = float(
            self.get_parameter("max_ee_delta_rad").get_parameter_value().double_value
        )
        self.hold_on_expire = bool(
            self.get_parameter("hold_on_expire").get_parameter_value().bool_value
        )
        arm_names = self.get_parameter("arm_joint_names").get_parameter_value().string_array_value
        finger_names = (
            self.get_parameter("finger_joint_names").get_parameter_value().string_array_value
        )
        self.arm_joint_names: List[str] = list(arm_names) if arm_names else list(DEFAULT_ARM_JOINTS)
        self.finger_joint_names: List[str] = (
            list(finger_names) if finger_names else list(DEFAULT_FINGER_JOINTS)
        )

        self._topic_ns = topic_device_id(self.device_id)
        self._q = Q_HOME.copy()
        self._dq = np.zeros(7, dtype=np.float64)
        self._q_cmd = Q_HOME.copy()
        self._q_hold = Q_HOME.copy()
        self._ee_des = pose7_from_T(fk_tcp(self._q))
        self._gripper = 0.0  # 0=开
        self._have_state = False
        self._ik_status = "idle"
        self._safety_event = "none"
        self._run_id = ""
        self._last_intent_mono: Optional[float] = None
        self._expire_ms = self.default_expire_ms
        self._holding = True
        self._cmd_t0 = time.monotonic()

        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
        )
        cmd_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        js_topic = (
            self.get_parameter("joint_states_topic").get_parameter_value().string_value
        )
        jc_topic = (
            self.get_parameter("joint_command_topic").get_parameter_value().string_value
        )
        self.create_subscription(JointState, js_topic, self._on_joint_states, sensor_qos)
        self._pub_joint_cmd = self.create_publisher(JointState, jc_topic, cmd_qos)

        intent_topic = f"/skill/{self._topic_ns}/intent"
        low_topic = f"/perception/{self._topic_ns}/low_state"
        self.create_subscription(SkillIntent, intent_topic, self._on_intent, cmd_qos)
        self._pub_low = self.create_publisher(LowStateFeedback, low_topic, sensor_qos)

        hz = float(self.get_parameter("control_hz").get_parameter_value().double_value)
        self.create_timer(1.0 / max(hz, 1.0), self._tick)
        self.get_logger().info(
            f"franka_sim_bridge ready device={self.device_id} backend={self.backend} "
            f"js={js_topic} jc={jc_topic} intent={intent_topic} low={low_topic}"
        )
        self.get_logger().info(
            "Expect Isaac: official FR3 USD + ROS2 JointStates OmniGraph (see package README)."
        )

    def _on_joint_states(self, msg: JointState) -> None:
        name_to_i = {n: i for i, n in enumerate(msg.name)}
        q = self._q.copy()
        dq = self._dq.copy()
        ok = 0
        for j, jn in enumerate(self.arm_joint_names):
            if jn in name_to_i:
                idx = name_to_i[jn]
                if idx < len(msg.position):
                    q[j] = float(msg.position[idx])
                    ok += 1
                if idx < len(msg.velocity):
                    dq[j] = float(msg.velocity[idx])
        if ok >= 7:
            self._q = q
            self._dq = dq
            self._have_state = True
            if self._holding:
                self._q_hold = q.copy()

    def _on_intent(self, msg: SkillIntent) -> None:
        if msg.device_id and msg.device_id != self.device_id:
            return
        if msg.run_id:
            self._run_id = msg.run_id

        mode = (msg.skill_mode or "").strip().lower()
        if mode in ("", "idle", "hold"):
            self._holding = True
            self._q_hold = self._q.copy()
            self._ik_status = "hold"
            self._last_intent_mono = time.monotonic()
            return

        if mode != "task_space":
            self.get_logger().warn(f"unsupported skill_mode={msg.skill_mode}; HOLD")
            self._holding = True
            self._ik_status = "hold"
            return

        delta = np.array(list(msg.ee_delta), dtype=np.float64)
        if delta.shape[0] != 6:
            self._safety_event = "bad_ee_delta"
            self._ik_status = "failed"
            return

        # 软件限幅（M2 安全最小集）
        if np.any(np.abs(delta[:3]) > self.max_ee_delta_m) or np.any(
            np.abs(delta[3:]) > self.max_ee_delta_rad
        ):
            self._safety_event = "ee_delta_limited"
            delta[:3] = np.clip(delta[:3], -self.max_ee_delta_m, self.max_ee_delta_m)
            delta[3:] = np.clip(delta[3:], -self.max_ee_delta_rad, self.max_ee_delta_rad)
        else:
            self._safety_event = "none"

        q_now = self._q if self._have_state else Q_HOME
        q_des, status, pose_des = apply_ee_delta(q_now, delta)
        self._q_cmd = q_des
        self._ee_des = pose_des
        self._ik_status = status
        self._gripper = float(np.clip(msg.gripper, 0.0, 1.0))
        self._expire_ms = int(msg.expire_ms) if msg.expire_ms > 0 else self.default_expire_ms
        self._last_intent_mono = time.monotonic()
        self._holding = False
        if msg.frame_id:
            self.frame_id = msg.frame_id

    def _finger_positions(self) -> List[float]:
        # 0=开 → 半宽 0.04；1=闭 → 0
        half = 0.5 * GRIPPER_WIDTH_OPEN * (1.0 - self._gripper)
        return [half, half]

    def _publish_joint_command(self) -> None:
        msg = JointState()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = list(self.arm_joint_names) + list(self.finger_joint_names)
        q = self._q_hold if self._holding else self._q_cmd
        msg.position = q.tolist() + self._finger_positions()
        self._pub_joint_cmd.publish(msg)

    def _publish_low_state(self) -> None:
        T = fk_tcp(self._q)
        actual = pose7_from_T(T)
        tracking = float(np.linalg.norm(actual[:3] - self._ee_des[:3]))
        width = GRIPPER_WIDTH_OPEN * (1.0 - self._gripper)

        out = LowStateFeedback()
        out.header = Header()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = self.frame_id
        out.device_id = self.device_id
        out.run_id = self._run_id
        out.frame_id = self.frame_id
        out.ee_pose_actual = actual.astype(np.float32).tolist()
        out.ee_pose_desired = self._ee_des.astype(np.float32).tolist()
        out.q = self._q.astype(np.float32).tolist()
        out.dq = self._dq.astype(np.float32).tolist()
        out.tau_ext = [0.0] * 7
        out.wrench_ee = [0.0] * 6
        out.gripper_width = float(width)
        out.tracking_error = tracking
        out.contact_flag = False
        out.ik_status = self._ik_status
        out.safety_event = self._safety_event
        out.backend = self.backend
        out.latency_ms = float((time.monotonic() - self._cmd_t0) * 1000.0)
        self._pub_low.publish(out)
        self._cmd_t0 = time.monotonic()

    def _tick(self) -> None:
        if self._last_intent_mono is not None and not self._holding:
            age_ms = (time.monotonic() - self._last_intent_mono) * 1000.0
            if self.hold_on_expire and age_ms > float(self._expire_ms):
                self._holding = True
                self._q_hold = self._q_cmd.copy()
                self._ik_status = "hold"

        self._publish_joint_command()
        self._publish_low_state()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = FrankaSimBridgeNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    main()
