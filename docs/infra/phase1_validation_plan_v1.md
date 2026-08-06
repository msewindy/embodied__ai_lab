# Phase 1 验证测试方案 v1.4


| 属性        | 内容                                                                                                                                                                                                                                                                      |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **文档编号**  | INFRA-02                                                                                                                                                                                                                                                                |
| **版本**    | v1.4                                                                                                                                                                                                                                                                    |
| **维护人**   | R2                                                                                                                                                                                                                                                                      |
| **依据**    | [PLAN-FUSION-01](../plan/platform_wm_fusion_plan_v0.md) · [TECH-09](../architecture/platform_technical_architecture_v1.md) · [TECH-02](../software/ros2_interface_v1.md) · [TECH-04](../software/version_matrix_v1.md) · [TECH-13](../software/isaac_job_adapter_v1.md) |
| **主锚点设备** | `franka-01`（**Franka Research 3 + Hand**）                                                                                                                                                                                                                               |
| **主场景**   | M2：**官方 FR3 USD**（禁止自研场景）；M4+：`tabletop_pickplace_v0` / Scene v0                                                                                                                                                                                                        |
| **回归设备**  | `quadruped-01`（Go2）— **不计入 Phase-1 主交付**                                                                                                                                                                                                                                |
| **用途**    | Phase 1：Walking Skeleton → **FR3 控制仿真同构闭环**（ROS2 + Isaac）                                                                                                                                                                                                               |


---



## 〇、方向变更摘要



### 0.1 v1.3 → v1.4（本版）


| 项 | v1.3 | v1.4 |
| -- | ---- | ---- |
| M2 场景 | 「极简桌面 / 官方 demo 不强制」 | **强制官方 FR3（+ Hand）USD**；自研场景 / Scene v0 推迟到 M4+ |
| M2 启动 SOP | Isaac 启动仅注释占位 | **可复制步骤**：启 Sim、开官方 USD、启 ROS2 bridge、再跑控制图 |
| M2 代码门禁 | 隐含「先写再跑」 | **显式前置**：msg / bridge / launch / hello 未建或未冒烟 → **不计 M2 通过** |


### 0.2 v1.2 → v1.3（仍有效）


| 项          | v1.2           | v1.3                                          |
| ---------- | -------------- | --------------------------------------------- |
| ws-02 ROS2 | 禁止进域           | **双模式**：控制仿真 **推荐 ROS2**；批训练可不启               |
| M2 控法      | 偏进程内 Isaac API | **主路径：ROS2 Topic 同构**；API 仅作排障旁路              |
| M2–M6      | 验收要点           | **补详细技术方案**（拓扑 / 包 / Topic / 步骤 / 验收）         |
| 真机域隔离      | DOMAIN=42      | 仿真控制域 `ROS_DOMAIN_ID=43`；真机域仍 **42**；**禁止混用** |




### 0.3 v1.1 → v1.2（仍有效）

主锚点 Go2→FR3；E 序列引入 M0–M6；Go2 真机后置。世界模型 SSOT：`external/world_model/docs/FR3*.md`。

---



## 一、当前进度（手动更新）



### 1.1 主路径（FR3 融合 · 必须完成）


| ID     | 场景                                            | 节点       | 映射 F1  | 状态  | 完成日         |
| ------ | --------------------------------------------- | -------- | ------ | --- | ----------- |
| **E0** | 代码仓库 + 网络 + 环境安装                              | ws-01/02 | —      | ✅   | 2026-08（环境） |
| **M0** | `external/world_model` 挂载 + 版本钉扎表可填           | ws-02    | F1-0   | ✅   | 2026-08-03  |
| **E1** | Skeleton 全流程冒烟                                | ws-02    | （编排基线） | ✅   | 2026-08-03  |
| **M2** | Isaac+ROS2 FR3 Hello：Δpose + LowStateFeedback | ws-02    | F1-2   | ✅   | 2026-08-04  |
| **M3** | RunManager 归档一次 FR3 控制仿真 `run`                | ws-02    | F1-1   | ✅   | 2026-08-04  |
| **M4** | 录 1 条可回放（日志轨或 LeRobot）                        | ws-02    | F1-3   | ✅   | 2026-08-05  |
| **M5** | Mid 最小：Template MidGoal + stub/Oracle         | ws-02    | F1-4   | ✅   | 2026-08-05  |
| **M6** | PreFlight/SOP：成员按清单独立开跑                       | ws-02    | F1-5   | ⬜   |             |


**Phase-1 主交付**：E0 + M0 + E1 + **M2～M6**。  
**一句话出口**：任意成员能按 SOP 启动一次「FR3 桌面抓放**控制仿真**」：有 `run_id`、有 High/Mid/Low 最小 ROS2 链路、有可回放数据。

### 1.2 回归（Go2 · 不阻塞）


