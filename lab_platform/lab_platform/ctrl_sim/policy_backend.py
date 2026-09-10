"""兼容 shim → strategy_runtime（L1）。"""

from strategy_runtime.policy_backend import *  # noqa: F403
from strategy_runtime.policy_backend import (
    ACTION_DIM,
    STATE_DIM,
    OracleServoBackend,
    PolicyAction,
    PolicyBackend,
    PolicyObs,
    TemplateBackend,
    create_backend,
)

__all__ = [
    "ACTION_DIM",
    "STATE_DIM",
    "OracleServoBackend",
    "PolicyAction",
    "PolicyBackend",
    "PolicyObs",
    "TemplateBackend",
    "create_backend",
]
