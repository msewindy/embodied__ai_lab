# docs/ 怎么读（不要按文件夹从头读）

**目的圣经：** [PLAN-CHARTER-01 实验室平台宪章](plan/lab_charter_v0.md)  
**全量目录：** [governance_index_v1.md](org/governance_index_v1.md)（索引，不是入门教材）

`docs/` 里同时有建设总纲、CTRL-SIM 现状、Walking Skeleton 历史、开源笔记。**混乱来自把它们当成同一效力。** 按下面四层读；冲突时上层覆盖下层。

---

## 效力分层

```text
① 宪章 CHARTER     目的、架构史、时空上下文、三层边界
② 结构 STRUCT      落点、契约、模块展开
③ 进度 INFRA-02    现在做到哪（看板 SSOT）
④ 操作 SOP/As-Built 怎么跑、代码实际如何
── 以下默认不指导当前开发 ──
⑤ 历史融合/早期 TECH/MDD   与 ①–③ 冲突则该段作废
⑥ research/               调研，永不驱动采购或推翻宪章
```

---

## 日常只打开这些

| 我要… | 打开 | 不要打开 |
|--------|------|----------|
| 判断功能偏没偏（有没有做成无上下文的学习壳 / 第二套 Lab OS） | [宪章](plan/lab_charter_v0.md) **v1.1** | 开源笔记、早期蓝图 |
| 看 L0/L1/L2 落点 | [STRUCT](plan/lab_strategy_runtime_structure_v0.md) | FUSION 里的旧 L1 框图（已划回 L2-Low） |
| 看 Phase-1 是否完成 | [INFRA-02 §1](infra/phase1_validation_plan_v1.md) | WBS / 总体方案里的 16 周表 |
| 跑仿真 | [SOP](infra/sop_franka_ctrl_sim_v0.md) · [E2E](infra/sop_franka_ctrl_sim_e2e_validation_v0.md) | MDD |
| 看代码已实现什么 | [TECH-14 As-Built](architecture/platform_architecture_as_built_v1.md) | TECH-06/08 功能详设（骨架期） |
| L1 下一步（Design 输入） | [RES-L1-REQ-01](research/l1_framework_requirements_v0.md) | [PLAN-SR-B](plan/strategy_runtime_b_vision_act_plan_v0.md)（暂停，服从宪章/REQ） |
| 真机 | [PHASE2](infra/phase2_franka_real_e2e_plan_v0.md)（**暂缓**） | — |

**当前状态（2026-08-14）：** Phase-1 仿真 E2E PASS；宪章 **v1.1** 把灵魂钉在 L1 时空上下文（WM-B 先于 WM-A）；并环=单一 `ctrl-sim run`；LeRobot=算法库+B 轨。**下一步是 L1 Framework Design**，不先拆包、不上 ACT。

---

## 文件夹实际装的是什么

| 目录 | 角色 | 读法 |
|------|------|------|
| [plan/](plan/) | 宪章、STRUCT、FUSION、预算/WBS、暂停中的 B 方案 | **先宪章再 STRUCT**；FUSION 只查双模式/融合边界 |
| [infra/](infra/) | 进度看板、SOP、环境、真机计划 | 进度只信 INFRA-02 |
| [architecture/](architecture/) | 蓝图 + **As-Built** | 现状以 As-Built 为准；blueprint / detailed_design 为骨架期 |
| [software/](software/) [data/](data/) | ROS 接口、版本、PreFlight、run_id、A→B 映射 | 现行契约 |
| [org/](org/) [process/](process/) [meeting/](meeting/) | 制度、RACI、评审纪要 | 治理，不写控制环 |
| [device/](device/) [layout/](layout/) [safety/](safety/) | 设备、场地、安全 | 现场 |
| [modules/](modules/) | Walking Skeleton MDD | **历史**；与 STRUCT/INFRA 冲突以后者为准 |
| [research/](research/) | 开源笔记、论文、L1 需求推导 | [research/README](research/README.md)；**非建设依据**（需求文除外：只作 Design 输入） |

物理路径暂不搬家（避免打断引用）。整理方式是 **效力分层 + 本页阅读图**，不是再复制一份目录。

**口径检查：** `python scripts/check_doc_role_codes.py`

---

*docs/README · 阅读图 · 2026-08-14*