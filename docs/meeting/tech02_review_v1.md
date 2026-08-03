# TECH-02 ROS2 接口短评审记录 v1

| 属性 | 内容 |
|------|------|
| **日期** | 2026-06-11 |
| **文档** | TECH-02 `ros2_interface_v1.md` v1.0 |
| **评审焦点** | `RunContext`、`SkillIntent` 是否满足**首台真机**联调 |
| **首台设备假设** | **A：`quadruped-01`（Go2，locomotion 首条 Sim2Real）** · **B：`franka-01`（manipulation 首条 bringup/collect）** |

---

## 一、 「短评审 TECH-02」是什么意思？

不是重写整份接口规范，而是一次 **30–60 分钟的字段级核对**：

1. 拿出实验室**第一台要接 ROS2 的设备**（谁驱动、几自由度、数采方式、首条 Run 类型）。
2. 对照 TECH-02 里 **`RunContext`（实验上下文）** 和 **`SkillIntent`（慢环控制意图）** 的每个字段。
3. 回答三个问题：
   - 现有字段**够不够**跑 `real_bringup` → `real_collect` / `real_deploy`？
   - 要不要**增删字段**（在 v1.0 冻结前改）？
   - Driver Bridge / policy_manifest 能否**无歧义映射**？

通过标准：**首台设备不必改 msg 就能开始编码**；若需改，记录进 TECH-02 v1.1 变更项。

---

## 二、 RunContext 评审

### 2.1 现有字段

| 字段 | 用途 | bringup | collect | deploy/eval |
|------|------|:-------:|:-------:|:-----------:|
| `run_id` | 血缘、Rosbag、Safety | ✅ | ✅ | ✅ |
| `run_type` | 节点行为模式 | ✅ | ✅ | ✅ |
| `device_ids[]` | 命名空间 `{device_id}` | ✅ | ✅ | ✅ |
| `policy_id` | 加载 checkpoint | — | — | ✅ |
| `experiment_plan_id` | PreFlight PF-09 | — | ✅ | ✅ |
| `operator` | 审计 | ✅ | ✅ | ✅ |

### 2.2 缺口

| 缺失字段 | 影响 | 建议 |
|----------|------|------|
| `task_id` | eval 脚本、policy 节点不知任务配置 | **v1.1 增加**（可选 string，deploy/eval 时填） |
| `eval_protocol_id` | real_eval 节点需知指标协议 | **v1.1 增加**（real_eval 时必填） |
| `scene_id` | real_eval 场景对齐 | **v1.1 增加**（real_eval 时必填） |
| `project_id` | 多课题预留 | R2 可延后 |

### 2.3 首台设备结论（RunContext）

| 设备 | 结论 |
|------|------|
| **quadruped-01** bringup/collect/deploy | ✅ **够用**（eval 建议补 `eval_protocol_id`） |
| **franka-01** 同上 | ✅ **够用**（同上） |

**短评审决议**：RunContext **有条件通过** — bringup/collect/deploy 可开工；**real_eval 前**补 2–3 个字段或约定从 RunManager 参数 server 读取（二选一，推荐补 msg）。

---

## 三、 SkillIntent 评审

### 3.1 字段与首台设备匹配

#### 场景 A：`quadruped-01`（宇树 Go2 · locomotion）

| 能力 | SkillIntent 字段 | 匹配度 |
|------|------------------|--------|
| 速度跟踪 RL 策略 | `cmd_vel` (Twist) | ✅ 主路径 |
| 关节级 RL / WBC | `target_joint_pos/vel/tau[]`（12 DOF） | ✅ |
| Isaac `velocity_rough_go2` action | 映射 `target_joint_pos` 或 `cmd_vel` | ✅ 与 TECH-12 示例一致 |
| 限速 / Limiter | `kp/kd` + Safety `speed_scale` | ✅ |

**Perception 侧**：`RobotState.base_lin_vel`、`projected_gravity`、`joint_pos` 与 Isaac Lab Go2 观测对齐 ✅。

