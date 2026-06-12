from __future__ import annotations

from datetime import datetime


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def make_isaac_job_id(operator: str, kind: str) -> str:
    return f"isaac_{_ts()}_{operator}_{kind}"


def make_real_run_id(prefix: str, operator: str, device_id: str) -> str:
    return f"{prefix}_{_ts()}_{operator}_{device_id}"


def make_gap_job_id(operator: str) -> str:
    return f"gap_{_ts()}_{operator}"


def make_policy_id(task_slug: str) -> str:
    slug = task_slug.replace("-", "_")[:24]
    return f"pol_{_ts()}_{slug}"


def make_demo_id(device_id: str) -> str:
    return f"demo_{_ts()}_{device_id}"


def make_eval_id(protocol_id: str, source: str = "sim") -> str:
    slug = protocol_id.replace("-", "_")[:20]
    return f"eval_{_ts()}_{source}_{slug}"


def make_calibration_id(device_id: str, cal_type: str) -> str:
    return f"calib_{device_id}_{cal_type}_{_ts()}"


def make_scene_id(layout_version: str, slug: str) -> str:
    return f"scene_{layout_version}_{slug}"
