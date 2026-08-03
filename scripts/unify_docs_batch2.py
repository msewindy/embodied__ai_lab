# -*- coding: utf-8 -*-
"""Batch 2 document unification: INFRA + platform_architecture + meeting reviews."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILES = [
    "docs/infra/phase1_validation_plan_v1.md",
    "docs/infra/env_setup_checklist_v1.md",
    "docs/infra/infra_plan_draft_v0.md",
    "docs/software/ros2_interface_v1.md",
    "docs/architecture/platform_architecture_v1.md",
    "docs/meeting/tech02_review_v1.md",
    "docs/meeting/tech09_review_v1.md",
    "docs/meeting/tech14_review_v1.md",
]


def is_procurement_priority_line(line: str) -> bool:
    if "| P0 |" in line or "| P1 |" in line or "| P2 |" in line:
        if any(k in line for k in ("优先级", "¥", "万", "布线", "辅材", "P0")):
            return True
    return False


def is_task_id(line: str) -> bool:
    """Phase/task IDs like P2-1, P2-2 — not role codes."""
    import re
    return bool(re.search(r"\bP[123]-\d", line))


def unify_line(line: str) -> str:
    if is_procurement_priority_line(line) or is_task_id(line):
        return line
    replacements = [
        ("| **P1** |", "| **R1** |"),
        ("| **P2** |", "| **R2** |"),
        ("| **P3** |", "| **R3** |"),
        ("| P1 |", "| R1 |"),
        ("| P2 |", "| R2 |"),
        ("| P3 |", "| R3 |"),
        ("P1/P2/P3", "R1/R2/R3"),
        ("P2/P3", "R2/R3"),
        ("P1/P2", "R1/R2"),
        ("P2+P3", "R2+R3"),
        ("P1 提出", "R1 提出"),
        ("P2 可延后", "R2 可延后"),
        ("P2 负责", "R2 负责"),
        ("P3 确认", "R3 确认"),
        ("(P2 视角)", "(R2 视角)"),
        ("P2 负责的", "R2 负责的"),
        ("P2 负责", "R2 负责"),
        ("P1（契约）、P2（架构）、P3（安全/资产）", "R1（契约）、R2（架构）、R3（安全/资产）"),
    ]
    for old, new in replacements:
        line = line.replace(old, new)
    return line


def unify_text(text: str, rel: str) -> str:
    lines = [unify_line(ln) for ln in text.split("\n")]
    text = "\n".join(lines)

    text = text.replace("| **维护人** | P2 |", "| **维护人** | R2 |")
    text = text.replace("| **维护人** | P1 |", "| **维护人** | R1 |")
    text = text.replace("| **维护人** | P3 |", "| **维护人** | R3 |")

    if "platform_architecture_v1" in rel:
        sw = [
            ("Ubuntu 22.04 + CUDA 12.1", "Ubuntu 24.04 + CUDA 12.4+"),
            ("Ubuntu 22.04 + ROS2 Humble", "Ubuntu 24.04 + ROS2 Jazzy"),
            ("Ubuntu 22.04 + ROS2 Humble / CUDA 12.1", "Ubuntu 24.04 + ROS2 Jazzy / CUDA 12.4+"),
            ("v1.0-draft", "v1.1"),
        ]
        for old, new in sw:
            text = text.replace(old, new)

    if rel.startswith("docs/infra/") or rel.startswith("docs/meeting/"):
        text = text.replace(
            "| **依据** | [TECH-04 版本矩阵](../software/version_matrix_v1.md)",
            "| **依据** | [governance_index_v1.md](../org/governance_index_v1.md) · [plan_review_w1.md](../meeting/plan_review_w1.md) · [TECH-04 版本矩阵](../software/version_matrix_v1.md)",
        )
        if "phase1_validation" in rel or "env_setup" in rel:
            text = text.replace("| **版本** | v1.0 |", "| **版本** | v1.1 |")

    return text


def main():
    for rel in FILES:
        path = ROOT / rel
        if not path.exists():
            print("MISSING", rel)
            continue
        original = path.read_text(encoding="utf-8")
        updated = unify_text(original, rel)
        path.write_text(updated, encoding="utf-8")
        print("OK", rel)


if __name__ == "__main__":
    main()
