"""仿真 GT ObjectPose：按 scene.yaml 名义位姿发布 PoseStamped（Oracle）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_runtime.scene_targets import SceneTargets


def gt_poses_from_scene(
    scene: SceneTargets,
    *,
    cup_grid_id: int | None = None,
) -> dict[str, list[float]]:
    return {
        "red_cup": scene.cup_center_from_cfg(cup_grid_id),
        "bowl": scene.bowl_center_from_cfg(),
    }


def make_pose_stamped(node: Any, xyz: list[float], frame_id: str):
    from geometry_msgs.msg import PoseStamped

    msg = PoseStamped()
    msg.header.stamp = node.get_clock().now().to_msg()
    msg.header.frame_id = frame_id
    msg.pose.position.x = float(xyz[0])
    msg.pose.position.y = float(xyz[1])
    msg.pose.position.z = float(xyz[2])
    msg.pose.orientation.w = 1.0
    return msg


def attach_oracle_publishers(
    node: Any,
    scene: SceneTargets,
    *,
    cup_grid_id: int | None = None,
) -> tuple[Any, Any, dict[str, list[float]]]:
    """在已有 Node 上挂 cup/bowl 发布者；返回 (cup_pub, bowl_pub, poses)。"""
    from geometry_msgs.msg import PoseStamped
    from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

    qos = QoSProfile(
        reliability=ReliabilityPolicy.RELIABLE,
        history=HistoryPolicy.KEEP_LAST,
        depth=1,
    )
    poses = gt_poses_from_scene(scene, cup_grid_id=cup_grid_id)
    cup_pub = node.create_publisher(PoseStamped, scene.cup_topic, qos)
    bowl_pub = node.create_publisher(PoseStamped, scene.bowl_topic, qos)
    return cup_pub, bowl_pub, poses


def run_oracle_publisher(
    *,
    scene_yaml: Path,
    domain: int = 43,
    rate_hz: float = 10.0,
    cup_grid_id: int | None = None,
    duration_s: float | None = None,
) -> None:
    """阻塞发布 cup/bowl PoseStamped，直到 Ctrl-C 或 duration 到期。"""
    import os
    import time

    import rclpy
    from rclpy.node import Node

    os.environ["ROS_DOMAIN_ID"] = str(domain)
    os.environ.setdefault("RMW_IMPLEMENTATION", "rmw_cyclonedds_cpp")

    scene = SceneTargets.load(Path(scene_yaml))

    owned = False
    if not rclpy.ok():
        rclpy.init()
        owned = True

    node = Node("scene_oracle_gt")
    cup_pub, bowl_pub, poses = attach_oracle_publishers(
        node, scene, cup_grid_id=cup_grid_id
    )

    period = 1.0 / max(rate_hz, 0.1)
    t0 = time.time()
    n = 0
    print(
        f"[oracle] scene={scene.path} cup={scene.cup_topic}@{poses['red_cup']} "
        f"bowl={scene.bowl_topic}@{poses['bowl']}",
        flush=True,
    )
    try:
        while rclpy.ok():
            cup_pub.publish(make_pose_stamped(node, poses["red_cup"], scene.frame_id))
            bowl_pub.publish(make_pose_stamped(node, poses["bowl"], scene.frame_id))
            n += 1
            if n % int(max(rate_hz, 1)) == 0:
                print(f"[oracle] published n={n}", flush=True)
            if duration_s is not None and (time.time() - t0) >= duration_s:
                break
            rclpy.spin_once(node, timeout_sec=0.0)
            time.sleep(period)
    finally:
        node.destroy_node()
        if owned:
            try:
                rclpy.shutdown()
            except Exception:
                pass
