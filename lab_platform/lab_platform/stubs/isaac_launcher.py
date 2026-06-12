from __future__ import annotations

import json
import time
from pathlib import Path

from lab_platform.config import LabConfig
from lab_platform.models import RunExecutionResult
from lab_platform.protocols import IsaacLauncher


class StubIsaacLauncher(IsaacLauncher):
    """假 Isaac：sleep + 写 stub checkpoint / metrics。"""

    def __init__(self, config: LabConfig) -> None:
        self._config = config

    def run(
        self, kind: str, task_id: str, workspace: Path, config_path: Path | None
    ) -> tuple[int, Path]:
        time.sleep(self._config.stub_sleep_seconds)
        native = workspace / "native_out"
        native.mkdir(parents=True, exist_ok=True)
        ckpt_dir = native / "checkpoints"
        ckpt_dir.mkdir(exist_ok=True)
        (ckpt_dir / "best.pt").write_text(f"stub checkpoint for {task_id}\n", encoding="utf-8")
        if kind == "eval":
            (native / "metrics.json").write_text(
                json.dumps({"success_rate": 0.92, "episodes": 100}),
                encoding="utf-8",
            )
        (native / "isaac.log").write_text(f"stub isaac {kind} {task_id}\n", encoding="utf-8")
        return 0, native
