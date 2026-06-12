# Pipeline C 运维 Run 模块详细设计 v1.0

| 属性 | 内容 |
|------|------|
| **模块** | Pipeline C · real_bringup / calibration_session |
| **版本** | v1.0-draft |
| **维护人** | P2 + P3 |
| **依据** | TECH-09 §8.7；TECH-11 Bridge 成熟度 |

---

## 一、 目标

将「上电 smoke」与「标定」纳入框架登记，产出可审计报告并**驱动 Bridge 晋升**与 CalibrationRegistry 更新。

**部署**：ws-01 + onboard ROS2；**不**跑策略训练。

---

## 二、 real_bringup

### 2.1 用途

- 新设备入库后首次验证
- 维护恢复后重新验证 L1
- 日常开机可选快速检查

### 2.2 流程

```
lab run create --type real_bringup --device franka-01
  → PreFlight: PF-01, PF-02 only
  → RunManager.start
  → BringupRunner 执行 smoke 脚本
  → 写 bringup_report.json
  → 若全 pass → bridge_maturity.level = L1
  → RunManager.finish
```

### 2.3 BringupRunner 检查项

| ID | 检查 | pass 条件 |
|----|------|-----------|
| BU-01 | ROS2 域连通 | ws-01 ping onboard 关键节点 |
| BU-02 | Driver Bridge 加载 | bridge 节点 active |
| BU-03 | joint_states 发布 | 频率 ≥ 50Hz，5s |
| BU-04 | 读 SDK 版本 | 与 vendor 元数据一致 |
| BU-05 | ESTOP 链路 | 软件 ESTOP 触发 + 恢复 |
| BU-06 | Limiter 生效 | 发送超限指令被 clip |

### 2.4 bringup_report.json

```json
{
  "run_id": "rb_20260610_090000_p3_franka-01",
  "device_id": "franka-01",
  "checks": [
    {"id": "BU-01", "result": "pass", "latency_ms": 12},
    {"id": "BU-02", "result": "pass"}
  ],
  "overall": "pass",
  "bridge_level_after": "L1"
}
```

### 2.5 组件

```text
lab_platform/pipeline_c/
├── bringup_runner.py
├── checks/              # BU-01 .. BU-06
└── bridge_updater.py    # 写 bridge_maturity.yaml + IndexService
```

---

## 三、 calibration_session

### 3.1 用途

产出 **CalibrationArtifact**，供 deploy/eval PreFlight PF-04 校验。

### 3.2 流程

```
lab run create --type calibration_session \
  --device franka-01 \
  --cal-types camera_extrinsic,hand_eye

  → PreFlight: PF-01, PF-02, PF-03(L≥L1)
  → 操作员运行标定工具（框架不替换厂家/开源标定 UI）
  → 框架收录 raw + 生成 calibration.yaml
  → 注册 CalibrationArtifact
  → RunManager.finish
```

### 3.3 calibration.yaml（Artifact 核心）

```yaml
calibration_id: calib_franka-01_handeye_20260610
device_id: franka-01
types: [camera_extrinsic, hand_eye]
valid_until: "2026-09-10T00:00:00+08:00"
frames:
  camera_wrist:
    parent: ee_link
    translation: [0.01, 0.02, 0.03]
    rotation: [0, 0, 0, 1]
data_files:
  - raw/camera_intrinsic.yaml
  - raw/handeye_result.npz
producer_run_id: cal_20260610_100000_p2_franka-01
```

### 3.4 过期策略

- 默认 `valid_until = created + 90d`（可 CR 调整）
- 过期后 PF-04 fail；collect 视觉任务拒绝，deploy/eval 拒绝

---

## 四、 Bridge 晋升（L2–L4）

| 级别 | 触发 Run | 自动化程度 |
|------|----------|------------|
| L1 | real_bringup pass | 全自动 |
| L2 | real_collect 首段无 fault 或 dedicated teleop smoke | 半自动（RunManager 回调） |
| L3 | real_deploy smoke episode 完成 | 半自动 |
| L4 | real_eval protocol 完成 | 半自动 |

`bridge_updater.py` 在对应 Run `finish` 时读取 result，满足条件则写 yaml + audit。

---

## 五、 CLI

```bash
lab ops bringup --device franka-01
lab ops calibrate --device franka-01 --types hand_eye,camera_extrinsic
lab ops bridge-status --device franka-01
```

`lab ops *` 为 `lab run create --type ...` 的便捷封装。

---

## 六、 与 P3 衔接

- 设备 `status=blocked`（maintenance_policy）→ PreFlight 拒绝 bringup
- 场地/layout 变更 → P3 更新 SceneManifest，**不**自动改 Bridge level
- 安全 SOP 二人规则不适用于 bringup（静态 smoke）；calibration 在 Z-FIX 时可单人

---

## 七、 验收标准

- [ ] 新设备 L0 → bringup pass → L1
- [ ] calibration_session 产出 Artifact，PF-04 在 valid_until 内 pass
- [ ] bringup fail 不晋升，report 可查
- [ ] Driver CR 后手动触发降级至 L1

---

*MDD-PIPE-C | pipeline_c_ops_mdd_v1*
