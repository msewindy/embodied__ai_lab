# 设备能力矩阵与 Bridge 成熟度规范 v1.0

| 属性 | 内容 |
|------|------|
| **文档编号** | TECH-11 |
| **版本** | v1.0 |
| **维护人** | P2（矩阵）/ P3（台账状态） |
| **依据** | TECH-09 v1.0-approved §8.5 |

---

## 一、 文件位置

```text
data/registry/device_capabilities.yaml   # 每 device 能力
data/registry/bridge_maturity.yaml       # 每 device Bridge 状态
data/vendor/{device_model}/              # Driver Bridge 插件元数据
```

PreFlight、CompatibilityCheck、RunManager 只读；变更经 **change_control** + P3 台账同步。

---

## 二、 device_capabilities.yaml  schema

```yaml
# data/registry/device_capabilities.yaml
devices:
  franka-01:
    model: franka_emika_panda
    status: active              # active | maintenance | blocked
    zone: Z-DYN
    task_domains: [manipulation]
    has_force_control: true
    onboard_compute: medium     # high | medium | low
    max_speed_cap: 0.5          # m/s 或框架归一化上限
    sensors: [joint_states, ee_pose, wrist_camera, force_torque]
    driver_bridge_plugin: vendor/franka_panda/bridge_v1
    power: wired                # wired | battery
    notes: "固定工位，动态区需二人规则"

  quadruped-01:
    model: unitree_go2
    status: active
    zone: Z-DYN
    task_domains: [locomotion, navigation]
    has_force_control: false
    onboard_compute: high
    max_speed_cap: 1.5
    sensors: [joint_states, imu, lidar, depth_camera]
    driver_bridge_plugin: vendor/unitree_go2/bridge_v1
    power: battery
    notes: "电池供电，急停不可依赖切 wall 电源"
```

| 字段 | 必填 | 说明 |
|------|:----:|------|
| model | ✓ | 厂家型号 |
| status | ✓ | `blocked` 时 PreFlight PF-02 拒绝 |
| zone | ✓ | 关联 zone_lock |
| task_domains | ✓ | locomotion / manipulation / navigation / loco_manipulation |
| has_force_control | ✓ | 力控任务兼容 |
| onboard_compute | ✓ | 影响 onboard_runtime 选择 |
| max_speed_cap | ✓ | Limiter 基线 |
| sensors | ✓ | CompatibilityCheck 传感器子集 |
| driver_bridge_plugin | ✓ | 插件路径 |
| power | ✓ | 安全 SOP 关联 |

---

## 三、 bridge_maturity.yaml schema

```yaml
# data/registry/bridge_maturity.yaml
devices:
  franka-01:
    level: L3                   # L0 | L1 | L2 | L3 | L4
    updated_at: "2026-06-10T09:30:00+08:00"
    updated_by_run: rb_20260610_090000_p3_franka-01
    history:
      - level: L1
        run_id: rb_20260610_090000_p3_franka-01
        at: "2026-06-10T09:30:00+08:00"
      - level: L3
        run_id: rd_20260610_120000_p2_franka-01
        at: "2026-06-10T12:00:00+08:00"
        note: "deploy smoke passed at 0.2 m/s cap"
```

### 级别定义与晋升条件

| 级别 | 含义 | 晋升条件（Run 产出） |
|------|------|----------------------|
| **L0** | 台账登记，Bridge 未验证 | 设备入库默认 |
| **L1** | 通信与 SDK smoke 通过 | `real_bringup` → `bringup_report.json` 全 pass |
| **L2** | 静态/慢速 teleop 通过 | `real_collect` 或专用 smoke：关节/read/write/teleop ≥30s 无 fault |
| **L3** | Policy deploy smoke 通过 | `real_deploy` 低速运行 ≥1 episode 无 ESTOP |
| **L4** | eval 协议验证通过 | `real_eval` 完整 protocol 跑通 |

### 降级触发

- Driver Bridge 插件 CR 合并 → 降至 **L1**
- 维护点检 fail / `status=blocked` → 不可启动任何 Run；恢复后从 **L1** 重验
- 硬件更换（相机/IMU/臂体）→ 相关标定失效 + Bridge 降至 **L2**

---

## 四、 zone 与并发

| zone_id | 说明 | 并发规则 |
|---------|------|----------|
| Z-DYN | 动态实验区 | 最多 **2** 个 `device_lock` 同时持有 |
| Z-FIX | 固定工位 | 每 device 独立 lock |
| Z-SIM | 仿真区（ws-02） | 仅 gpu_lock |

---

## 五、 初始设备清单（实验室规划）

| device_id | 类型 | 初始 level | 备注 |
|-----------|------|------------|------|
| franka-01 | 机械臂 | L0 | 采购后 bringup |
| quadruped-01 | 四足 | L0 | Go2 |
| humanoid-01 | 人形 | L0 | 待定型号 |

新设备入库流程：P3 台账 → 写入 `device_capabilities.yaml`（L0）→ 排期 `real_bringup`。

---

## 六、 与 PreFlight / MDD 衔接

- PreFlight PF-02 读 `status`
- PreFlight PF-03 读 `level` 与 Run 类型门槛表（见 `preflight_checklist_spec.md` §四）
- CompatibilityCheck 读 `task_domains`、`sensors`、`onboard_compute`
- `pipeline_c_ops_mdd_v1.md` 定义 bringup 如何写 `bringup_report.json` 并晋升 L1

---

*TECH-11 | device_capability_matrix_v1.0*
