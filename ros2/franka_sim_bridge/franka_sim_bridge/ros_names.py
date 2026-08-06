"""ROS2 topic/service 命名：台账 device_id → topic 段（禁止 '-'）。"""


def topic_device_id(device_id: str) -> str:
    """如 franka-01 → franka_01。"""
    return device_id.replace("-", "_")
