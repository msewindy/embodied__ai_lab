from __future__ import annotations

import json
from pathlib import Path

import yaml

from ..config import LabConfig
from ..ids import make_calibration_id, make_demo_id, make_eval_id, make_policy_id
from ..models import ArtifactRecord, now_iso
from ..protocols import IndexClient


class ArtifactRegistry:
    def __init__(self, config: LabConfig, index: IndexClient) -> None:
        self._config = config
        self._index = index

    def register_policy(
        self,
        producer_run_id: str,
        task_id: str,
        native_dir: Path,
        lifecycle: str = "draft",
    ) -> str:
        policy_id = make_policy_id(task_id.replace("-", "_")[:24])
        root = self._config.artifacts_dir / "policies" / policy_id
        ckpt_src = native_dir / "checkpoints" / "best.pt"
        root.mkdir(parents=True, exist_ok=True)
        ckpt_dst = root / "checkpoints"
        ckpt_dst.mkdir(exist_ok=True)
        if ckpt_src.exists():
            (ckpt_dst / "best.pt").write_text(ckpt_src.read_text(encoding="utf-8"), encoding="utf-8")

        manifest = {
            "policy_id": policy_id,
            "lifecycle_status": lifecycle,
            "source_isaac_job_id": producer_run_id,
            "task_id": task_id,
            "task_domain": self._task_domain(task_id),
            "created_at": now_iso(),
            "checkpoint": {"path": "checkpoints/best.pt", "format": "stub"},
            "onboard_runtime": {"engine": "stub", "node": "policy_runner_low"},
            "supported_devices": ["*"],
        }
        (root / "policy_manifest.yaml").write_text(
            yaml.dump(manifest, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        (root / "producer_run.json").write_text(
            json.dumps({"isaac_job_id": producer_run_id}), encoding="utf-8"
        )
        record = ArtifactRecord(
            artifact_id=policy_id,
            artifact_type="policy",
            lifecycle_status=lifecycle,
            producer_run_id=producer_run_id,
            storage_path=str(root.relative_to(self._config.data_root)),
            metadata={"task_id": task_id},
        )
        self._index.register_artifact(record)
        self._index.link_run_artifact(producer_run_id, policy_id, "downstream")
        return policy_id

    def _task_domain(self, task_id: str) -> str:
        path = self._config.tasks_dir / task_id / "task_manifest.yaml"
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return data.get("task_domain", "locomotion")
        return "locomotion"

    def register_eval(
        self,
        producer_run_id: str,
        protocol_id: str,
        metrics: dict,
        source: str = "sim",
    ) -> str:
        eval_id = make_eval_id(protocol_id, source=source)
        root = self._config.artifacts_dir / "evals" / eval_id
        root.mkdir(parents=True, exist_ok=True)
        manifest = {
            "eval_id": eval_id,
            "eval_protocol_id": protocol_id,
            "source": source,
            "producer_run_id": producer_run_id,
        }
        (root / "eval_manifest.yaml").write_text(
            yaml.dump(manifest, allow_unicode=True), encoding="utf-8"
        )
        (root / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        record = ArtifactRecord(
            artifact_id=eval_id,
            artifact_type="eval",
            lifecycle_status="active",
            producer_run_id=producer_run_id,
            storage_path=str(root.relative_to(self._config.data_root)),
            metadata=metrics,
        )
        self._index.register_artifact(record)
        self._index.link_run_artifact(producer_run_id, eval_id, "downstream")
        return eval_id

    def register_demo(self, producer_run_id: str, device_id: str) -> str:
        demo_id = make_demo_id(device_id)
        root = self._config.artifacts_dir / "demos" / demo_id
        root.mkdir(parents=True, exist_ok=True)
        manifest = {
            "demo_id": demo_id,
            "device_id": device_id,
            "producer_run_id": producer_run_id,
        }
        (root / "demo_manifest.yaml").write_text(
            yaml.dump(manifest, allow_unicode=True), encoding="utf-8"
        )
        record = ArtifactRecord(
            artifact_id=demo_id,
            artifact_type="demo",
            lifecycle_status="active",
            producer_run_id=producer_run_id,
            storage_path=str(root.relative_to(self._config.data_root)),
            metadata={"device_id": device_id},
        )
        self._index.register_artifact(record)
        self._index.link_run_artifact(producer_run_id, demo_id, "downstream")
        return demo_id

    def register_calibration(
        self, producer_run_id: str, device_id: str, cal_types: list[str]
    ) -> str:
        cal_type = cal_types[0] if cal_types else "hand_eye"
        cal_id = make_calibration_id(device_id, cal_type)
        root = self._config.artifacts_dir / "calibrations" / cal_id
        root.mkdir(parents=True, exist_ok=True)
        from datetime import datetime, timedelta

        valid = (datetime.now() + timedelta(days=90)).isoformat(timespec="seconds")
        manifest = {
            "calibration_id": cal_id,
            "device_id": device_id,
            "types": cal_types,
            "valid_until": valid,
            "producer_run_id": producer_run_id,
        }
        (root / "calibration.yaml").write_text(
            yaml.dump(manifest, allow_unicode=True), encoding="utf-8"
        )
        record = ArtifactRecord(
            artifact_id=cal_id,
            artifact_type="calibration",
            lifecycle_status="active",
            producer_run_id=producer_run_id,
            storage_path=str(root.relative_to(self._config.data_root)),
            metadata=manifest,
        )
        self._index.register_artifact(record)
        self._index.link_run_artifact(producer_run_id, cal_id, "downstream")
        return cal_id

    def promote_policy(self, policy_id: str, lifecycle: str) -> None:
        self._index.patch_artifact(policy_id, lifecycle_status=lifecycle)
        root = self._config.artifacts_dir / "policies" / policy_id / "policy_manifest.yaml"
        if root.exists():
            data = yaml.safe_load(root.read_text(encoding="utf-8"))
            data["lifecycle_status"] = lifecycle
            root.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
