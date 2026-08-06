from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lab_platform.config import LabConfig
from lab_platform.index.service import IndexService, ResourceConflictError
from lab_platform.models import RunCreateRequest, RunStatus
from lab_platform.preflight.gate import DefaultPreFlightGate
from lab_platform.pipelines.demo_full import run_full_demo
from lab_platform.run_manager.manager import RunManager, RunRejectedError
from lab_platform.scheduler.locks import DefaultResourceScheduler
from lab_platform.ctrl_sim import CtrlSimLauncher
from lab_platform.stubs import (
    StubGapAnalyzer,
    StubIsaacLauncher,
    StubRealRuntime,
    StubRos2Bridge,
)
from lab_platform.workspace import init_workspace, promote_bridge


def build_run_manager(
    config: LabConfig,
    use_ros: bool = False,
    sim: bool = True,
    *,
    ctrl_auto_launch: bool = True,
    ctrl_keep_launch: bool = False,
    ctrl_record: bool = False,
    ctrl_record_fps: float = 10.0,
) -> RunManager:
    index = IndexService(config)
    preflight = DefaultPreFlightGate(config, index)
    scheduler = DefaultResourceScheduler(config, index)
    if use_ros:
        from lab_platform.pipeline_c.ros2_runtime import HybridRealRuntime, RclpyRos2Bridge

        ros2 = RclpyRos2Bridge()
        real = HybridRealRuntime(config, index, use_ros=True, sim=sim)
    else:
        ros2 = StubRos2Bridge()
        real = StubRealRuntime(config, index)
    isaac = StubIsaacLauncher(config)
    gap = StubGapAnalyzer()
    ctrl_sim = CtrlSimLauncher(config)
    ctrl_sim.auto_launch = ctrl_auto_launch
    ctrl_sim.keep_launch = ctrl_keep_launch
    ctrl_sim.record = ctrl_record
    ctrl_sim.record_fps = ctrl_record_fps
    return RunManager(
        config, index, preflight, scheduler, real, ros2, isaac, gap, ctrl_sim
    )


def _find_ctrl_sim_run_dir(config: LabConfig, run_id: str) -> Path | None:
    direct = config.runs_dir / "ctrl_sim" / run_id
    if direct.is_dir():
        return direct
    # fallback: index storage_path
    index = IndexService(config)
    rec = index.get_run(run_id)
    if rec and rec.storage_path:
        p = config.data_root / rec.storage_path
        if p.is_dir():
            return p
    return None


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.data_root)
    config = LabConfig.from_env(root)
    init_workspace(config)
    print(f"Workspace initialized at {config.data_root.resolve()}")
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    config = LabConfig.from_env(Path(args.data_root))
    if not config.index_db.exists():
        init_workspace(config)
    rm = build_run_manager(config)
    try:
        summary = run_full_demo(rm, config)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0
    except RunRejectedError as e:
        print(f"PreFlight rejected: {e}", file=sys.stderr)
        if e.result.checklist:
            for item in e.result.checklist:
                if item.result == "fail":
                    print(f"  {item.check_id}: {item.detail}", file=sys.stderr)
        return 1


def cmd_isaac(args: argparse.Namespace) -> int:
    config = LabConfig.from_env(Path(args.data_root))
    rm = build_run_manager(config)
    req = RunCreateRequest(
        run_type="isaac_job",
        operator=args.operator or config.operator,
        project_id=config.project_id,
        job_kind=args.kind,
        task_id=args.task,
        policy_id=args.policy,
        demo_id=args.demo,
        eval_protocol_id=args.eval_protocol,
        upstream_artifact_ids=[x for x in [args.policy, args.demo] if x],
    )
    try:
        record = rm.execute(req)
        meta = record.metadata.get("execution", {})
        aids = meta.get("downstream_artifact_ids", [])
        print(
            json.dumps(
                {"run_id": record.run_id, "status": record.status.value, "artifacts": aids},
                indent=2,
            )
        )
        return 0
    except RunRejectedError as e:
        print(f"rejected: {e}", file=sys.stderr)
        return 1


