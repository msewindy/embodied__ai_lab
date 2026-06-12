from __future__ import annotations

import json
from pathlib import Path

from lab_platform.artifacts.registry import ArtifactRegistry
from lab_platform.config import LabConfig
from lab_platform.protocols import IndexClient


class IsaacPipelineHooks:
    """Pipeline A 产出收录 — 真实逻辑，Isaac 执行由 Stub 替代。"""

    def __init__(self, config: LabConfig, index: IndexClient) -> None:
        self._config = config
        self._registry = ArtifactRegistry(config, index)

    def register_outputs(
        self,
        isaac_job_id: str,
        kind: str,
        task_id: str,
        native_dir: Path,
        eval_protocol_id: str | None,
        policy_id: str | None = None,
    ) -> list[str]:
        aids: list[str] = []
        if kind == "train":
            pid = self._registry.register_policy(isaac_job_id, task_id, native_dir)
            aids.append(pid)
        elif kind == "eval":
            metrics_path = native_dir / "metrics.json"
            metrics = (
                json.loads(metrics_path.read_text(encoding="utf-8"))
                if metrics_path.exists()
                else {"success_rate": 0.0}
            )
            protocol = eval_protocol_id or "loco_vel_v1"
            eid = self._registry.register_eval(
                isaac_job_id, protocol, metrics, source="sim"
            )
            aids.append(eid)
            if policy_id and metrics.get("success_rate", 0) >= 0.85:
                self._registry.promote_policy(policy_id, "candidate")
                print(f"[PipelineA] policy {policy_id} → candidate")
        manifest = {
            "isaac_job_id": isaac_job_id,
            "job_kind": kind,
            "artifacts_registered": aids,
        }
        run_dir = self._config.data_root / "runs" / "isaac_jobs" / isaac_job_id
        (run_dir / "outputs.manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        return aids
