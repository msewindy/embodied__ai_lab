"""从 scene.yaml + ObjectPose 解析命名目标点（任务系 fr3_link0）。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SceneTargets:
    raw: dict[str, Any]
    path: Path

    @classmethod
    def load(cls, path: Path) -> "SceneTargets":
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict):
            raise ValueError(f"invalid scene.yaml: {path}")
        return cls(raw=raw, path=Path(path))

    @property
    def frame_id(self) -> str:
        return str((self.raw.get("frames") or {}).get("task_origin") or "fr3_link0")

    @property
    def cup_topic(self) -> str:
        return str((self.raw.get("oracle") or {}).get("cup_pose_topic") or "/perception/scene/red_cup/pose")

    @property
    def bowl_topic(self) -> str:
        return str((self.raw.get("oracle") or {}).get("bowl_pose_topic") or "/perception/scene/bowl/pose")

    def cup_center_from_cfg(self, grid_id: int | None = None) -> list[float]:
        grid = self.raw.get("cup_grid") or {}
        gid = int(grid_id if grid_id is not None else grid.get("default_grid_id", 4))
        cells = grid.get("cells") or {}
        xy = cells.get(gid, cells.get(str(gid)))
        if xy is None:
            raise KeyError(f"cup_grid cell {gid} missing in {self.path}")
        x, y = float(xy[0]), float(xy[1])
        h = float((self.raw.get("objects") or {}).get("red_cup", {}).get("height_m", 0.1))
        return [x, y, h / 2.0]

    def bowl_center_from_cfg(self) -> list[float]:
        bowl = (self.raw.get("objects") or {}).get("bowl") or {}
        base = list(bowl.get("base_center_m") or [0.58, -0.18, 0.0])
        h = float(bowl.get("height_m", 0.055))
        return [float(base[0]), float(base[1]), float(base[2]) + h / 2.0]

    def resolve_target(
        self,
        target_ref: str,
        *,
        cup_xyz: list[float] | None,
        bowl_xyz: list[float] | None,
        ee_xyz: list[float] | None = None,
    ) -> list[float] | None:
        """返回目标位置 xyz；无法解析则 None。"""
        ref = (target_ref or "none").strip()
        pre = self.raw.get("pregrasp") or {}
        pred = self.raw.get("predicates") or {}
        approach = float(pre.get("approach_offset_m", 0.12))
        h_delta = float(pre.get("height_delta_m", 0.02))
        h_lift = float(pre.get("h_lift_m", 0.08))
        above_z = float(pre.get("above_bowl_z_m", 0.12))

        if ref in ("none", "stub_forward"):
            return None

        if ref == "pregrasp_red_cup":
            if cup_xyz is None:
                return None
            # 杯心正上方 standoff（顶向接近）
            return [cup_xyz[0], cup_xyz[1], cup_xyz[2] + approach]

        if ref in ("red_cup", "grasp_red_cup"):
            if cup_xyz is None:
                return None
            # 抓取高度：略高于杯心（便于顶向接近后闭合）
            return [cup_xyz[0], cup_xyz[1], cup_xyz[2] + h_delta]

        if ref == "above_bowl":
            if bowl_xyz is None:
                return None
            bowl_h = float((self.raw.get("objects") or {}).get("bowl", {}).get("height_m", 0.055))
            base_z = bowl_xyz[2] - bowl_h / 2.0
            return [bowl_xyz[0], bowl_xyz[1], base_z + above_z]

        if ref == "bowl":
            if bowl_xyz is None:
                return None
            return list(bowl_xyz[:3])

        if ref == "place_bowl":
            # ee≈杯心；杯底 = bowl_top + place_clearance（默认留空再释放，靠重力落下）
            if bowl_xyz is None:
                return None
            objs = self.raw.get("objects") or {}
            bowl_h = float(objs.get("bowl", {}).get("height_m", 0.055))
            cup_h = float(objs.get("red_cup", {}).get("height_m", 0.1))
            clearance = float(pre.get("place_clearance_m", 0.025))
            base_z = bowl_xyz[2] - bowl_h / 2.0
            bowl_top = base_z + bowl_h
            return [
                bowl_xyz[0],
                bowl_xyz[1],
                bowl_top + clearance + cup_h / 2.0,
            ]

        if ref == "retreat":
            r = list(pre.get("retreat_m") or [0.35, 0.0, 0.35])
            return [float(r[0]), float(r[1]), float(r[2])]

        if ref == "lift_hold":
            # 注意：调用方应在步进开始时锁存，避免目标随 ee 上漂
            if ee_xyz is None:
                return None
            return [ee_xyz[0], ee_xyz[1], ee_xyz[2] + h_lift]

        return None

    def needs_latched_target(self, target_ref: str) -> bool:
        return (target_ref or "") in ("lift_hold",)

    def grasp_gripper_cmd(self) -> float:
        """开口宽度 → SkillIntent.gripper∈[0,1]（0=开）。"""
        pre = self.raw.get("pregrasp") or {}
        width_open = float(pre.get("gripper_width_open_m", 0.080))
        width_close = float(pre.get("grasp_close_width_m", 0.045))
        if width_open <= 1e-9:
            return 0.5
        return max(0.0, min(1.0, 1.0 - width_close / width_open))

    def bowl_top_z(self) -> float:
        bowl = (self.raw.get("objects") or {}).get("bowl") or {}
        base = list(bowl.get("base_center_m") or [0.58, -0.18, 0.0])
        h = float(bowl.get("height_m", 0.055))
        return float(base[2]) + h

    def place_clearance_m(self) -> float:
        return float((self.raw.get("pregrasp") or {}).get("place_clearance_m", 0.025))

    def eps_for(self, target_ref: str, goal_eps: float | None = None) -> float:
        if goal_eps is not None and goal_eps > 0:
            return float(goal_eps)
        pred = self.raw.get("predicates") or {}
        ref = target_ref or ""
        if ref == "retreat":
            return float(pred.get("retreat_eps_m", 0.03))
        return float(pred.get("approach_eps_pos_m", 0.015))


def bounded_ee_delta(
    ee_xyz: list[float],
    target_xyz: list[float],
    *,
    max_step_m: float = 0.03,
) -> tuple[list[float], float]:
    """位置误差 → 有界 ee_delta（仅平移，姿态 0）；返回 (delta6, dist)。"""
    err = [float(t) - float(e) for e, t in zip(ee_xyz[:3], target_xyz[:3])]
    dist = sum(x * x for x in err) ** 0.5
    if dist < 1e-9:
        return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 0.0
    step = min(float(max_step_m), dist)
    scale = step / dist
    return [err[0] * scale, err[1] * scale, err[2] * scale, 0.0, 0.0, 0.0], dist
