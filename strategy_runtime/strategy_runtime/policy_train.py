"""从 LeRobot v3 parquet 训练 state-only MLP。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from strategy_runtime.lerobot_state_policy import NumpyMlp
from strategy_runtime.policy_backend import ACTION_DIM, STATE_DIM


@dataclass(frozen=True)
class TrainResult:
    checkpoint: Path
    meta_path: Path
    num_frames: int
    final_mse: float | None
    datasets: list[str]
    policy_id: str


class PolicyTrainError(ValueError):
    pass


def _vec_from_cell(cell: Any, n: int) -> np.ndarray:
    arr = np.asarray(cell, dtype=np.float64).reshape(-1)
    if arr.shape[0] < n:
        out = np.zeros(n, dtype=np.float64)
        out[: arr.shape[0]] = arr
        return out
    return arr[:n]


def load_v3_arrays(dataset_roots: list[Path]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    try:
        import pandas as pd
    except ImportError as e:
        raise PolicyTrainError("pandas required (pip install pandas pyarrow)") from e

    xs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    used: list[str] = []
    for root in dataset_roots:
        root = Path(root)
        parquet = root / "data" / "chunk-000" / "file-000.parquet"
        if not parquet.is_file():
            # allow passing the parquet itself
            if root.is_file() and root.suffix == ".parquet":
                parquet = root
            else:
                raise PolicyTrainError(f"missing parquet: {parquet}")
        df = pd.read_parquet(parquet)
        if "observation.state" not in df.columns or "action" not in df.columns:
            raise PolicyTrainError(f"{parquet}: need observation.state and action columns")
        for _, row in df.iterrows():
            xs.append(_vec_from_cell(row["observation.state"], STATE_DIM))
            ys.append(_vec_from_cell(row["action"], ACTION_DIM))
        used.append(str(root))
    if not xs:
        raise PolicyTrainError("no frames loaded")
    return np.stack(xs, axis=0), np.stack(ys, axis=0), used


def train_lerobot_state(
    *,
    dataset_roots: list[Path],
    out_dir: Path,
    hidden: int = 128,
    epochs: int = 80,
    batch_size: int = 64,
    lr: float = 1e-3,
    seed: int = 0,
    policy_id: str | None = None,
) -> TrainResult:
    x, y, used = load_v3_arrays(dataset_roots)
    model = NumpyMlp(in_dim=STATE_DIM, hidden=hidden, out_dim=ACTION_DIM, seed=seed)
    stats = model.fit(x, y, epochs=epochs, batch_size=batch_size, lr=lr, seed=seed)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pid = policy_id or f"pol_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ckpt = out_dir / "policy.npz"
    meta = {
        "policy_id": pid,
        "backend": "lerobot_state",
        "source_datasets": used,
        "num_frames": int(x.shape[0]),
        "hidden": hidden,
        "epochs": epochs,
        "batch_size": batch_size,
        "lr": lr,
        "seed": seed,
        "final_mse": stats.get("final_mse"),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "observation": "q[7]+gripper_width",
        "action": "ee_delta[6]+gripper",
        "weights": ckpt.name,
    }
    model.save(ckpt, meta=meta)
    meta_path = ckpt.with_suffix(".meta.json")
    # also write train_meta.json for Index convenience
    (out_dir / "train_meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return TrainResult(
        checkpoint=ckpt,
        meta_path=meta_path,
        num_frames=int(x.shape[0]),
        final_mse=stats.get("final_mse"),
        datasets=used,
        policy_id=pid,
    )
