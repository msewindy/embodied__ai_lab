# Phase 1 验证测试方案 v1.2

| 属性 | 内容 |
|------|------|
| **文档编号** | INFRA-02 |
| **版本** | v1.2 |
| **维护人** | R2 |
| **依据** | [PLAN-FUSION-01](../plan/platform_wm_fusion_plan_v0.md)（**工作基线**）· [governance_index_v1.md](../org/governance_index_v1.md) · [TECH-14 As-Built](../architecture/platform_architecture_as_built_v1.md) · [INFRA-01](./env_setup_checklist_v1.md) · [TECH-02](../software/ros2_interface_v1.md) · [TECH-04](../software/version_matrix_v1.md) |
| **主锚点设备** | `franka-01`（**Franka Research 3 + Hand**） |
| **主场景** | `tabletop_pickplace_v0`（Isaac 仿真优先） |
| **回归设备** | `quadruped-01`（Unitree Go2）— **不计入 Phase-1 主交付** |
| **用途** | Phase 1：Walking Skeleton → **FR3 Isaac 最小融合闭环**；Go2 仅作多本体回归 |

---

## 〇、方向变更摘要（v1.1 → v1.2）

| 项 | v1.1 | v1.2 |
|----|------|------|
| 主验收本体 | Go2 | **FR3（Isaac）** |
| Phase-1 完整交付 | E1～E7（含 Go2 真机） | **M0～M6 + E1**（仿真融合闭环） |
| Go2 E2/E3 | 主路径 | **历史已通过 → 回归集 R-Go2** |
| Go2 E4/E7 真机 | Phase 1 | **Phase 2+ / 回归**（围栏急停门禁前禁止动态真机） |
| Isaac E5 | `velocity_rough_go2` | **`tabletop_pickplace_v0` / FR3 Hello** |
| 上层依据 | 仅 W1 | **+ PLAN-FUSION-01 工作基线** |

世界模型控制语义与数值 SSOT：本地挂载 `external/world_model/docs/FR3*.md`（不进本仓库）。

---

## 一、当前进度（手动更新）

### 1.1 主路径（FR3 融合 · 必须完成）

| ID | 场景 | 节点 | 映射 F1 | 状态 | 完成日 |
|----|------|------|---------|:----:|--------|
| **E0** | 代码仓库 + 网络 + 环境安装 | ws-01/02 | — | ✅ | 2026-08（环境） |
| **M0** | `external/world_model` 挂载 + 版本钉扎表可填 | 开发机/ws-02 | F1-0 | ⬜ | |
| **E1** | Skeleton 全流程冒烟 | ws-02 | （编排基线） | ✅ | 2026-08-03 |
| **M2** | Isaac FR3 Hello：Δpose 动 5cm + LowStateFeedback | ws-02 | F1-2 | ⬜ | |
| **M3** | RunManager 归档一次 FR3 仿真 `run` | ws-02 | F1-1 | ⬜ | |
| **M4** | 录 1 条可回放（日志轨或 LeRobot 主路径） | ws-02 | F1-3 | ⬜ | |
| **M5** | Mid 最小：Template MidGoal + stub/Oracle | ws-02 | F1-4 | ⬜ | |
| **M6** | PreFlight/SOP：成员按清单独立开跑仿真实验 | ws-02 | F1-5 | ⬜ | |

**Phase-1 主交付（融合 Go）**：E0 + M0 + E1 + **M2～M6** 全部通过。  
**一句话出口**（与 PLAN-FUSION-01 一致）：

> 任意成员能按 SOP 启动一次「FR3 桌面抓放仿真实验」：有 `run_id`、有 High/Mid/Low 最小链路、有可回放数据。

### 1.2 历史 / 回归路径（Go2 · 不阻塞主交付）

| ID | 场景 | 状态 | 说明 |
|----|------|:----:|------|
| **E2** | ROS2 三包编译（ws-01） | ✅ 2026-06-16 | 保留；msg 扩展后需重编 |
| **E3 / R-Go2** | Go2 sim real_bringup | ✅ 2026-06-16 | **回归**：证明多本体契约未退化 |
| **E4** | Go2 跨机 Topic | ⬜ | Phase 2+ / 回归 |
| **E6** | checkpoint 同步 ws-02→ws-01 | ⬜ | 策略部署前置；可与 M3 后并行 |
| **E7** | Go2 真机 bringup | ⬜ | **围栏+急停验收前禁止** |

