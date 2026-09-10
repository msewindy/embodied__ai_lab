"""兼容 shim → strategy_runtime（L1）。"""

from strategy_runtime.policy_train import *  # noqa: F403
from strategy_runtime.policy_train import PolicyTrainError, TrainResult, train_lerobot_state

__all__ = ["PolicyTrainError", "TrainResult", "train_lerobot_state"]