| ID      | 状态  | 说明                        |
| ------- | --- | ------------------------- |
| E2 / E3 | ✅   | ROS2 编译 + Go2 sim bringup |
| E4 / E7 | ⬜   | 真机后置；围栏急停前禁止              |
| E6      | ⬜   | checkpoint 同步；可与 M3 后并行   |


---



## 二、lab-ws-02 双模式（架构修正 · 强制）



### 2.1 模式定义


| 模式        | 代号           | 何时用                              | ROS2  | DOMAIN |
| --------- | ------------ | -------------------------------- | ----- | ------ |
| **控制栈仿真** | **CTRL-SIM** | M2–M6、bringup/collect 通路、与真机同构验证 | **开** | **43** |
| **离线批处理** | **BATCH**    | 大规模 RL/数据工厂、可不跑完整控制图             | 可不启   | —      |


**Phase-1 主路径 = CTRL-SIM。** BATCH 不取消，但不作为 M2–M6 验收形态。

### 2.2 CTRL-SIM 目标拓扑（与真机同构）

```text
lab-ws-02 · ROS_DOMAIN_ID=43
┌─────────────────────────────────────────────────────────────┐
│ Lab OS（可同机）                                              │
│   RunManager / PreFlight / Index（M3+）                      │
│   发布 /system/run_context                                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ Agent Runtime                                                │
│   High（薄，M5+ 可 Template）                                  │
│   Mid（M5 Template；M2 可用脚本代替）                           │
│        │ /skill/franka_01/intent  (task_space)               │
│        ▼                                                     │
│   Low / franka_sim_bridge                                    │
│        │ 内部：限幅 · HOLD · IK/阻抗                            │
│        ▼                                                     │
│   Isaac Sim/Lab + ROS2 Bridge（官方优先，失败再自研适配）         │
│        M2：官方 FR3(+Hand) USD · M4+：Scene v0 桌面杯碗         │
│        │                                                     │
│        ▼ /perception/franka_01/low_state 等                  │
└─────────────────────────────────────────────────────────────┘

真机期（Phase-2）同一套 Topic/msg：
  DOMAIN=42 · ws-01 大脑 + FR3 工控/Driver · backend=franka_real
```



### 2.3 硬纪律

1. **禁止** CTRL-SIM 使用 `ROS_DOMAIN_ID=42`（真机域）。
2. **禁止** 在 BATCH 作业脚本里默认 `source` 进 43 域后误连真机网段设备。
3. 仿真与真机 **msg 字段名、device_id、skill_mode 对齐**（TECH-02）；允许实现类不同。
4. Mid 五模块 **不得** 写入 `RunManager` / `protocols.py` 核心。
5. **M2 必须加载官方 FR3（+ Hand）USD**；禁止用未验证的自研 USD 冒充 M2 通过。实验室 Scene v0（杯碗/相机）自 **M4+** 起作为验收场景规格。



### 2.4 包与进程规划（目标名，实现时可微调）


| 组件                                | 建议位置                               | M2     | M3+      |
| --------------------------------- | ---------------------------------- | ------ | -------- |
| `embodied_lab_msgs`               | `ros2/`                            | ✓ 扩展编译 | ✓        |
| `franka_sim_bridge`               | `ros2/` 新包                         | ✓ MVP  | ✓        |
| `embodied_lab_bringup` FR3 launch | `ros2/`                            | ✓      | ✓        |
| `m2_franka_hello` / Mid 脚本        | `lab_platform/scripts` 或 `ros2` 节点 | ✓      | → Mid 节点 |
| RunManager + isaac/ctrl-sim 入口    | `lab_platform/`                    | —      | ✓        |
| Isaac 场景 USD                      | **官方 Nucleus FR3**（见 §6.2）         | **强制** | —        |
| 实验室 Scene / Lab 任务                | `tasks/tabletop_pickplace_v0/`（待建） | **不做** | Scene v0 |


---



## 三、框架骨架对照（实现状态）



### 3.1 `lab_platform/`


| 模块                                                | 状态      | 说明                          |
| ------------------------------------------------- | ------- | --------------------------- |
| RunManager / Index / PreFlight / Locks / Artifact | **真实**  | E1 已冒烟                      |
| IsaacLauncher                                     | Stub→替换 | M3 须能拉起 CTRL-SIM 或包装 launch |
| Agent Runtime                                     | **待建**  | High/Mid/Low；经 ROS2 交互      |
| RealRuntime 真机                                    | Stub    | Phase-2                     |




### 3.2 `ros2/`


| 包                                | 状态                                      |
| -------------------------------- | --------------------------------------- |
| `embodied_lab_msgs`              | 真实；已按 TECH-02 扩展 `ee_delta` / `LowStateFeedback` |
| `go2_*`                          | 回归保留                                    |
| `franka_sim_bridge` + FR3 launch | **代码已建**；ws-02 Isaac 联调验收仍开            |