---

## 二、框架骨架：真实 vs 占位（对照表）

### 2.1 Python 框架 `lab_platform/`

| 模块 | 实现 | 状态 | 说明 |
|------|------|:----:|------|
| **RunManager** | `run_manager/manager.py` | **真实** | PreFlight → Lock → 目录 → 执行 → Artifact → Release |
| **IndexService** | `index/service.py` SQLite | **真实** | runs / artifacts / locks / lineage |
| **PreFlightGate** | `preflight/gate.py` | **真实** | PF 子集；读 registry yaml |
| **ResourceScheduler** | `scheduler/locks.py` | **真实** | device_lock |
| **ArtifactRegistry** | `artifacts/registry.py` | **真实** | Policy / Demo / Eval / Calibration |
| **Pipeline A 收录** | `pipelines/pipeline_a.py` | **真实** | Isaac 产出扫描与注册 |
| **IsaacLauncher** | `stubs/isaac_launcher.py` | **Stub→替换中** | M2/M3 须接真 Isaac 或明确适配器 |
| **RealRuntime 主体** | `stubs/real_runtime.py` | **Stub** | 真机 FR3 在 Phase 2 |
| **bringup（sim）** | `pipeline_c/bringup_runner.py` | **真实（Go2）** | FR3 bringup 检查项待扩展 |
| **Ros2Bridge** | `pipeline_c/ros2_runtime.py` | **混合** | `--ros` 时真发 `/system/run_context` |
| **Agent Runtime（三层）** | （待建） | **未实现** | Mid/High **不得**写入 RunManager 核心 |

### 2.2 ROS2 栈 `ros2/`

| 包 | 状态 | 说明 |
|----|:----:|------|
| `embodied_lab_msgs` | **真实** | TECH-02；v1.2 起含 TaskSpace 消息（实现可分批落地） |
| `go2_driver_bridge` | **真实** | **回归**用 |
| `embodied_lab_bringup` | **真实** | Go2 launch 已有；FR3 launch 待加 |
| `franka_driver_bridge`（名可改） | **待建** | Phase-1 仿真期可用 Isaac 侧 WorldBackend 代替真 ROS Bridge |

**Topic 命名**：台账 `device_id` 用 `franka-01` / `quadruped-01`；ROS 段 `-` → `_`。

### 2.3 Phase-1 明确不做

- Cosmos / LDA / 完整在线 V-JEPA  
- H1/H2 研究主结论  
- 工业跨夹具完整工位  
- 真机相机采购与完整真机 P0r  
- Go2 真机 E4/E7 作为主交付  

---

## 三、验证要得到什么（主路径产物）

| 层级 | 验收产物 | 含义 |
|------|----------|------|
| **挂载/钉扎** | M0：`external/world_model/README.md` 可读；manifest 含 Isaac/驱动版本 | 资料与环境可追溯 |
| **L0 编排** | E1：`smoke_test.py` ALL PASSED | Run 生命周期可重复 |
| **Low 契约** | M2：FR3 末端按 Δpose 移动；反馈字段齐 | Agent Runtime Low 可用 |
| **编排×场景** | M3：`run_id` + FR3/`tabletop_pickplace_v0` manifest | 平台托住仿真实验 |
| **数据** | M4：至少一条可回放轨迹 | 采数通路 |
| **Mid 薄** | M5：Template MidGoal 驱动短序列 | 非完整五模块 |
| **可运营** | M6：他人按 SOP 独立开跑 | 框架期「标准实验流程」 |

---

## 四、主路径执行手册（按序）

> 环境安装见 [INFRA-01](./env_setup_checklist_v1.md)。版本钉扎见 [TECH-04 v1.2](../software/version_matrix_v1.md)。  
> FR3 控制/Scene 细节 SSOT：`external/world_model/docs/FR3验证框架详细设计与阶段计划.md` 等。

