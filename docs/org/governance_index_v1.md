# 实验室制度包目录 v1

| 属性 | 内容 |
|------|------|
| **文档编号** | GOV-INDEX-01 |
| **版本** | v1.1 |
| **维护人** | P1 |

---

## 一、管理与流程制度 (P1 统筹)

| 编号 | 制度/规范 | 路径 | 状态 |
|------|-----------|------|------|
| GOV-01 | RACI 职责矩阵 | `docs/org/raci_v1.md` | draft |
| GOV-04 | 实验流程规范 | `docs/process/experiment_workflow_v1.md` | draft |
| GOV-05 | 变更控制规范 | `docs/process/change_control_v1.md` | draft |

## 二、技术与架构规范 (P1/P2 负责)

| 编号 | 规范 | 路径 | 状态 |
|------|------|------|------|
| TECH-01 | 系统整体架构设计 | `docs/architecture/blueprint_v0.md` | draft |
| TECH-02 | 统一消息接口 (ROS2) | `docs/software/ros2_interface_v1.md` | **v1.0** |
| TECH-03 | 算力与网络规划 | `docs/infra/infra_plan_draft_v0.md` | draft |
| INFRA-01 | 环境安装与验收清单 | `docs/infra/env_setup_checklist_v1.md` | **v1.0** |
| INFRA-02 | Phase 1 验证测试方案 | `docs/infra/phase1_validation_plan_v1.md` | **v1.0** |
| TECH-04 | 软件版本矩阵 | `docs/software/version_matrix_v1.md` | draft |
| TECH-05 | 数据与实验记录规范 | `docs/data/run_id_spec.md` | **v1.0** |
| TECH-06 | 平台软件架构与部署拓扑图 | `docs/architecture/platform_architecture_v1.md` | draft |
| TECH-07 | 具身智能核心硬件与外设调研 | `docs/device/embodied_hardware_survey_v1.md` | draft |
| TECH-08 | 具身智能平台软件架构详细设计（功能架构） | `docs/architecture/platform_detailed_design_v1.md` | draft |
| TECH-09 | 具身智能平台详细技术架构 | `docs/architecture/platform_technical_architecture_v1.md` | **v1.0-approved** |
| TECH-14 | 平台架构 As-Built（Walking Skeleton 评审） | `docs/architecture/platform_architecture_as_built_v1.md` | **v1.0** |
| TECH-10 | PreFlight 启动门禁规范 | `docs/software/preflight_checklist_spec.md` | **v1.0** |
| TECH-11 | 设备能力矩阵与 Bridge 成熟度 | `docs/device/device_capability_matrix_v1.md` | **v1.0** |
| TECH-12 | PolicyArtifact 与策略注册规范 | `docs/data/policy_registry_spec.md` | **v1.0** |
| TECH-13 | Isaac Job 薄封装适配器规范 | `docs/software/isaac_job_adapter_v1.md` | **v1.0** |

## 三、模块详细设计 (P2)

| 编号 | 模块 MDD | 路径 | 状态 |
|------|----------|------|------|
| MDD-01 | MDD 索引与开发顺序 | `docs/modules/README.md` | v1.0 |
| MDD-02 | F7 IndexService | `docs/modules/F7_index_service_mdd_v1.md` | draft |
| MDD-03 | F7 RunManager | `docs/modules/F7_run_manager_mdd_v1.md` | draft |
| MDD-04 | Isaac Job Adapter | `docs/modules/isaac_job_adapter_mdd_v1.md` | draft |
| MDD-05 | Pipeline C 运维 | `docs/modules/pipeline_c_ops_mdd_v1.md` | draft |
| MDD-06 | Real 栈 F5/F6 | `docs/modules/F6_real_stack_mdd_v1.md` | skeleton |

## 四、评审记录

| 文档 | 路径 | 结论 |
|------|------|------|
| TECH-09 架构短评审 | `docs/meeting/tech09_review_v1.md` | 通过 2026-06-10 |
| TECH-14 As-Built 评审 | `docs/meeting/tech14_review_v1.md` | 自动化验收通过 2026-06-11 · **待签字** |
| TECH-02 ROS2 接口短评审 | `docs/meeting/tech02_review_v1.md` | 有条件通过 2026-06-11 · **待签字** |

## 五、安全与资产规范 (P3 负责)

| 编号 | 规范 | 路径 | 状态 |
|------|------|------|------|
| SFT-01 | 实验室安全操作规程 (SOP) | `docs/safety/safety_sop_v1.md` | draft |
| SFT-02 | 软硬安全接口电气逻辑图 | `docs/safety/estop_wiring_v1.md` | draft |
| AST-01 | 资产台账与维护制度 | `docs/device/maintenance_policy_v1.md` | draft |
