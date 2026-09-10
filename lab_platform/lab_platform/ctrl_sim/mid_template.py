"""兼容 shim → strategy_runtime（L1）。新代码请直接 import strategy_runtime。"""

from strategy_runtime.mid_template import *  # noqa: F403
from strategy_runtime.mid_template import MidGoal, MidTemplate, default_template_path, run_mid_template

__all__ = ["MidGoal", "MidTemplate", "default_template_path", "run_mid_template"]