### M0 — 挂载与钉扎

> 说明见 [`external/README.md`](../../external/README.md)。**不进 Git / 禁止 Submodule**；仅本机 symlink。

**lab-ws-02（Ubuntu，与 `world_model` 同级时）**：

```bash
cd ~/project/embodied__ai_lab
chmod +x scripts/link_external_world_model.sh
./scripts/link_external_world_model.sh ~/project/world_model

# 校验
ls -ld external/world_model
test -f external/world_model/README.md && echo OK
```

手写等价：

```bash
cd ~/project/embodied__ai_lab
mkdir -p external
ln -sfn ../world_model external/world_model
```

**Windows 开发机**：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\link_external_world_model.ps1
Test-Path .\external\world_model\README.md
```

在 run manifest 模板中预留字段：`isaac_sim`、`isaac_lab`、`pytorch`、`nvidia_driver`、`device_id=franka-01`、`scene_id=tabletop_pickplace_v0`。

**通过**：挂载可读；钉扎表有人可填（允许先手填）。

---

### E1 — ws-02 Skeleton 冒烟

**目的**：确认 Python 框架在 ws-02 可独立运行（无需 ROS2）。

```bash
cd ~/project/embodied__ai_lab/lab_platform
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip && pip install -e .
python scripts/smoke_test.py
```

**通过**：`=== ALL SMOKE TESTS PASSED ===`  
**ws-02 禁止**：日常 shell 设 `ROS_DOMAIN_ID`；不跑 ROS2 节点。

---

### M2 — Isaac FR3 Hello（Low 契约）

**前置**：ws-02 上 NVIDIA 驱动、Isaac Sim **6.0.x**、Isaac Lab **3.0 线**已按 TECH-04 安装；FR3 资产可用。

**目标**（对应世界模型 P-1 / F1-2）：

1. 仿真中 FR3 + Hand 加载  
2. 下发相对 Δpose（基座系）使末端移动约 **5 cm**  
3. 打印/记录 `LowStateFeedback` 最小字段：`ee_pose_actual`、`ee_pose_desired`、`q[7]`、`gripper_width`、`tracking_error`、`safety_event`、`backend=isaac_sim`  
4. 可演示 HOLD / 限幅（无新令保持或刹停）

**过渡实现**：允许独立脚本/`WorldBackend` 先跑通，**不强制**当日接满 RunManager。  
**通过**：动作可重复；反馈字段齐；版本写入本地笔记或草稿 manifest。

---

### M3 — RunManager 归档 FR3 仿真 Run

```bash
# 目标形态（命令名以实现为准；Stub 须替换或包装真 Isaac）
lab --data-root ~/embodied-ai-lab-data isaac run \
  --kind eval \
  --task tabletop_pickplace_v0 \
  --device franka-01
```

**通过**：

- Run status `completed`（或等价）  
- 存在 `run_id`；manifest 含 `device_id=franka-01`、`scene_id=tabletop_pickplace_v0`  
- index.db 可查到该 run  

> 若当日仍只能 Stub：可标「编排通路 OK」，**不计入** Phase-1 融合 Go；融合 Go 要求真仿真或真 WorldBackend 被编排。

---

### M4 — 录制与回放

- 以 `record_fps=10`（与 TECH-02 / 世界模型数据契约一致）录至少 **1** 条轨迹  
- 轨道：**运行日志** 或 **LeRobot v3** 至少打通一条主路径  
- 回放：动作误差「可接受」（人工目视 + 简单数值阈值即可）

**通过**：路径写入该 `run_id` 产物目录；可复现回放命令。

---

### M5 — Mid 最小（Template）

- 不要求完整五模块中层  
- 可用 TemplatePlayer / 键切注入 MidGoal 序列（APPROACH→… 或更短子集）  
- 情境可用 stub 或 Oracle（S1）；**不宣称 H1**

**通过**：至少 2 个 MidGoal 步进可观测；Low 仍只收 TaskSpaceCommand。

---

### M6 — SOP 独立开跑

- 文档化：从环境 activate → 启动仿真 → `lab ...` → 哪里看 `run_id`/产物  
- 非作者成员（或交叉角色）按清单完成一次 M3+M4 级实验  

**通过**：R1/R2 签字或纪要确认「可按 SOP 独立完成」。

---

### E6 — checkpoint 同步（可选并行）

策略部署前置；**不阻塞** M2～M5。

```bash
rsync -av ~/embodied-ai-lab-data/artifacts/policies/ \
  user@lab-ws-01:~/embodied-ai-lab-data/artifacts/policies/