def cmd_run(args: argparse.Namespace) -> int:
    config = LabConfig.from_env(Path(args.data_root))
    rm = build_run_manager(config)
    req = RunCreateRequest(
        run_type=args.type,
        operator=args.operator or config.operator,
        project_id=config.project_id,
        device_ids=args.device or [],
        job_kind=args.kind,
        task_id=args.task,
        policy_id=args.policy,
        experiment_plan_id=args.plan,
        scene_id=args.scene,
        eval_protocol_id=args.eval_protocol,
        upstream_artifact_ids=[args.policy] if args.policy else [],
        cal_types=args.cal_types.split(",") if args.cal_types else [],
    )
    try:
        record = rm.execute(req)
        meta = record.metadata.get("execution", {})
        aids = meta.get("downstream_artifact_ids", [])
        print(
            json.dumps(
                {"run_id": record.run_id, "status": record.status.value, "artifacts": aids},
                indent=2,
            )
        )
        return 0
    except (RunRejectedError, ResourceConflictError) as e:
        print(f"failed: {e}", file=sys.stderr)
        return 1


def cmd_list(args: argparse.Namespace) -> int:
    config = LabConfig.from_env(Path(args.data_root))
    index = IndexService(config)
    if args.artifacts:
        arts = index.list_artifacts(artifact_type=args.artifact_type)
        for a in arts:
            print(f"{a.artifact_id}\t{a.artifact_type}\t{a.lifecycle_status}")
    else:
        runs = index.list_runs(run_type=args.run_type)
        for r in runs:
            print(f"{r.run_id}\t{r.run_type}\t{r.status.value}")
    return 0


def cmd_lineage(args: argparse.Namespace) -> int:
    config = LabConfig.from_env(Path(args.data_root))
    index = IndexService(config)
    print(json.dumps(index.get_lineage(args.run_id), indent=2, ensure_ascii=False))
    return 0


def cmd_bridge(args: argparse.Namespace) -> int:
    config = LabConfig.from_env(Path(args.data_root))
    promote_bridge(config, args.device, args.level.upper())
    return 0


