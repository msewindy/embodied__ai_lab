from __future__ import annotations

import json
from pathlib import Path

from lab_platform.protocols import GapAnalyzer


class StubGapAnalyzer(GapAnalyzer):
    def analyze(
        self, sim_eval_id: str, real_eval_id: str, policy_id: str, job_dir: Path
    ) -> dict:
        report = {
            "policy_id": policy_id,
            "sim_eval_id": sim_eval_id,
            "real_eval_id": real_eval_id,
            "sim_success_rate": 0.92,
            "real_success_rate": 0.78,
            "gap": 0.14,
            "recommendations": [
                "increase domain randomization on friction",
                "add real_collect episodes for edge cases",
            ],
        }
        print(f"[StubGap] gap={report['gap']:.0%} sim={report['sim_success_rate']} real={report['real_success_rate']}")
        return report
