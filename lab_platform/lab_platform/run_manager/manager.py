from __future__ import annotations

import json
import shutil
from pathlib import Path

from lab_platform.config import LabConfig
from lab_platform.ids import (
    make_gap_job_id,
    make_isaac_job_id,
    make_real_run_id,
)
from lab_platform.models import (
    Pipeline,
    PreFlightResult,
    RunCreateRequest,
    RunExecutionResult,
    RunRecord,
    RunStatus,
    now_iso,
)
from lab_platform.protocols import (
    GapAnalyzer,
    IndexClient,
    IsaacLauncher,
    PreFlightGate,
    RealRuntime,
    ResourceScheduler,
    Ros2Bridge,
)


class RunRejectedError(Exception):
    def __init__(self, result: PreFlightResult) -> None:
        self.result = result
        super().__init__(result.block_reason or "preflight failed")


class RunManager:
    """统一 Run 生命周期：PreFlight → Lock → 目录 → 执行 → Artifact → Release。"""

    RUN_PREFIX = {
        "isaac_job": ("isaac_jobs", make_isaac_job_id),
        "real_collect": ("real_collect", lambda op, d: make_real_run_id("rc", op, d)),
        "real_deploy": ("real_deploy", lambda op, d: make_real_run_id("rd", op, d)),
        "real_eval": ("real_eval", lambda op, d: make_real_run_id("re", op, d)),
        "real_bringup": ("real_bringup", lambda op, d: make_real_run_id("rb", op, d)),
        "calibration_session": (
            "calibration_session",
            lambda op, d: make_real_run_id("cal", op, d),
        ),
    }

    PIPELINE = {
        "isaac_job": Pipeline.A,
        "real_collect": Pipeline.B,
        "real_deploy": Pipeline.B,
        "real_eval": Pipeline.B,
        "real_bringup": Pipeline.C,
        "calibration_session": Pipeline.C,
    }

    def __init__(
        self,
        config: LabConfig,
        index: IndexClient,
        preflight: PreFlightGate,
        scheduler: ResourceScheduler,
        real_runtime: RealRuntime,
        ros2: Ros2Bridge,
        isaac_launcher: IsaacLauncher | None = None,
        gap_analyzer: GapAnalyzer | None = None,
    ) -> None:
        self._config = config
        self._index = index
        self._preflight = preflight
        self._scheduler = scheduler
        self._real = real_runtime
        self._ros2 = ros2
        self._isaac = isaac_launcher
        self._gap = gap_analyzer

    def execute(self, request: RunCreateRequest) -> RunRecord:
        """create → start → finish 一步完成（骨架期）。"""
        record = self.create(request)
        try:
            self.start(record.run_id)
            result = self._run_body(record, request)
            status = RunStatus.COMPLETED if result.success else RunStatus.FAILED
            self.finish(record.run_id, status, result)
            return self._index.get_run(record.run_id) or record
        except Exception:
            self._scheduler.release(record.run_id)
            self._index.patch_run(record.run_id, status=RunStatus.FAILED)
            self._ros2.clear_run_context()
            raise

    def create(self, request: RunCreateRequest) -> RunRecord:
        pf = self._preflight.check(request)
        if not pf.passed:
            raise RunRejectedError(pf)

        run_id = self._allocate_id(request)
        subdir, _ = self.RUN_PREFIX[request.run_type]
        run_dir = self._config.runs_dir / subdir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        self._scheduler.acquire(run_id, request)

        metadata = {
            "preflight_passed_at": now_iso(),
            "preflight_checklist": [
                {"id": i.check_id, "result": i.result, "detail": i.detail}
                for i in pf.checklist
            ],
            "experiment_plan_id": request.experiment_plan_id,
            "upstream_artifact_ids": request.upstream_artifact_ids,
            "scene_id": request.scene_id,
            "eval_protocol_id": request.eval_protocol_id,
            "policy_id": request.policy_id,
        }
        meta_path = run_dir / "metadata.json"
        meta_path.write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "run_type": request.run_type,
                    "job_kind": request.job_kind,
                    "operator": request.operator,
                    "device_ids": request.device_ids,
                    **metadata,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (run_dir / "inputs").mkdir(exist_ok=True)
        (run_dir / "logs").mkdir(exist_ok=True)

        for aid in request.upstream_artifact_ids:
            self._index.link_run_artifact(run_id, aid, "upstream")

        record = RunRecord(
            run_id=run_id,
            run_type=request.run_type,
            pipeline=self.PIPELINE[request.run_type],
            status=RunStatus.PENDING,
            operator=request.operator,
            project_id=request.project_id,
            storage_path=str(run_dir.relative_to(self._config.data_root)),
            device_ids=request.device_ids,
            job_kind=request.job_kind,
            metadata=metadata,
        )
        self._index.register_run(record)
        return record

    def start(self, run_id: str) -> None:
        run = self._index.get_run(run_id)
        if not run:
            raise KeyError(run_id)
        policy_id = run.metadata.get("policy_id")
        self._ros2.publish_run_context(run_id, run.device_ids, policy_id)
        self._index.patch_run(run_id, status=RunStatus.RUNNING)

    def finish(
        self,
        run_id: str,
        status: RunStatus,
        result: RunExecutionResult | None = None,
    ) -> None:
        meta_update: dict = {}
        if result:
            meta_update["execution"] = {
                "message": result.message,
                "downstream_artifact_ids": result.downstream_artifact_ids,
                **result.extra,
            }
            for aid in result.downstream_artifact_ids:
                self._index.link_run_artifact(run_id, aid, "downstream")
        self._index.patch_run(run_id, status=status, metadata=meta_update)
        self._scheduler.release(run_id)
        self._ros2.clear_run_context()

    def _run_body(
        self, record: RunRecord, request: RunCreateRequest
    ) -> RunExecutionResult:
        run_dir = self._config.data_root / record.storage_path
        rt = request.run_type

        if rt == "isaac_job":
            return self._run_isaac(record, request, run_dir)
        if rt == "real_bringup":
            return self._real.bringup(record.run_id, request.device_ids[0], run_dir)
        if rt == "calibration_session":
            return self._real.calibrate(
                record.run_id, request.device_ids[0], request.cal_types, run_dir
            )
        if rt == "real_collect":
            return self._real.collect(record.run_id, request.device_ids[0], run_dir)
        if rt == "real_deploy":
            return self._real.deploy(
                record.run_id,
                request.device_ids[0],
                request.policy_id or "",
                run_dir,
            )
        if rt == "real_eval":
            return self._real.eval_run(
                record.run_id,
                request.device_ids[0],
                request.policy_id or "",
                request.scene_id or "",
                request.eval_protocol_id or "",
                run_dir,
            )
        raise ValueError(f"unsupported run_type: {rt}")

    def _run_isaac(
        self, record: RunRecord, request: RunCreateRequest, run_dir: Path
    ) -> RunExecutionResult:
        if not self._isaac:
            raise RuntimeError("IsaacLauncher not configured")
        workspace = run_dir / "workspace"
        workspace.mkdir(exist_ok=True)
        config_path = run_dir / "inputs" / "train.yaml"
        if request.job_kind == "train" and not config_path.exists():
            config_path.write_text("# stub train config\n", encoding="utf-8")

        exit_code, native_dir = self._isaac.run(
            request.job_kind or "train",
            request.task_id or "stub_task",
            workspace,
            config_path if config_path.exists() else None,
        )
        shutil.copytree(native_dir, run_dir / "native", dirs_exist_ok=True)
        if exit_code != 0:
            return RunExecutionResult(False, f"isaac exit {exit_code}")

        from lab_platform.pipelines.pipeline_a import IsaacPipelineHooks

        hooks = IsaacPipelineHooks(self._config, self._index)
        aids = hooks.register_outputs(
            record.run_id,
            request.job_kind or "train",
            request.task_id or "stub_task",
            run_dir / "native",
            request.eval_protocol_id,
            policy_id=request.policy_id,
        )
        return RunExecutionResult(True, "isaac stub completed", aids)

    def _allocate_id(self, request: RunCreateRequest) -> str:
        if request.run_type == "isaac_job":
            return make_isaac_job_id(request.operator, request.job_kind or "train")
        device = request.device_ids[0] if request.device_ids else "nodevice"
        _, maker = self.RUN_PREFIX[request.run_type]
        return maker(request.operator, device)

    def run_gap_job(
        self, operator: str, sim_eval_id: str, real_eval_id: str, policy_id: str
    ) -> dict:
        if not self._gap:
            raise RuntimeError("GapAnalyzer not configured")
        req = RunCreateRequest(
            run_type="sim2real_gap_job",
            operator=operator,
            project_id=self._config.project_id,
            upstream_artifact_ids=[sim_eval_id, real_eval_id],
            policy_id=policy_id,
        )
        pf = self._preflight.check(req)
        if not pf.passed:
            raise RunRejectedError(pf)
        job_id = make_gap_job_id(operator)
        job_dir = self._config.jobs_dir / "sim2real_gap" / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        report = self._gap.analyze(sim_eval_id, real_eval_id, policy_id, job_dir)
        (job_dir / "gap_report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return {"job_id": job_id, "report": report}
