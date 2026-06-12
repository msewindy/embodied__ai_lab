# PreFlight 启动门禁规范 v1.0

| 属性 | 内容 |
|------|------|
| **文档编号** | TECH-10 |
| **版本** | v1.0 |
| **维护人** | P2 |
| **依据** | TECH-09 v1.0-approved §8.2–§8.5 |

---

## 一、 定位

PreFlightGate 是 Run 启动前的**统一校验模块**，嵌入 `RunManager` 与 `lab isaac run`，**不是独立 Run**。

**输出**：
- 通过 → 写入 `metadata.preflight_checklist[]` 与 `preflight_passed_at`
- 失败 → 拒绝启动，写 audit 日志，不分配 resource_lock

---

## 二、 检查项清单

每项检查结果：`pass` | `fail` | `skip` | `warn`（warn 仅 Pipeline A 或非阻塞项）

| ID | 检查项 | Pipeline | 数据源 | 失败动作 |
|----|--------|----------|--------|----------|
| PF-01 | `check_env` 版本一致 | A, B, C | `version_matrix_v1.md` + 本机探测 | fail |
| PF-02 | 设备 `status != blocked` | B, C | `maintenance_policy` 台账 / IndexService | fail |
| PF-03 | Bridge 成熟度 ≥ 要求 | B, C | `registry/bridge_maturity.yaml` | fail |
| PF-04 | 标定未过期 | B (deploy/eval) | CalibrationRegistry | fail；collect 视觉任务 fail |
| PF-05 | `scene_id` 已登记 | B (eval) | SceneRegistry | fail |
| PF-06 | `eval_protocol_id` 存在 | B (eval) | `registry/eval_protocols/` | fail |
| PF-07 | ResourceScheduler 可获取锁 | B | resource_locks 表 | fail 或 queue |
| PF-08 | GPU 锁可获取 | A (train) | gpu_lock | fail 或 queue |
| PF-09 | `experiment_plan_id` 有效 | B | experiment_workflow | fail |
| PF-10 | risk 审批完成 | B (medium/high) | 实验计划 metadata | fail |
| PF-11 | SOP 二人规则确认 | B (动态区) | 实验计划 metadata | fail |
| PF-12 | Policy↔Device 兼容 | B (deploy/eval) | CompatibilityCheck | fail |
| PF-13 | Policy lifecycle 允许 | B (deploy) | PolicyRegistry | fail |
| PF-14 | 磁盘空间 ≥ 阈值 | A, B | LabOpsMonitor | fail (<20% 剩余) |
| PF-15 | 上游 Artifact 存在且可读 | A, B | ArtifactRegistry | fail |

---

## 三、 各 Run 类型最小检查集

| Run 类型 | 必跑检查项 |
|----------|------------|
| `isaac_job` play | PF-01, PF-15 |
| `isaac_job` train | PF-01, PF-08, PF-14, PF-15（IL 时） |
| `isaac_job` eval | PF-01, PF-15 |
| `real_bringup` | PF-01, PF-02 |
| `calibration_session` | PF-01, PF-02, PF-03(L≥L1) |
| `real_collect` | PF-01–03(L≥L2), PF-07, PF-09–11, PF-04(视觉任务) |
| `real_deploy` | PF-01–04,07,09–13 |
| `real_eval` | PF-01–07,09–13 + PF-05, PF-06 |

---

## 四、 Bridge 成熟度门槛

| Run 类型 | 最低 Bridge 级别 |
|----------|------------------|
| `real_bringup` | L0（新设备登记后首次） |
| `calibration_session` | L1 |
| `real_collect` | L2 |
| `real_deploy` | L3 |
| `real_eval` | L4 |

---

## 五、 preflight_checklist 记录格式

```json
{
  "preflight_passed_at": "2026-06-10T15:59:30+08:00",
  "preflight_checklist": [
    {"id": "PF-01", "result": "pass", "detail": "ubuntu=24.04 ros2=jazzy"},
    {"id": "PF-03", "result": "pass", "detail": "bridge_level=L3"},
    {"id": "PF-07", "result": "pass", "detail": "device_lock acquired"},
    {"id": "PF-12", "result": "pass", "detail": "policy task_domain=locomotion matches device"}
  ]
}
```

---

## 六、 CompatibilityCheck 规则（deploy/eval）

1. `policy_manifest.task_domain` ∈ `device_capabilities.task_domains`
2. `policy_manifest.supported_devices` 包含目标 `device_id`（或 `*` 实验室通用）
3. `policy_manifest.observation_schema` 所需传感器 ⊆ device 已标定且未过期类型
4. `policy_manifest.onboard_runtime` 与 onboard 算力等级兼容
5. force_control 任务 → `device_capabilities.has_force_control == true`

失败时返回可读错误，例如：`PF-12: policy requires hand_eye calibration, valid calibration missing`。

---

## 七、 与 ResourceScheduler 交互

```
PreFlight 开始
  → PF-07/PF-08 尝试 acquire lock（TTL = run 预估时长 + 30min）
  → 任一 fail → 不创建 Run 目录
PreFlight 通过 → Run 创建
Run finish / fail / interrupt → release all locks
Run 超时无心跳 → TTL 自动 release
```

---

## 八、 API（RunManager 内部）

```python
class PreFlightGate:
    def check(self, run_request: RunRequest) -> PreFlightResult:
        """返回 passed: bool, checklist: list, block_reason: str|None"""

class RunRequest:
    run_type: str
    device_ids: list[str]
    job_kind: str | None          # isaac only
    upstream_artifact_ids: list[str]
    experiment_plan_id: str | None
    scene_id: str | None
    eval_protocol_id: str | None
    policy_id: str | None
```

---

*TECH-10 | preflight_checklist_spec v1.0*
