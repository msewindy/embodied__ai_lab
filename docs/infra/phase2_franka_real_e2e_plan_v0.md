# Phase-2：真机 Franka Research 3 E2E 计划 v0

| 属性 | 内容 |
|------|------|
| **文档编号** | PHASE2-FR3-REAL-01 |
| **版本** | v0.1 |
| **日期** | 2026-08-07 |
| **状态** | **paused**（2026-08-10：优先仿真加深 L1=`strategy_runtime/`；真机联调暂缓） |
| **上位** | [PLAN-FUSION-01](../plan/platform_wm_fusion_plan_v0.md) §4.2 · [PLAN-STRUCT-01](../plan/lab_strategy_runtime_structure_v0.md) · [INFRA-02](phase1_validation_plan_v1.md) |
| **安全** | [SFT-01](../safety/safety_sop_v1.md) · [SFT-02](../safety/estop_wiring_v1.md) |
| **仿真基线** | DOMAIN **43** 已通；同构 Topic 见 [TECH-02](../software/ros2_interface_v1.md) |
| **真机域** | `ROS_DOMAIN_ID=**42**`（与 43 **禁止混用**） |

---

## 0. 一句话目标

在 **不破坏 CTRL-SIM 同构契约** 的前提下，把 `WorldBackend=franka_real` 接到 L0：真机也能走  
`run_id` → PreFlight（含安全门禁）→ TECH-02 SkillIntent / LowState → A 轨归档 →（可选）B 轨 / policy rollout。

**第一刀出口（R2）：** 真机 Hello——小 Δpose + HOLD + `lab` 归档一条 `real_*` 或 `ctrl_real` run。  
**E2E 出口（R5）：** 桌面抓放级闭环（可先薄 Mid / 示教，不强制 sim2real 一次成功）。

---

## 1. 与 Phase-1 的关系（叠放）

| 层 | Phase-1（已完成） | Phase-2（本计划） |
|----|-------------------|-------------------|
| L0 | RunManager / Index / 双轨 / SOP | 真机 PreFlight、锁、`run_context`@42、真机 SOP |
| L1 | Mid 脚本 + `lerobot_state` | 复用；真机限速 / 限工作空间 |
| L2 | Task Pack 仿真 Scene | 真机工位 pin（桌/标定/Hand）；可先简化几何 |
| Low | `franka_sim_bridge`@43 | **新建** `franka_driver_bridge`@42（官方 `franka_ros2`） |

复用：TECH-02 msg、device_id=`franka-01`、A/B 轨纪律、ArtifactHub。  
不复用：Isaac launch、DOMAIN 43、仿真 Oracle 位姿当真机 GT。

---

## 2. 硬前置（未满足禁止动臂）

| ID | 门禁 | 验收 |
|----|------|------|
| **G0** | 物理急停 / Desk 急停可用；操作者会停 | 实测拍停 → 电机去使能 |
| **G1** | 围栏 / Z-DYN 区域清理；二人规则（SFT-01） | R3 或现场负责人确认 |
| **G2** | FCI 网络：工控 ↔ Arm（IP 可达、防火墙放行） | `ping` / Desk 连接正常 |
| **G3** | 官方栈：`libfranka` + `franka_ros2`（Jazzy）可 launch | `franka_bringup` 起得来 |
| **G4** | `ROS_DOMAIN_ID=42` 专网；**无** 43 进程串域 | `echo $ROS_DOMAIN_ID` + topic 隔离抽检 |
| **G5** | L0：真机 run 类型 PreFlight 含 bridge 级别 / 急停检查项 | PF 失败则拒跑 |

**G0–G2 未勾选 → 不允许写驱动桥发令代码联调以外的动臂实验。**

---

## 3. 里程碑（R0–R5）

### R0 — 环境与官方栈钉扎（约 0.5–2 天）

- 工控机：Ubuntu 24.04 · ROS2 Jazzy · Cyclone · DOMAIN 42  
- 安装并记录：`libfranka` 版本、`franka_ros2` 版本、FR3 + Hand 序列号、FCI IP  
- 文档落点：新建 `lab_platform/scripts/r0_franka_real_env_pin.md`（对标 `m2_env_pin.md`）  
- 官方冒烟（**不用**本仓 bridge）：

```bash
export ROS_DOMAIN_ID=42 RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source /opt/ros/jazzy/setup.bash
# source franka_ros2 workspace
ros2 launch franka_bringup franka.launch.py robot_type:=fr3 robot_ip:=<fci-ip>
```

**出口：** env pin 表填齐；官方 joint_states 有数；急停演练一次。

### R1 — `franka_driver_bridge` MVP（约 3–5 天）

新建包（建议）：`ros2/franka_driver_bridge/`

| 职责 | 说明 |
|------|------|
| 订阅 | `/skill/<ns>/intent`（TECH-02，与仿真同） |
| 发布 | `/perception/<ns>/low_state` |
| 后端 | 官方 `franka_ros2` 控制接口（优先笛卡尔阻抗 / 与现 Δpose 语义可对齐的一条） |
| HOLD | `expire_ms` 与仿真同纪律；断流必 HOLD |
| 限幅 | 真机最大 Δ / 速度 / 工作空间盒（参数化，默认保守） |

