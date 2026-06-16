"""ROS2 topic/service 命名：台账 device_id → topic 段（禁止 '-'）."""


def topic_device_id(device_id: str) -> str:
    """如 quadruped-01 → quadruped_01（ROS 名仅允许字母数字与 '_'）。"""
    return device_id.replace("-", "_")
