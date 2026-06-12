from __future__ import annotations

from pathlib import Path

import yaml

from lab_platform.config import LabConfig


def init_workspace(config: LabConfig) -> None:
    """创建 data/ 目录树与默认 registry。"""
    dirs = [
        config.data_root,
        config.runs_dir / "isaac_jobs",
        config.runs_dir / "real_collect",
        config.runs_dir / "real_deploy",
        config.runs_dir / "real_eval",
        config.runs_dir / "real_bringup",
        config.runs_dir / "calibration_session",
        config.jobs_dir / "sim2real_gap",
        config.artifacts_dir / "policies",
        config.artifacts_dir / "demos",
        config.artifacts_dir / "evals",
        config.artifacts_dir / "calibrations",
        config.artifacts_dir / "scenes",
        config.registry_dir / "eval_protocols",
        config.tasks_dir,
        config.data_root / "vendor",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    _write_if_missing(config.registry_dir / "device_capabilities.yaml", DEVICE_CAPABILITIES)
    _write_if_missing(config.registry_dir / "bridge_maturity.yaml", BRIDGE_MATURITY)
    _write_if_missing(config.registry_dir / "version_matrix.yaml", VERSION_MATRIX)
    _write_if_missing(
        config.registry_dir / "eval_protocols" / "loco_vel_v1.yaml",
        EVAL_PROTOCOL,
    )
    _write_if_missing(
        config.artifacts_dir / "scenes" / "scene_v1_pickplace_bench" / "scene_manifest.yaml",
        SCENE_MANIFEST,
    )
    (config.artifacts_dir / "scenes" / "scene_v1_pickplace_bench" / "layout").mkdir(
        exist_ok=True
    )
    _write_if_missing(
        config.tasks_dir / "velocity_rough_go2" / "task_manifest.yaml",
        TASK_MANIFEST,
    )
    _write_if_missing(
        config.data_root / "vendor" / "unitree_go2" / "plugin.yaml",
        VENDOR_GO2_PLUGIN,
    )

    from lab_platform.index.service import IndexService

    index = IndexService(config)
    index.initialize()


def promote_bridge(config: LabConfig, device_id: str, level: str, run_id: str = "manual") -> None:
    path = config.registry_dir / "bridge_maturity.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    devices = data.setdefault("devices", {})
    devices[device_id] = {
        "level": level,
        "updated_at": run_id,
        "updated_by_run": run_id,
    }
    path.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"[Bridge] {device_id} → {level}")


def _write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip() + "\n", encoding="utf-8")


DEVICE_CAPABILITIES = """
devices:
  franka-01:
    model: franka_emika_panda
    status: active
    zone: Z-DYN
    task_domains: [manipulation]
    has_force_control: true
    onboard_compute: medium
    max_speed_cap: 0.5
    sensors: [joint_states, ee_pose, wrist_camera, force_torque]
    driver_bridge_plugin: vendor/franka_panda/bridge_v1
    power: wired

  quadruped-01:
    model: unitree_go2
    status: active
    zone: Z-DYN
    task_domains: [locomotion, navigation]
    has_force_control: false
    onboard_compute: high
    max_speed_cap: 1.5
    sensors: [joint_states, imu, lidar, depth_camera]
    driver_bridge_plugin: vendor/unitree_go2/bridge_v1
    power: battery
"""

BRIDGE_MATURITY = """
devices:
  franka-01:
    level: L0
  quadruped-01:
    level: L0
"""

VERSION_MATRIX = """
ubuntu: "24.04"
ros2: jazzy
isaac_sim: "6.0"
isaac_lab: "3.0"
"""

EVAL_PROTOCOL = """
eval_protocol_id: loco_vel_v1
task_domain: locomotion
metrics:
  - name: success_rate
    type: float
    threshold_candidate: 0.85
  - name: episodes
    type: int
    default: 100
"""

SCENE_MANIFEST = """
scene_id: scene_v1_pickplace_bench
layout_version: v1
eval_protocol_id: loco_vel_v1
lighting_note: lab default
"""

TASK_MANIFEST = """
task_id: velocity_rough_go2
task_domain: locomotion
isaac_lab_env: Isaac-Velocity-Rough-Go2-v0
description: stub task for walking skeleton
"""

VENDOR_GO2_PLUGIN = """
plugin_id: vendor/unitree_go2/bridge_v1
device_model: unitree_go2
sdk_version: unitree_go2_sim_1.0
real_sdk_version: unitree_go2_sdk_1.0
ros2_package: go2_driver_bridge
bridge_node: go2_driver_bridge
smoke_service: /go2_driver_bridge/{device_id}/smoke
joint_count: 12
sensors:
  - joint_states
  - imu
  - odom
  - robot_state
"""