**不**在 bridge 内实现完整 MoveIt；首版允许「小步笛卡尔」对齐 CTRL-SIM Hello。

**出口：** 与仿真相同 hello 脚本（改 `--domain 42`）字段检查 PASS；停发 HOLD。

### R2 — L0 真机 Run 归档（约 2–3 天）

- CLI：`lab real …` 或 `lab ctrl-real run`（名称待钉；须 `run_id` + manifest）  
- bringup launch：`franka_real.launch.py`（driver + bridge + run_context@42）  
- PreFlight：G 系列 + device lock + bridge maturity ≥ 约定级  
- A 轨：至少 `low.jsonl`（真机建议同时 rosbag，GOV-04）

**出口：** 一条 completed run；`lab lineage` 可查；**未**要求抓放成功。

### R3 — 薄 Mid / 安全工作空间（约 3–5 天）

- 复用 `m5_template` 量级：APPROACH → RETREAT（限速、限位移）  
- 真机 scene pin：桌高度、Home、禁区（文档 + yaml，可先无完整 USD）  
- 软件限速 + 硬件急停双通道演练记入 run

**出口：** Mid 两步 success（宽松 ε）；无碰撞、无超限报错逃逸。

### R4 — 标定与感知最小集（可与 R3 并行，约 3–7 天）

- Hand-eye / 桌面坐标（Pipeline C 子集）  
- ObjectPose：真机可用 ArUco / 固定夹具位，**不**直接信仿真 Oracle  
- 写入 CalibrationArtifact + Index

**出口：** 标定产物可被 Mid 引用；重复定位误差可记录。

### R5 — 真机 E2E（抓放或等价）（约 1–2 周）

| 路径 | 说明 |
|------|------|
| **5a 示教 / 脚本 Mid** | 真机 `m5_pickplace` 简化版或示教回放 → eval 谓词（水平距 / 净空可手工量） |
| **5b 策略 rollout** | `lab policy rollout` 同类入口，backend=`franka_real`，**极低速** + 人工监护 |

**出口（E2E PASS）：**

1. L0 run 完整（context / A 轨 / manifest）  
2. 安全门禁全程有效  
3. 至少一种：脚本抓放成功 **或** 策略短 rollout 无危险停机且可审计  
4. 真机 SOP 一页可复跑  

---

## 4. 建议仓库落点

```text
ros2/
  franka_driver_bridge/          # NEW · TECH-02 ↔ franka_ros2
  embodied_lab_bringup/
    launch/franka_real.launch.py # NEW
lab_platform/
  # real 或 ctrl_real launcher（对标 ctrl_sim）
  scripts/r0_franka_real_env_pin.md
docs/infra/
  sop_franka_real_v0.md          # R2 后写（对标 CTRL-SIM SOP）
  phase2_franka_real_e2e_plan_v0.md  # 本文
tasks/
  tabletop_pickplace_v0/         # 增 real_pin / 真机 profile 或旁路 real.yaml
```

---

## 5. 同构纪律（防漂移）

| 项 | 规则 |
|----|------|
| Topic / msg | 与 CTRL-SIM 同一 TECH-02；禁止真机私造第二套 intent |
| DOMAIN | 42=真机；43=仿真；双网卡/双 daemon 时写清 |
| device_id | 仍 `franka-01`（或 CR 新增 `franka-real-01` 并改矩阵） |
| HOLD | 断流 / expire 必须停；真机更严 |
| 速度 | 真机默认 ≤ 仿真验收速度的一小截（参数钉死） |
| 策略 | 仿真训的 `pol_*` **不得**默认 production；真机 lifecycle 单独晋升 |

---

## 6. 进度表（手动更新）

| ID | 内容 | 状态 | 完成日 |
|----|------|------|--------|
| G0–G2 | 急停 / 围栏 / FCI | ⬜ | |
| R0 | 官方栈 + env pin | ⬜ | |
| R1 | `franka_driver_bridge` Hello | ⬜ | |
| R2 | L0 真机 run 归档 | ⬜ | |
| R3 | 薄 Mid 限速 | ⬜ | |
| R4 | 标定最小集 | ⬜ | |
| R5 | 真机 E2E PASS | ⬜ | |

---

## 7. 本周建议切片（启动包）

1. **今天–明天：** 勾选 G0–G2；确认 FCI IP、Desk、急停；填 R0 pin 草稿。  
2. **本周：** R0 官方 `franka_bringup` 通；起草 `franka_driver_bridge` 包骨架（先不接大电流动作）。  
3. **联调窗：** R1 Hello@42（二人规则）；同步开 L0 `real` 入口设计。  

CTRL-SIM 保持可回归，避免真机开发打断 Phase-1 基线。

---

## 8. 明确不做（本阶段）

- 用仿真 DOMAIN 43 控真机  
- 无急停演练的「先看看能不能动」  
- 一上来全速度 ACT / VLA  
- Go2 真机并行主攻  
- 未标定就把仿真 Oracle 当真机物体位姿  

---

## 9. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-08-07 | Phase-1 E2E PASS 后首版；R0–R5 + 安全门禁 |

---

*PHASE2-FR3-REAL-01 v0.1 · 真机 E2E 工作基线草案*