### 3.3 Phase-1 明确不做

Cosmos/LDA/完整 V-JEPA；H1/H2 主结论；工业跨夹具交付；真机相机完整 P0r；Go2 真机作主交付；**CTRL-SIM 与真机共 DOMAIN**。

---



## 四、主路径产物


| ID  | 产物                                  | 含义       |
| --- | ----------------------------------- | -------- |
| M0  | 挂载 + 钉扎表                            | 可追溯      |
| E1  | smoke ALL PASSED                    | 编排骨架     |
| M2  | CTRL-SIM：Δpose 5cm + low_state      | Low 契约同构 |
| M3  | `run_id` + manifest（franka / scene） | 平台托举     |
| M4  | 可回放轨迹                               | 采数       |
| M5  | ≥2 MidGoal 步进                       | 薄中层      |
| M6  | SOP 交叉执行通过                          | 可运营      |


---



## 五、M0 / E1 执行摘要



### 5.1 M0 — 挂载（✅）

见 `[external/README.md](../../external/README.md)`。ws-02：

```bash
cd ~/project/embodied__ai_lab
ln -sfn ../world_model external/world_model   # 或 ./scripts/link_external_world_model.sh
test -f external/world_model/README.md && echo OK
```



### 5.2 E1 — Skeleton 冒烟（✅）

```bash
cd ~/project/embodied__ai_lab/lab_platform
source .venv/bin/activate
python scripts/smoke_test.py
# === ALL SMOKE TESTS PASSED ===
```

E1 **不要求** ROS2。CTRL-SIM 从 M2 开始。

---



## 六、M2 — 技术方案与执行（CTRL-SIM · Low 契约）



### 6.0 实现状态与前置门禁（必读）

截至 2026-08-04：M2 **代码已合入**，且 **lab-ws-02 联调通过**（见 `lab_platform/scripts/m2_env_pin.md`）：


| 交付物 | 仓库现状 | 说明 |
| --- | --- | --- |
| `SkillIntent` 扩展（`ee_delta` / `gripper` / `expire_ms` 等） | **已合入代码** | 须 `colcon build` 后 `ros2 interface show` 复核 |
| `LowStateFeedback.msg` | **已合入代码** | TECH-02 字段 |
| `franka_sim_bridge` | **已合入代码** | 适配 Isaac **官方** `/joint_states`·`/joint_command`（非自研物理） |
| `franka_ctrl_sim.launch.py` | **已合入代码** | `embodied_lab_bringup` |
| `m2_franka_hello.py` / `m2_env_pin.md` | **已合入 + pin 已填** | `lab_platform/scripts/`；Hello 两次 PASS field check |
| 既有 `go2_*` 包 | 已有 | **只证明 Go2 路径**；**不**算 M2 已测 |
| Isaac + FR3 联调 | **ws-02 已测通过** | 桥方案 A；HOLD 后约 2–5 cm track 残留已记入 pin |

**门禁（任一未满足则 §6.8 不计通过）**：

1. `colcon build --packages-up-to franka_sim_bridge embodied_lab_bringup` 成功，且 `source install/setup.bash` 后 `ros2 interface show` 可见扩展后的 `SkillIntent` 与 `LowStateFeedback`（或约定临时等价 msg）。
2. `ros2 launch embodied_lab_bringup franka_ctrl_sim.launch.py --show-args` 可解析。
3. `python3 lab_platform/scripts/m2_franka_hello.py --help` 可运行（依赖与 INFRA-01 相同：系统 ROS Python / venv 混用策略）。
4. Isaac 侧已按 §6.7 加载 **官方 FR3 USD**，桥方案 A 或 B 已选定并写入 `m2_env_pin.md`。

### 6.1 目标

在 **lab-ws-02 · DOMAIN 43** 上，用与真机一致的 ROS2 控制语义：

1. 加载 **Isaac 官方 FR3 + Hand USD**（禁止自研场景冒充通过）
2. 发布相对 Δpose，末端移动约 **5 cm**
3. 订阅并打印 `LowStateFeedback` 最小字段
4. 无新令时 **HOLD**（保持最后指令或刹停，可配置）

**不强制**当日接 RunManager（→ M3）。M2 **只验控制契约**，不验杯碗/相机/采数。

### 6.2 场景策略（强制官方资产）


| 项 | M2 规定 |
| --- | --- |
| 机器人 USD | **强制** Nucleus / Content Browser 官方路径（见下）；**禁止**仓库内未验证自研 USD |
| 夹爪 | 优先带 **Franka Hand** 的官方变体；若本机仅有裸臂 `fr3.usd`，须在 `m2_env_pin.md` 注明，且 `gripper_width` 可填占位但字段仍要出 |
| 场景内容 | **官方机器人资产即可**（地面 / 默认灯光随官方资产）；**不要求**桌面、杯碗、相机 |
| 自研 `tabletop_pickplace_v0` | **M2 禁止作为通过依据**；M4+ 再对齐 `FR3_Scene_v0` |
| 官方 MoveIt / Panda 示例 | 可用作 **ROS2 bridge 操作参考**；若示例是 Panda，**不得**把 Panda 当作 FR3 验收资产——资产必须换成官方 FR3 |

