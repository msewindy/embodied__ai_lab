# 文档体系统一方案 v1

| 属性 | 内容 |
|------|------|
| **文档编号** | PLAN-DOC-UNIFY-01 |
| **版本** | v1.4 |
| **日期** | 2026-07-09 |
| **维护人** | R1 |
| **状态** | **已完成**（Batch 1–4） |

---

## 一、统一目标

将仓库内 **建设/制度/技术/运维** 文档对齐至 **2026-07-09 W1 冻结决策**（见 [plan_review_w1.md](../meeting/plan_review_w1.md)），消除多版本口径并存导致的执行混乱。

**不在本次统一范围内：**

- `docs/research/` — 论文/博客调研；其中的「P1/P2」多为论文术语（如第三人称视角），**不修改**
- `lab_platform/`、`ros2/` 代码 — 仅文档引用路径对齐，不改代码逻辑
- 已废止的 `budget_draft_v1.md` — 保留 superseded 标记，不删正文

---

## 二、权威基线（Single Source of Truth）

| 维度 | 权威文档 | 冻结值 |
|------|----------|--------|
| **建设总纲** | `实验室运行框架建设总体方案.md` | 16 周框架 Go；工业 Pilot 后挂 |
| **文档导航** | `docs/org/governance_index_v1.md` | 唯一索引 |
| **角色/RACI** | `docs/org/raci_v1.md` | **R1–R5**（R1–R4 标准编制） |
| **预算** | `docs/plan/budget_v2_framework.md` | 框架 CAPEX **¥10 万**；Pilot 池单列 |
| **WBS** | `docs/plan/master_wbs_v1.md` | 16 周 A→E |
| **软件基线** | `docs/software/version_matrix_v1.md` | Ubuntu **24.04** + ROS2 **Jazzy** + Isaac 6.0 |
| **代码仓库** | `lab_platform/` + `ros2/` | 非 `embodied_lab/` |
| **设备清单** | `docs/device/embodied_hardware_survey_v1.md` | TECH-07 |
| **W1 决策** | `docs/meeting/plan_review_w1.md` | 2026-07-09 |

### 2.1 角色代号对照（全文统一规则）

| 旧代号 | 新代号 | 角色 |
|--------|--------|------|
| P1 / 规划负责人 | **R1** | 实验室负责人 |
| P2 / 平台负责人 | **R2** | 平台与基础设施工程师 |
| P3 / 现场负责人 | **R3** | 现场、资产与安全工程师 |
| （无） | **R4** | 机器人应用/控制工程师（标准编制） |
| （无） | **R5** | 算法研究员（按需） |

**注意：** 采购优先级 **P0/P1/P2**、事故等级 **L1/L2/L3**、Bridge 级别 **L0–L4** **不得**替换。

---

## 三、不一致项扫描（2026-07-09）

| 类别 | 影响文件数（约） | 典型问题 |
|------|:----------------:|----------|
| A. 角色代号 P1/P2/P3 | ~35 | 维护人、主责、RACI 表 |
| B. 团队编制「三人」 | ~15 | 与 4 人标准编制冲突 |
| C. 软件基线 Humble/22.04 | ~5 | 与 version_matrix / 已实施环境冲突 |
| D. 预算 v1 / 14.85 万 | ~3 | 已 superseded，需交叉引用 v2 |
| E. 路径 `embodied_lab/` | ~5 | 应为 lab_platform + ros2 |
| F. 路径 `docs/assets/` | ~3 | 应为 docs/device/ |
| G. 评审纪要待签字 | 3 | tech02/tech14 + plan_review |

**排除：** `docs/research/**` 约 10 个文件（误匹配，不处理）

---

## 四、分批执行计划

### Batch 1 — 规划与制度（最高优先级）✅ 本批执行

| 文件 | 统一项 |
|------|--------|
| `实验室运行框架建设总体方案.md` | 角色、编制、软件基线、仓库路径、预算、W1 状态 |
| `docs/process/experiment_workflow_v1.md` | R1/R3；升 v1.1 |
| `docs/process/change_control_v1.md` | 审批矩阵 → R1–R5 |
| `docs/process/meeting_policy_v1.md` | 主持/参与 → R1 |
| `docs/process/document_management_v1.md` | 维护人、路径、仓库名 |
| `docs/safety/safety_sop_v1.md` | 维护人 R3；访客 R3 |
| `docs/device/maintenance_policy_v1.md` | R3/R1 |
| `docs/layout/layout_draft_v0.md` | 维护人、下一步 R3 |
| `docs/device/embodied_hardware_survey_v1.md` | 维护人字段 |
| `docs/architecture/blueprint_v0.md` | L3 软件层 Jazzy；维护人 |

