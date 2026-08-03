# Phase 1 验证测试方案 v1.3


| 属性        | 内容                                                                                                                                                                                                                                                                      |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **文档编号**  | INFRA-02                                                                                                                                                                                                                                                                |
| **版本**    | v1.3                                                                                                                                                                                                                                                                    |
| **维护人**   | R2                                                                                                                                                                                                                                                                      |
| **依据**    | [PLAN-FUSION-01](../plan/platform_wm_fusion_plan_v0.md) · [TECH-09](../architecture/platform_technical_architecture_v1.md) · [TECH-02](../software/ros2_interface_v1.md) · [TECH-04](../software/version_matrix_v1.md) · [TECH-13](../software/isaac_job_adapter_v1.md) |
| **主锚点设备** | `franka-01`（**Franka Research 3 + Hand**）                                                                                                                                                                                                                               |
| **主场景**   | `tabletop_pickplace_v0`（Isaac 控制仿真；M2 允许极简桌面）                                                                                                                                                                                                                           |
| **回归设备**  | `quadruped-01`（Go2）— **不计入 Phase-1 主交付**                                                                                                                                                                                                                                |
| **用途**    | Phase 1：Walking Skeleton → **FR3 控制仿真同构闭环**（ROS2 + Isaac）                                                                                                                                                                                                               |


---



## 〇、方向变更摘要



### 0.1 v1.2 → v1.3（本版）


| 项          | v1.2           | v1.3                                          |
| ---------- | -------------- | --------------------------------------------- |
| ws-02 ROS2 | 禁止进域           | **双模式**：控制仿真 **推荐 ROS2**；批训练可不启               |
| M2 控法      | 偏进程内 Isaac API | **主路径：ROS2 Topic 同构**；API 仅作排障旁路              |
| M2–M6      | 验收要点           | **补详细技术方案**（拓扑 / 包 / Topic / 步骤 / 验收）         |
| 真机域隔离      | DOMAIN=42      | 仿真控制域 `ROS_DOMAIN_ID=43`；真机域仍 **42**；**禁止混用** |




### 0.2 v1.1 → v1.2（仍有效）

主锚点 Go2→FR3；E 序列引入 M0–M6；Go2 真机后置。世界模型 SSOT：`external/world_model/docs/FR3*.md`。

---



## 一、当前进度（手动更新）



### 1.1 主路径（FR3 融合 · 必须完成）


| ID     | 场景                                            | 节点       | 映射 F1  | 状态  | 完成日         |
| ------ | --------------------------------------------- | -------- | ------ | --- | ----------- |
| **E0** | 代码仓库 + 网络 + 环境安装                              | ws-01/02 | —      | ✅   | 2026-08（环境） |
| **M0** | `external/world_model` 挂载 + 版本钉扎表可填           | ws-02    | F1-0   | ✅   | 2026-08-03  |
| **E1** | Skeleton 全流程冒烟                                | ws-02    | （编排基线） | ✅   | 2026-08-03  |
| **M2** | Isaac+ROS2 FR3 Hello：Δpose + LowStateFeedback | ws-02    | F1-2   | ⬜   |             |
| **M3** | RunManager 归档一次 FR3 控制仿真 `run`                | ws-02    | F1-1   | ⬜   |             |
| **M4** | 录 1 条可回放（日志轨或 LeRobot）                        | ws-02    | F1-3   | ⬜   |             |
| **M5** | Mid 最小：Template MidGoal + stub/Oracle         | ws-02    | F1-4   | ⬜   |             |
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
│   Isaac Sim/Lab + ROS2 Bridge（官方或自研适配）                 │
│        FR3 + Hand + 桌面（M2 极简 / M4+ Scene v0）             │
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
5. 官方 Isaac 场景/资产可用；**验收场景规格**以实验室 Scene / 本文为准。



### 2.4 包与进程规划（目标名，实现时可微调）


