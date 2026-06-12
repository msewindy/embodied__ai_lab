from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from .models import (
    ArtifactRecord,
    LockRecord,
    PreFlightResult,
    RunCreateRequest,
    RunExecutionResult,
    RunRecord,
    RunStatus,
)


@runtime_checkable
class IndexClient(Protocol):
    def register_run(self, record: RunRecord) -> None: ...
    def patch_run(self, run_id: str, **fields: Any) -> None: ...
    def get_run(self, run_id: str) -> RunRecord | None: ...
    def list_runs(
        self, run_type: str | None = None, status: RunStatus | None = None, limit: int = 50
    ) -> list[RunRecord]: ...
    def register_artifact(self, record: ArtifactRecord) -> None: ...
    def patch_artifact(self, artifact_id: str, **fields: Any) -> None: ...
    def get_artifact(self, artifact_id: str) -> ArtifactRecord | None: ...
    def list_artifacts(
        self, artifact_type: str | None = None, limit: int = 50
    ) -> list[ArtifactRecord]: ...
    def link_run_artifact(self, run_id: str, artifact_id: str, relation: str) -> None: ...
    def get_lineage(self, run_id: str) -> dict: ...
    def acquire_locks(
        self, run_id: str, locks: list[tuple[str, str]], ttl_seconds: int
    ) -> list[LockRecord]: ...
    def release_locks(self, run_id: str) -> None: ...
    def list_active_locks(self, zone: str | None = None) -> list[LockRecord]: ...


@runtime_checkable
class PreFlightGate(Protocol):
    def check(self, request: RunCreateRequest) -> PreFlightResult: ...


@runtime_checkable
class ResourceScheduler(Protocol):
    def locks_for(self, request: RunCreateRequest) -> list[tuple[str, str]]: ...
    def acquire(self, run_id: str, request: RunCreateRequest) -> list[LockRecord]: ...
    def release(self, run_id: str) -> None: ...


@runtime_checkable
class IsaacLauncher(Protocol):
    def run(
        self, kind: str, task_id: str, workspace: Path, config_path: Path | None
    ) -> tuple[int, Path]: ...


@runtime_checkable
class RealRuntime(Protocol):
    def bringup(self, run_id: str, device_id: str, run_dir: Path) -> RunExecutionResult: ...
    def calibrate(
        self, run_id: str, device_id: str, cal_types: list[str], run_dir: Path
    ) -> RunExecutionResult: ...
    def collect(self, run_id: str, device_id: str, run_dir: Path) -> RunExecutionResult: ...
    def deploy(
        self, run_id: str, device_id: str, policy_id: str, run_dir: Path
    ) -> RunExecutionResult: ...
    def eval_run(
        self,
        run_id: str,
        device_id: str,
        policy_id: str,
        scene_id: str,
        protocol_id: str,
        run_dir: Path,
    ) -> RunExecutionResult: ...


@runtime_checkable
class Ros2Bridge(Protocol):
    def publish_run_context(self, run_id: str, device_ids: list[str], policy_id: str | None) -> None: ...
    def clear_run_context(self) -> None: ...


@runtime_checkable
class GapAnalyzer(Protocol):
    def analyze(
        self, sim_eval_id: str, real_eval_id: str, policy_id: str, job_dir: Path
    ) -> dict: ...
