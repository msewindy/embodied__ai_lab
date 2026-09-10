#!/usr/bin/env python3
"""组装 tabletop_pickplace_v0 合成 USD（FR3 + 桌/杯/碗原语）。

优先用本机 Isaac `python.sh` 的 pxr（无需 Play/GPU 即可写盘）：

  /home/ljqy/isaacsim/python.sh \\
    tasks/tabletop_pickplace_v0/scripts/assemble_scene_usd.py

碗碰撞默认用薄垫片（collision_mode=pad），外观圆柱无碰撞，减轻放置穿透弹飞。
会按 scene.yaml ``robot_cfg.q_home_rad`` 覆盖 FR3 关节 drive/state（度），
避免官方资产默认全 0 关节（EE 过高）导致抓放开场失败。
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

# 与 frankaFR3.usd / bridge DEFAULT_ARM_JOINTS 对齐
FR3_ARM_JOINT_PATHS = (
    "/fr3/fr3_link0/fr3_joint1",
    "/fr3/fr3_link1/fr3_joint2",
    "/fr3/fr3_link2/fr3_joint3",
    "/fr3/fr3_link3/fr3_joint4",
    "/fr3/fr3_link4/fr3_joint5",
    "/fr3/fr3_link5/fr3_joint6",
    "/fr3/fr3_link6/fr3_joint7",
)

DEFAULT_Q_HOME_RAD = (0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785)


def _load_yaml(path: Path) -> dict:
    try:
        import yaml
    except ImportError:
        raise SystemExit("PyYAML required: pip install pyyaml") from None
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _repo_paths(script: Path) -> tuple[Path, Path, Path]:
    pack = script.resolve().parents[1]
    repo = pack.parents[1]
    return pack, repo, pack / "scene.yaml"


def assemble(
    *,
    scene_yaml: Path,
    fr3_usd: Path,
    out_path: Path,
    cup_grid_id: int,
) -> Path:
    from pxr import Gf, Sdf, Usd, UsdGeom

    cfg = _load_yaml(scene_yaml)
    table = cfg["table"]
    objs = cfg["objects"]
    grid = cfg["cup_grid"]
    cam = cfg.get("camera") or {}
    cup_cfg = objs["red_cup"]
    bowl_cfg = objs["bowl"]

    L, W, H = [float(x) for x in table["size_lwh_m"]]
    tx, ty = [float(x) for x in table["top_center_xy_m"]]
    cup_d = float(cup_cfg["outer_diameter_m"])
    cup_h = float(cup_cfg["height_m"])
    cup_m = float(cup_cfg["mass_kg"])
    bowl_d = float(bowl_cfg["outer_diameter_m"])
    bowl_h = float(bowl_cfg["height_m"])
    bx, by, bz = [float(x) for x in bowl_cfg["base_center_m"]]
    pad_h = float(bowl_cfg.get("collision_pad_height_m", 0.008))
    collision_mode = str(bowl_cfg.get("collision_mode") or "pad")

    cells = grid["cells"]
    if cup_grid_id not in cells and str(cup_grid_id) in cells:
        cx, cy = [float(v) for v in cells[str(cup_grid_id)]]
    else:
        cx, cy = [float(v) for v in cells[cup_grid_id]]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()

    stage = Usd.Stage.CreateNew(str(out_path))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    root = stage.GetRootLayer()
    rel_fr3 = Path(os_relpath(fr3_usd, out_path.parent))
    root.subLayerPaths.append(rel_fr3.as_posix())

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # --- Table ---
    table_path = "/World/Table"
    cube = UsdGeom.Cube.Define(stage, table_path)
    cube.CreateSizeAttr(1.0)
    xf = UsdGeom.Xformable(cube)
    xf.ClearXformOpOrder()
    xf.AddTranslateOp().Set(Gf.Vec3d(tx, ty, -H / 2.0))
    xf.AddScaleOp().Set(Gf.Vec3f(L, W, H))
    _bind_preview_color(stage, table_path, (0.75, 0.75, 0.72))
    _make_kinematic_collider(
        stage,
        table_path,
        restitution=0.0,
        friction_static=0.8,
        friction_dynamic=0.7,
    )

    # --- red_cup (dynamic) ---
    cup_path = "/World/red_cup"
    cup = UsdGeom.Cylinder.Define(stage, cup_path)
    cup.CreateRadiusAttr(cup_d / 2.0)
    cup.CreateHeightAttr(cup_h)
    cup.CreateAxisAttr(UsdGeom.Tokens.z)
    cxf = UsdGeom.Xformable(cup)
    cxf.ClearXformOpOrder()
    cxf.AddTranslateOp().Set(Gf.Vec3d(cx, cy, cup_h / 2.0))
    _bind_preview_color(stage, cup_path, (0.85, 0.12, 0.10))
    _make_dynamic_rigid(
        stage,
        cup_path,
        mass=cup_m,
        linear_damping=float(cup_cfg.get("linear_damping", 2.0)),
        angular_damping=float(cup_cfg.get("angular_damping", 3.0)),
        restitution=float(cup_cfg.get("restitution", 0.0)),
        friction_static=float(cup_cfg.get("friction_static", 0.9)),
        friction_dynamic=float(cup_cfg.get("friction_dynamic", 0.7)),
    )

    # --- bowl: visual (no collision) + thin pad collider ---
    bowl_root = "/World/bowl"
    UsdGeom.Xform.Define(stage, bowl_root)
    bxf = UsdGeom.Xformable(stage.GetPrimAtPath(bowl_root))
    bxf.ClearXformOpOrder()
    bxf.AddTranslateOp().Set(Gf.Vec3d(bx, by, bz))

    visual_path = f"{bowl_root}/visual"
    vis = UsdGeom.Cylinder.Define(stage, visual_path)
    vis.CreateRadiusAttr(bowl_d / 2.0)
    vis.CreateHeightAttr(bowl_h)
    vis.CreateAxisAttr(UsdGeom.Tokens.z)
    vxf = UsdGeom.Xformable(vis)
    vxf.ClearXformOpOrder()
    vxf.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, bowl_h / 2.0))
    _bind_preview_color(stage, visual_path, (0.55, 0.55, 0.58))

    if collision_mode == "solid":
        # 旧行为：整柱碰撞（易弹飞；仅调试用）
        col_path = f"{bowl_root}/collision"
        col = UsdGeom.Cylinder.Define(stage, col_path)
        col.CreateRadiusAttr(bowl_d / 2.0)
        col.CreateHeightAttr(bowl_h)
        col.CreateAxisAttr(UsdGeom.Tokens.z)
        cxf2 = UsdGeom.Xformable(col)
        cxf2.ClearXformOpOrder()
        cxf2.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, bowl_h / 2.0))
    else:
        # pad：顶面薄垫，中心在碗顶下方 pad_h/2
        col_path = f"{bowl_root}/collision_pad"
        col = UsdGeom.Cylinder.Define(stage, col_path)
        col.CreateRadiusAttr(bowl_d / 2.0)
        col.CreateHeightAttr(pad_h)
        col.CreateAxisAttr(UsdGeom.Tokens.z)
        cxf2 = UsdGeom.Xformable(col)
        cxf2.ClearXformOpOrder()
        cxf2.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, bowl_h - pad_h / 2.0))

    _bind_preview_color(stage, col_path, (0.45, 0.45, 0.48))
    _make_kinematic_collider(
        stage,
        col_path,
        restitution=float(bowl_cfg.get("restitution", 0.0)),
        friction_static=float(bowl_cfg.get("friction_static", 0.9)),
        friction_dynamic=float(bowl_cfg.get("friction_dynamic", 0.7)),
    )

    if cam.get("position_m"):
        cam_path = "/World/CameraThirdPerson"
        cam_xf = UsdGeom.Xform.Define(stage, cam_path)
        px, py, pz = [float(v) for v in cam["position_m"]]
        cam_xf.AddTranslateOp().Set(Gf.Vec3d(px, py, pz))
        prim = cam_xf.GetPrim()
        prim.CreateAttribute("scene:lookAt", Sdf.ValueTypeNames.Double3).Set(
            Gf.Vec3d(*[float(v) for v in cam.get("look_at_m", [0, 0, 0])])
        )
        prim.CreateAttribute("scene:cameraKey", Sdf.ValueTypeNames.String).Set(
            str(cam.get("key") or "observation.images.third_person")
        )

    q_home = _resolve_q_home_rad(cfg)
    q_home_deg = _apply_fr3_q_home(stage, q_home)

    stage.SetMetadata(
        "comment",
        f"tabletop_pickplace_v0; cup_grid_id={cup_grid_id}; "
        f"bowl_collision={collision_mode}; q_home_deg={q_home_deg}; "
        f"subLayer={rel_fr3.as_posix()}",
    )
    stage.GetRootLayer().Save()
    return out_path


def _resolve_q_home_rad(cfg: dict) -> list[float]:
    raw = (cfg.get("robot_cfg") or {}).get("q_home_rad") or DEFAULT_Q_HOME_RAD
    q = [float(x) for x in raw]
    if len(q) != 7:
        raise ValueError(f"robot_cfg.q_home_rad must have 7 values, got {len(q)}")
    return q


def _apply_fr3_q_home(stage, q_home_rad: list[float]) -> list[float]:
    """在场景根层覆盖 FR3 关节 drive target + 初始角（Isaac 资产用度）。"""
    from pxr import Sdf

    q_deg = [math.degrees(x) for x in q_home_rad]
    missing: list[str] = []
    for path, deg in zip(FR3_ARM_JOINT_PATHS, q_deg):
        prim = stage.GetPrimAtPath(path)
        if not prim or not prim.IsValid():
            missing.append(path)
            continue

        lo = prim.GetAttribute("physics:lowerLimit")
        hi = prim.GetAttribute("physics:upperLimit")
        if lo and hi and lo.HasAuthoredValue() and hi.HasAuthoredValue():
            lo_v, hi_v = float(lo.Get()), float(hi.Get())
            if deg < lo_v - 1e-3 or deg > hi_v + 1e-3:
                raise ValueError(
                    f"{path}: q_home {deg:.3f} deg outside limits [{lo_v:.3f}, {hi_v:.3f}]"
                )

        drive = prim.GetAttribute("drive:angular:physics:targetPosition")
        if not drive:
            drive = prim.CreateAttribute(
                "drive:angular:physics:targetPosition", Sdf.ValueTypeNames.Float
            )
        drive.Set(float(deg))

        # PhysX 启动姿态；无 schema 时仍写成同名属性供 Isaac 读取
        state = prim.GetAttribute("state:angular:physics:position")
        if not state:
            state = prim.CreateAttribute(
                "state:angular:physics:position", Sdf.ValueTypeNames.Float
            )
        state.Set(float(deg))

    if missing:
        raise ValueError(
            "FR3 joint prims missing (is frankaFR3.usd subLayered?): " + ", ".join(missing)
        )
    return [round(x, 4) for x in q_deg]


def os_relpath(target: Path, start: Path) -> str:
    import os

    return os.path.relpath(str(target.resolve()), str(start.resolve()))


def _bind_preview_color(stage, prim_path: str, rgb: tuple[float, float, float]) -> None:
    from pxr import Gf, Sdf, UsdShade

    mat_path = f"{prim_path}/Looks/Preview"
    mat = UsdShade.Material.Define(stage, mat_path)
    shader = UsdShade.Shader.Define(stage, f"{mat_path}/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*rgb))
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.7)
    mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    UsdShade.MaterialBindingAPI.Apply(stage.GetPrimAtPath(prim_path)).Bind(mat)


def _ensure_physics_material(
    stage,
    prim_path: str,
    *,
    restitution: float,
    friction_static: float,
    friction_dynamic: float,
) -> None:
    from pxr import UsdPhysics

    prim = stage.GetPrimAtPath(prim_path)
    mat_api = UsdPhysics.MaterialAPI.Apply(prim)
    mat_api.CreateRestitutionAttr(float(restitution))
    mat_api.CreateStaticFrictionAttr(float(friction_static))
    mat_api.CreateDynamicFrictionAttr(float(friction_dynamic))


def _make_kinematic_collider(
    stage,
    prim_path: str,
    *,
    restitution: float = 0.0,
    friction_static: float = 0.8,
    friction_dynamic: float = 0.7,
) -> None:
    from pxr import UsdPhysics

    prim = stage.GetPrimAtPath(prim_path)
    UsdPhysics.CollisionAPI.Apply(prim)
    rb = UsdPhysics.RigidBodyAPI.Apply(prim)
    rb.CreateKinematicEnabledAttr(True)
    _ensure_physics_material(
        stage,
        prim_path,
        restitution=restitution,
        friction_static=friction_static,
        friction_dynamic=friction_dynamic,
    )


def _make_dynamic_rigid(
    stage,
    prim_path: str,
    *,
    mass: float,
    linear_damping: float = 2.0,
    angular_damping: float = 3.0,
    restitution: float = 0.0,
    friction_static: float = 0.9,
    friction_dynamic: float = 0.7,
) -> None:
    from pxr import Sdf, UsdPhysics

    prim = stage.GetPrimAtPath(prim_path)
    UsdPhysics.CollisionAPI.Apply(prim)
    UsdPhysics.RigidBodyAPI.Apply(prim)
    mass_api = UsdPhysics.MassAPI.Apply(prim)
    mass_api.CreateMassAttr(float(mass))
    # Isaac PhysX 常识别的自定义阻尼属性
    prim.CreateAttribute("physxRigidBody:linearDamping", Sdf.ValueTypeNames.Float).Set(
        float(linear_damping)
    )
    prim.CreateAttribute("physxRigidBody:angularDamping", Sdf.ValueTypeNames.Float).Set(
        float(angular_damping)
    )
    _ensure_physics_material(
        stage,
        prim_path,
        restitution=restitution,
        friction_static=friction_static,
        friction_dynamic=friction_dynamic,
    )


def main() -> int:
    script = Path(__file__)
    pack, repo, default_scene = _repo_paths(script)
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scene-yaml", type=Path, default=default_scene)
    p.add_argument("--fr3-usd", type=Path, default=repo / "frankaFR3.usd")
    p.add_argument("--out", type=Path, default=pack / "assets" / "tabletop_pickplace_v0.usda")
    p.add_argument("--cup-grid-id", type=int, default=None)
    args = p.parse_args()

    if not args.fr3_usd.is_file():
        print(f"ERROR: FR3 USD missing: {args.fr3_usd}", file=sys.stderr)
        return 2
    if not args.scene_yaml.is_file():
        print(f"ERROR: scene.yaml missing: {args.scene_yaml}", file=sys.stderr)
        return 2

    cfg = _load_yaml(args.scene_yaml)
    grid_id = (
        args.cup_grid_id
        if args.cup_grid_id is not None
        else int(cfg.get("cup_grid", {}).get("default_grid_id", 4))
    )

    try:
        out = assemble(
            scene_yaml=args.scene_yaml,
            fr3_usd=args.fr3_usd,
            out_path=args.out,
            cup_grid_id=grid_id,
        )
    except ImportError as e:
        print(
            "ERROR: pxr not available. Run with Isaac python:\n"
            f"  /home/ljqy/isaacsim/python.sh {script}",
            file=sys.stderr,
        )
        print(f"detail: {e}", file=sys.stderr)
        return 2

    q_home = _resolve_q_home_rad(cfg)
    q_deg = [round(math.degrees(x), 2) for x in q_home]
    print(f"Wrote {out}")
    print(f"  subLayer FR3: {args.fr3_usd}")
    print(f"  cup_grid_id: {grid_id}")
    print(f"  q_home_rad: {q_home}")
    print(f"  q_home_deg (authored): {q_deg}")
    print("  bowl: visual + collision_pad (reopen USD in Isaac after regenerate)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
