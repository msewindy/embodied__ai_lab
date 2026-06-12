from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LabConfig:
    data_root: Path
    operator: str = "p2"
    project_id: str = "lab-default"
    lock_ttl_seconds: int = 3600
    stub_sleep_seconds: float = 0.05

    @classmethod
    def from_env(cls, data_root: Path | None = None) -> LabConfig:
        root = data_root or Path(os.environ.get("LAB_DATA_ROOT", "data"))
        return cls(
            data_root=root.resolve(),
            operator=os.environ.get("LAB_OPERATOR", "p2"),
            project_id=os.environ.get("LAB_PROJECT_ID", "lab-default"),
        )

    @property
    def index_db(self) -> Path:
        return self.data_root / "index.db"

    @property
    def runs_dir(self) -> Path:
        return self.data_root / "runs"

    @property
    def artifacts_dir(self) -> Path:
        return self.data_root / "artifacts"

    @property
    def registry_dir(self) -> Path:
        return self.data_root / "registry"

    @property
    def tasks_dir(self) -> Path:
        return self.data_root / "tasks"

    @property
    def jobs_dir(self) -> Path:
        return self.data_root / "jobs"