**结论**：**满足** Go2 作为首台 locomotion 设备，**无需改 SkillIntent**。

---

#### 场景 B：`franka-01`（Franka Panda · manipulation）

| 能力 | SkillIntent 字段 | 匹配度 |
|------|------------------|--------|
| 关节空间 teleop / IL | `target_joint_pos[]`（7 DOF） | ✅ |
| 力控 | `target_joint_torque[]`, `kp/kd` | ✅（`has_force_control=true`） |
| **笛卡尔空间 teleop**（SpaceMouse/VR 常用） | 无 `ee_pose` / `twist` 末端字段 | ⚠️ **缺口** |
| **夹爪**（独立于 7 轴） | 无 `gripper_pos/force` | ⚠️ **缺口** |
| 轨迹跟踪 | 可用 `/plan/.../trajectory` 绕开 SkillIntent | ✅ 备选 |

**Perception 侧**：台账有 `ee_pose`, `force_torque`, `wrist_camera`；TECH-02 有 `joint_states`、`RobotState`，但 **RobotState 无 `ee_pose`**，**无 `WrenchStamped` Topic** ⚠️。

**结论**：Franka 作首台时，**纯关节空间 collect/deploy 够用**；**笛卡尔 teleop + 夹爪 + 力矩反馈** 需在 v1.1 补充或强制走 `/plan/trajectory` + 扩展 Perception。

### 3.2 SkillIntent 设计优点（两设备通用）

- `skill_mode` + `source` 区分 teleop / policy / plan ✅
- `run_id` 与 RunContext 双重携带，便于 rosbag 对齐 ✅
- 数组字段与 `policy_manifest.action_schema` 映射规则清晰 ✅
- locomotion 与 manipulation **共用一个 msg**，避免设备定制 msg 泛滥 ✅

---

## 四、 与 policy_manifest（TECH-12）交叉核对

| manifest 示例（Go2） | TECH-02 映射 | 状态 |
|---------------------|--------------|------|
| `observation: base_lin_vel` | `RobotState.base_lin_vel` | ✅ |
| `observation: joint_pos` | `RobotState.joint_pos` | ✅ |
| `action: joint_target_pos` | `SkillIntent.target_joint_pos` | ✅ |
| manifest `source: /perception/robot_state` | Topic 已定义 | ✅ |

| manifest（Franka 典型 IL） | TECH-02 | 状态 |
|---------------------------|---------|------|
| `ee_pose` 观测 | 无 dedicated 字段 | ⚠️ 需 RobotState 扩展或 Camera+TF |
| `gripper_width` action | 无 | ⚠️ v1.1 |

---

## 五、 评审决议

| 项 | 决议 |
|----|------|
| **TECH-02 v1.0 整体** | **有条件通过** |
| **首台推荐** | **quadruped-01** 作第一条 Real 栈联调（与 skeleton demo / Isaac Go2 一致，SkillIntent 零修改） |
| **franka-01** | bringup + 关节空间 collect **可开始**；笛卡尔/夹爪/力矩 **v1.1 补丁** |
| **RunContext** | v1.1 增加 `task_id`、`eval_protocol_id`、`scene_id`（可选字段） |
| **SkillIntent** | v1.1 增加 `geometry_msgs/Pose ee_pose`（可选）、`float32 gripper_width`（可选） |
| **Perception** | v1.1 增加 `/perception/{id}/wrench`（Franka）；`RobotState` 增加 `ee_pose`（可选） |

**不阻塞 P2-1**：可立即创建 `embodied_lab_msgs` 按 **v1.0 现有定义**编译；v1.1 字段以 **optional 新增** 方式扩展，不破坏 v1.0。

---

## 六、 签字

| 角色 | 姓名 | 日期 | 结论 |
|------|------|------|------|
| R1 | | | |
| R2 | | | |
| R3 | | | |

---

*tech02_review_v1 · 2026-06-11*