| 组件                                | 建议位置                               | M2     | M3+      |
| --------------------------------- | ---------------------------------- | ------ | -------- |
| `embodied_lab_msgs`               | `ros2/`                            | ✓ 扩展编译 | ✓        |
| `franka_sim_bridge`               | `ros2/` 新包                         | ✓ MVP  | ✓        |
| `embodied_lab_bringup` FR3 launch | `ros2/`                            | ✓      | ✓        |
| `m2_franka_hello` / Mid 脚本        | `lab_platform/scripts` 或 `ros2` 节点 | ✓      | → Mid 节点 |
| RunManager + isaac/ctrl-sim 入口    | `lab_platform/`                    | —      | ✓        |
| Isaac 场景 USD / Lab 任务             | `tasks/tabletop_pickplace_v0/`（待建） | 极简     | Scene v0 |


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


| 包                                | 状态                            |
| -------------------------------- | ----------------------------- |
| `embodied_lab_msgs`              | 真实；需按 TECH-02 v1.2/v1.3 扩展并重编 |
| `go2_*`                          | 回归保留                          |
| `franka_sim_bridge` + FR3 launch | **待建（M2 关键）**                 |




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



### 6.1 目标

在 **lab-ws-02 · DOMAIN 43** 上，用与真机一致的 ROS2 控制语义：

1. 加载 FR3 + Hand（官方资产）+ 极简桌面（可无杯碗）
2. 发布相对 Δpose，末端移动约 **5 cm**
3. 订阅并打印 `LowStateFeedback` 最小字段
4. 无新令时 **HOLD**（保持最后指令或刹停，可配置）

**不强制**当日接 RunManager（→ M3）。

### 6.2 场景策略


| 项               | M2 规定                            |
| --------------- | -------------------------------- |
| 机器人资产           | Isaac **官方 FR3 + Hand** USD/URDF |
| 场景              | **极简**：固定基座 + 平面桌即可              |
| 是否用官方完整 demo 场景 | **不强制**；可借官方 launch/桥组件，验收以本文为准  |
| Scene v0 杯碗相机   | **M4+** 再对齐 `FR3_Scene_v0`       |




### 6.3 软件架构

```text
终端 A：Isaac Sim/Lab（带 ROS2 bridge 或 isaac 侧 ros 节点）
终端 B：ros2 launch ... franka_ctrl_sim.launch.py
         - franka_sim_bridge
         - （可选）safety stub
终端 C：python m2_franka_hello.py
         - 发布 1～N 次 TaskSpaceCommand
         - 打印 low_state
```


| 层级     | M2 实现                | Topic（device 段 `franka_01`）             |
| ------ | -------------------- | --------------------------------------- |
| Mid 替代 | `m2_franka_hello` 脚本 | pub `/skill/franka_01/intent`           |
| Low    | `franka_sim_bridge`  | sub intent；pub low_state / joint_states |
| 物理     | Isaac + bridge       | 内部 API；**不**对 Mid 暴露                    |
| 安全     | 软件限幅 + expire HOLD   | 可先无完整 F6S                               |




### 6.4 消息契约（验收用最小集）

**下行** `embodied_lab_msgs/SkillIntent`（`skill_mode=task_space`）：

```text
ee_delta[6] = {dx,dy,dz,droll,dpitch,dyaw}   # 基座系相对；M2 测 dx=+0.05
gripper ∈ [0,1]
control_mode = POSE(1) 或 IMPEDANCE(2)
expire_ms = 150–200
frame_id = "fr3_link0"   # 或与资产一致的基座 frame
device_id = "franka-01"
```

**上行**（可用临时自定义 msg / JSON over String，但字段名冻结；优先 `LowStateFeedback.msg`）：

```text
ee_pose_actual, ee_pose_desired
q[7], gripper_width
tracking_error, contact_flag?
safety_event, backend="isaac_sim", latency_ms
```

时钟默认：`control_hz≈50`（bridge 内），脚本侧可 10 Hz 发令；`record_fps` 留到 M4。

### 6.5 Isaac ↔ ROS2 桥（实现选项）

按可用性**自上而下选一**，选定后写入钉扎表：


| 选项                               | 说明                                           | 适用     |
| -------------------------------- | -------------------------------------------- | ------ |
| **A. 官方 Isaac ROS / 场景 ROS2 组件** | 与 Isaac 6 + Jazzy 组合匹配时优先                    | 少自研    |
| **B. 自研** `franka_sim_bridge`    | 进程内调 Isaac Lab API，两端用 rclpy 出 TECH-02 Topic | 官方桥难装时 |
| **C. 旁路（不计入 M2 通过）**             | 纯 API 无 ROS2                                 | 仅排障    |


