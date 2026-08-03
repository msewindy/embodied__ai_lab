# 实验室制度与文档索引 v2

| 属性 | 内容 |
|------|------|
| **文档编号** | GOV-INDEX-01 |
| **版本** | v2.5 |
| **日期** | 2026-08-03 |
| **维护人** | R1 |
| **说明** | 仓库**唯一文档导航**；新增/废止文档须同步更新本表 |

---

## 〇、快速入口

| 我要… | 打开 |
|--------|------|
| 了解实验室建什么 | [实验室运行框架建设总体方案.md](../../实验室运行框架建设总体方案.md)（**L0**） |
| 报批预算 | [budget_approval_onepager_v1.md](../plan/budget_approval_onepager_v1.md) → [budget_v2_framework.md](../plan/budget_v2_framework.md) |
| 看排期 | [master_wbs_v1.md](../plan/master_wbs_v1.md) |
| W1 决策记录 | [plan_review_w1.md](../meeting/plan_review_w1.md) |
| 写代码/跑验证 | [lab_platform/README.md](../../lab_platform/README.md) · [INFRA-02](../infra/phase1_validation_plan_v1.md) |
| 平台×世界模型融合 | [platform_wm_fusion_plan_v0.md](../plan/platform_wm_fusion_plan_v0.md) · [external 挂载](../../external/README.md) |
| 招人 | [docs/org/jd/](./jd/) |

**状态图例：** `approved` 已生效 · `R1-approved` 负责人已确认、待现场/到岗复核 · `draft` 草案 · `superseded` 已废止

---

## 一、规划与预算（PLAN）

| 编号 | 文档 | 路径 | 状态 |
|------|------|------|------|
| L0 | 实验室运行框架建设总体方案 | `实验室运行框架建设总体方案.md` | **v1.1 approved**（2026-07-09 角色/预算统一） |
| PLAN-DOC-UNIFY-01 | **文档体系统一方案** | `docs/plan/document_unification_plan_v1.md` | v1.4 · **全部完成** |
| PLAN-WBS-01 | 16 周建设 WBS | `docs/plan/master_wbs_v1.md` | R1-approved |
| PLAN-BUDGET-02 | **框架预算 v2（工业导向）** | `docs/plan/budget_v2_framework.md` | **R1-approved · 待上级批** |
| PLAN-BUDGET-02-1P | 预算报批一页纸 | `docs/plan/budget_approval_onepager_v1.md` | R1-approved · 待上级批 |
| PLAN-BUDGET-01 | ~~预算草案 v1~~ | `docs/plan/budget_draft_v1.md` | **superseded** → 见 v2 |
| PLAN-FUSION-01 | **平台 × 世界模型控制运行时融合规划** | `docs/plan/platform_wm_fusion_plan_v0.md` | **v0.3 working-baseline** · 双模式 ROS2 |
| — | 世界模型资料（本地 Junction，不进 Git） | `external/world_model/` ← 见 `external/README.md` | 本机挂载 · **禁止 Submodule** |

---

## 二、管理与流程制度（GOV）

| 编号 | 制度/规范 | 路径 | 状态 |
|------|-----------|------|------|
| GOV-INDEX-01 | 本索引 | `docs/org/governance_index_v1.md` | v2.0 |
| GOV-01 | RACI 职责矩阵 | `docs/org/raci_v1.md` | **v1.1 approved** |
| GOV-04 | 实验流程规范 | `docs/process/experiment_workflow_v1.md` | **v1.1 R1-approved** |
| GOV-05 | 变更控制规范 | `docs/process/change_control_v1.md` | **v1.1 R1-approved** |
| GOV-06 | 例会机制 | `docs/process/meeting_policy_v1.md` | **v1.1 R1-approved** |
| GOV-07 | 文档管理规范 | `docs/process/document_management_v1.md` | **v1.1 R1-approved** |
| MTG-W1 | W1 方案评审纪要 | `docs/meeting/plan_review_w1.md` | R1-signed · 2026-07-09 |

---

## 三、技术架构（TECH / INFRA）

| 编号 | 规范 | 路径 | 状态 |
|------|------|------|------|
| TECH-01 | 系统整体架构设计 | `docs/architecture/blueprint_v0.md` | **v1.1 R1-approved** |
| TECH-02 | 统一消息接口 (ROS2) | `docs/software/ros2_interface_v1.md` | **v1.3** · DOMAIN 42/43 · CTRL-SIM |
| TECH-03 | 算力与网络规划 | `docs/infra/infra_plan_draft_v0.md` | R1-approved |
| TECH-04 | 软件版本矩阵 | `docs/software/version_matrix_v1.md` | **v1.3** · 双模式 · DOMAIN 钉扎 |
| TECH-05 | run_id 规范 | `docs/data/run_id_spec.md` | v1.1 |
| TECH-06 | 平台软件架构（功能拓扑） | `docs/architecture/platform_architecture_v1.md` | v1.1 |
| TECH-07 | 设备清单与外设调研 | `docs/device/embodied_hardware_survey_v1.md` | **v1.1 R1-approved** · Pilot 池选型 |
| TECH-08 | 平台详细设计（功能） | `docs/architecture/platform_detailed_design_v1.md` | **v1.1** |
| TECH-09 | 平台详细技术架构 | `docs/architecture/platform_technical_architecture_v1.md` | **v1.2** · ws-02 双模式 |
| TECH-10 | PreFlight 门禁 | `docs/software/preflight_checklist_spec.md` | v1.1 |
| TECH-11 | 设备能力矩阵 | `docs/device/device_capability_matrix_v1.md` | v1.1 |
| TECH-12 | Policy 注册规范 | `docs/data/policy_registry_spec.md` | v1.1 |
| TECH-13 | Isaac Job 适配器 | `docs/software/isaac_job_adapter_v1.md` | v1.1 |
| TECH-14 | 平台 As-Built | `docs/architecture/platform_architecture_as_built_v1.md` | **v1.1** · 评审待签字 |
| INFRA-01 | 环境安装清单 | `docs/infra/env_setup_checklist_v1.md` | v1.1 |
| INFRA-02 | Phase 1 验证方案 | `docs/infra/phase1_validation_plan_v1.md` | **v1.3** · CTRL-SIM + M2–M6 详设 |
| LAYOUT-01 | 场地布局草案 | `docs/layout/layout_draft_v0.md` | draft · **待实测 v1** |
| LAYOUT-02 | **弱电与配电连接设计** | `docs/layout/electrical_design_v1.md` | **v1.0-draft** · 支撑 BOM §2.1/§2.2 |

