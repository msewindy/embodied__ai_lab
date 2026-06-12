from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Pipeline(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"
    REJECTED = "rejected"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@dataclass
class RunRecord:
    run_id: str
    run_type: str
    pipeline: Pipeline
    status: RunStatus
    operator: str
    project_id: str
    storage_path: str
    device_ids: list[str] = field(default_factory=list)
    job_kind: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ArtifactRecord:
    artifact_id: str
    artifact_type: str
    lifecycle_status: str
    producer_run_id: str
    storage_path: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LockRecord:
    lock_type: str
    resource_id: str
    holder_run_id: str
    acquired_at: str
    expires_at: str


@dataclass
class PreFlightItem:
    check_id: str
    result: str  # pass | fail | skip | warn
    detail: str = ""


@dataclass
class PreFlightResult:
    passed: bool
    checklist: list[PreFlightItem]
    block_reason: str | None = None


@dataclass
class RunCreateRequest:
    run_type: str
    operator: str
    project_id: str
    device_ids: list[str] = field(default_factory=list)
    job_kind: str | None = None
    upstream_artifact_ids: list[str] = field(default_factory=list)
    experiment_plan_id: str | None = None
    scene_id: str | None = None
    eval_protocol_id: str | None = None
    policy_id: str | None = None
    cal_types: list[str] = field(default_factory=list)
    task_id: str | None = None
    demo_id: str | None = None
    approved_by: str | None = None
    risk_level: str = "low"  # low | medium | high


@dataclass
class RunExecutionResult:
    success: bool
    message: str = ""
    downstream_artifact_ids: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
