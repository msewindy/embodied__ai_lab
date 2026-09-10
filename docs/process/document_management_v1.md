# 文档管理规范 v1

| 属性 | 内容 |
|------|------|
| **文档编号** | GOV-07 |
| **版本** | v1.3 |
| **维护人** | R1 |

---

## 一、文档分层与归属

| 层级 | 目录 | 内容 | 维护方 |
|------|------|------|--------|
| **圣经** | `docs/plan/lab_charter_v0.md` | 目的、架构史、时空上下文、三层边界（PLAN-CHARTER-01 v1.1）；冲突时最高 | R1 |
| **L0 建设** | 根目录总体方案 | 建设期 16 周/预算（不替代宪章） | R1 |
| **结构** | `docs/plan/lab_strategy_runtime_structure_v0.md` | L0×L1×L2 落点 | R1 |
| **进度** | `docs/infra/phase1_validation_plan_v1.md` | 看板 SSOT | R1/R2 |
| **架构现状** | `docs/architecture/` As-Built | 已实现；早期 blueprint 为 historical | R1/R2 |
| **制度** | `docs/org/` `docs/process/` | 索引、RACI、流程 | R1 |
| **契约/SOP** | `docs/software/` `docs/data/` `docs/infra/` | 接口、数据、操作 | R2 |
| **现场** | `docs/layout/` `docs/safety/` `docs/device/` | 场地、安全、设备 | R3 |
| **调研** | `docs/research/` | 非建设依据 | R5/R1 |

**入门：** [docs/README](../README.md)（效力分层）。**目录：** [GOV-INDEX](../org/governance_index_v1.md)。

**效力：** 宪章 > STRUCT > INFRA-02 > As-Built/SOP > FUSION/早期 TECH/MDD。`research/` 不得推翻宪章。

## 二、版本控制原则
- 所有文档必须存放在 Git 仓库中（待 R2 初始化 monorepo）。
- 纲领性文件（如总体方案、架构蓝图）升版必须走 CR 流程。
