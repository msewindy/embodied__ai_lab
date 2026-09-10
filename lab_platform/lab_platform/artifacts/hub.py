"""P5：Dataset / State-Policy 进 Index（私有类 Hub）。"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import yaml

from lab_platform.config import LabConfig
from lab_platform.ids import make_dataset_id, make_policy_id
from lab_platform.models import ArtifactRecord, now_iso
from lab_platform.protocols import IndexClient


class ArtifactHub:
    """相对 ArtifactRegistry stub 路径，面向 CTRL-SIM / LeRobot v3 资产。"""

    def __init__(self, config: LabConfig, index: IndexClient) -> None:
        self._config = config
        self._index = index

    def register_dataset(
        self,
        *,
        dataset_root: Path,
        source_run_id: str,
        relative_path: str,
        num_frames: int,
        fps: float,
        format: str = "lerobot-v3",
        extra_meta: dict[str, Any] | None = None,
        dataset_id: str | None = None,
        lifecycle: str = "active",
    ) -> str:
        aid = dataset_id or make_dataset_id(source_run_id)
        root = Path(dataset_root).resolve()
        meta = {
            "dataset_id": aid,
            "format": format,
            "source_run_ids": [source_run_id],
            "num_frames": int(num_frames),
            "fps": float(fps),
            "path": relative_path,
            "registered_at": now_iso(),
        }
        if extra_meta:
            meta.update(extra_meta)

        # 旁路 manifest，便于脱离 Index 时阅读
        (root / "meta").mkdir(parents=True, exist_ok=True)
        (root / "meta" / "lab_dataset.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        record = ArtifactRecord(
            artifact_id=aid,
            artifact_type="dataset",
            lifecycle_status=lifecycle,
            producer_run_id=source_run_id,
            storage_path=relative_path,
            metadata=meta,
        )
        self._index.upsert_artifact(record)
        self._index.link_run_artifact(source_run_id, aid, "downstream")
        return aid

    def register_state_policy(
        self,
        *,
        policy_dir: Path,
        policy_id: str | None,
        source_dataset_ids: list[str],
        producer_run_id: str = "",
        backend: str = "lerobot_state",
        train_meta: dict[str, Any] | None = None,
        lifecycle: str = "draft",
    ) -> str:
        pid = policy_id or make_policy_id("state_mlp")
        src = Path(policy_dir).resolve()
        if not (src / "policy.npz").is_file():
            raise FileNotFoundError(f"missing policy.npz under {src}")

        # 规范落点：artifacts/policies/<policy_id>/
        dst = self._config.artifacts_dir / "policies" / pid
        dst.mkdir(parents=True, exist_ok=True)
        for name in ("policy.npz", "policy.meta.json", "train_meta.json"):
            p = src / name
            if p.is_file():
                target = dst / name
                if p.resolve() != target.resolve():
                    shutil.copy2(p, target)

        meta = {
            "policy_id": pid,
            "backend": backend,
            "checkpoint": "policy.npz",
            "source_dataset_ids": list(source_dataset_ids),
            "producer_run_id": producer_run_id,
            "registered_at": now_iso(),
            "lifecycle_status": lifecycle,
        }
        if train_meta:
            for k in ("num_frames", "final_mse", "hidden", "epochs", "lr", "seed"):
                if k in train_meta:
                    meta[k] = train_meta[k]
            meta["source_datasets"] = train_meta.get("source_datasets")

        manifest = {
            "policy_id": pid,
            "lifecycle_status": lifecycle,
            "backend": backend,
            "checkpoint": {"path": "policy.npz", "format": "lab_numpy_mlp_v0"},
            "source_dataset_ids": list(source_dataset_ids),
            "created_at": now_iso(),
            "supported_devices": ["franka-01"],
            "task_domain": "manipulation",
        }
        (dst / "policy_manifest.yaml").write_text(
            yaml.dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        (dst / "hub_meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        try:
            rel = str(dst.relative_to(self._config.data_root))
        except ValueError:
            rel = str(dst)

        record = ArtifactRecord(
            artifact_id=pid,
            artifact_type="policy",
            lifecycle_status=lifecycle,
            producer_run_id=producer_run_id or (source_dataset_ids[0] if source_dataset_ids else ""),
            storage_path=rel,
            metadata=meta,
        )
        self._index.upsert_artifact(record)
        # 链到各源 dataset 的 producer run（collect → policy）
        for ds in source_dataset_ids:
            art = self._index.get_artifact(ds)
            if art and art.producer_run_id:
                self._index.link_run_artifact(art.producer_run_id, pid, "downstream")
        if producer_run_id and producer_run_id.startswith("cs_"):
            self._index.link_run_artifact(producer_run_id, pid, "downstream")
        return pid

    @staticmethod
    def _dataset_id_from_root(root: Path) -> str | None:
        for name in ("lab_dataset.json", "lab_source.json"):
            p = root / "meta" / name
            if not p.is_file():
                continue
            try:
                doc = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            did = doc.get("dataset_id")
            if isinstance(did, str) and did:
                return did
        return None

    def resolve_dataset_root(self, ref: str) -> tuple[Path, str | None]:
        """path 或 dataset_id → (root, dataset_id|None)。"""
        raw = (ref or "").strip()
        if not raw:
            raise FileNotFoundError("empty dataset ref")
        p = Path(raw).expanduser()
        if p.is_dir() and (p / "data").is_dir():
            root = p.resolve()
            return root, self._dataset_id_from_root(root)
        under = (self._config.data_root / raw).resolve()
        if under.is_dir() and (under / "data").is_dir():
            return under, self._dataset_id_from_root(under)
        art = self._index.get_artifact(raw)
        if art and art.artifact_type == "dataset":
            root = (self._config.data_root / art.storage_path).resolve()
            if not root.is_dir():
                raise FileNotFoundError(f"dataset {raw} storage missing: {root}")
            return root, art.artifact_id
        raise FileNotFoundError(f"dataset not found: {ref}")

    @staticmethod
    def _policy_id_from_dir(root: Path) -> str | None:
        for name in ("hub_meta.json", "train_meta.json", "policy.meta.json"):
            p = root / name
            if not p.is_file():
                continue
            try:
                doc = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            pid = doc.get("policy_id")
            if isinstance(pid, str) and pid:
                return pid
        return None

    def resolve_policy_checkpoint(self, ref: str) -> tuple[Path, str | None]:
        """path 或 policy_id → (policy.npz, policy_id|None)。"""
        raw = (ref or "").strip()
        if not raw:
            raise FileNotFoundError("empty policy ref")
        p = Path(raw).expanduser()
        if p.is_file() and p.suffix == ".npz":
            ckpt = p.resolve()
            return ckpt, self._policy_id_from_dir(ckpt.parent)
        if p.is_dir() and (p / "policy.npz").is_file():
            root = p.resolve()
            return root / "policy.npz", self._policy_id_from_dir(root)
        under = (self._config.data_root / raw).resolve()
        if under.is_file() and under.suffix == ".npz":
            return under, self._policy_id_from_dir(under.parent)
        if under.is_dir() and (under / "policy.npz").is_file():
            return under / "policy.npz", self._policy_id_from_dir(under)
        art = self._index.get_artifact(raw)
        if art and art.artifact_type == "policy":
            root = (self._config.data_root / art.storage_path).resolve()
            ckpt = root / "policy.npz"
            if not ckpt.is_file():
                raise FileNotFoundError(f"policy {raw} missing policy.npz at {ckpt}")
            return ckpt, art.artifact_id
        raise FileNotFoundError(f"policy checkpoint not found: {ref}")
