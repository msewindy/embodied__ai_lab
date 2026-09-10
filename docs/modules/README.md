# 模块详细设计 (MDD) 索引

| 属性 | 内容 |
|------|------|
| **版本** | v1.2 |
| **日期** | 2026-08-07 |
| **维护人** | R2 |
| **依据** | [governance_index](../org/governance_index_v1.md) · [PLAN-STRUCT-01](../plan/lab_strategy_runtime_structure_v0.md) |
| **架构基线** | TECH-09 · **若冲突以 STRUCT / INFRA / TECH-14 As-Built 为准** |

> **注意：** Phase-1 主路径已是 **CTRL-SIM + Task Pack + 双轨 + ArtifactHub**（见 [TECH-14 v1.2](../architecture/platform_architecture_as_built_v1.md)）。下列 MDD 仍描述 Walking Skeleton / Pipeline A–C 目标拆分，**不覆盖** CTRL-SIM 实现细节。

---

## 开发顺序（历史骨架 → 当前）

```
TECH-09 + P0 规范
  → ⓪ Walking Skeleton（接口 + Stub）           ✅
  → ① F7 IndexService / RunManager               ✅
  → ①b CTRL-SIM + franka_sim_bridge + Task Pack ✅  ← 当前主路径（非 MDD 原文范围）
  → ③ Isaac Job Adapter（BATCH / 真 train）       后置
  → ④ Pipeline C 真机 bringup/calibrate           后置
  → ⑤ Real 栈 (F5/F6) DOMAIN 42                   后置
```

**代码**：`lab_platform/` · `ros2/` · `tasks/` · 骨架设计 `framework_skeleton_design_v1.md`

```bash
cd lab_platform && pip install -e .
lab init
lab demo full
lab test concurrency
```

## 文档清单

| 顺序 | 模块 | 文档 | 状态 |
|:----:|------|------|------|
| 1 | F7 IndexService | [F7_index_service_mdd_v1.md](./F7_index_service_mdd_v1.md) | draft |
| 2 | F7 RunManager | [F7_run_manager_mdd_v1.md](./F7_run_manager_mdd_v1.md) | draft |
| 3 | Isaac Adapter | [isaac_job_adapter_mdd_v1.md](./isaac_job_adapter_mdd_v1.md) | draft |
| 4 | Pipeline C | [pipeline_c_ops_mdd_v1.md](./pipeline_c_ops_mdd_v1.md) | draft |
| 5 | Real 栈 F5/F6 | [F6_real_stack_mdd_v1.md](./F6_real_stack_mdd_v1.md) | skeleton |

## P0 规范（字段级输入）

| 规范 | 路径 |
|------|------|
| Run & Artifact | `docs/data/run_id_spec.md` |
| PreFlight | `docs/software/preflight_checklist_spec.md` |
| Device / Bridge | `docs/device/device_capability_matrix_v1.md` |
| Policy Registry | `docs/data/policy_registry_spec.md` |
| Isaac Adapter | `docs/software/isaac_job_adapter_v1.md` |

## 待 R1

- `docs/software/ros2_interface_v1.md` 重写
- `eval_protocol` YAML（`data/registry/eval_protocols/`）