**钉死资产路径（Isaac Sim 6 Content Browser）**：

```text
Isaac Sim > Robots > FrankaRobotics > FrankaFR3 > fr3.usd
# 文档相对路径：FrankaRobotics/FrankaFR3/fr3.usd
# 运行时常见绝对形态（以本机 Nucleus / assets root 为准，写入 pin）：
#   <assets_root>/Isaac/Robots/FrankaRobotics/FrankaFR3/fr3.usd
```

带 Hand 的官方变体若存在于同目录或官方 catalog，**优先选用**，并把完整路径记入 `m2_env_pin.md` 的 `isaac_usd_path` / `isaac_asset_rev`。

参考：[Isaac Sim 6 Robot Assets](https://docs.isaacsim.omniverse.nvidia.com/6.0.0/assets/usd_assets_robots.html) · ROS2 Joint 教程（桥接操作，资产示例或为 Panda）[ROS2 Joint Control](https://docs.isaacsim.omniverse.nvidia.com/6.0.0/ros2_tutorials/tutorial_ros2_manipulation.html)。

### 6.3 软件架构

```text
终端 A：Isaac Sim 6（已开官方 FR3 USD + isaacsim.ros2.bridge）
终端 B：ros2 launch ... franka_ctrl_sim.launch.py
         - franka_sim_bridge   # 选项 B 必起；选项 A 时作 TECH-02 适配层
         - （可选）safety stub
终端 C：python m2_franka_hello.py
         - 发布 1～N 次 task_space SkillIntent
         - 打印 low_state
```


| 层级 | M2 实现 | Topic（device 段 `franka_01`） |
| --- | --- | --- |
| Mid 替代 | `m2_franka_hello` 脚本 | pub `/skill/franka_01/intent` |
| Low | `franka_sim_bridge` | sub intent；pub `/perception/franka_01/low_state`（及内部 joint 适配） |
| 物理 | Isaac + 官方 ROS2 bridge（或 Lab API） | **不**对 Mid 暴露 |
| 安全 | 软件限幅 + expire HOLD | 可先无完整 F6S |

### 6.4 消息契约（验收用最小集）

**下行** `embodied_lab_msgs/SkillIntent`（`skill_mode=task_space`）：

```text
ee_delta[6] = {dx,dy,dz,droll,dpitch,dyaw}   # 基座系相对；M2 测 dx=+0.05
gripper ∈ [0,1]
control_mode = POSE(1) 或 IMPEDANCE(2)
expire_ms = 150–200
frame_id = "fr3_link0"   # 或与官方资产一致的基座 frame（须写入 pin）
device_id = "franka-01"
```

**上行**（优先正式 `LowStateFeedback.msg`；临时 JSON/`String` 仅排障，字段名仍冻结）：

```text
ee_pose_actual, ee_pose_desired
q[7], gripper_width
tracking_error, contact_flag?
safety_event, backend="isaac_sim", latency_ms
```

时钟默认：`control_hz≈50`（bridge 内），脚本侧可 10 Hz 发令；`record_fps` 留到 M4。

### 6.5 Isaac ↔ ROS2 桥（实现选项）

按可用性**自上而下选一**，选定后写入 `m2_env_pin.md`：


| 选项 | 说明 | 适用 |
| --- | --- | --- |
| **A. 官方** `isaacsim.ros2.bridge` + OmniGraph（JointStates 等） | Isaac 内启用 ROS2 bridge；用官方节点出/入 joint（或等价）；**本仓库** `franka_sim_bridge` 将官方 topic **适配**为 TECH-02 `SkillIntent` / `LowStateFeedback` | **优先**；少自研物理侧 |
| **B. 自研** `franka_sim_bridge`（Lab/Sim API） | 进程内调 Isaac Lab / Sim API，rclpy 直接出 TECH-02 Topic；仍须加载 **同一官方 FR3 USD** | 官方桥与 Jazzy/Cyclone 不兼容或难装时 |
| **C. 旁路（不计入 M2 通过）** | 纯 API、无 ROS2 | 仅排障 |

**M2 正式通过必须走 A 或 B。** 推荐顺序：先 A 打通官方 `/joint_states` 冒烟 → 再挂适配层出 TECH-02 → 再跑 hello。

### 6.6 推荐仓库落点

```text
ros2/                              # 本仓库当前为扁平包布局（非 src/）
  embodied_lab_msgs/               # 扩展 SkillIntent；新增 LowStateFeedback
  franka_sim_bridge/               # Low：intent→Isaac；反馈→low_state（待建）
  embodied_lab_bringup/
    launch/franka_ctrl_sim.launch.py
lab_platform/scripts/
  m2_franka_hello.py               # 发 Δpose + 打印反馈（待建）
  m2_env_pin.md                    # 手填版本 / USD / 桥方案钉扎（待建）
```

### 6.7 执行步骤（ws-02）

以下路径以仓库根 `~/project/embodied__ai_lab`、Isaac Lab `~/IsaacLab` 为例；本机不一致时以 `m2_env_pin.md` 为准。

#### 6.7.1 终端公共环境（每个 CTRL-SIM 终端）

```bash
export ROS_DOMAIN_ID=43
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
# 若 Isaac 官方桥要求 FastDDS profile，按本机 pin 设置；默认实验室用 Cyclone
source /opt/ros/jazzy/setup.bash
```

#### 6.7.2 代码编译与接口冒烟（门禁）

```bash
cd ~/project/embodied__ai_lab/ros2
colcon build --symlink-install --packages-up-to franka_sim_bridge embodied_lab_bringup
source install/setup.bash

ros2 interface show embodied_lab_msgs/msg/SkillIntent | grep -E 'ee_delta|gripper|expire'
ros2 interface show embodied_lab_msgs/msg/LowStateFeedback
ros2 launch embodied_lab_bringup franka_ctrl_sim.launch.py --show-args
```

#### 6.7.3 终端 A — 启动 Isaac Sim 并加载官方 FR3

**方式 1（GUI · 推荐首次）**

```bash
# 按本机安装方式启动 Isaac Sim 6（示例：Isaac Lab 捆绑）
cd ~/IsaacLab
./isaaclab.sh -s
# 或直接调用本机 isaac-sim.sh / omni_python 入口（写入 pin）
```

在 GUI 中：

1. **Window → Extensions**：启用 `isaacsim.ros2.bridge`（及依赖）。
2. Content Browser 打开官方资产：  
   `Isaac Sim > Robots > FrankaRobotics > FrankaFR3 > fr3.usd`  
   （带 Hand 变体优先；完整路径记入 pin。）
3. 确认 Stage 中 Articulation Root（常见为 `/fr3` 或资产默认 prim；**以 Stage 为准写入 pin** 的 `articulation_prim`）。
4. **Tools → Robotics → ROS 2 OmniGraphs → JointStates**（或按官方 Joint Control 教程搭 Publish/Subscribe Joint State + Articulation Controller），`targetPrim` / `robotPath` 指向上述 FR3 prim。
5. 按 **Play**。另开 ROS 终端验证官方桥：

```bash
# 与 Isaac 同一 DOMAIN=43
ros2 topic list | grep -E 'joint_states|joint_command'
ros2 topic echo /joint_states --once
```

**方式 2（命令行打开 USD · 路径以 pin 为准）**

```bash
# 示例：用 Isaac 入口直接打开官方 USD（具体可执行文件名因安装而异）
ISAAC_USD="<assets_root>/Isaac/Robots/FrankaRobotics/FrankaFR3/fr3.usd"
# ./isaac-sim.sh --/app/file/open="$ISAAC_USD"
# 打开后仍须启用 ros2.bridge + JointStates 图 + Play（同方式 1 步骤 1–5）
```

**选项 B 差异**：GUI 仍加载 **同一官方 FR3 USD** 并 Play；可不搭官方 JointStates 图，改由 `franka_sim_bridge` 经 Lab/Sim API 驱动。仍须能在 DOMAIN 43 上看到 TECH-02 topic。

#### 6.7.4 终端 B — 启动实验室控制图

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=43
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
cd ~/project/embodied__ai_lab/ros2 && source install/setup.bash

ros2 launch embodied_lab_bringup franka_ctrl_sim.launch.py \
  device_id:=franka-01 backend:=isaac_sim
```

期望：`ros2 topic list` 可见 `/skill/franka_01/intent` 与 `/perception/franka_01/low_state`（或 launch 参数声明的等价名）。

#### 6.7.5 终端 C — Hello Δpose

```bash
cd ~/project/embodied__ai_lab/lab_platform
# 保证能 import rclpy / embodied_lab_msgs（与 INFRA-01 相同注意事项）
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=43
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
# 若使用 venv：按 INFRA-01 策略激活，且勿遮蔽系统 site-packages 中的 rclpy
python3 scripts/m2_franka_hello.py --dx 0.05 --domain 43
```

#### 6.7.6 钉扎 `m2_env_pin.md`（验收必填）

至少记录：

```text
date:
host: lab-ws-02
isaac_sim: 6.0.x
isaac_lab: <tag/commit>
driver: <nvidia-smi>
ros: jazzy + rmw_cyclonedds_cpp
ROS_DOMAIN_ID: 43
bridge_option: A | B
isaac_usd_path: <完整路径或 Content Browser 路径>
isaac_asset_rev: <若可知>
articulation_prim: /fr3   # 以 Stage 实测为准
frame_id_base: fr3_link0
notes: Hand 是否加载；官方 JointStates 是否使用
```

### 6.8 验收标准（M2）


| # | 标准 |
| --- | --- |
| 0 | §6.0 门禁全部满足；**所用 USD 为官方 FR3（非自研 Scene）** |
| 1 | `ROS_DOMAIN_ID=43`；`ros2 topic list` 可见 intent / low_state（或约定名） |
| 2 | 末端沿基座 x（或 pin 声明轴）移动约 **5 cm**，可重复 |
| 3 | 打印字段齐：`ee_pose_*`、`q[7]`、`gripper_width`、`tracking_error`、`safety_event`、`backend=isaac_sim` |
| 4 | 停止发布后进入 HOLD（无持续漂移） |
| 5 | `m2_env_pin.md` 已填：Sim/Lab 版本、桥方案 A/B、**官方 USD 路径**、`articulation_prim`、驱动、日期 |


### 6.9 失败排查


| 现象 | 处理 |
| --- | --- |
| 无 topic | 域是否 43；是否 source install；Isaac 是否 Play；`isaacsim.ros2.bridge` 是否启用 |
| Content 无 FR3 | Nucleus / assets 未同步；核对 Isaac 6 Robot Assets 文档路径；禁止临时改用未声明的 Panda 充数 |
| 臂不动 | bridge / OmniGraph 日志；`articulation_prim` 是否匹配；限幅；IK 失败；单位 m/rad |
| 官方桥有 joint、无 TECH-02 | 适配层 `franka_sim_bridge` 未起或 topic 重映射错误 |
| DDS 奇怪设备 | 是否误用 42；防火墙/多网卡 Cyclone 配置 |
| rclpy 与 venv 冲突 | 参照 INFRA-01：系统 ROS Python 与 venv 混用策略 |
| 仅 API 能动、无 ROS2 | 属选项 C，**不计 M2 通过** |


---



## 七、M3 — 技术方案与执行（Run 归档）



### 7.1 目标

Lab OS 能**编排并归档**一次 CTRL-SIM 实验：有 `run_id`、manifest、index 可查。控制图仍为 M2 拓扑。

### 7.2 架构

```text
lab CLI / RunManager
  → PreFlight（GPU/域/设备锁；CTRL-SIM 检查 DOMAIN=43）
  → 写 run 目录 + manifest
  → 拉起（或附着）franka_ctrl_sim.launch + 可选 hello/短任务
  → 结束：清 run_context、收尾日志、Index 登记
```


| 项               | 规定                                                            |
| --------------- | ------------------------------------------------------------- |
| `device_id`     | `franka-01`                                                   |
| `scene_id`      | M3 可用 `tabletop_pickplace_v0_min` 或正式 `tabletop_pickplace_v0` |
| `backend`       | `isaac_sim`                                                   |
| `ros_domain_id` | **43**（写入 manifest）                                           |
| run_type        | 建议 `real_bringup` 仿真等价，或新增 `ctrl_sim`（实现时二选一，写进 TECH-05）      |




### 7.3 实现要点

1. **CTRL-SIM 不走 StubIsaacLauncher**：`CtrlSimLauncher` 检查 topic → 必要时自动 `franka_ctrl_sim.launch` → 跑 `m2_hello` → 写 manifest。
2. **RunManager 仍不跑 Mid 逻辑**；只管生命周期。
3. `/system/run_context` 在 DOMAIN 43 由 `RclpyRos2Bridge` 发布（TRANSIENT_LOCAL；`run_type=ctrl_sim`）。
4. 产出目录：`~/embodied-ai-lab-data/runs/ctrl_sim/<run_id>/` + `manifest.json`。
5. CLI：`lab ctrl-sim run`（`--no-launch` / `--keep-launch`）。



### 7.4 目标命令形态

```bash
# 前置：Isaac 官方 FR3 Play + JointStates；终端 B 已 launch franka_ctrl_sim
export ROS_DOMAIN_ID=43
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source /opt/ros/jazzy/setup.bash
source ~/project/embodied__ai_lab/ros2/install/setup.bash
cd ~/project/embodied__ai_lab/lab_platform && source .venv/bin/activate

lab --data-root ~/embodied-ai-lab-data ctrl-sim run \
  --device franka-01 \
  --scene tabletop_pickplace_v0_min \
  --profile m2_hello
```

首跑（2026-08-04）：`cs_20260804_145201_p2_franka-01` status=`completed`；manifest 含 `ros_domain_id=43` / `backend=isaac_sim` / Isaac 版本。  

后续增强：`lab ctrl-sim run` 默认 **真 ROS** 发布 `/system/run_context`；若 TECH-02 topic 缺失且 `/joint_states` 已可见则 **自动** `franka_ctrl_sim.launch`（`--no-launch` / `--keep-launch` 可调）。



### 7.5 验收标准（M3）


| #   | 标准                                                                      |
| --- | ----------------------------------------------------------------------- |
| 1   | Run `completed`（或失败时有可诊断日志，但主验收为成功路径）                                   |
| 2   | manifest 含：`device_id`、`scene_id`、`backend`、`ros_domain_id=43`、Isaac 版本 |
| 3   | Index 可查该 `run_id`                                                      |
| 4   | **非 Stub**：确实拉起过 Isaac+ROS2 控制图（日志可证）                                   |


仅 Stub 假跑 → 标「编排通路 OK」，**不计入**融合 Go。

---



## 八、M4 — 技术方案与执行（录制与回放）



### 8.1 目标

在某一 `run_id` 下录 **≥1** 条可回放轨迹；双轨至少打通一条主路径。

### 8.2 双轨（SSOT：世界模型数据契约）


| 轨道         | 格式                                       | 用途    |
| ---------- | ---------------------------------------- | ----- |
| **A 运行日志** | `logs/low.jsonl` + `mid.jsonl`（可先只有 low） | 复盘、评测 |
| **B 学习集**  | LeRobot Dataset **v3.0**                 | 训练    |


纪律：主结论评测认 A；训练认 B；`manifest` 互链。

### 8.3 技术方案

```text
录制节点（10 Hz）：
  订 /perception/franka_01/low_state
  订 /skill/franka_01/intent
  订（可选）相机 CompressedImage
  → 写 run 目录

回放：
  读轨迹 → 再发 intent（开环）或对比 ee_pose 误差
```


| 项            | 值                                                |
| ------------ | ------------------------------------------------ |
| `record_fps` | **10**                                           |
| 场景           | 建议开始对齐 Scene v0（杯碗可选：若未摆，录「空载 Δpose 轨迹」仍算 M4 通路） |
| 成功           | 有回放命令；误差「可接受」（目视 + 简单阈值）                         |




**已实现（A 轨 · 2026-08-05）**

```bash
# 录制（挂在 M3 run 上）
lab --data-root ~/embodied-ai-lab-data ctrl-sim run \
  --device franka-01 --scene tabletop_pickplace_v0_min \
  --profile m2_hello --record --keep-launch

# 回放
lab --data-root ~/embodied-ai-lab-data ctrl-sim replay \
  --run-id <run_id> --device franka-01
```

产物：`runs/ctrl_sim/<run_id>/logs/low.jsonl` + `replay_metrics.json`；manifest.`tracks.A`。



### 8.4 验收标准（M4）

1. 产物落在对应 `run_id` 下
2. 一键/文档化回放命令可复现
3. manifest 标明轨道 A/B 路径

---



## 九、M5 — 技术方案与执行（薄 Mid）



### 9.1 目标

用 **Template MidGoal** 驱动短序列；Low 仍只收 TaskSpaceCommand；**不宣称 H1**。

### 9.2 架构

```text
TemplatePlayer / 键切（High 可缺省）
  → MidGoal[] 如 APPROACH → RETREAT（≥2 步）
  → Mid 节点：把 goal 译成一串 Δpose intent
  → Low / franka_sim_bridge（同 M2）
```


| 项            | M5 规定                      |
| ------------ | -------------------------- |
| 情境           | stub 或 Oracle S1（仿真 GT）    |
| 前向 WM        | **stub off**               |
| 完整五模块        | **不做**                     |
| 与 RunManager | Mid 仍是独立节点；RM 只 start/stop |




### 9.3 MidGoal 最小结构（逻辑字段）

```text
MidGoal:
  name: APPROACH | GRASP | ... | RETREAT
  target_ref: red_cup | bowl | home | none
  success_predicate: ...   # M5 可简化为超时或位移阈值
```



**已实现（2026-08-05）**

```bash
lab --data-root ~/embodied-ai-lab-data ctrl-sim run \
  --device franka-01 --scene tabletop_pickplace_v0_min \
  --profile m5_template --keep-launch

# 或独立脚本
python3 lab_platform/scripts/m5_mid_template.py --domain 43
```

模板：`lab_platform/templates/m5_approach_retreat.yaml`（APPROACH → RETREAT）。  
产物：`logs/m5_mid_template.log`、`logs/mid_steps.json`；manifest.`mid`。



### 9.4 验收标准（M5）

1. ≥2 个 MidGoal 步进可在日志/屏幕观察
2. intent 仅 task_space；无策略直出关节扭矩
3. 失败可 HOLD/停，不失控连续发令

---



## 十、M6 — 技术方案与执行（SOP）



### 10.1 目标

非作者按文档独立完成一次 **M3+M4 级** CTRL-SIM 实验。

### 10.2 SOP 必含章节（文档落点建议）

`docs/infra/sop_franka_ctrl_sim_v0.md`（M6 前写成）：

1. 环境：DOMAIN=43、source ROS、venv
2. 启动顺序：Isaac → launch → `lab ctrl-sim run`
3. 如何查看 `run_id` / manifest / 日志
4. 正常停止与急停（软件）
5. 常见故障表（链到本文 §六.9）



### 10.3 验收标准（M6）

R1 或交叉角色签字/纪要：「按 SOP 独立完成一次仿真实验」。

---



## 十一、回归 Go2（摘要）

不阻塞融合 Go。E2/E3 已通过；E4/E7 真机后置。命令见历史 v1.1；**DOMAIN=42**。

---



## 十二、本周优先（更新）


| 序号  | 任务                               | 验收       |
| --- | -------------------------------- | -------- |
| 1   | msg 扩展 + `franka_sim_bridge` MVP + launch/hello | ✅ §6.0 门禁 |
| 2   | **M2** CTRL-SIM Hello（官方 FR3 USD）            | ✅ §六.8（2026-08-04） |
| 3   | **M3** Run 归档（真 ROS run_context + 自动 launch） | ✅ §七.5 |
| 4   | **M4** 录回放（A 轨 `--record` / `replay`） | ✅ §八.4 |
| 5   | **M5** 薄 Mid（`m5_template`）     | ✅ §九.4 |
| 6   | **M6** SOP                         | §十       |


**不要做**：Go2 真机主攻；Mid 五模块进 RunManager；CTRL-SIM 用 DOMAIN 42。

---



## 十三、常见问题


| 现象                | 处理                             |
| ----------------- | ------------------------------ |
| 找不到世界模型文档         | `external/README.md` / symlink |
| 仿真误连真机            | 检查是否误 export 42；改用 **43**      |
| Stub 假跑当完成        | M3 融合 Go 不计数                   |
| Isaac 与 ROS2 版本冲突 | TECH-04 钉桥；选项 B 自研 bridge      |
| pip/PyPI 超时       | 镜像源；见 E1 排障经验                  |


---



## 十四、相关文档


| 文档                                                               | 用途                            |
| ---------------------------------------------------------------- | ----------------------------- |
| [PLAN-FUSION-01](../plan/platform_wm_fusion_plan_v0.md)          | 融合宪法；双模式已同步                   |
| [TECH-09](../architecture/platform_technical_architecture_v1.md) | 部署视图；ws-02 双模式                |
| [TECH-02](../software/ros2_interface_v1.md)                      | Topic/msg                     |
| [TECH-04](../software/version_matrix_v1.md)                      | 版本与 DOMAIN                    |
| [TECH-13](../software/isaac_job_adapter_v1.md)                   | Job 薄封装（BATCH / 可扩展 CTRL-SIM） |
| `external/world_model/docs/FR3*.md`                              | Scene/数据数值 SSOT               |


---



## 十五、变更记录


| 版本       | 日期         | 说明                                                     |
| -------- | ---------- | ------------------------------------------------------ |
| v1.0     | 2026-06-16 | 首版；E2/E3                                               |
| v1.1     | 2026-07-09 | R1–R3 口径                                               |
| v1.2     | 2026-08-03 | FR3 主路径；M0–M6                                          |
| v1.3     | 2026-08-03 | **ws-02 双模式**；CTRL-SIM=ROS2 DOMAIN 43；**M2–M6 详细技术方案** |
| **v1.4** | 2026-08-04 | **M2 SOP**：强制官方 FR3 USD；Isaac 启动步骤；代码门禁与未测状态写清 |
| v1.4.1   | 2026-08-04 | **M2 联调通过**（ws-02）：`m2_env_pin.md` 钉扎；Hello PASS×2；进度表 M2→✅ |
| v1.4.1   | 2026-08-04 | **M3 骨架首跑**：`lab ctrl-sim run` → `completed` + manifest/index；`run_context` 仍为 Stub ROS |
| v1.4.2   | 2026-08-04 | **M3 收口**：真 ROS `/system/run_context`；缺 bridge 时自动 `franka_ctrl_sim.launch`；进度表 M3→✅ |
| v1.4.3   | 2026-08-05 | **M4 A 轨通过**：`--record` 51 帧 + `replay`；manifest tracks.A；相对 Δpose 开环误差仅作旁证 |
| v1.4.4   | 2026-08-05 | **M5 通过**：`m5_template` APPROACH→RETREAT 两步 success；`mid_steps.json`；task_space only |


---

*INFRA-02 v1.4.1 | Phase 1 · FR3 控制仿真同构闭环*
