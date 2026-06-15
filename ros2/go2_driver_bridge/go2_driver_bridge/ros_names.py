"""ROS2 topic/service 命名与 QoS 辅助（与 go2_driver_bridge.ros_names 保持一致）."""

from __future__ import annotations

from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy


def topic_device_id(device_id: str) -> str:
    """台账 device_id（可含 '-'）→ ROS topic 段（仅 '_'）。"""
    return device_id.replace("-", "_")


def sensor_qos() -> QoSProfile:
    """与 Driver Bridge Perception 发布一致（Best Effort）。"""
    return QoSProfile(
        reliability=ReliabilityPolicy.BEST_EFFORT,
        history=HistoryPolicy.KEEP_LAST,
        depth=5,
    )


def latched_qos() -> QoSProfile:
    return QoSProfile(
        reliability=ReliabilityPolicy.RELIABLE,
        durability=DurabilityPolicy.TRANSIENT_LOCAL,
        history=HistoryPolicy.KEEP_LAST,
        depth=1,
    )


def param_bool(node, name: str, default: bool = False) -> bool:
    """Launch 传入的 sim:=true 常为字符串，需显式解析。"""
    if not node.has_parameter(name):
        return default
    value = node.get_parameter(name).value
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "on")
    return default
