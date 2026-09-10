"""State-only MLP 策略（兼容 lab A→B v3 parquet；无 torch）。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from strategy_runtime.policy_backend import (
    ACTION_DIM,
    STATE_DIM,
    PolicyAction,
    PolicyObs,
)


@dataclass
class MlpWeights:
    w1: np.ndarray
    b1: np.ndarray
    w2: np.ndarray
    b2: np.ndarray
    x_mean: np.ndarray
    x_std: np.ndarray
    y_mean: np.ndarray
    y_std: np.ndarray

    @property
    def hidden(self) -> int:
        return int(self.w1.shape[1])


class NumpyMlp:
    """2 层 ReLU MLP；输入/输出做 z-score。"""

    def __init__(
        self,
        in_dim: int = STATE_DIM,
        hidden: int = 128,
        out_dim: int = ACTION_DIM,
        seed: int = 0,
    ) -> None:
        rng = np.random.default_rng(seed)
        scale1 = 1.0 / np.sqrt(in_dim)
        scale2 = 1.0 / np.sqrt(hidden)
        self.w1 = rng.normal(0.0, scale1, size=(in_dim, hidden)).astype(np.float64)
        self.b1 = np.zeros(hidden, dtype=np.float64)
        self.w2 = rng.normal(0.0, scale2, size=(hidden, out_dim)).astype(np.float64)
        self.b2 = np.zeros(out_dim, dtype=np.float64)
        self.x_mean = np.zeros(in_dim, dtype=np.float64)
        self.x_std = np.ones(in_dim, dtype=np.float64)
        self.y_mean = np.zeros(out_dim, dtype=np.float64)
        self.y_std = np.ones(out_dim, dtype=np.float64)

    def set_norm(
        self,
        x_mean: np.ndarray,
        x_std: np.ndarray,
        y_mean: np.ndarray,
        y_std: np.ndarray,
    ) -> None:
        self.x_mean = np.asarray(x_mean, dtype=np.float64)
        self.x_std = np.maximum(np.asarray(x_std, dtype=np.float64), 1e-6)
        self.y_mean = np.asarray(y_mean, dtype=np.float64)
        self.y_std = np.maximum(np.asarray(y_std, dtype=np.float64), 1e-6)

    def _norm_x(self, x: np.ndarray) -> np.ndarray:
        return (x - self.x_mean) / self.x_std

    def _denorm_y(self, y: np.ndarray) -> np.ndarray:
        return y * self.y_std + self.y_mean

    def forward(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        xn = self._norm_x(x)
        h = np.maximum(0.0, xn @ self.w1 + self.b1)
        yn = h @ self.w2 + self.b2
        return self._denorm_y(yn), h

    def predict(self, x: np.ndarray) -> np.ndarray:
        y, _ = self.forward(np.asarray(x, dtype=np.float64))
        return y

    def fit(
        self,
        x: np.ndarray,
        y: np.ndarray,
        *,
        epochs: int = 80,
        batch_size: int = 64,
        lr: float = 1e-3,
        seed: int = 0,
    ) -> dict[str, Any]:
        x = np.asarray(x, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        n = x.shape[0]
        self.set_norm(x.mean(0), x.std(0), y.mean(0), y.std(0))
        rng = np.random.default_rng(seed)
        history: list[float] = []
        for ep in range(epochs):
            idx = rng.permutation(n)
            total = 0.0
            steps = 0
            for start in range(0, n, batch_size):
                sel = idx[start : start + batch_size]
                xb = x[sel]
                yb = y[sel]
                xn = self._norm_x(xb)
                yn_tgt = (yb - self.y_mean) / self.y_std
                h_pre = xn @ self.w1 + self.b1
                h = np.maximum(0.0, h_pre)
                yn_pred = h @ self.w2 + self.b2
                err = yn_pred - yn_tgt
                loss = float(np.mean(err**2))
                total += loss
                steps += 1
                # dL/dyn
                dyn = (2.0 / err.shape[0]) * err
                dw2 = h.T @ dyn
                db2 = dyn.sum(axis=0)
                dh = dyn @ self.w2.T
                dh_pre = dh * (h_pre > 0.0)
                dw1 = xn.T @ dh_pre
                db1 = dh_pre.sum(axis=0)
                self.w2 -= lr * dw2
                self.b2 -= lr * db2
                self.w1 -= lr * dw1
                self.b1 -= lr * db1
            history.append(total / max(steps, 1))
        return {"epochs": epochs, "final_mse": history[-1] if history else None, "history": history}

    def save(self, path: Path, meta: dict[str, Any] | None = None) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            w1=self.w1,
            b1=self.b1,
            w2=self.w2,
            b2=self.b2,
            x_mean=self.x_mean,
            x_std=self.x_std,
            y_mean=self.y_mean,
            y_std=self.y_std,
        )
        meta_path = path.with_suffix(".meta.json")
        doc = {
            "format": "lab_numpy_mlp_v0",
            "backend": "lerobot_state",
            "state_dim": int(self.w1.shape[0]),
            "action_dim": int(self.w2.shape[1]),
            "hidden": int(self.w1.shape[1]),
            "weights": str(path.name),
        }
        if meta:
            doc.update(meta)
        meta_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "NumpyMlp":
        path = Path(path)
        data = np.load(path)
        model = cls(
            in_dim=int(data["w1"].shape[0]),
            hidden=int(data["w1"].shape[1]),
            out_dim=int(data["w2"].shape[1]),
        )
        model.w1 = np.asarray(data["w1"], dtype=np.float64)
        model.b1 = np.asarray(data["b1"], dtype=np.float64)
        model.w2 = np.asarray(data["w2"], dtype=np.float64)
        model.b2 = np.asarray(data["b2"], dtype=np.float64)
        model.set_norm(data["x_mean"], data["x_std"], data["y_mean"], data["y_std"])
        return model


class LerobotStateBackend:
    """从 checkpoint 推理；失败 → HOLD。"""

    name = "lerobot_state"

    def __init__(self, checkpoint: Path, *, hold_on_miss: bool = True) -> None:
        self.checkpoint = Path(checkpoint)
        self.hold_on_miss = hold_on_miss
        weights = self.checkpoint
        if weights.suffix == ".json":
            meta = json.loads(weights.read_text(encoding="utf-8"))
            weights = weights.parent / meta.get("weights", "policy.npz")
        if not weights.is_file():
            raise FileNotFoundError(f"checkpoint not found: {weights}")
        self.model = NumpyMlp.load(weights)
        self._meta_path = weights.with_suffix(".meta.json")
        self.meta: dict[str, Any] = {}
        if self._meta_path.is_file():
            self.meta = json.loads(self._meta_path.read_text(encoding="utf-8"))
        self._n_act = 0
        self._n_hold = 0

    def reset(self, context: dict[str, Any] | None = None) -> None:
        self._n_act = 0
        self._n_hold = 0

    def act(self, obs: PolicyObs) -> PolicyAction:
        try:
            state = np.asarray(obs.as_state_vec(), dtype=np.float64)
            if state.shape[0] != STATE_DIM or not np.all(np.isfinite(state)):
                raise ValueError("invalid observation.state")
            y = self.model.predict(state.reshape(1, -1))[0]
            if y.shape[0] != ACTION_DIM or not np.all(np.isfinite(y)):
                raise ValueError("invalid action")
            # 软限幅，避免炸桥
            ee = np.clip(y[:6], -0.05, 0.05)
            grip = float(np.clip(y[6], 0.0, 1.0))
            self._n_act += 1
            return PolicyAction(
                hold=False,
                ee_delta=[float(v) for v in ee],
                gripper=grip,
                expire_ms=200,
                reason="mlp",
            )
        except Exception as e:  # noqa: BLE001 — inference boundary
            self._n_hold += 1
            if self.hold_on_miss:
                return PolicyAction.hold_action(f"infer_fail: {e}")
            raise

    def close(self) -> None:
        return None

    def stats(self) -> dict[str, Any]:
        return {
            "checkpoint": str(self.checkpoint),
            "n_act": self._n_act,
            "n_hold": self._n_hold,
            "meta": self.meta,
        }
