from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml

from lab_platform.config import LabConfig
from lab_platform.models import PreFlightItem, PreFlightResult, RunCreateRequest
from lab_platform.protocols import IndexClient, PreFlightGate


class DefaultPreFlightGate(PreFlightGate):
    """骨架期 PreFlight：读 registry yaml，实现核心 PF 检查。"""

    BRIDGE_MIN = {
        "real_bringup": 0,
        "calibration_session": 1,
        "real_collect": 2,
        "real_deploy": 3,
        "real_eval": 3,
    }

    def __init__(self, config: LabConfig, index: IndexClient) -> None:
        self._config = config
        self._index = index

    def check(self, request: RunCreateRequest) -> PreFlightResult:
        items: list[PreFlightItem] = []
        rt = request.run_type

        items.append(self._check_env())
        if rt == "isaac_job":
            items.extend(self._check_isaac(request))
        elif rt in self.BRIDGE_MIN:
            items.extend(self._check_real(request, rt))
        elif rt == "sim2real_gap_job":
            items.extend(self._check_gap(request))

        failed = [i for i in items if i.result == "fail"]
        passed = not failed
        return PreFlightResult(
            passed=passed,
            checklist=items,
            block_reason=failed[0].detail if failed else None,
        )

    def _check_env(self) -> PreFlightItem:
        vm = self._config.registry_dir / "version_matrix.yaml"
        if not vm.exists():
            return PreFlightItem("PF-01", "warn", "version_matrix.yaml missing (stub ok)")
        return PreFlightItem("PF-01", "pass", "check_env stub ok")

    def _check_isaac(self, request: RunCreateRequest) -> list[PreFlightItem]:
        items: list[PreFlightItem] = []
        if request.job_kind == "train":
            active_gpu = self._index.list_active_locks()
            if any(l.lock_type == "gpu_lock" for l in active_gpu):
                items.append(PreFlightItem("PF-08", "fail", "gpu_lock held"))
            else:
                items.append(PreFlightItem("PF-08", "pass", "gpu available"))
        for aid in request.upstream_artifact_ids:
            if not self._index.get_artifact(aid):
                items.append(PreFlightItem("PF-15", "fail", f"artifact missing: {aid}"))
            else:
                items.append(PreFlightItem("PF-15", "pass", aid))
        if request.policy_id and not self._index.get_artifact(request.policy_id):
            items.append(PreFlightItem("PF-15", "fail", f"policy missing: {request.policy_id}"))
        elif request.policy_id:
            items.append(PreFlightItem("PF-15", "pass", request.policy_id))
        if request.demo_id and not self._index.get_artifact(request.demo_id):
            items.append(PreFlightItem("PF-15", "fail", f"demo missing: {request.demo_id}"))
        elif request.demo_id:
            items.append(PreFlightItem("PF-15", "pass", request.demo_id))
        return items

    def _check_real(self, request: RunCreateRequest, run_type: str) -> list[PreFlightItem]:
        items: list[PreFlightItem] = []
        caps = self._load_yaml(self._config.registry_dir / "device_capabilities.yaml")
        bridge = self._load_yaml(self._config.registry_dir / "bridge_maturity.yaml")
        devices = caps.get("devices") or {}
        bridge_dev = bridge.get("devices") or {}

        for device_id in request.device_ids:
            dev = devices.get(device_id)
            if not dev:
                items.append(PreFlightItem("PF-02", "fail", f"unknown device: {device_id}"))
                continue
            if dev.get("status") == "blocked":
                items.append(PreFlightItem("PF-02", "fail", f"{device_id} blocked"))
            else:
                items.append(PreFlightItem("PF-02", "pass", device_id))

            level = self._bridge_level(bridge_dev.get(device_id, {}))
            need = self.BRIDGE_MIN.get(run_type, 0)
            if level < need:
                items.append(
                    PreFlightItem(
                        "PF-03",
                        "fail",
                        f"{device_id} bridge L{level} < L{need}",
                    )
                )
            else:
                items.append(PreFlightItem("PF-03", "pass", f"L{level}"))

        if run_type in ("real_deploy", "real_eval") and request.policy_id:
            pol = self._index.get_artifact(request.policy_id)
            if not pol:
                items.append(PreFlightItem("PF-15", "fail", "policy missing"))
            elif pol.lifecycle_status == "draft":
                items.append(PreFlightItem("PF-13", "fail", "policy is draft"))
            elif pol.lifecycle_status == "deprecated":
                items.append(PreFlightItem("PF-13", "fail", "policy deprecated"))
            else:
                items.append(PreFlightItem("PF-13", "pass", pol.lifecycle_status))

        if run_type == "real_eval":
            if not request.scene_id:
                items.append(PreFlightItem("PF-05", "fail", "scene_id required"))
            elif not (self._config.artifacts_dir / "scenes" / request.scene_id).exists():
                items.append(PreFlightItem("PF-05", "fail", f"scene missing: {request.scene_id}"))
            else:
                items.append(PreFlightItem("PF-05", "pass", request.scene_id))
            if not request.eval_protocol_id:
                items.append(PreFlightItem("PF-06", "fail", "eval_protocol_id required"))
            else:
                proto = self._config.registry_dir / "eval_protocols" / f"{request.eval_protocol_id}.yaml"
                if not proto.exists():
                    items.append(PreFlightItem("PF-06", "fail", "protocol missing"))
                else:
                    items.append(PreFlightItem("PF-06", "pass", request.eval_protocol_id))

        if run_type in ("real_collect", "real_deploy", "real_eval"):
            if not request.experiment_plan_id:
                items.append(PreFlightItem("PF-09", "fail", "experiment_plan_id required"))
            else:
                items.append(PreFlightItem("PF-09", "pass", request.experiment_plan_id))
            if request.risk_level in ("medium", "high") and not request.approved_by:
                items.append(PreFlightItem("PF-10", "fail", "approved_by required"))
            else:
                items.append(PreFlightItem("PF-10", "pass", request.approved_by or "n/a"))

        if run_type in ("real_deploy", "real_eval") and request.policy_id:
            items.extend(self._compatibility_check(request))

        return items

    def _compatibility_check(self, request: RunCreateRequest) -> list[PreFlightItem]:
        items: list[PreFlightItem] = []
        pol_path = (
            self._config.artifacts_dir
            / "policies"
            / request.policy_id
            / "policy_manifest.yaml"
        )
        caps = self._load_yaml(self._config.registry_dir / "device_capabilities.yaml")
        if not pol_path.exists():
            items.append(PreFlightItem("PF-12", "fail", "policy_manifest missing"))
            return items
        manifest = yaml.safe_load(pol_path.read_text(encoding="utf-8")) or {}
        for device_id in request.device_ids:
            dev = (caps.get("devices") or {}).get(device_id, {})
            domain = manifest.get("task_domain")
            domains = dev.get("task_domains") or []
            if domain and domain not in domains:
                items.append(
                    PreFlightItem(
                        "PF-12",
                        "fail",
                        f"task_domain {domain} not in {domains}",
                    )
                )
            else:
                items.append(PreFlightItem("PF-12", "pass", f"{device_id} compatible"))
        return items

    def _check_gap(self, request: RunCreateRequest) -> list[PreFlightItem]:
        items: list[PreFlightItem] = []
        for aid in request.upstream_artifact_ids:
            art = self._index.get_artifact(aid)
            if not art or art.artifact_type != "eval":
                items.append(PreFlightItem("PF-15", "fail", f"eval artifact: {aid}"))
            else:
                items.append(PreFlightItem("PF-15", "pass", aid))
        return items

    @staticmethod
    def _load_yaml(path: Path) -> dict:
        if not path.exists():
            return {}
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    @staticmethod
    def _bridge_level(entry: dict) -> int:
        raw = entry.get("level", "L0")
        if isinstance(raw, int):
            return raw
        return int(str(raw).lstrip("L") or 0)
