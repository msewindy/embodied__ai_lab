# -*- coding: utf-8 -*-
"""
Verify docs/ (excluding research/) have no legacy role codes P1/P2/P3.

Allowed contexts (not violations):
  - Procurement / gap priority: | P0 |, | P1 |, | **P1** | in priority columns
  - Task IDs: P2-1, P2-2, ...
  - Mapping tables in document_unification_plan, raci historical note
  - Superseded budget_draft_v1 body (header-only check still applies elsewhere)
  - Phrases: P1 可选项, P0 先行, P0 规范
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
L0 = ROOT / "实验室运行框架建设总体方案.md"

ROLE_RE = re.compile(r"\bP([123])\b")
TASK_ID_RE = re.compile(r"\bP[123]-\d")
GAP_PRIORITY_RE = re.compile(r"^\|\s*\*\*P[0-3]\*\*\s*\|")
PROCUREMENT_ROW_RE = re.compile(r"\|\s*P[0-3]\s*\|")
ALLOWLIST_FILES = {
    "docs/plan/document_unification_plan_v1.md",
    "docs/plan/budget_draft_v1.md",  # superseded archive
}


def is_allowed_line(line: str, rel: str) -> bool:
    if TASK_ID_RE.search(line):
        return True
    if GAP_PRIORITY_RE.match(line.strip()):
        return True
    if "P1 可选项" in line or "P0 先行" in line or "P0 规范" in line:
        return True
    if re.search(r"P0/P1/P2", line):
        return True
    if "P1/P2/P3" in line and ("对照" in line or "历史" in line or "不得" in line):
        return True
    if "采购优先级" in line or "优先级" in line and "P0/P1/P2" in line:
        return True
    if rel in ALLOWLIST_FILES:
        return True
    if "docs/org/raci_v1.md" in rel and "历史文档中的 P1/P2/P3" in line:
        return True
    # Procurement BOM: priority column before week or after ¥
    if PROCUREMENT_ROW_RE.search(line):
        if any(k in line for k in ("¥", "W3", "W4", "W6", "万", "布线", "辅材", "优先级", "可选项")):
            return True
        if re.search(r"\|\s*P[0-3]\s*\|\s*W\d", line):
            return True
        if re.search(r"\|\s*\*\*P[0-3]\*\*\s*\|", line) and "R2" in line:
            return True  # budget_v2 summary table: | **P1** | ... | R2/R3 |
        # BOM detail rows: amount columns then priority
        if re.search(r"\|\s*\d{1,3}(?:,\d{3})*\s*\|\s*P[0-3]\s*\|", line):
            return True
        if re.search(r"\|\s*P[0-3]\s*\|\s*bringup", line):
            return True
        if re.search(r"\|\s*P[0-3]\s*\|\s*日常", line):
            return True
    # L0 §14.5 procurement schedule
    if "实验室运行框架建设总体方案" in rel:
        if re.match(r"^\|\s*P[0-3]\s*\|", line.strip()) and "W" in line:
            return True
    # Research directions priority table in L0 §17
    if "实验室运行框架建设总体方案" in rel and re.match(r"^\|\s*P[0-4]\s*\|", line.strip()):
        if any(k in line for k in ("S1", "S2", "S3", "S4", "S5", "跨形态", "人形", "Franka")):
            return True
    return False


def scan_file(path: Path) -> list[tuple[int, str]]:
    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    if rel.startswith("docs/research/"):
        return []
    violations = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not ROLE_RE.search(line):
            continue
        if is_allowed_line(line, rel):
            continue
        violations.append((i, line.strip()))
    return violations


def main() -> int:
    paths = []
    if L0.exists():
        paths.append(L0)
    paths.extend(sorted(DOCS.rglob("*.md")))

    all_violations: list[tuple[str, int, str]] = []
    for path in paths:
        for lineno, text in scan_file(path):
            rel = str(path.relative_to(ROOT)).replace("\\", "/")
            all_violations.append((rel, lineno, text))

    if not all_violations:
        print("OK: no legacy role codes P1/P2/P3 found (allowed contexts excluded).")
        return 0

    print(f"FAIL: {len(all_violations)} legacy role code occurrence(s):\n")
    for rel, lineno, text in all_violations:
        print(f"  {rel}:{lineno}: {text[:120]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
