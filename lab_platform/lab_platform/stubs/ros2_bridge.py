from __future__ import annotations

from typing import Any

from lab_platform.protocols import Ros2Bridge


class StubRos2Bridge(Ros2Bridge):
    """假 ROS2：打印 run_context，不启动 DDS。"""

    _context: dict | None = None

    def publish_run_context(
        self,
        run_id: str,
        device_ids: list[str],
        policy_id: str | None,
        context: dict[str, Any] | None = None,
    ) -> None:
        self._context = {
            "run_id": run_id,
            "device_ids": device_ids,
            "policy_id": policy_id,
            **(context or {}),
        }
        print(f"[StubROS2] run_context → {self._context}")

    def clear_run_context(self) -> None:
        if self._context:
            print(f"[StubROS2] clear run_context (was {self._context['run_id']})")
        self._context = None
