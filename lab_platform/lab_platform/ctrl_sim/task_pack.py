"""L2 Task Pack 解析：仓库 tasks/<scene_id>/（STRUCT PLAN-STRUCT-01）。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# 无 Task Pack 的遗留 scene_id（仅标签；CTRL-SIM 可跑空载）
LEGACY_SCENE_IDS = frozenset({"tabletop_pickplace_v0_min"})

REQUIRED_SCENE_KEYS = (
    "scene_id",
    "schema_version",
    "record_fps",
    "action_schema",
    "cameras",
)


def repo_root() -> Path:
    """lab_platform/lab_platform/ctrl_sim/task_pack.py → 仓库根。"""
    return Path(__file__).resolve().parents[3]


def tasks_search_roots(data_root: Path | None = None) -> list[Path]:
    roots: list[Path] = []
    env = os.environ.get("LAB_TASKS_ROOT", "").strip()
    if env:
        roots.append(Path(env).expanduser().resolve())
    roots.append(repo_root() / "tasks")
    if data_root is not None:
        roots.append(Path(data_root).resolve() / "tasks")
    # 去重且保序
    seen: set[Path] = set()
    out: list[Path] = []
    for r in roots:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


@dataclass(frozen=True)
class TaskPack:
    scene_id: str
    root: Path
    scene: dict[str, Any]
    scene_yaml: Path
    pin_md: Path | None

    def profile_path(self, profile: str) -> Path | None:
        rel = (self.scene.get("profiles") or {}).get(profile)
        if not rel:
            # 约定：profiles/<profile>.yaml
            candidate = self.root / "profiles" / f"{profile}.yaml"
            return candidate if candidate.is_file() else None
        p = (self.root / str(rel)).resolve()
        return p if p.is_file() else None

    def summary(self) -> dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "schema_version": self.scene.get("schema_version"),
            "pack_root": str(self.root),
            "scene_yaml": str(self.scene_yaml),
            "record_fps": self.scene.get("record_fps"),
            "action_schema": self.scene.get("action_schema"),
            "cameras": self.scene.get("cameras"),
            "backend": self.scene.get("backend"),
        }


class TaskPackError(ValueError):
    pass


def find_pack_dir(scene_id: str, data_root: Path | None = None) -> Path | None:
    if not scene_id:
        return None
    for root in tasks_search_roots(data_root):
        candidate = root / scene_id
        if (candidate / "scene.yaml").is_file():
            return candidate
    return None


def load_task_pack(scene_id: str, data_root: Path | None = None) -> TaskPack:
    pack_dir = find_pack_dir(scene_id, data_root)
    if pack_dir is None:
        searched = ", ".join(str(r / scene_id) for r in tasks_search_roots(data_root))
        raise TaskPackError(
            f"Task Pack not found for scene_id={scene_id!r}. Searched: {searched}"
        )
    scene_yaml = pack_dir / "scene.yaml"
    raw = yaml.safe_load(scene_yaml.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise TaskPackError(f"scene.yaml must be a mapping: {scene_yaml}")

    missing = [k for k in REQUIRED_SCENE_KEYS if k not in raw]
    if missing:
        raise TaskPackError(f"{scene_yaml}: missing keys {missing}")

    file_id = str(raw.get("scene_id") or "")
    if file_id and file_id != scene_id:
        raise TaskPackError(
            f"scene_id mismatch: CLI/request={scene_id!r} scene.yaml={file_id!r}"
        )

    pin = pack_dir / "scene_pin.md"
    return TaskPack(
        scene_id=scene_id,
        root=pack_dir,
        scene=raw,
        scene_yaml=scene_yaml,
        pin_md=pin if pin.is_file() else None,
    )


def resolve_scene_for_ctrl_sim(
    scene_id: str,
    *,
    data_root: Path | None = None,
) -> tuple[TaskPack | None, str | None]:
    """返回 (pack, warn)。legacy scene 允许无 pack；正式 scene 必须有 pack。"""
    sid = scene_id or ""
    if sid in LEGACY_SCENE_IDS:
        pack_dir = find_pack_dir(sid, data_root)
        if pack_dir is None:
            return None, f"legacy scene_id={sid} (no Task Pack; tag-only)"
        return load_task_pack(sid, data_root), None
    if not sid:
        return None, "empty scene_id"
    return load_task_pack(sid, data_root), None
