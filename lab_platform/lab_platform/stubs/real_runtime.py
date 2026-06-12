from __future__ import annotations

import json
import time
from pathlib import Path

import yaml

from lab_platform.artifacts.registry import ArtifactRegistry
from lab_platform.config import LabConfig
from lab_platform.models import RunExecutionResult
from lab_platform.protocols import IndexClient, RealRuntime


class StubRealRuntime(RealRuntime):
    """假 Real 运行时：打印 + 写报告 + 调 ArtifactRegistry。"""

    def __init__(self, config: LabConfig, index: IndexClient) -> None:
        self._config = config
        self._artifacts = ArtifactRegistry(config, index)

    def _sleep(self) -> None:
        time.sleep(self._config.stub_sleep_seconds)

    def bringup(self, run_id: str, device_id: str, run_dir: Path) -> RunExecutionResult:
        self._sleep()
        report = {
            "run_id": run_id,
            "device_id": device_id,
            "checks": [{"id": f"BU-{i:02d}", "result": "pass"} for i in range(1, 7)],
            "overall": "pass",
            "bridge_level_after": "L1",
        }
        results = run_dir / "results"
        results.mkdir(exist_ok=True)
        (results / "bringup_report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        self._set_bridge_level(device_id, "L1", run_id)
        print(f"[StubReal] bringup {device_id} → L1")
        return RunExecutionResult(True, "bringup ok", extra={"bridge_level": "L1"})

    def calibrate(
        self, run_id: str, device_id: str, cal_types: list[str], run_dir: Path
    ) -> RunExecutionResult:
        self._sleep()
        cal_id = self._artifacts.register_calibration(run_id, device_id, cal_types or ["hand_eye"])
        print(f"[StubReal] calibration {device_id} → {cal_id}")
        return RunExecutionResult(True, "calibration ok", [cal_id])

    def collect(self, run_id: str, device_id: str, run_dir: Path) -> RunExecutionResult:
        self._sleep()
        bag = run_dir / "rosbags"
        bag.mkdir(exist_ok=True)
        (bag / "stub.mcap").write_text("stub rosbag\n", encoding="utf-8")
        demo_id = self._artifacts.register_demo(run_id, device_id)
        print(f"[StubReal] collect {device_id} → {demo_id}")
        return RunExecutionResult(True, "collect ok", [demo_id])

    def deploy(
        self, run_id: str, device_id: str, policy_id: str, run_dir: Path
    ) -> RunExecutionResult:
        self._sleep()
        bag = run_dir / "rosbags"
        bag.mkdir(exist_ok=True)
        (bag / "deploy.mcap").write_text("stub deploy rosbag\n", encoding="utf-8")
        results = run_dir / "results"
        results.mkdir(exist_ok=True)
        (results / "result.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
        print(f"[StubReal] deploy {policy_id} on {device_id}")
        return RunExecutionResult(True, "deploy ok")

    def eval_run(
        self,
        run_id: str,
        device_id: str,
        policy_id: str,
        scene_id: str,
        protocol_id: str,
        run_dir: Path,
    ) -> RunExecutionResult:
        self._sleep()
        metrics = {"success_rate": 0.78, "episodes": 50, "protocol_id": protocol_id}
        eval_id = self._artifacts.register_eval(
            run_id, protocol_id, metrics, source="real"
        )
        results = run_dir / "results"
        results.mkdir(exist_ok=True)
        (results / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
        self._set_bridge_level(device_id, "L4", run_id)
        print(f"[StubReal] eval {device_id} → {eval_id} (success_rate=0.78)")
        return RunExecutionResult(True, "eval ok", [eval_id])

    def _set_bridge_level(self, device_id: str, level: str, run_id: str) -> None:
        path = self._config.registry_dir / "bridge_maturity.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
        devices = data.setdefault("devices", {})
        entry = devices.setdefault(device_id, {})
        entry["level"] = level
        entry["updated_at"] = run_id
        entry["updated_by_run"] = run_id
        path.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
