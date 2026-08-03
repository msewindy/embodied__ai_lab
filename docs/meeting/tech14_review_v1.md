# TECH-14 As-Built 架构评审记录 v1

| 属性 | 内容 |
|------|------|
| **日期** | 2026-06-11 |
| **文档** | TECH-14 `platform_architecture_as_built_v1.md` |
| **演示环境** | Windows · Python 3.11 · `lab_platform/` |
| **自动化验收** | **通过** |
| **正式决议** | 待 R1/R2/R3 签字确认 Phase 2 启动 |

---

## 一、 演示与测试命令

```bash
cd lab_platform
pip install -e .
python scripts/smoke_test.py    # 一键：清空 data → init → demo full → concurrency
```

或分步：

```bash
lab --data-root data init
lab --data-root data demo full
lab --data-root data test concurrency
lab --data-root data list
lab --data-root data list --artifacts
lab --data-root data lineage isaac_20260611_112524_p2_train
```

---

## 二、 测试结果摘要（2026-06-11 11:25）

### 2.1 `lab demo full` — 通过（exit 0）

| 步骤 | Pipeline | Run 类型 | 结果 |
|------|----------|----------|------|
| ① | C | real_bringup | ✅ Bridge → L1 |
| ② | — | bridge promote L2 | ✅ |
| ③ | C | calibration_session | ✅ CalibrationArtifact |
| ④ | B | real_collect | ✅ DemoArtifact |
| ⑤ | A | isaac_job train | ✅ PolicyArtifact(draft) |
| ⑥ | A | isaac_job eval | ✅ EvalArtifact(sim) + policy→**candidate** |
| ⑦ | — | bridge promote L3 | ✅ |
| ⑧ | B | real_deploy | ✅ |
| ⑨ | B | real_eval | ✅ EvalArtifact(real), success_rate=0.78 |
| ⑩ | 跨 | sim2real_gap_job | ✅ gap=14%, job_id=gap_20260611_112524_p2 |

**关键 Artifact ID（本次 run）**：

- Policy: `pol_20260611_112524_velocity_rough_go2` (candidate)
- Sim Eval: `eval_20260611_112524_sim_loco_vel_v1`
- Real Eval: `eval_20260611_112524_real_loco_vel_v1`
- Demo: `demo_20260611_112524_quadruped-01`

### 2.2 `lab test concurrency` — 通过（exit 0）

```
holding locks: quadruped-01, humanoid-01
OK: third Z-DYN deploy rejected: Z-DYN concurrent limit (2) exceeded
```

### 2.3 索引与目录 — 通过

| 指标 | 值 |
|------|-----|
| runs 表 | 7 条（7 种 Run 各 1 次） |
| artifacts 表 | 6 条 |
| run_artifact_links | 10 条 |
| resource_locks（测试后） | 0（已释放） |

**血缘抽查**（`isaac_job train`）：

```json
{
  "upstream": [{"artifact_id": "demo_20260611_112524_quadruped-01", "type": "demo"}],
  "downstream": [{"artifact_id": "pol_20260611_112524_velocity_rough_go2", "type": "policy"}]
}
```

**目录抽查**：`data/runs/`（7 类 Run 目录）、`data/artifacts/`（policy/demo/eval/calibration）、`data/jobs/sim2real_gap/gap_*/gap_report.json` 均存在。

---

## 三、 TECH-14 §九 评审清单（自动化项）

| 项 | 结论 |
|----|------|
| 三条 Pipeline + gap 可跑通 | ✅ |
| LabOps PreFlight + Scheduler 生效 | ✅ |
| Artifact 传递与 TECH-09 一致 | ✅ |
| `protocols.py` 边界未破坏 | ✅（Stub 注入） |
| Walking Skeleton 可作为 Phase-1 基线 | ✅ 建议接受 |
| 三节点 / ROS2 / Isaac 真机 | ⏸ Phase 2（已知 Gap） |

---

## 四、 已知限制（评审时声明）

1. 执行层均为 **Stub**（Isaac / ROS2 / Driver / Safety 未接入）。
2. 单机单进程，未分 ws-02 / ws-01 / onboard。
3. Rosbag 为占位 `.mcap` 文件，非真实 mcap 格式。
4. LabOpsMonitor 未实现。

---

## 五、 决议建议

| # | 建议 |
|---|------|
| 1 | **接受** TECH-14 As-Built v1.0 为 Phase-1 基线 |
| 2 | **启动 Phase 2**：ros2_interface 重写 + StubIsaacLauncher 替换 |
| 3 | 将 `python scripts/smoke_test.py` 纳入日常冒烟 |

---

## 六、 签字（正式评审时填写）

| 角色 | 姓名 | 日期 | 结论 |
|------|------|------|------|
| R1 | | | |
| R2 | | | |
| R3 | | | |

---

*tech14_review_v1 · 自动化验收 2026-06-11*