**Batch 1 完成标志：** L0 + GOV 流程/安全/场地 无 P1/P2/P3（角色义）。

---

### Batch 2 — 基础设施与验证 ✅ 本批完成

| 文件 | 统一项 |
|------|--------|
| `docs/infra/phase1_validation_plan_v1.md` | 维护人 R2；负责人表 R1–R3；升 v1.1 |
| `docs/infra/env_setup_checklist_v1.md` | 角色引用；验收签字表；升 v1.1 |
| `docs/infra/infra_plan_draft_v0.md` | R1/R2；预算引用 |
| `docs/software/ros2_interface_v1.md` | 维护人 R2 |
| `docs/architecture/platform_architecture_v1.md` | **22.04/Humble → 24.04/Jazzy**；升 v1.1 |
| `docs/meeting/tech02_review_v1.md` | 签字栏 R1/R2/R3 |
| `docs/meeting/tech09_review_v1.md` | 同上 |
| `docs/meeting/tech14_review_v1.md` | 同上 |

**Batch 2 完成标志：** INFRA + TECH-05 无角色义 P1/P2/P3；platform_architecture 软件基线对齐 version_matrix。

---

### Batch 3 — 架构与 MDD ✅ 本批完成

| 文件 | 统一项 |
|------|--------|
| `docs/architecture/platform_technical_architecture_v1.md` | R1–R3；实施路线阶段命名；升 v1.1 |
| `docs/architecture/platform_detailed_design_v1.md` | R1/R2；升 v1.1 |
| `docs/architecture/platform_architecture_as_built_v1.md` | Gap 负责人 R2/R3；签字栏；升 v1.1 |
| `docs/modules/*.md`（7 份） | 维护人、分工表 R1–R3 |
| `docs/software/*.md`（除 ros2_interface） | 维护人 R2 |
| `docs/data/*.md` | 维护人 R2 |
| `docs/device/device_capability_matrix_v1.md` | R2/R3 |
| `docs/safety/estop_wiring_v1.md` | 依据链接；升 v1.1 |

**Batch 3 完成标志：** TECH-08/09/14 + MDD + 规范层无角色义 P1/P2/P3（Gap 优先级列除外）。

---

### Batch 4 — 收尾与自动化 ✅ 本批完成

| 任务 | 说明 | 结果 |
|------|------|------|
| 全库 grep 验收 | `scripts/check_doc_role_codes.py` | ✅ 2026-07-09 通过 |
| L0 变更记录 | `实验室运行框架建设总体方案.md` v1.1 | ✅ 已补 §变更记录；修正研究方向优先级表 |
| `budget_draft_v1` | 废止文档头字段 | ✅ 维护人/审批人标注 R1–R3 + 历史说明 |
| CI 脚本 | `scripts/check_doc_role_codes.py` | ✅ 可纳入 pre-commit / CI |

**Batch 4 完成标志：** 验收脚本 exit 0；除 `research/`、`budget_draft` 正文、`document_unification` 对照表外，无角色义 P1/P2/P3。

---

## 五、各文档头字段统一模板

```markdown
| **维护人** | R2 |          # 单主责用 R*
| **维护人** | R1（制度）/ R2（技术） |   # 双主责
| **版本** | v1.1 |
| **依据** | [governance_index_v1.md](../org/governance_index_v1.md) · [plan_review_w1.md](../meeting/plan_review_w1.md) |
```

**状态用词：**

- `draft` → 未经 R1 确认
- `R1-approved` → R1 已确认，待现场/到岗复核
- `approved` / `v1.0` → 已生效
- `superseded` → 已废止，指向新文档

---

## 六、进度跟踪

| Batch | 范围 | 状态 | 完成日 |
|:-----:|------|:----:|--------|
| **1** | L0 + GOV/SFT/LAYOUT/TECH-01/07 | ✅ 完成 | 2026-07-09 |
| **2** | INFRA + platform_architecture + meeting | ✅ 完成 | 2026-07-09 |
| **3** | TECH-09/14 + MDD + data/software/device | ✅ 完成 | 2026-07-09 |
| **4** | 验收 grep + 版本升号 | ✅ 完成 | 2026-07-09 |

---

## 七、变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-07-09 | 初版；启动 Batch 1 |
| v1.1 | 2026-07-09 | Batch 1 完成 |
| v1.2 | 2026-07-09 | Batch 2 完成 |
| v1.3 | 2026-07-09 | Batch 3 完成 |
| v1.4 | 2026-07-09 | Batch 4 完成；验收脚本 `check_doc_role_codes.py` |

---

*PLAN-DOC-UNIFY-01 | 文档体系统一方案*
