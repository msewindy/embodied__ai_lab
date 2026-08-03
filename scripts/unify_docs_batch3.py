# -*- coding: utf-8 -*-
"""Batch 3: architecture, MDD, software/data/device specs — P1/P2/P3 -> R1/R2/R3."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILES = [
    "docs/architecture/platform_technical_architecture_v1.md",
    "docs/architecture/platform_detailed_design_v1.md",
    "docs/architecture/platform_architecture_as_built_v1.md",
    "docs/modules/README.md",
    "docs/modules/framework_skeleton_design_v1.md",
    "docs/modules/F6_real_stack_mdd_v1.md",
    "docs/modules/pipeline_c_ops_mdd_v1.md",
    "docs/modules/isaac_job_adapter_mdd_v1.md",
    "docs/modules/F7_index_service_mdd_v1.md",
    "docs/modules/F7_run_manager_mdd_v1.md",
    "docs/software/isaac_job_adapter_v1.md",
    "docs/software/preflight_checklist_spec.md",
    "docs/software/version_matrix_v1.md",
    "docs/data/policy_registry_spec.md",
    "docs/data/run_id_spec.md",
    "docs/device/device_capability_matrix_v1.md",
    "docs/safety/estop_wiring_v1.md",
]


def is_gap_priority_row(line: str) -> bool:
    return bool(re.match(r"^\|\s*\*\*P[0-3]\*\*\s*\|", line.strip()))


def is_procurement_priority_line(line: str) -> bool:
    if "| P0 |" in line or "| P1 |" in line or "| P2 |" in line:
        if any(k in line for k in ("优先级", "¥", "万", "布线", "辅材")):
            return True
    return False


def is_task_id(line: str) -> bool:
    return bool(re.search(r"\bP[123]-\d", line))


def fix_gap_row(line: str) -> str:
    if not is_gap_priority_row(line):
        return line
    line = line.replace("P3 台账", "R3 台账")
    parts = line.split("|")
    if len(parts) >= 5:
        owner = parts[-2].strip()
        owner_map = {"P2": "R2", "P3": "R3", "P2+P3": "R2+R3"}
        if owner in owner_map:
            parts[-2] = f" {owner_map[owner]} "
    return "|".join(parts)


def unify_line(line: str) -> str:
    if is_gap_priority_row(line):
        return fix_gap_row(line)
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
        ("P2 + P3", "R2 + R3"),
        ("P2+P3", "R2+R3"),
        ("P2（矩阵）/ P3（台账状态）", "R2（矩阵）/ R3（台账状态）"),
        ("P3 场地登记", "R3 场地登记"),
        ("P3 资产台账", "R3 资产台账"),
        ("P3 台账", "R3 台账"),
        ("+ P3 台账", "+ R3 台账"),
        ("接 P3 台账", "接 R3 台账"),
        ("经 **change_control** + P3 台账", "经 **change_control** + R3 台账"),
        ("P3 台账 →", "R3 台账 →"),
        ("P1 顶层", "R1 顶层"),
        ("P1 契约", "R1 契约"),
        ("关联 P1", "关联 R1"),
        ("落实 P1", "落实 R1"),
        ("P1 experiment_workflow", "R1 experiment_workflow"),
        ("实施路线 (P2)", "实施路线 (R2)"),
        ("下一步 (P2)", "下一步 (R2)"),
        ("与 P3 衔接", "与 R3 衔接"),
        ("P3 更新 SceneManifest", "R3 更新 SceneManifest"),
        ("提示 P2 补", "提示 R2 补"),
        ("## 待 P1", "## 待 R1"),
        ("5. **P1**：", "5. **R1**："),
        ("| P3 | `data/registry", "| R3 | `data/registry"),
        ("（F7 / Isaac / Real / P3 registry）", "（F7 / Isaac / Real / R3 registry）"),
        ("三人并行切分", "核心团队并行切分"),
        ("由 P1 审批", "由 R1 审批"),
        ("P2 自行决定", "R2 自行决定"),
        ("（P1 阶段重写）", "（阶段一重写）"),
        ("重写（P1）", "重写（阶段一）"),
        ("P1  blueprint_v0", "R1  blueprint_v0"),
        ("P2  platform_detailed_design_v1", "R2  platform_detailed_design_v1"),
        ("P2  platform_technical_architecture_v1", "R2  platform_technical_architecture_v1"),
        ("P2  ros2_interface_v1", "R2  ros2_interface_v1"),
        ("### P1 — W2–W4", "### 阶段一 — W2–W4"),
        ("### P2 — 项目接入期", "### 阶段二 — 项目接入期"),
    ]
    for old, new in replacements:
        line = line.replace(old, new)
    return line


def unify_text(text: str, rel: str) -> str:
    lines = [unify_line(ln) for ln in text.split("\n")]
    text = "\n".join(lines)

    text = text.replace("| **维护人** | P2 |", "| **维护人** | R2 |")
    text = text.replace("| **维护人**  | P2", "| **维护人**  | R2")
    text = text.replace("| **维护人** | P1 |", "| **维护人** | R1 |")
    text = text.replace("| **维护人** | P3 |", "| **维护人** | R3 |")
    text = text.replace("| **维护人** | P2 + P3 |", "| **维护人** | R2 + R3 |")

    if rel.startswith("docs/architecture/") or rel.startswith("docs/modules/"):
        text = text.replace(
            "| **前置依据** |",
            "| **依据** | [governance_index_v1.md](../org/governance_index_v1.md) · [plan_review_w1.md](../meeting/plan_review_w1.md) · ",
            1,
        ) if "| **依据** |" not in text[:800] else text

    batch3_version_bump = [
        "docs/architecture/platform_technical_architecture_v1.md",
        "docs/architecture/platform_detailed_design_v1.md",
        "docs/architecture/platform_architecture_as_built_v1.md",
        "docs/device/device_capability_matrix_v1.md",
        "docs/software/version_matrix_v1.md",
        "docs/software/preflight_checklist_spec.md",
        "docs/software/isaac_job_adapter_v1.md",
        "docs/data/policy_registry_spec.md",
        "docs/data/run_id_spec.md",
        "docs/modules/README.md",
    ]
    if rel in batch3_version_bump:
        text = text.replace("| **版本** | v1.0-draft |", "| **版本** | v1.1 |")
        text = text.replace("| **版本**   | v1.0-approved", "| **版本**   | v1.1")
        text = text.replace("| **版本** | v1.0-approved |", "| **版本** | v1.1 |")
        text = text.replace("| **版本** | v1.0 |", "| **版本** | v1.1 |")
        text = text.replace("| **版本** | v1.0-draft |", "| **版本** | v1.1 |")

    if "estop_wiring" in rel:
        text = text.replace("| **版本** | v1.0-draft |", "| **版本** | v1.1 |")

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
