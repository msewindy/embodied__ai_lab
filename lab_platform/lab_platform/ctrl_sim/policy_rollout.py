"""兼容 shim → strategy_runtime（L1）。"""

from strategy_runtime.policy_rollout import *  # noqa: F403
from strategy_runtime.policy_rollout import load_rollout_profile, run_policy_rollout

__all__ = ["load_rollout_profile", "run_policy_rollout"]