```

---

## 五、回归手册：Go2（R-Go2）

> 以下保留自 v1.1，用于多本体回归；**完成与否不决定 Phase-1 融合 Go**。

### E2 — ws-01 ROS2 编译（已完成；msg 变更后重做）

```bash
cd ~/project/embodied__ai_lab/ros2
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 pkg list | grep -E 'embodied_lab|go2_driver'
```

### E3 — Go2 sim bringup（已通过 · 回归时重跑）

```bash
ros2 launch embodied_lab_bringup go2_bringup.launch.py \
  device_id:=quadruped-01 sim:=true
# 另终端：
lab --data-root ~/embodied-ai-lab-data ops bringup --device quadruped-01 --ros --sim
```

**通过**：`bringup_report.json` overall=pass；`quadruped-01: L1`。

### E4 / E7 — Go2 真机（Phase 2+）

围栏+急停物理验收前 **禁止**。步骤仍见历史：onboard `go2_bridge` → 跨机 `joint_states` ≥50Hz → `lab ops bringup --ros --no-sim`。

---

## 六、本周优先清单（ws-02）

| 序号 | 任务 | 验收 |
|:----:|------|------|
| 1 | **M0** 挂载 + 钉扎表 | README 可读 |
| 2 | **E1** `smoke_test.py` | ALL PASSED |
| 3 | 确认 Isaac Sim 6 / Lab 3 线可用 | 版本写入笔记 |
| 4 | **M2** FR3 Hello Δpose | 动 5cm + 反馈 |
| 5 | **M3→M4** Run + 录制 | run_id + 回放 |
| 6 | （并行）定 E6 同步方式 | 可选 |

**不要做**：把本周主攻改回 Go2 E4/E7；不要把 Mid 五模块做进 RunManager。

---

## 七、常见问题

| 现象 | 处理 |
|------|------|
| 找不到世界模型文档 | 跑 `scripts/link_external_world_model.ps1`；见 `external/README.md` |
| Isaac 与 ROS2 同机冲突 | ws-02 **不进** ROS 域；真机桥接只在 ws-01 |
| StubIsaac 假跑 | M3 融合 Go 不计数；优先换真 WorldBackend |
| `[StubReal]` / Go2 bringup 问题 | 仅回归时排查；见 v1.1 FAQ（numpy/rclpy/QoS） |
| 误走 Go2 主路径 | 对照本文 §〇；主交付以 §一.1 为准 |

---

## 八、相关文档

| 文档 | 用途 |
|------|------|
| [PLAN-FUSION-01](../plan/platform_wm_fusion_plan_v0.md) | 融合宪法与 F1 映射 |
| [INFRA-01](./env_setup_checklist_v1.md) | 安装清单（P1 将补 FR3 段落） |
| [TECH-02](../software/ros2_interface_v1.md) | TaskSpace / SkillIntent |
| [TECH-04](../software/version_matrix_v1.md) | 版本钉扎 |
| [TECH-14 As-Built](../architecture/platform_architecture_as_built_v1.md) | 架构与 Gap |
| `external/world_model/docs/FR3*.md` | FR3 控制与 Scene SSOT |

---

## 九、变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-06-16 | 首版；E2/E3 ws-01 已通过 |
| v1.1 | 2026-07-09 | 角色口径 R1–R3；对齐 W1 |
| **v1.2** | 2026-08-03 | **主锚点切 FR3**；引入 M0–M6；Go2→回归；对齐 PLAN-FUSION-01 |

---

*INFRA-02 v1.2 | Phase 1 验证方案 · 主路径 FR3 融合闭环*
