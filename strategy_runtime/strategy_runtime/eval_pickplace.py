"""抓放评测：写入 logs/eval.json（运动代理 + 放置净空检查）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from strategy_runtime.scene_targets import SceneTargets


def build_pickplace_eval(
    *,
    mid_summary: dict[str, Any],
    scene: SceneTargets | None,
    place_ee_xyz: list[float] | None,
    release_ee_xyz: list[float] | None,
) -> dict[str, Any]:
    """Mid 步进 + 释放 ee 相对碗水平距 + 杯底相对碗顶净空（静态几何代理）。"""
    mid_ok = bool(mid_summary.get("success"))
    steps = list(mid_summary.get("steps") or [])
    step_ok = {
        str(s.get("name")): str(s.get("status", "")).startswith("success") for s in steps
    }

    bowl = scene.bowl_center_from_cfg() if scene is not None else None
    pred = (scene.raw.get("predicates") or {}) if scene is not None else {}
    horiz_lim = float(pred.get("goal_horizontal_m", 0.045))
    hold_s = float(pred.get("success_hold_s", 2.0))

    ref = release_ee_xyz or place_ee_xyz
    horiz = None
    horiz_ok = False
    if bowl is not None and ref is not None:
        horiz = ((ref[0] - bowl[0]) ** 2 + (ref[1] - bowl[1]) ** 2) ** 0.5
        horiz_ok = horiz <= horiz_lim

    clearance = None
    clearance_req = None
    clearance_ok = True
    cup_bottom_z = None
    bowl_top_z = None
    if scene is not None and ref is not None:
        cup_h = float((scene.raw.get("objects") or {}).get("red_cup", {}).get("height_m", 0.1))
        bowl_top_z = scene.bowl_top_z()
        cup_bottom_z = float(ref[2]) - cup_h / 2.0
        clearance = cup_bottom_z - bowl_top_z
        clearance_req = scene.place_clearance_m()
        # 允许略小于名义净空（控制误差），但禁止穿透（clearance < 0）
        clearance_ok = clearance >= min(0.005, 0.4 * clearance_req)

    success = mid_ok and horiz_ok and clearance_ok
    return {
        "schema": "eval_pickplace_v0",
        "success": success,
        "mid_success": mid_ok,
        "profile": mid_summary.get("profile"),
        "predicates": {
            "all_steps_ok": mid_ok,
            "step_ok": step_ok,
            "place_horizontal_m": horiz,
            "place_horizontal_limit_m": horiz_lim,
            "place_horizontal_ok": horiz_ok,
            "place_clearance_m": clearance,
            "place_clearance_required_m": clearance_req,
            "place_clearance_ok": clearance_ok,
            "cup_bottom_z_proxy": cup_bottom_z,
            "bowl_top_z": bowl_top_z,
            "success_hold_s_required": hold_s,
            "success_hold_enforced": False,
            "success_hold_note": "P2 deferred; motion proxy only",
        },
        "place_ee_xyz": place_ee_xyz,
        "release_ee_xyz": release_ee_xyz,
        "bowl_xyz_gt": bowl,
        "grasp_gripper_cmd": scene.grasp_gripper_cmd() if scene is not None else None,
        "notes": (
            "Oracle GT is static. Horizontal + release clearance assume ee≈cup center. "
            "Not Isaac object GT; 2s hold not enforced."
        ),
    }


def write_eval_json(path: Path, eval_doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(eval_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
