# -*- coding: utf-8 -*-
"""Batch 1 document unification: P1/P2/P3 -> R1/R2/R3, team size, software baseline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILES = [
    "实验室运行框架建设总体方案.md",
    "docs/process/experiment_workflow_v1.md",
    "docs/process/change_control_v1.md",
    "docs/process/meeting_policy_v1.md",
    "docs/process/document_management_v1.md",
    "docs/safety/safety_sop_v1.md",
    "docs/device/maintenance_policy_v1.md",
    "docs/layout/layout_draft_v0.md",
    "docs/device/embodied_hardware_survey_v1.md",
    "docs/architecture/blueprint_v0.md",
]


def is_procurement_priority_line(line: str) -> bool:
    if "| P0 |" in line or "| P1 |" in line or "| P2 |" in line:
        if any(k in line for k in ("优先级", "W3", "W4", "W6", "下单", "¥", "万")):
            return True
    return False


def unify_line(line: str) -> str:
    if is_procurement_priority_line(line):
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
        ("P3+P2", "R3+R2"),
        ("P2+P3", "R2+R3"),
        ("P1+P2", "R1+R2"),
        ("P1/P3", "R1/R3"),
        ("P1 为总 A", "R1 为总 A"),
        ("P1 统筹", "R1 统筹"),
        ("P1 批准", "R1 批准"),
        ("P1 监督", "R1 监督"),
        ("P1 签字", "R1 签字"),
        ("P1 有权", "R1 有权"),
        ("P1 备审", "R1 备审"),
        ("P1 统稿", "R1 统稿"),
        ("P1 维护", "R1 维护"),
        ("P2 等待", "R2 等待"),
        ("P2 初始化", "R2 初始化"),
        ("P2 预算", "R2 预算"),
        ("P2 网络", "R2 网络"),
        ("P2 负责", "R2 负责"),
        ("P3（安全", "R3（安全"),
        ("P3 或", "R3 或"),
        ("P3 提交", "R3 提交"),
        ("P3 负责", "R3 负责"),
        ("P3 设备", "R3 设备"),
        ("P3 台账", "R3 台账"),
        ("P3 安全", "R3 安全"),
        ("规划负责人 / P1", "实验室负责人 / R1"),
        ("平台负责人 / P2", "平台工程师 / R2"),
        ("现场负责人 / P3", "现场工程师 / R3"),
        ("| **P1** | 系统", "| **R1** | 实验室"),
        ("| **P2** | 平台", "| **R2** | 平台"),
        ("| **P3** | 现场", "| **R3** | 现场"),
    ]
    for old, new in replacements:
        line = line.replace(old, new)
    return line


def unify_text(text: str, rel: str) -> str:
    lines = [unify_line(ln) for ln in text.split("\n")]
    text = "\n".join(lines)

    team_replacements = [
        ("三人可登录、可协作、可录实验", "核心团队可登录、可协作、可录实验"),
        ("3 人组织与 16 周", "标准 4 人组织（R1–R4）与 16 周"),
        ("**3 人 × 全职**", "**4 人 × 全职**（R1–R4）"),
        ("≈ 12 人月", "≈ 16 人月"),
        ("维持 3 人；", "维持 4 人（标准编制）；"),
        ("三人各完成", "核心成员各完成"),
        ("三人读方案", "核心团队读方案"),
        ("三人过稿", "核心团队过稿"),
        ("三人确认", "核心团队确认"),
        ("三人签字", "核心成员签字（R1–R3 最低）"),
        ("三人全员同意", "核心成员全员同意（R1–R3 最低）"),
        ("三人 check_env", "团队 check_env"),
        ("三人是否对 RACI", "团队是否对 RACI"),
        ("三人时间冲突", "核心成员时间冲突"),
        ("| **三人全员同意**", "| **核心成员全员同意**"),
    ]
    for old, new in team_replacements:
        text = text.replace(old, new)

    if "总体方案" in rel or "blueprint" in rel:
        sw = [
            ("Ubuntu 22.04 LTS", "Ubuntu 24.04 LTS"),
            ("Ubuntu 22.04", "Ubuntu 24.04"),
            ("ROS2 Humble", "ROS2 Jazzy"),
            ("| Humble |", "| Jazzy |"),
            ("Python | 3.10", "Python | 3.12"),
            ("Isaac Sim 4.x", "Isaac Sim 6.0"),
            ("CUDA 12.1", "CUDA 12.4+"),
        ]
        for old, new in sw:
            text = text.replace(old, new)

    if "总体方案" in rel:
        text = text.replace(
            "embodied_lab/\n├── configs/",
            "lab_platform/ + ros2/\n├── configs/  # 见 lab_platform/",
        )
        text = text.replace(
            "`embodied_lab/` 仅目录+README",
            "`lab_platform/` + `ros2/`（Walking Skeleton 已存在）",
        )
        text = text.replace(
            "docs/assets/asset_registry_draft.md",
            "docs/device/embodied_hardware_survey_v1.md",
        )
        text = text.replace(
            "docs/plan/as_is_survey_w1.md",
            "docs/device/embodied_hardware_survey_v1.md",
        )
        text = text.replace("blueprint_v0.md", "docs/architecture/blueprint_v0.md")

    text = text.replace("| **维护人** | P1 |", "| **维护人** | R1 |")
    text = text.replace("| **维护人** | P2 |", "| **维护人** | R2 |")
    text = text.replace("| **维护人** | P3 |", "| **维护人** | R3 |")
    text = text.replace("| **维护人** | P2 (技术选型) / P3 (资产纳管) |", "| **维护人** | R2 / R3 |")
    text = text.replace("| **审批人** | P1 (总额度 ≤ 20万) |", "| **审批人** | R1 (总额度 ≤ 20万) |")

    if rel.startswith("docs/process/") or rel.startswith("docs/safety/") or "maintenance" in rel:
        text = text.replace("v1.0-draft", "v1.1")

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
