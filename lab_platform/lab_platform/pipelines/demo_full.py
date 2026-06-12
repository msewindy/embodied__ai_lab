from __future__ import annotations

from lab_platform.config import LabConfig
from lab_platform.models import RunCreateRequest
from lab_platform.run_manager.manager import RunManager
from lab_platform.workspace import promote_bridge


def run_full_demo(rm: RunManager, config: LabConfig) -> dict:
    """
    一键跑通 Sim2Real 全链路（Stub 内部逻辑）：
    bringup → calibrate → collect → isaac train/eval → deploy → real eval → gap
    """
    device = "quadruped-01"
    operator = config.operator
    project = config.project_id
    task = "velocity_rough_go2"
    plan = "exp_demo_full"
    scene = "scene_v1_pickplace_bench"
    protocol = "loco_vel_v1"

    print("\n=== ① Pipeline C: real_bringup ===")
    rm.execute(
        RunCreateRequest(
            run_type="real_bringup",
            operator=operator,
            project_id=project,
            device_ids=[device],
        )
    )

    print("\n=== ② Bridge promote L2 (demo shortcut) ===")
    promote_bridge(config, device, "L2", "demo_promote_l2")

    print("\n=== ③ Pipeline C: calibration_session ===")
    rm.execute(
        RunCreateRequest(
            run_type="calibration_session",
            operator=operator,
            project_id=project,
            device_ids=[device],
            cal_types=["hand_eye", "camera_extrinsic"],
        )
    )

    print("\n=== ④ Pipeline B: real_collect ===")
    collect = rm.execute(
        RunCreateRequest(
            run_type="real_collect",
            operator=operator,
            project_id=project,
            device_ids=[device],
            experiment_plan_id=plan,
        )
    )
    demo_id = collect.metadata.get("execution", {}).get("downstream_artifact_ids", [None])[0]

    print("\n=== ⑤ Pipeline A: isaac_job train ===")
    train = rm.execute(
        RunCreateRequest(
            run_type="isaac_job",
            operator=operator,
            project_id=project,
            job_kind="train",
            task_id=task,
            demo_id=demo_id,
            upstream_artifact_ids=[demo_id] if demo_id else [],
        )
    )
    policy_id = train.metadata.get("execution", {}).get("downstream_artifact_ids", [None])[0]

    print("\n=== ⑥ Pipeline A: isaac_job eval ===")
    eval_run = rm.execute(
        RunCreateRequest(
            run_type="isaac_job",
            operator=operator,
            project_id=project,
            job_kind="eval",
            task_id=task,
            policy_id=policy_id,
            upstream_artifact_ids=[policy_id] if policy_id else [],
            eval_protocol_id=protocol,
        )
    )
    sim_eval_id = eval_run.metadata.get("execution", {}).get("downstream_artifact_ids", [None])[0]

    print("\n=== ⑦ Bridge promote L3 (deploy gate) ===")
    promote_bridge(config, device, "L3", "demo_promote_l3")

    print("\n=== ⑧ Pipeline B: real_deploy ===")
    rm.execute(
        RunCreateRequest(
            run_type="real_deploy",
            operator=operator,
            project_id=project,
            device_ids=[device],
            policy_id=policy_id,
            upstream_artifact_ids=[policy_id] if policy_id else [],
            experiment_plan_id=plan,
        )
    )

    print("\n=== ⑨ Pipeline B: real_eval ===")
    real_eval = rm.execute(
        RunCreateRequest(
            run_type="real_eval",
            operator=operator,
            project_id=project,
            device_ids=[device],
            policy_id=policy_id,
            upstream_artifact_ids=[policy_id] if policy_id else [],
            experiment_plan_id=plan,
            scene_id=scene,
            eval_protocol_id=protocol,
        )
    )
    real_eval_id = real_eval.metadata.get("execution", {}).get("downstream_artifact_ids", [None])[0]

    print("\n=== ⑩ sim2real_gap_job ===")
    gap = rm.run_gap_job(operator, sim_eval_id, real_eval_id, policy_id or "")

    print("\n=== Demo 完成 ===")
    return {
        "policy_id": policy_id,
        "sim_eval_id": sim_eval_id,
        "real_eval_id": real_eval_id,
        "gap_job_id": gap["job_id"],
        "gap": gap["report"],
    }
