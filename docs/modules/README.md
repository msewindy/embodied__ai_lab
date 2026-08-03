# 模块详细设计 (MDD) 索引

| 属性 | 内容 |
|------|------|
| **版本** | v1.1 |
| **维护人** | R2 |
| **依据** | [governance_index_v1.md](../org/governance_index_v1.md) · [plan_review_w1.md](../meeting/plan_review_w1.md) |
| **架构基线** | TECH-09 v1.1 |

---

## 开发顺序

```
TECH-09 approved + P0 规范
  → ⓪ Walking Skeleton（lab_platform 包，接口 + Stub）  ← 当前
  → ① F7 IndexService（已内嵌 SQLite 真实实现）
  → ② F7 RunManager (+ PreFlight + Scheduler)
  → ③ Isaac Job Adapter（替换 StubIsaacLauncher）
  → ④ Pipeline C（替换 StubRealRuntime.bringup/calibrate）
  → ⑤ Real 栈 (F5/F6) + ros2_interface_v1
```

**Walking Skeleton 代码**：`lab_platform/` · 设计 `framework_skeleton_design_v1.md`

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
