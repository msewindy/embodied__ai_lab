"""MidGoal 播放器：相对 Δpose（m5_template）或朝目标有界步进（P1+）。"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from strategy_runtime.scene_targets import SceneTargets, bounded_ee_delta


@dataclass
class MidGoal:
    name: str
    target_ref: str = "none"
    ee_delta: list[float] = field(default_factory=lambda: [0.0] * 6)
    rate_hz: float = 10.0
    max_duration_s: float = 2.0
    success_ee_travel_m: float = 0.04
    success_eps_pos_m: float = 0.0  # >0 时优先用目标误差判成功
    max_step_m: float = 0.03
    expire_ms: int = 200
    gripper: float = 0.0
    gripper_dwell: float | None = None  # 到位 dwell 阶段夹爪；None=沿用 gripper
    dwell_s: float = 0.0
    mode: str = "auto"  # auto | relative | toward

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MidGoal":
        delta = list(d.get("ee_delta") or [0.0] * 6)
        while len(delta) < 6:
            delta.append(0.0)
        gd = d.get("gripper_dwell")
        return cls(
            name=str(d["name"]),
            target_ref=str(d.get("target_ref") or "none"),
            ee_delta=[float(x) for x in delta[:6]],
            rate_hz=float(d.get("rate_hz") or 10.0),
            max_duration_s=float(d.get("max_duration_s") or 2.0),
            success_ee_travel_m=float(d.get("success_ee_travel_m") or 0.04),
            success_eps_pos_m=float(d.get("success_eps_pos_m") or 0.0),
            max_step_m=float(d.get("max_step_m") or 0.03),
            expire_ms=int(d.get("expire_ms") or 200),
            gripper=float(d.get("gripper") or 0.0),
            gripper_dwell=float(gd) if gd is not None else None,
            dwell_s=float(d.get("dwell_s") or 0.0),
            mode=str(d.get("mode") or "auto"),
        )

    def resolved_mode(self) -> str:
        if self.mode in ("relative", "toward"):
            return self.mode
        ref = self.target_ref
        if ref in ("none", "stub_forward") or (
            any(abs(x) > 1e-9 for x in self.ee_delta) and ref in ("none", "stub_forward", "")
        ):
            return "relative"
        if ref not in ("none", "", "stub_forward"):
            return "toward"
        return "relative"


@dataclass
class MidTemplate:
    profile: str
    situation: str
    forward_wm: str
    goals: list[MidGoal]
    cup_grid_id: int | None = None

    @classmethod
    def load(cls, path: Path) -> "MidTemplate":
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        goals = [MidGoal.from_dict(g) for g in (raw.get("goals") or [])]
        if len(goals) < 1:
            raise ValueError(f"Mid template requires ≥1 MidGoal, got 0 in {path}")
        gid = raw.get("cup_grid_id")
        return cls(
            profile=str(raw.get("profile") or "m5_template"),
            situation=str(raw.get("situation") or "stub"),
            forward_wm=str(raw.get("forward_wm") or "off"),
            goals=goals,
            cup_grid_id=int(gid) if gid is not None else None,
        )


def default_template_path() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "templates" / "m5_approach_retreat.yaml",
        here.parents[3] / "lab_platform" / "templates" / "m5_approach_retreat.yaml",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return candidates[0]


def _xyz_from_pose_msg(msg: Any) -> list[float]:
    p = msg.pose.position
    return [float(p.x), float(p.y), float(p.z)]


def run_mid_template(
    *,
    device_id: str = "franka-01",
    domain: int = 43,
    template_path: Path | None = None,
    scene_yaml: Path | None = None,
    run_id: str = "",
    steps_log: Path | None = None,
    eval_log: Path | None = None,
    publish_oracle_gt: bool = True,
) -> dict[str, Any]:
    """执行 MidGoal 序列；返回摘要（供 launcher / CLI）。"""
    import os

    os.environ["ROS_DOMAIN_ID"] = str(domain)
    os.environ.setdefault("RMW_IMPLEMENTATION", "rmw_cyclonedds_cpp")

    import rclpy
    from geometry_msgs.msg import PoseStamped
    from rclpy.node import Node
    from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
    from embodied_lab_msgs.msg import LowStateFeedback, SkillIntent

    from strategy_runtime.eval_pickplace import build_pickplace_eval, write_eval_json
    from strategy_runtime.oracle_gt import attach_oracle_publishers, make_pose_stamped

    path = Path(template_path) if template_path else default_template_path()
    tmpl = MidTemplate.load(path)
    ns = device_id.replace("-", "_")
    intent_topic = f"/skill/{ns}/intent"
    low_topic = f"/perception/{ns}/low_state"

    scene: SceneTargets | None = None
    if scene_yaml is not None:
        scene = SceneTargets.load(Path(scene_yaml))
    elif tmpl.situation == "oracle":
        # 约定：profile 旁的 ../../scene.yaml（tasks/.../profiles → pack root）
        cand = path.resolve().parents[1] / "scene.yaml"
        if cand.is_file():
            scene = SceneTargets.load(cand)

    needs_toward = any(g.resolved_mode() == "toward" for g in tmpl.goals)
    if needs_toward and scene is None:
        raise ValueError(
            f"toward MidGoals require --scene-yaml (profile={tmpl.profile} path={path})"
        )

    owned = False
    if not rclpy.ok():
        rclpy.init()
        owned = True

    class _Node(Node):
        pass

    node = _Node("m5_mid_runtime")
    intent_qos = QoSProfile(
        reliability=ReliabilityPolicy.RELIABLE,
        history=HistoryPolicy.KEEP_LAST,
        depth=1,
    )
    sensor_qos = QoSProfile(
        reliability=ReliabilityPolicy.BEST_EFFORT,
        history=HistoryPolicy.KEEP_LAST,
        depth=5,
    )
    pose_qos = QoSProfile(
        reliability=ReliabilityPolicy.RELIABLE,
        history=HistoryPolicy.KEEP_LAST,
        depth=1,
    )
    pub = node.create_publisher(SkillIntent, intent_topic, intent_qos)
    latest: dict[str, Any] = {"low": None, "cup": None, "bowl": None}

    def _on_low(msg: LowStateFeedback) -> None:
        latest["low"] = msg

    node.create_subscription(LowStateFeedback, low_topic, _on_low, sensor_qos)

    cup_pub = bowl_pub = None
    gt_poses: dict[str, list[float]] = {}
    if scene is not None:
        node.create_subscription(
            PoseStamped,
            scene.cup_topic,
            lambda m: latest.__setitem__("cup", m),
            pose_qos,
        )
        node.create_subscription(
            PoseStamped,
            scene.bowl_topic,
            lambda m: latest.__setitem__("bowl", m),
            pose_qos,
        )
        if publish_oracle_gt:
            cup_pub, bowl_pub, gt_poses = attach_oracle_publishers(
                node, scene, cup_grid_id=tmpl.cup_grid_id
            )
            print(
                f"[mid] oracle GT cup={gt_poses['red_cup']} bowl={gt_poses['bowl']} "
                f"topics={scene.cup_topic},{scene.bowl_topic}",
                flush=True,
            )

    # discovery + seed oracle
    t_end = time.time() + 1.0
    while time.time() < t_end:
        if cup_pub is not None and scene is not None:
            cup_pub.publish(make_pose_stamped(node, gt_poses["red_cup"], scene.frame_id))
            bowl_pub.publish(make_pose_stamped(node, gt_poses["bowl"], scene.frame_id))
        rclpy.spin_once(node, timeout_sec=0.05)

    steps: list[dict[str, Any]] = []
    aborted = False
    abort_reason = ""
    place_ee_xyz: list[float] | None = None
    release_ee_xyz: list[float] | None = None

    print(
        f"[mid] template={path.name} situation={tmpl.situation} "
        f"wm={tmpl.forward_wm} goals={[g.name for g in tmpl.goals]}",
        flush=True,
    )

    try:
        for gi, goal in enumerate(tmpl.goals):
            mode = goal.resolved_mode()
            print(
                f"[mid] STEP {gi + 1}/{len(tmpl.goals)} MidGoal={goal.name} "
                f"mode={mode} target_ref={goal.target_ref} "
                f"gripper={goal.gripper} dwell_s={goal.dwell_s}",
                flush=True,
            )
            wait0 = time.time() + 1.5
            while latest["low"] is None and time.time() < wait0:
                if cup_pub is not None and scene is not None:
                    cup_pub.publish(
                        make_pose_stamped(node, gt_poses["red_cup"], scene.frame_id)
                    )
                    bowl_pub.publish(
                        make_pose_stamped(node, gt_poses["bowl"], scene.frame_id)
                    )
                rclpy.spin_once(node, timeout_sec=0.05)
            if latest["low"] is None:
                aborted = True
                abort_reason = "no low_state"
                steps.append(
                    {
                        "index": gi,
                        "name": goal.name,
                        "status": "failed",
                        "reason": abort_reason,
                        "mode": mode,
                    }
                )
                break

            start_ee = [float(x) for x in latest["low"].ee_pose_actual[:3]]
            t0 = time.time()
            period = 1.0 / max(goal.rate_hz, 0.1)
            n_pub = 0
            status = "running"
            reason = ""
            last_dist: float | None = None
            last_delta = list(goal.ee_delta)
            latched_target: list[float] | None = None
            dwell_until: float | None = None
            phase = "move"  # move | dwell

            if mode == "toward" and scene is not None:
                cup_xyz0 = (
                    _xyz_from_pose_msg(latest["cup"])
                    if latest["cup"] is not None
                    else gt_poses.get("red_cup")
                )
                bowl_xyz0 = (
                    _xyz_from_pose_msg(latest["bowl"])
                    if latest["bowl"] is not None
                    else gt_poses.get("bowl")
                )
                if scene.needs_latched_target(goal.target_ref):
                    latched_target = scene.resolve_target(
                        goal.target_ref,
                        cup_xyz=cup_xyz0,
                        bowl_xyz=bowl_xyz0,
                        ee_xyz=start_ee,
                    )
                    print(f"[mid]   latched target={latched_target}", flush=True)

            while True:
                if cup_pub is not None and scene is not None:
                    cup_pub.publish(
                        make_pose_stamped(node, gt_poses["red_cup"], scene.frame_id)
                    )
                    bowl_pub.publish(
                        make_pose_stamped(node, gt_poses["bowl"], scene.frame_id)
                    )
                rclpy.spin_once(node, timeout_sec=0.0)
                low = latest["low"]
                if low is not None and str(low.safety_event) not in ("", "none"):
                    status = "hold"
                    reason = f"safety_event={low.safety_event}"
                    aborted = True
                    abort_reason = reason
                    break

                ee = [float(x) for x in (low.ee_pose_actual[:3] if low else start_ee)]
                grip_cmd = float(goal.gripper)
                target: list[float] | None = None
                if mode == "toward":
                    assert scene is not None
                    cup_xyz = (
                        _xyz_from_pose_msg(latest["cup"])
                        if latest["cup"] is not None
                        else gt_poses.get("red_cup")
                    )
                    bowl_xyz = (
                        _xyz_from_pose_msg(latest["bowl"])
                        if latest["bowl"] is not None
                        else gt_poses.get("bowl")
                    )
                    if latched_target is not None:
                        target = list(latched_target)
                    else:
                        target = scene.resolve_target(
                            goal.target_ref,
                            cup_xyz=cup_xyz,
                            bowl_xyz=bowl_xyz,
                            ee_xyz=ee,
                        )
                    if target is None:
                        status = "failed"
                        reason = f"unresolved target_ref={goal.target_ref}"
                        aborted = True
                        abort_reason = reason
                        break
                    if phase == "dwell":
                        delta = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                        _, last_dist = bounded_ee_delta(
                            ee, target, max_step_m=goal.max_step_m
                        )
                        if goal.gripper_dwell is not None:
                            grip_cmd = float(goal.gripper_dwell)
                    else:
                        delta, dist = bounded_ee_delta(
                            ee, target, max_step_m=goal.max_step_m
                        )
                        last_dist = dist
                    last_delta = delta
                    eps = scene.eps_for(
                        goal.target_ref,
                        goal.success_eps_pos_m if goal.success_eps_pos_m > 0 else None,
                    )
                else:
                    delta = [float(x) for x in goal.ee_delta]
                    last_delta = delta
                    dist = None
                    eps = None

                msg = SkillIntent()
                msg.header.stamp = node.get_clock().now().to_msg()
                msg.device_id = device_id
                msg.run_id = run_id
                msg.source = "m5_mid_runtime"
                msg.skill_mode = "task_space"
                msg.ee_delta = delta
                msg.gripper = grip_cmd
                msg.control_mode = 1  # POSE
                msg.expire_ms = int(goal.expire_ms)
                msg.frame_id = scene.frame_id if scene is not None else "fr3_link0"
                pub.publish(msg)
                n_pub += 1

                rclpy.spin_once(node, timeout_sec=0.0)
                low = latest["low"]
                travel = 0.0
                if low is not None:
                    cur = [float(x) for x in low.ee_pose_actual[:3]]
                    travel = sum((a - b) ** 2 for a, b in zip(cur, start_ee)) ** 0.5
                    if mode == "toward" and target is not None:
                        _, last_dist = bounded_ee_delta(
                            cur, target, max_step_m=goal.max_step_m
                        )

                elapsed = time.time() - t0
                if mode == "toward" and last_dist is not None and eps is not None:
                    if phase == "dwell":
                        assert dwell_until is not None
                        if time.time() >= dwell_until:
                            status = "success"
                            reason = (
                                f"dist={last_dist:.4f}<={eps} dwell_done "
                                f"gripper={grip_cmd}"
                            )
                            break
                    elif last_dist <= eps:
                        if goal.dwell_s > 0:
                            phase = "dwell"
                            dwell_until = time.time() + goal.dwell_s
                            if goal.name.upper() == "PLACE":
                                place_ee_xyz = list(ee)
                            print(
                                f"[mid]   pose ok → dwell {goal.dwell_s}s "
                                f"gripper_dwell={goal.gripper_dwell}",
                                flush=True,
                            )
                        else:
                            status = "success"
                            reason = f"dist={last_dist:.4f}<={eps}"
                            break
                    if elapsed >= goal.max_duration_s:
                        status = "failed_timeout"
                        reason = f"timeout {elapsed:.2f}s dist={last_dist:.4f} eps={eps}"
                        aborted = True
                        abort_reason = reason
                        break
                else:
                    if travel >= goal.success_ee_travel_m:
                        status = "success"
                        reason = f"ee_travel={travel:.4f}>={goal.success_ee_travel_m}"
                        break
                    if elapsed >= goal.max_duration_s:
                        status = "success_timeout"
                        reason = f"timeout {elapsed:.2f}s travel={travel:.4f}"
                        break

                time.sleep(period)

            # PLACE 释放点：dwell 结束时 ee
            if (
                goal.name.upper() == "PLACE"
                and str(status).startswith("success")
                and latest["low"] is not None
            ):
                release_ee_xyz = [
                    float(x) for x in latest["low"].ee_pose_actual[:3]
                ]
                if place_ee_xyz is None:
                    place_ee_xyz = list(release_ee_xyz)

            time.sleep(max(goal.expire_ms / 1000.0, 0.25))

            step = {
                "index": gi,
                "name": goal.name,
                "target_ref": goal.target_ref,
                "mode": mode,
                "status": status,
                "reason": reason,
                "n_pub": n_pub,
                "ee_delta_last": last_delta,
                "dist_final": last_dist,
                "gripper": goal.gripper,
                "gripper_dwell": goal.gripper_dwell,
                "dwell_s": goal.dwell_s,
            }
            steps.append(step)
            print(f"[mid]   → {status}: {reason} n_pub={n_pub}", flush=True)

            if aborted:
                break

        ok = (
            not aborted
            and len(steps) >= 1
            and all(str(s.get("status", "")).startswith("success") for s in steps)
        )
        # 相对模板仍要求 ≥2 步（M5 回归契约）
        if tmpl.profile == "m5_template" and len(steps) < 2:
            ok = False
        if tmpl.profile == "m5_pickplace" and len(steps) < len(tmpl.goals):
            ok = False

        summary = {
            "success": ok,
            "profile": tmpl.profile,
            "situation": tmpl.situation,
            "forward_wm": tmpl.forward_wm,
            "template": str(path),
            "scene_yaml": str(scene.path) if scene is not None else None,
            "oracle_gt": bool(cup_pub is not None),
            "num_goals": len(tmpl.goals),
            "num_steps_done": len(steps),
            "steps": steps,
            "aborted": aborted,
            "abort_reason": abort_reason,
            "skill_mode": "task_space",
            "place_ee_xyz": place_ee_xyz,
            "release_ee_xyz": release_ee_xyz,
        }
        if steps_log is not None:
            steps_log.parent.mkdir(parents=True, exist_ok=True)
            steps_log.write_text(
                json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        if tmpl.profile == "m5_pickplace" or eval_log is not None:
            eval_doc = build_pickplace_eval(
                mid_summary=summary,
                scene=scene,
                place_ee_xyz=place_ee_xyz,
                release_ee_xyz=release_ee_xyz,
            )
            summary["eval"] = eval_doc
            # 抓放正式成功以 eval 为准（含水平谓词）
            if tmpl.profile == "m5_pickplace":
                summary["success"] = bool(eval_doc.get("success"))
                ok = summary["success"]
            out_eval = eval_log
            if out_eval is None and steps_log is not None:
                out_eval = steps_log.parent / "eval.json"
            if out_eval is not None:
                write_eval_json(Path(out_eval), eval_doc)
                summary["eval_log"] = str(out_eval)
                print(
                    f"[mid] eval success={eval_doc.get('success')} → {out_eval}",
                    flush=True,
                )

        print(
            f"[mid] DONE success={ok} steps={len(steps)} aborted={aborted}",
            flush=True,
        )
        return summary
    finally:
        node.destroy_node()
        if owned:
            try:
                import rclpy as _rclpy

                _rclpy.shutdown()
            except Exception:
                pass