**M2 正式通过必须走 A 或 B（ROS2 主路径）。**

### 6.6 推荐仓库落点

```text
ros2/src/
  embodied_lab_msgs/          # 扩展 SkillIntent / LowStateFeedback
  franka_sim_bridge/          # Low + Isaac 适配
  embodied_lab_bringup/
    launch/franka_ctrl_sim.launch.py
lab_platform/scripts/
  m2_franka_hello.py          # 发 Δpose + 打印反馈
  m2_env_pin.md               # 手填版本钉扎
docs/ 或 data/notes/
```



### 6.7 执行步骤（ws-02）

```bash
# 0) 域与环境
export ROS_DOMAIN_ID=43
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source /opt/ros/jazzy/setup.bash

# 1) 编译消息与 bridge（首次）
cd ~/project/embodied__ai_lab/ros2
colcon build --symlink-install --packages-up-to franka_sim_bridge embodied_lab_bringup
source install/setup.bash

# 2) 启动 Isaac（按本机安装方式；示例）
# 官方桥：按钉扎文档启动带 ROS2 的 FR3 场景
# 自研桥：先起 Isaac/Lab，再起 bridge 节点

# 3) 启动控制图
ros2 launch embodied_lab_bringup franka_ctrl_sim.launch.py \
  device_id:=franka-01 backend:=isaac_sim

# 4) Hello
cd ~/project/embodied__ai_lab/lab_platform
source .venv/bin/activate
# 保证能 import rclpy / embodied_lab_msgs（与 INFRA-01 相同注意事项）
python scripts/m2_franka_hello.py --dx 0.05 --domain 43
```



### 6.8 验收标准（M2）


| #   | 标准                                                                                           |
| --- | -------------------------------------------------------------------------------------------- |
| 1   | `ROS_DOMAIN_ID=43`；`ros2 topic list` 可见 intent / low_state（或约定名）                             |
| 2   | 末端沿基座 x（或文档声明轴）移动约 **5 cm**，可重复                                                              |
| 3   | 打印字段齐：`ee_pose_*`、`q[7]`、`gripper_width`、`tracking_error`、`safety_event`、`backend=isaac_sim` |
| 4   | 停止发布后进入 HOLD（无持续漂移）                                                                          |
| 5   | `m2_env_pin.md`（或等价）记录 Isaac Sim/Lab、桥方案 A/B、驱动、日期                                           |




### 6.9 失败排查


| 现象              | 处理                                    |
| --------------- | ------------------------------------- |
| 无 topic         | 域是否 43；是否 source install；Isaac 桥是否起   |
| 臂不动             | bridge 日志；限幅；IK 失败；单位 m/rad           |
| DDS 奇怪设备        | 是否误用 42；防火墙/多网卡 Cyclone 配置            |
| rclpy 与 venv 冲突 | 参照 INFRA-01：系统 ROS Python 与 venv 混用策略 |


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

1. **替换 StubIsaacLauncher**：不要假 sleep；改为调用 launch/脚本并等待退出码。
2. **RunManager 仍不跑 Mid 逻辑**；只管生命周期。
3. `/system/run_context` 在 DOMAIN 43 发布（与真机同 msg）。
4. 产出目录：`data/runs/<run_type>/<run_id>/` + `manifest.json`。



### 7.4 目标命令形态

```bash
export ROS_DOMAIN_ID=43
lab --data-root ~/embodied-ai-lab-data ctrl-sim run \
  --device franka-01 \
  --scene tabletop_pickplace_v0 \
  --profile m2_hello
# 或扩展既有：lab isaac run --kind ...（须标明 ctrl-sim / domain 43）
```



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
| 1   | msg 扩展 + `franka_sim_bridge` MVP | colcon 过 |
| 2   | **M2** CTRL-SIM Hello            | §六.8     |
| 3   | **M3** Run 归档                    | §七.5     |
| 4   | **M4** 录回放                       | §八.4     |
| 5   | **M5→M6**                        | §九 / §十  |


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
| **v1.3** | 2026-08-03 | **ws-02 双模式**；CTRL-SIM=ROS2 DOMAIN 43；**M2–M6 详细技术方案** |


---

*INFRA-02 v1.3 | Phase 1 · FR3 控制仿真同构闭环*