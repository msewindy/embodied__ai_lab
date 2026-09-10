"""L1 PolicyBackend 协议与工厂（STRUCT §6.1）。

换后端不改 L0 / Low msg；断流或推理失败必须 HOLD。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


STATE_DIM = 8
ACTION_DIM = 7


@dataclass
class PolicyObs:
    """与 B 轨 observation.state 对齐：q[7] + gripper_width。"""

    q: list[float]
    gripper_width: float
    t: float = 0.0
    ee_pose: list[float] | None = None
    run_id: str = ""

    def as_state_vec(self) -> list[float]:
        q = list(self.q)[:7]
        while len(q) < 7:
            q.append(0.0)
        return q + [float(self.gripper_width)]


@dataclass
class PolicyAction:
    hold: bool = False
    ee_delta: list[float] = field(default_factory=lambda: [0.0] * 6)
    gripper: float = 0.0
    expire_ms: int = 200
    reason: str = ""

    @classmethod
    def hold_action(cls, reason: str = "hold") -> "PolicyAction":
        return cls(hold=True, reason=reason, ee_delta=[0.0] * 6, gripper=0.0)


class PolicyBackend(Protocol):
    name: str

    def reset(self, context: dict[str, Any] | None = None) -> None: ...

    def act(self, obs: PolicyObs) -> PolicyAction: ...

    def close(self) -> None: ...


class TemplateBackend:
    """占位：相对 Δpose 剧本仍由 mid_template 播放；工厂可识别此名。"""

    name = "template"

    def reset(self, context: dict[str, Any] | None = None) -> None:
        return None

    def act(self, obs: PolicyObs) -> PolicyAction:
        return PolicyAction.hold_action("template backend is mid_template-driven")

    def close(self) -> None:
        return None


class OracleServoBackend:
    """占位：toward/oracle 剧本仍由 mid_template 播放。"""

    name = "oracle_servo"

    def reset(self, context: dict[str, Any] | None = None) -> None:
        return None

    def act(self, obs: PolicyObs) -> PolicyAction:
        return PolicyAction.hold_action("oracle_servo backend is mid_template-driven")

    def close(self) -> None:
        return None


def create_backend(
    name: str,
    *,
    checkpoint: Path | str | None = None,
    hold_on_miss: bool = True,
) -> PolicyBackend:
    key = (name or "template").strip().lower()
    if key in ("template", "rules"):
        return TemplateBackend()
    if key in ("oracle_servo", "oracle"):
        return OracleServoBackend()
    if key in ("lerobot_state", "mlp", "state_mlp"):
        from strategy_runtime.lerobot_state_policy import LerobotStateBackend

        if not checkpoint:
            raise ValueError("lerobot_state backend requires checkpoint path")
        return LerobotStateBackend(Path(checkpoint), hold_on_miss=hold_on_miss)
    raise ValueError(
        f"unknown policy_backend={name!r}; "
        "expected template|oracle_servo|lerobot_state"
    )
