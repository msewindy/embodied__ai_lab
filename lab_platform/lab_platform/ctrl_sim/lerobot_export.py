"""A 轨 low.jsonl → LeRobot Dataset v3.0 布局（B 轨）。

字段映射见 docs/data/low_jsonl_to_lerobot_v3.md（与 STRUCT §5.4 / §13.4 对齐）。
本导出器不依赖 lerobot 包；写出可被下游训练加载的最小 v3 目录。
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

CODEBASE_VERSION = "v3.0"
DATA_PATH_TMPL = "data/chunk-{chunk_index:03d}/file-{file_index:03d}.parquet"
VIDEO_PATH_TMPL = "videos/{video_key}/chunk-{chunk_index:03d}/file-{file_index:03d}.mp4"

# observation.state = q[7] + gripper_width[1]
STATE_DIM = 8
STATE_NAMES = [f"q_{i}" for i in range(7)] + ["gripper_width"]

# action = ee_delta[6] + gripper[1]（intent 缺失时填 0）
ACTION_DIM = 7
ACTION_NAMES = [
    "ee_dx",
    "ee_dy",
    "ee_dz",
    "ee_droll",
    "ee_dpitch",
    "ee_dyaw",
    "gripper",
]


@dataclass(frozen=True)
class ExportResult:
    dataset_root: Path
    run_id: str
    num_frames: int
    fps: float
    relative_path: str  # 相对 data_root
    dataset_id: str | None = None


class LerobotExportError(ValueError):
    pass


def _require_deps() -> None:
    try:
        import pandas  # noqa: F401
        import pyarrow  # noqa: F401
    except ImportError as e:
        raise LerobotExportError(
            "lerobot-v3 export requires pandas and pyarrow "
            "(pip install 'pandas>=2' 'pyarrow>=14')"
        ) from e


def _f32(arr: Any, n: int, default: float = 0.0) -> list[float]:
    if arr is None:
        return [default] * n
    out = [float(x) for x in arr]
    if len(out) < n:
        out = out + [default] * (n - len(out))
    return out[:n]


def _row_to_vectors(row: dict[str, Any]) -> tuple[list[float], list[float]]:
    low = row.get("low") or {}
    intent = row.get("intent")
    q = _f32(low.get("q"), 7)
    gw = float(low.get("gripper_width") or 0.0)
    state = q + [gw]
    if intent:
        action = _f32(intent.get("ee_delta"), 6) + [float(intent.get("gripper") or 0.0)]
    else:
        action = [0.0] * ACTION_DIM
    return state, action


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise LerobotExportError(f"{path}:{line_no}: invalid JSON: {e}") from e
            if not isinstance(obj, dict) or "low" not in obj:
                raise LerobotExportError(f"{path}:{line_no}: expected object with 'low'")
            rows.append(obj)
    if not rows:
        raise LerobotExportError(f"{path}: empty trajectory")
    return rows


def _infer_fps(rows: list[dict[str, Any]], fallback: float) -> float:
    if len(rows) < 2:
        return float(fallback)
    ts = [float(r["t"]) for r in rows if "t" in r]
    if len(ts) < 2:
        return float(fallback)
    dts = np.diff(ts)
    dts = dts[dts > 1e-6]
    if len(dts) == 0:
        return float(fallback)
    med = float(np.median(dts))
    return round(1.0 / med, 3) if med > 0 else float(fallback)


def _feature_stats(arr: np.ndarray) -> dict[str, list[float]]:
    # arr: [N, D]
    return {
        "mean": arr.mean(axis=0).astype(float).tolist(),
        "std": arr.std(axis=0).astype(float).tolist(),
        "min": arr.min(axis=0).astype(float).tolist(),
        "max": arr.max(axis=0).astype(float).tolist(),
        "count": [int(arr.shape[0])] * int(arr.shape[1]),
    }


def _default_task(manifest: dict[str, Any] | None, scene: dict[str, Any] | None) -> str:
    if scene and scene.get("task_language_default"):
        return str(scene["task_language_default"])
    if manifest and manifest.get("scene_id"):
        return f"ctrl_sim:{manifest['scene_id']}"
    return "franka_ctrl_sim"


def export_low_jsonl_to_lerobot_v3(
    *,
    run_dir: Path,
    data_root: Path,
    out_dir: Path | None = None,
    fps: float | None = None,
    task: str | None = None,
    overwrite: bool = False,
) -> ExportResult:
    """从 run 目录导出 B 轨，并写回 manifest.tracks.B / lerobot_dataset_path。"""
    _require_deps()
    import pandas as pd

    run_dir = Path(run_dir).resolve()
    data_root = Path(data_root).resolve()
    jsonl = run_dir / "logs" / "low.jsonl"
    if not jsonl.is_file():
        raise LerobotExportError(f"missing A-track: {jsonl}")

    manifest_path = run_dir / "manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) or {}

    scene: dict[str, Any] | None = None
    scene_snap = run_dir / "logs" / "scene.yaml"
    if scene_snap.is_file():
        import yaml

        raw = yaml.safe_load(scene_snap.read_text(encoding="utf-8")) or {}
        if isinstance(raw, dict):
            scene = raw

    rows = _load_jsonl(jsonl)
    run_id = str(manifest.get("run_id") or rows[0].get("run_id") or run_dir.name)

    fps_fallback = 10.0
    if scene and scene.get("record_fps"):
        fps_fallback = float(scene["record_fps"])
    tracks_a = (manifest.get("tracks") or {}).get("A") or {}
    if tracks_a.get("record_fps"):
        fps_fallback = float(tracks_a["record_fps"])
    fps_out = float(fps) if fps is not None else _infer_fps(rows, fps_fallback)

    task_text = task or _default_task(manifest, scene)
    robot_type = "franka_fr3_hand"
    if scene and scene.get("robot"):
        robot_type = str(scene["robot"])

    if out_dir is None:
        out_dir = data_root / "datasets" / "lerobot_v3" / run_id
    else:
        out_dir = Path(out_dir).resolve()

    if out_dir.exists() and any(out_dir.iterdir()) and not overwrite:
        raise LerobotExportError(
            f"dataset dir not empty (use --overwrite): {out_dir}"
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "meta" / "episodes" / "chunk-000").mkdir(parents=True, exist_ok=True)
    (out_dir / "data" / "chunk-000").mkdir(parents=True, exist_ok=True)

    states: list[list[float]] = []
    actions: list[list[float]] = []
    timestamps: list[float] = []
    t0 = float(rows[0].get("t") or 0.0)
    for i, row in enumerate(rows):
        st, act = _row_to_vectors(row)
        states.append(st)
        actions.append(act)
        t = float(row.get("t") or (t0 + i / fps_out))
        timestamps.append(t - t0)

    n = len(rows)
    state_arr = np.asarray(states, dtype=np.float32)
    action_arr = np.asarray(actions, dtype=np.float32)
    ts_arr = np.asarray(timestamps, dtype=np.float32)

    frame_df = pd.DataFrame(
        {
            "observation.state": list(state_arr),
            "action": list(action_arr),
            "timestamp": ts_arr,
            "frame_index": np.arange(n, dtype=np.int64),
            "episode_index": np.zeros(n, dtype=np.int64),
            "index": np.arange(n, dtype=np.int64),
            "task_index": np.zeros(n, dtype=np.int64),
        }
    )
    data_parquet = out_dir / "data" / "chunk-000" / "file-000.parquet"
    frame_df.to_parquet(data_parquet, index=False)

    # meta/tasks.parquet：task_index → 自然语言
    tasks_df = pd.DataFrame({"task_index": [0], "task": [task_text]})
    tasks_df.to_parquet(out_dir / "meta" / "tasks.parquet", index=False)

    # meta/episodes/...：单集，整文件偏移
    episodes_df = pd.DataFrame(
        {
            "episode_index": [0],
            "tasks": [[task_text]],
            "length": [n],
            "dataset_from_index": [0],
            "dataset_to_index": [n],
            "data/chunk_index": [0],
            "data/file_index": [0],
            "data/from_index": [0],
            "data/to_index": [n],
        }
    )
    episodes_df.to_parquet(
        out_dir / "meta" / "episodes" / "chunk-000" / "file-000.parquet",
        index=False,
    )

    features: dict[str, Any] = {
        "observation.state": {
            "dtype": "float32",
            "shape": [STATE_DIM],
            "names": STATE_NAMES,
        },
        "action": {
            "dtype": "float32",
            "shape": [ACTION_DIM],
            "names": ACTION_NAMES,
        },
        "timestamp": {"dtype": "float32", "shape": [1], "names": None},
        "frame_index": {"dtype": "int64", "shape": [1], "names": None},
        "episode_index": {"dtype": "int64", "shape": [1], "names": None},
        "index": {"dtype": "int64", "shape": [1], "names": None},
        "task_index": {"dtype": "int64", "shape": [1], "names": None},
    }

    info = {
        "codebase_version": CODEBASE_VERSION,
        "robot_type": robot_type,
        "total_episodes": 1,
        "total_frames": n,
        "total_tasks": 1,
        "total_videos": 0,
        "total_chunks": 1,
        "chunks_size": 1000,
        "fps": fps_out,
        "splits": {"train": "0:1"},
        "data_path": DATA_PATH_TMPL,
        "video_path": VIDEO_PATH_TMPL,
        "features": features,
        "lab": {
            "source_run_id": run_id,
            "source_a_track": "logs/low.jsonl",
            "action_schema": (scene or {}).get("action_schema"),
            "cameras": (scene or {}).get("cameras", []),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "field_map": "docs/data/low_jsonl_to_lerobot_v3.md",
        },
    }
    (out_dir / "meta" / "info.json").write_text(
        json.dumps(info, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    stats = {
        "observation.state": _feature_stats(state_arr),
        "action": _feature_stats(action_arr),
        "timestamp": {
            "mean": [float(ts_arr.mean())],
            "std": [float(ts_arr.std())],
            "min": [float(ts_arr.min())],
            "max": [float(ts_arr.max())],
            "count": [n],
        },
    }
    (out_dir / "meta" / "stats.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # 相对 data_root 的路径（互链）
    try:
        rel = str(out_dir.relative_to(data_root))
    except ValueError:
        rel = str(out_dir)

    from lab_platform.ids import make_dataset_id

    dataset_id = make_dataset_id(run_id)
    tracks = dict(manifest.get("tracks") or {})
    tracks["B"] = {
        "format": "lerobot-v3",
        "path": rel,
        "lerobot_dataset_path": rel,
        "dataset_id": dataset_id,
        "source_run_id": run_id,
        "source_a_track": "logs/low.jsonl",
        "num_frames": n,
        "fps": fps_out,
        "exported_at": info["lab"]["exported_at"],
    }
    manifest["tracks"] = tracks
    manifest["lerobot_dataset_path"] = rel
    manifest["dataset_id"] = dataset_id
    # 保留历史导出记录
    history = list(manifest.get("lerobot_exports") or [])
    history.append(
        {
            "path": rel,
            "dataset_id": dataset_id,
            "num_frames": n,
            "fps": fps_out,
            "exported_at": info["lab"]["exported_at"],
        }
    )
    manifest["lerobot_exports"] = history
    if not math.isfinite(fps_out) or fps_out <= 0:
        raise LerobotExportError(f"invalid fps: {fps_out}")
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # dataset 内也放一份反向链接，便于脱离 run 目录时溯源
    (out_dir / "meta" / "lab_source.json").write_text(
        json.dumps(
            {
                "dataset_id": dataset_id,
                "source_run_id": run_id,
                "source_run_dir": str(run_dir),
                "source_a_track": str(jsonl),
                "manifest_lerobot_dataset_path": rel,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    return ExportResult(
        dataset_root=out_dir,
        run_id=run_id,
        num_frames=n,
        fps=fps_out,
        relative_path=rel,
        dataset_id=dataset_id,
    )
