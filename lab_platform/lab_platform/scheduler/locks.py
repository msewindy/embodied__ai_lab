from __future__ import annotations

from lab_platform.config import LabConfig
from lab_platform.index.service import IndexService
from lab_platform.models import RunCreateRequest
from lab_platform.protocols import IndexClient, ResourceScheduler


class DefaultResourceScheduler(ResourceScheduler):
    def __init__(self, config: LabConfig, index: IndexClient) -> None:
        self._config = config
        self._index = index

    def locks_for(self, request: RunCreateRequest) -> list[tuple[str, str]]:
        locks: list[tuple[str, str]] = []
        if request.run_type == "isaac_job" and request.job_kind == "train":
            locks.append(("gpu_lock", "lab-ws-02:gpu0"))
        for device_id in request.device_ids:
            locks.append(("device_lock", device_id))
        return locks

    def acquire(self, run_id: str, request: RunCreateRequest) -> list:
        locks = self.locks_for(request)
        if not locks:
            return []
        return self._index.acquire_locks(
            run_id, locks, ttl_seconds=self._config.lock_ttl_seconds
        )

    def release(self, run_id: str) -> None:
        self._index.release_locks(run_id)