def cmd_ctrl_sim_run(args: argparse.Namespace) -> int:
    """M3：归档一次 CTRL-SIM run（真 ROS run_context + 自动 launch/附着）。"""
    import os

    os.environ["ROS_DOMAIN_ID"] = "43"
    os.environ.setdefault("RMW_IMPLEMENTATION", "rmw_cyclonedds_cpp")

    config = LabConfig.from_env(Path(args.data_root))
    if not config.index_db.exists():
        init_workspace(config)

    from lab_platform.ctrl_sim.launcher import resolve_ros2_bin, ros2_missing_hint
    from lab_platform.pipeline_c.ros2_runtime import ros2_available

    if not ros2_available():
        print(
            "ERROR: rclpy/embodied_lab_msgs unavailable; source jazzy + ros2/install first",
            file=sys.stderr,
        )
        return 2
    if not resolve_ros2_bin():
        print(f"ERROR: {ros2_missing_hint()}", file=sys.stderr)
        return 2

    rm = build_run_manager(
        config,
        use_ros=True,
        ctrl_auto_launch=not args.no_launch,
        ctrl_keep_launch=args.keep_launch,
        ctrl_record=bool(args.record),
        ctrl_record_fps=float(args.record_fps),
    )
    req = RunCreateRequest(
        run_type="ctrl_sim",
        operator=args.operator or config.operator,
        project_id=config.project_id,
        device_ids=[args.device],
        scene_id=args.scene,
        job_kind=args.profile,
    )
    try:
        record = rm.execute(req)
        meta = record.metadata.get("execution", {})
        run_dir = config.data_root / record.storage_path
        print(
            json.dumps(
                {
                    "run_id": record.run_id,
                    "status": record.status.value,
                    "storage_path": record.storage_path,
                    "manifest": str(run_dir / "manifest.json"),
                    "ros_domain_id": meta.get("ros_domain_id", 43),
                    "backend": meta.get("backend", "isaac_sim"),
                    "isaac_sim_version": meta.get("isaac_sim_version"),
                    "mode": meta.get("mode"),
                    "launched_by_lab": meta.get("launched_by_lab"),
                    "run_context_seen": meta.get("run_context_seen"),
                    "recorded": meta.get("recorded"),
                    "record_frames": meta.get("record_frames"),
                    "low_jsonl": meta.get("low_jsonl"),
                    "message": meta.get("message"),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0 if record.status == RunStatus.COMPLETED else 1
    except (RunRejectedError, ResourceConflictError) as e:
        print(f"failed: {e}", file=sys.stderr)
        return 1


def cmd_ctrl_sim_replay(args: argparse.Namespace) -> int:
    """M4：开环回放某 run 的 low.jsonl。"""
    import os

    os.environ["ROS_DOMAIN_ID"] = "43"
    os.environ.setdefault("RMW_IMPLEMENTATION", "rmw_cyclonedds_cpp")

    config = LabConfig.from_env(Path(args.data_root))
    from lab_platform.ctrl_sim.launcher import resolve_ros2_bin, ros2_missing_hint
    from lab_platform.ctrl_sim.replayer import TrajectoryReplayer
    from lab_platform.pipeline_c.ros2_runtime import ros2_available

    if not ros2_available():
        print("ERROR: rclpy/embodied_lab_msgs unavailable", file=sys.stderr)
        return 2
    if not resolve_ros2_bin():
        print(f"ERROR: {ros2_missing_hint()}", file=sys.stderr)
        return 2

    run_dir = _find_ctrl_sim_run_dir(config, args.run_id)
    if run_dir is None:
        print(f"ERROR: run not found: {args.run_id}", file=sys.stderr)
        return 1
    jsonl = run_dir / "logs" / "low.jsonl"
    if not jsonl.is_file():
        print(f"ERROR: missing {jsonl} (run with --record first)", file=sys.stderr)
        return 1

    # 可选：缺 bridge 时自动 launch（与 run 一致）
    launcher = CtrlSimLauncher(config)
    launcher.auto_launch = not args.no_launch
    launcher.keep_launch = True
    # 轻量就绪检查：复用 topic list 逻辑
    from lab_platform.ctrl_sim.launcher import CTRL_SIM_DOMAIN, _topic_list

    ns = args.device.replace("-", "_")
    topics = _topic_list(CTRL_SIM_DOMAIN)
    need_lab = [f"/skill/{ns}/intent", f"/perception/{ns}/low_state"]
    if not all(t in topics for t in need_lab):
        if args.no_launch:
            print(
                "ERROR: CTRL-SIM topics missing; start bridge or omit --no-launch",
                file=sys.stderr,
            )
            return 1
        logs = run_dir / "logs"
        logs.mkdir(exist_ok=True)
        ok_launch, detail = launcher._start_launch(
            logs=logs,
            device_id=args.device,
            backend="isaac_sim",
            domain=CTRL_SIM_DOMAIN,
            wait_topics=need_lab,
        )
        if not ok_launch:
            print(f"ERROR: auto launch failed: {detail}", file=sys.stderr)
            return 1
        print(f"[CtrlSim] replay auto-launched bringup: {detail}", flush=True)

    replayer = TrajectoryReplayer(
        jsonl_path=jsonl,
        device_id=args.device,
        domain=43,
        rate=float(args.rate),
        run_id=args.run_id,
    )
    metrics = replayer.run()
    metrics_path = run_dir / "logs" / "replay_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    manifest_path = run_dir / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}
        manifest.setdefault("replay", {})
        manifest["replay"].update(
            {
                "metrics_path": "logs/replay_metrics.json",
                "last_replay_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
                "mean_ee_error_m": metrics.get("mean_ee_error_m"),
                "max_ee_error_m": metrics.get("max_ee_error_m"),
                "num_played": metrics.get("num_played"),
            }
        )
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    print(
        json.dumps(
            {
                "run_id": args.run_id,
                "jsonl": str(jsonl),
                "metrics": str(metrics_path),
                **metrics,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if metrics.get("success") else 1


def cmd_ops_bringup(args: argparse.Namespace) -> int:
    config = LabConfig.from_env(Path(args.data_root))
    if not config.index_db.exists():
        init_workspace(config)
    rm = build_run_manager(config, use_ros=args.ros, sim=args.sim)
    req = RunCreateRequest(
        run_type="real_bringup",
        operator=args.operator or config.operator,
        project_id=config.project_id,
        device_ids=[args.device],
    )
    try:
        record = rm.execute(req)
        meta = record.metadata.get("execution", {})
        print(
            json.dumps(
                {
                    "run_id": record.run_id,
                    "status": record.status.value,
                    "bridge_level": meta.get("bridge_level"),
                },
                indent=2,
            )
        )
        return 0 if record.status == RunStatus.COMPLETED else 1
    except RunRejectedError as e:
        print(f"rejected: {e}", file=sys.stderr)
        return 1


def cmd_concurrency_test(args: argparse.Namespace) -> int:
    """验收：Z-DYN 第 3 台 device 并发 deploy 应被拒绝。"""
    config = LabConfig.from_env(Path(args.data_root))
    if not config.index_db.exists():
        init_workspace(config)
    rm = build_run_manager(config)
    plan = "exp_concurrency_test"
    import yaml

    cap_path = config.registry_dir / "device_capabilities.yaml"
    caps = yaml.safe_load(cap_path.read_text(encoding="utf-8"))
    caps.setdefault("devices", {})["humanoid-01"] = {
        "model": "stub_humanoid",
        "status": "active",
        "zone": "Z-DYN",
        "task_domains": ["locomotion"],
        "has_force_control": False,
        "onboard_compute": "high",
        "max_speed_cap": 1.0,
        "sensors": ["joint_states"],
        "driver_bridge_plugin": "vendor/stub/bridge_v1",
        "power": "battery",
    }
    caps["devices"]["robot-03"] = {
        **caps["devices"]["humanoid-01"],
        "model": "stub_robot",
    }
    cap_path.write_text(yaml.dump(caps, allow_unicode=True, sort_keys=False), encoding="utf-8")
    for dev in ("quadruped-01", "humanoid-01", "robot-03"):
        promote_bridge(config, dev, "L3")

    from lab_platform.artifacts.registry import ArtifactRegistry

    index = IndexService(config)
    reg = ArtifactRegistry(config, index)
    native = config.data_root / "tmp_stub"
    native.mkdir(exist_ok=True)
    (native / "checkpoints").mkdir(exist_ok=True)
    (native / "checkpoints" / "best.pt").write_text("stub\n", encoding="utf-8")
    pol = reg.register_policy(
        f"stub_train_{id(native)}", f"concurrency_stub_{id(native)}", native, lifecycle="candidate"
    )

    # 清空残留锁，模拟 Z-DYN 两台占用
    with index._connect() as conn:
        conn.execute("DELETE FROM resource_locks")

    rid_a = "test_hold_a"
    rid_b = "test_hold_b"
    index.acquire_locks(rid_a, [("device_lock", "quadruped-01")], 3600)
    index.acquire_locks(rid_b, [("device_lock", "humanoid-01")], 3600)
    print("holding locks: quadruped-01, humanoid-01")

    try:
        rm.execute(
            RunCreateRequest(
                run_type="real_deploy",
                operator=config.operator,
                project_id=config.project_id,
                device_ids=["robot-03"],
                policy_id=pol,
                upstream_artifact_ids=[pol],
                experiment_plan_id=plan,
            )
        )
        print("ERROR: expected concurrency rejection", file=sys.stderr)
        return 1
    except (RunRejectedError, ResourceConflictError) as e:
        print(f"OK: third Z-DYN deploy rejected: {e}")
    finally:
        index.release_locks(rid_a)
        index.release_locks(rid_b)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lab", description="具身智能实验室运行框架")
    parser.add_argument("--data-root", default="data", help="数据根目录")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="初始化 workspace")
    p_init.set_defaults(func=cmd_init)

    p_demo = sub.add_parser("demo", help="全流程 demo")
    demo_sub = p_demo.add_subparsers(dest="demo_cmd", required=True)
    p_full = demo_sub.add_parser("full", help="跑通 Sim2Real 全链路")
    p_full.set_defaults(func=cmd_demo)

    p_isaac = sub.add_parser("isaac", help="Isaac job")
    p_isaac.add_argument("action", choices=["run"])
    p_isaac.add_argument("--kind", required=True, choices=["play", "train", "eval"])
    p_isaac.add_argument("--task", required=True)
    p_isaac.add_argument("--policy")
    p_isaac.add_argument("--demo")
    p_isaac.add_argument("--eval-protocol")
    p_isaac.add_argument("--operator")
    p_isaac.set_defaults(func=cmd_isaac)

    p_run = sub.add_parser("run", help="创建并执行 Run")
    p_run.add_argument("--type", required=True)
    p_run.add_argument("--device", action="append")
    p_run.add_argument("--kind")
    p_run.add_argument("--task")
    p_run.add_argument("--policy")
    p_run.add_argument("--plan")
    p_run.add_argument("--scene")
    p_run.add_argument("--eval-protocol")
    p_run.add_argument("--cal-types")
    p_run.add_argument("--operator")
    p_run.set_defaults(func=cmd_run)

    p_list = sub.add_parser("list", help="列出 runs 或 artifacts")
    p_list.add_argument("--artifacts", action="store_true")
    p_list.add_argument("--run-type")
    p_list.add_argument("--artifact-type")
    p_list.set_defaults(func=cmd_list)

    p_lin = sub.add_parser("lineage", help="查询 run 血缘")
    p_lin.add_argument("run_id")
    p_lin.set_defaults(func=cmd_lineage)

    p_br = sub.add_parser("bridge", help="手动设置 Bridge 级别（demo/测试用）")
    p_br.add_argument("action", choices=["promote"])
    p_br.add_argument("--device", required=True)
    p_br.add_argument("--level", required=True, help="L0-L4")
    p_br.set_defaults(func=cmd_bridge)

    p_cs = sub.add_parser("ctrl-sim", help="CTRL-SIM（DOMAIN 43）实验编排")
    cs_sub = p_cs.add_subparsers(dest="ctrl_sim_cmd", required=True)
    p_csr = cs_sub.add_parser(
        "run",
        help="归档一次 FR3 控制仿真 run（真 ROS run_context；缺 bridge 时自动 launch）",
    )
    p_csr.add_argument("--device", default="franka-01")
    p_csr.add_argument("--scene", default="tabletop_pickplace_v0_min")
    p_csr.add_argument(
        "--profile",
        default="m2_hello",
        choices=["m2_hello", "m5_template"],
        help="m2_hello=Δpose 冒烟；m5_template=薄 Mid APPROACH→RETREAT",
    )
    p_csr.add_argument(
        "--no-launch",
        action="store_true",
        help="不自动 launch；仅附着已有 franka_ctrl_sim",
    )
    p_csr.add_argument(
        "--keep-launch",
        action="store_true",
        help="若本次由 lab 拉起 bringup，结束后不杀掉",
    )
    p_csr.add_argument(
        "--record",
        action="store_true",
        help="M4：同步录制 A 轨 logs/low.jsonl（intent+low_state @record-fps）",
    )
    p_csr.add_argument("--record-fps", type=float, default=10.0, help="A 轨落盘 Hz（默认 10）")
    p_csr.add_argument("--operator")
    p_csr.set_defaults(func=cmd_ctrl_sim_run)

    p_csp = cs_sub.add_parser("replay", help="M4：开环回放某 run 的 low.jsonl")
    p_csp.add_argument("--run-id", required=True)
    p_csp.add_argument("--device", default="franka-01")
    p_csp.add_argument("--rate", type=float, default=1.0, help="回放速率倍率")
    p_csp.add_argument(
        "--no-launch",
        action="store_true",
        help="不自动 launch；仅附着已有 franka_ctrl_sim",
    )
    p_csp.set_defaults(func=cmd_ctrl_sim_replay)

    p_ops = sub.add_parser("ops", help="LabOps 运维命令")
    ops_sub = p_ops.add_subparsers(dest="ops_cmd", required=True)
    p_bu = ops_sub.add_parser("bringup", help="Go2 real_bringup（--ros 需先 launch go2_bringup）")
    p_bu.add_argument("--device", default="quadruped-01")
    p_bu.add_argument("--ros", action="store_true", help="使用 ROS2 BU-01..06 真检查")
    p_bu.add_argument("--sim", action="store_true", default=True, help="sim SDK 版本校验")
    p_bu.add_argument("--no-sim", dest="sim", action="store_false")
    p_bu.add_argument("--operator")
    p_bu.set_defaults(func=cmd_ops_bringup)

    p_test = sub.add_parser("test", help="框架验收测试")
    test_sub = p_test.add_subparsers(dest="test_cmd", required=True)
    p_conc = test_sub.add_parser("concurrency", help="Z-DYN 并发限制")
    p_conc.set_defaults(func=cmd_concurrency_test)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
