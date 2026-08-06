#!/usr/bin/env python3
"""M2 Hello：向 CTRL-SIM 发布相对 Δpose，并打印 LowStateFeedback。

用法（DOMAIN 43，已 source ros2/install）：

  export ROS_DOMAIN_ID=43
  export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
  source /opt/ros/jazzy/setup.bash
  source ~/project/embodied__ai_lab/ros2/install/setup.bash
  python3 lab_platform/scripts/m2_franka_hello.py --dx 0.05 --domain 43
"""

from __future__ import annotations

import argparse
import os
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description="M2 FR3 CTRL-SIM hello (Δpose + low_state)")
    parser.add_argument("--dx", type=float, default=0.05, help="base-frame Δx meters")
    parser.add_argument("--dy", type=float, default=0.0)
    parser.add_argument("--dz", type=float, default=0.0)
    parser.add_argument("--domain", type=int, default=43)
    parser.add_argument("--device-id", default="franka-01")
    parser.add_argument("--rate", type=float, default=10.0, help="intent publish Hz")
    parser.add_argument("--duration", type=float, default=2.0, help="publish duration seconds")
    parser.add_argument("--expire-ms", type=int, default=200)
    parser.add_argument("--gripper", type=float, default=0.0)
    parser.add_argument("--hold-wait", type=float, default=1.5, help="seconds to observe HOLD after stop")
    args = parser.parse_args()

    os.environ["ROS_DOMAIN_ID"] = str(args.domain)

    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
        from embodied_lab_msgs.msg import LowStateFeedback, SkillIntent
    except ImportError as e:
        print(
            "ERROR: cannot import rclpy / embodied_lab_msgs.\n"
            "  1) source /opt/ros/jazzy/setup.bash && source <repo>/ros2/install/setup.bash\n"
            "  2) 若在 lab_platform/.venv 中运行：pip install numpy\n"
            "     （ROS2 定长数组 msg 会 import numpy；或改用 /usr/bin/python3）\n"
            f"  detail: {e}",
            file=sys.stderr,
        )
        return 2

    topic_ns = args.device_id.replace("-", "_")
    intent_topic = f"/skill/{topic_ns}/intent"
    low_topic = f"/perception/{topic_ns}/low_state"

    rclpy.init()
    node = Node("m2_franka_hello")
    # intent：慢环 Reliable；low_state：与 franka_sim_bridge 一致用 BestEffort
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
    last: dict = {"msg": None}

    def _on_low(msg: LowStateFeedback) -> None:
        last["msg"] = msg

    node.create_subscription(LowStateFeedback, low_topic, _on_low, sensor_qos)

    # 等 discovery
    t_end = time.time() + 1.0
    while time.time() < t_end:
        rclpy.spin_once(node, timeout_sec=0.05)

    period = 1.0 / max(args.rate, 0.1)
    n_pub = max(1, int(args.duration * args.rate))
    print(
        f"[m2] domain={args.domain} pub {intent_topic} dx={args.dx} "
        f"n={n_pub} rate={args.rate}Hz expire_ms={args.expire_ms}"
    )

    for i in range(n_pub):
        msg = SkillIntent()
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.device_id = args.device_id
        msg.source = "m2_franka_hello"
        msg.skill_mode = "task_space"
        msg.ee_delta = [float(args.dx), float(args.dy), float(args.dz), 0.0, 0.0, 0.0]
        msg.gripper = float(args.gripper)
        msg.control_mode = 1  # POSE
        msg.expire_ms = int(args.expire_ms)
        msg.frame_id = "fr3_link0"
        pub.publish(msg)
        rclpy.spin_once(node, timeout_sec=0.0)
        if last["msg"] is not None and (i % max(1, int(args.rate)) == 0):
            _print_low(last["msg"])
        time.sleep(period)

    print(f"[m2] stop publishing; wait {args.hold_wait}s for HOLD...")
    t_hold = time.time() + args.hold_wait
    while time.time() < t_hold:
        rclpy.spin_once(node, timeout_sec=0.05)
        if last["msg"] is not None:
            _print_low(last["msg"])

    if last["msg"] is None:
        print(
            "[m2] WARN: no LowStateFeedback received. "
            "Is franka_sim_bridge running and Isaac Play + JointStates up?",
            file=sys.stderr,
        )
        node.destroy_node()
        rclpy.shutdown()
        return 1

    m = last["msg"]
    print("[m2] final low_state:")
    _print_low(m, force=True)
    ok = (
        m.backend == "isaac_sim"
        and len(m.q) == 7
        and len(m.ee_pose_actual) == 7
        and m.ik_status in ("ok", "limited", "hold", "idle")
    )
    node.destroy_node()
    rclpy.shutdown()
    print("[m2] PASS field check" if ok else "[m2] FAIL field check")
    return 0 if ok else 1


def _print_low(m, force: bool = False) -> None:
    # 节流：非 force 时由调用方控制频率
    # ROS2 定长数组字段在 Python 侧常为 numpy.ndarray，不能用 `if m.q` 判空
    ax = float(m.ee_pose_actual[0]) if len(m.ee_pose_actual) >= 1 else float("nan")
    dx = float(m.ee_pose_desired[0]) if len(m.ee_pose_desired) >= 1 else float("nan")
    q0 = float(m.q[0]) if len(m.q) >= 1 else float("nan")
    print(
        f"  low: backend={m.backend} ik={m.ik_status} safety={m.safety_event} "
        f"ee_x={ax:.4f} des_x={dx:.4f} track={m.tracking_error:.4f} "
        f"grip_w={m.gripper_width:.4f} q0={q0:.3f}"
    )


if __name__ == "__main__":
    sys.exit(main())