---

## 四、模块详细设计（MDD · R2）

| 编号 | 模块 MDD | 路径 | 状态 |
|------|----------|------|------|
| MDD-01 | MDD 索引 | `docs/modules/README.md` | v1.1 |
| MDD-02 | F7 IndexService | `docs/modules/F7_index_service_mdd_v1.md` | draft |
| MDD-03 | F7 RunManager | `docs/modules/F7_run_manager_mdd_v1.md` | draft |
| MDD-04 | Isaac Job Adapter | `docs/modules/isaac_job_adapter_mdd_v1.md` | draft |
| MDD-05 | Pipeline C 运维 | `docs/modules/pipeline_c_ops_mdd_v1.md` | draft |
| MDD-06 | Real 栈 F5/F6 | `docs/modules/F6_real_stack_mdd_v1.md` | skeleton |
| — | Walking Skeleton 设计 | `docs/modules/framework_skeleton_design_v1.md` | v1.0 |

---

## 五、安全与资产（SFT / AST）

| 编号 | 规范 | 路径 | 状态 |
|------|------|------|------|
| SFT-01 | 安全操作规程 | `docs/safety/safety_sop_v1.md` | **v1.1 R1-approved** · 待 R3 现场复核 |
| SFT-02 | 急停电气逻辑 | `docs/safety/estop_wiring_v1.md` | **v1.1** · R3 · 施工前冻结 |
| AST-01 | 点检与维护制度 | `docs/device/maintenance_policy_v1.md` | **v1.1 R1-approved** |

---

## 六、评审记录

| 文档 | 路径 | 结论 |
|------|------|------|
| TECH-09 架构短评审 | `docs/meeting/tech09_review_v1.md` | 通过 2026-06-10 |
| TECH-14 As-Built 评审 | `docs/meeting/tech14_review_v1.md` | 自动化通过 2026-06-11 · **待 R1 补签** |
| TECH-02 ROS2 接口评审 | `docs/meeting/tech02_review_v1.md` | 有条件通过 2026-06-11 · **待 R1 补签** |
| W1 方案评审 | `docs/meeting/plan_review_w1.md` | R1 确认 2026-07-09 |

---

## 七、人力资源（ORG）

| 文档 | 路径 | 说明 |
|------|------|------|
| R1 实验室负责人 JD | `docs/org/jd/jd-实验室负责人.txt` | |
| R2 平台工程师 JD | `docs/org/jd/jd-平台与基础设施工程师.txt` | Batch-1 |
| R3 现场安全 JD | `docs/org/jd/jd-现场、资产与安全工程师.txt` | Batch-1 |
| R4 应用工程师 JD | `docs/org/jd/jd-机器人应用控制工程师.txt` | Batch-2 |
| R5 算法研究员 JD | `docs/org/jd/jd-具身智能算法研究员.txt` | 按需 |

**编制：** 标准 4 人（R1–R4）；R5 框架 Go 后按需。

---

## 八、研究与参考（非建设依据）

| 目录 | 说明 |
|------|------|
| `docs/research/humanoid_mani_v_july_blogs/` | 技术调研与论文笔记；**不驱动框架期采购** |

---

## 九、已废止 / 已移除（勿引用）

| 原文件 | 处置 | 替代 |
|--------|------|------|
| `方案.txt` | 2026-07-09 删除 | L0 总体方案 |
| `方案_三人团队详细版.md` | 2026-07-09 删除 | L0 + PLAN-BUDGET-02 + 4 人编制 JD |
| `docs/plan/budget_draft_v1.md` | 保留只读，标 superseded | PLAN-BUDGET-02 |

---

## 十、变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.1 | 2026-06 | 初版索引 |
| **v2.4** | **2026-07-09** | 文档体系统一 Batch 1–4 全部完成 |
| **v2.3** | **2026-07-09** | Batch 3 文档统一（TECH-08/09/14、MDD、software/data/device） |
| **v2.2** | **2026-07-09** | Batch 2 文档统一（INFRA、TECH-05/06、评审纪要 R1–R3） |
| **v2.1** | **2026-07-09** | Batch 1 文档统一（R1–R5、L0 v1.1、GOV v1.1） |

---

*GOV-INDEX-01 v2.0 | 文档唯一导航*
