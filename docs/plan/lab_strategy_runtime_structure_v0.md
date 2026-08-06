# 实验室平台 × 策略运行时 × 任务包：结构设计 v0

| 属性 | 内容 |
|------|------|
| **文档编号** | PLAN-STRUCT-01 |
| **版本** | v0.2 |
| **日期** | 2026-08-05 |
| **状态** | draft（讨论基线） |
| **上位** | [PLAN-FUSION-01](./platform_wm_fusion_plan_v0.md) · INFRA-02 · TECH-09 |
| **本地研究资料** | `external/world_model/`（挂载，不进本 Git） |
| **外部对标** | Hugging Face [LeRobot](https://github.com/huggingface/lerobot)（学习栈 / Dataset v3；非 Lab OS） |

---

## 0. 一句话定调

**三层叠放，不揉并。**

1. **Lab OS**：管实验如何被合法地跑完、留下证据（执行过程与治理）。  
2. **Strategy Runtime（策略运行时）**：管具身智能如何理解并作用于物理世界（策略与情境基础能力）。  
3. **Task Pack（任务包）**：管「这一题」的场景资产、目标剧本与可选专用模块。

**世界模型**不是与 Lab OS 平行的第二套「大框架商标」，而是 Strategy Runtime 的一种（推荐）组织形态：以可计算的**物理世界上下文**（状态 / 约束 / 目标谓词 / 技能作用接口 / 可选预测）为核心来装配 High·Mid·Low。

即使不使用「世界模型」一词，**Strategy Runtime 这一层仍然必须存在**，否则场景开发会反复私造 Mid/情境/落盘约定。

与 PLAN-FUSION「叠放，不揉并」一致，并细化 L1 的内涵：L1 = Agent Control Runtime = 本结构中的 Strategy Runtime。

与 LeRobot 的关系（摘要）：**学其数据标准与可插拔策略闭环，不学其弱治理与自研总线替代 ROS。** 目标形态是  
`Lab OS（算数）× Strategy Runtime（情境与技能）× LeRobot（学习与数据标准）`，而非三选一。详见 [§13](#13-与-lerobot-的关系借鉴与边界)。

---

## 1. 总体结构

```text
┌──────────────────────────────────────────────────────────────────┐
│ L0  Lab Operating Framework（实验室运行平台 · 本仓库 lab_platform） │
│  RunManager · PreFlight · Locks · Index · Artifact · SOP         │
│  Recorder(A) · Exporter(B→LeRobot v3) · Eval harness（挂到 run）    │
│  关注：run_id、门禁、资源、归档、录制挂载、安全策略入口               │
└────────────────────────────┬─────────────────────────────────────┘
                             │ 编排：start / stop / pin / archive
                             │ 注入：run_context · data-root · domain
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ L1  Strategy Runtime（策略运行时 / 具身能力层）                     │
│  可称：Agent Control Runtime · 世界模型控制栈（一种实现）            │
│  High（薄）· Mid（技能/情境）· 世界上下文 · 技能库 · 成功谓词引擎     │
│  PolicyBackend ∈ {template, oracle, lerobot.*, wm.*}（可插拔）      │
│  关注：物理世界上下文 + MidGoal/Skill 接口 + 可选前向预测             │
│  代码落点：external/world_model（设计）+ 本仓 ros2/lab 适配实现       │
└────────────────────────────┬─────────────────────────────────────┘
                             │ 契约：MidGoal / SkillIntent / LowState
                             │      ObjectPose · scene 句柄 · 观测约定
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ L2  Task Pack + 本体/场景资产                                      │
│  tasks/<scene_id>/ · USD · scene.yaml · profile 剧本 · 专用策略    │
│  Low 桥：franka_sim_bridge / 真机 bridge · WorldBackend            │
│  关注：这一题怎么摆、怎么判成功、用 Runtime 的哪些能力                │
└──────────────────────────────────────────────────────────────────┘
```

### 1.1 与 PLAN-FUSION L0/L1/L2 对照

| PLAN-FUSION | 本文 | 说明 |
|-------------|------|------|
| L0 Lab Operating Framework | L0 Lab OS | 同义 |
| L1 Agent Control Runtime | L1 Strategy Runtime | 同义；强调「非仅世界模型品牌」 |
| L2 本体与场景 | L2 Task Pack + Backend | 场景升格为可版本化 Task Pack |

---

## 2. 职责矩阵（宪法级）

| 层 | 负责 | 禁止 |
|----|------|------|
| **L0 Lab OS** | 谁能开跑；GPU/设备锁；PreFlight；`run_id` 生命周期；统一落盘根与 Index；挂载 Recorder(A) / Exporter(B)；Eval harness；发/清 `/system/run_context`；SOP/审计入口；策略/数据集资产注册（私有「类 Hub」） | 实现抓取策略、Mid 情境推理、前向世界模型、Scene 几何算法；把训练循环塞进 RunManager 核心 |
| **L1 Strategy Runtime** | High/Mid 控制语义；世界上下文（状态/物体/谓词）；MidGoal 调度；朝目标有界技能步进；技能库；成功/失败/HOLD 语义；PolicyBackend 插件（含 LeRobot 策略适配）；可选前向 WM / Oracle；异步 rollout 客户端（可选） | 绕过 `run_id` 私自写「主结论」数据；直改急停硬件策略；把某一 Task 写死进 Runtime 核心；用自研总线替代 ROS TECH-02 |
| **L2 Task Pack** | `scene_id` 资产与 pin；格点/杯碗/相机外参；任务语言；`action_schema` / `fps` / `cameras`；profile 选择的 MidGoal 剧本；专用检测/策略权重 | 自建第二套 run 归档规范；私改 DOMAIN/急停；绕过 TECH-02 另搞控制协议（除非登记扩展） |

### 2.1 两类「共性」不要混层

| 共性 | 归属 | 例子 |
|------|------|------|
| **实验共性** | L0 | run、锁、录制挂载、Index、DOMAIN 门禁 |
| **具身/策略共性** | L1 | Mid 运行时、ObjectPose 契约、技能步进、谓词引擎 |
| **任务特异** | L2 | 红杯格点、这句指令、该 checkpoint |

---

## 3. 「物理世界上下文」在结构中的位置

L1 的核心不是某一个网络，而是对策略可消费的世界接口：

```text
World Context (L1)
├── State s          关节/ee/接触/安全/run 元数据
├── Objects          位姿与类别（Oracle / 感知）
├── Constraints      工作空间、软限、可供性提示
├── Goals / Predicates  要达成的状态（cup_in_bowl…）
├── Skill I/O        MidGoal ↔ SkillIntent / gripper
├── Memory（可选）    跨步失败原因、关系
└── Forward（可选）   若动作 a，世界如何变（世界模型预测头）
```

**世界模型** = 用显式/隐式状态 +（可选）预测 + 规划/技能，把上述上下文组织起来的一种 Runtime 后端。  
规则 Mid、Oracle、VLA、LeRobot Policy 都可以挂在同一 L1 接口上，作为不同 backend。

> **术语辨析**：LeRobot 语境里的 World Model 多指**学习策略中的预测头**；本文「世界模型 / 物理世界上下文」指 **L1 运行时组织方式**。二者可叠加（WM backend），不可混为一谈。

---

## 4. 仓库与进程落点（结合现状）

### 4.1 目录映射（目标态）

```text
embodied__ai_lab/
├── lab_platform/                 # L0 为主
│   ├── run_manager / preflight / index / cli
│   ├── ctrl_sim/                 # L0 对 CTRL-SIM 的编排适配（launch/录制挂载）
│   │   recorder / replayer       # L0 数据能力（挂到 run 上）
│   │   mid_template.py           # 过渡：薄 Mid（应逐步上收/对齐到 L1）
│   └── templates/                # 可引用的默认 profile（或改链到 tasks/）
├── ros2/
│   ├── embodied_lab_msgs/        # 跨层契约（SkillIntent / LowState / RunContext…）
│   ├── franka_sim_bridge/        # L2-Low：设备桥（也可视为 Runtime 的 Low 适配）
│   └── embodied_lab_bringup/     # L0/L2 启动图
├── tasks/                        # L2 Task Pack（待建主战场）
│   └── tabletop_pickplace_v0/
│       scene.yaml · scene_pin.md · usd 引用 · profiles/
├── docs/plan/                    # 融合与本结构
└── external/world_model/         # L1 设计 SSOT（挂载）；实现可逐步迁入本仓 packages
```

### 4.2 CTRL-SIM 进程视图（lab-ws-02 · DOMAIN 43）

```text
lab CLI / RunManager (L0)
  → PreFlight / locks / run_dir / run_context
  → attach|launch franka_ctrl_sim (Low 桥)
  → 挂 Recorder (L0)
  → 拉起 Strategy Runtime 入口 (L1)：profile = m5_template | m5_pickplace | …
       → 读 tasks/<scene>/scene.yaml + 世界上下文
       → MidGoal 调度 → SkillIntent
  → Low bridge → Isaac JointStates
  → finish：清 context · Index · manifest
```

### 4.3 与当前里程碑的对应

| 已完成 | 落在哪一层 |
|--------|------------|
| M2 Low 契约 + bridge | L2-Low + 契约 |
| M3 run 归档 / run_context | L0 |
| M4 A 轨录回放 | L0 数据能力 |
| M5 薄 Mid 模板 | **L1 最小萌芽**（仍偏脚本，待平台化） |
| Scene v0 升级（下一步） | L2 Task Pack + L1 朝目标技能 |

---

## 5. 层间契约（最小集）

### 5.1 L0 → L1

| 项 | 约定 |
|----|------|
| 启动 | `lab ctrl-sim run --scene <id> --profile <name>` |
| 注入 | `run_id`、`ROS_DOMAIN_ID`、`data_root`、device_id |
| 话题 | `/system/run_context`（TRANSIENT_LOCAL） |
| 期望产物 | 退出码；`logs/` 下 Runtime 自描述文件（如 `mid_steps.json`） |

### 5.2 L1 → L2-Low

| 项 | 约定 |
|----|------|
| 命令 | `SkillIntent`（`skill_mode=task_space`，ee_delta / gripper / expire_ms） |
| 反馈 | `LowStateFeedback` |
| 禁止 | 策略直出未限幅关节扭矩绕过 Low（Phase-1） |

### 5.3 L1 ↔ L2-Scene

| 项 | 约定 |
|----|------|
| 配置 | `tasks/<scene_id>/scene.yaml` |
| 目标源 | ObjectPose（Oracle/感知）话题或 Runtime 查询接口 |
| 剧本 | profile YAML：MidGoal[] + 谓词参数 |

### 5.4 L0 数据（双轨 · 架构一等公民）

双轨写进架构，不是附录。职责与互链：

| 轨 | 用途 | 路径 / 形态 | 谁写 |
|----|------|-------------|------|
| **A 运行日志** | 评测、复盘、Lab「主结论」 | `runs/.../logs/low.jsonl` | L0 Recorder（订 L1/L2 公开话题） |
| Mid 步进 | Runtime 自描述 | `logs/mid_steps.json` | L1 |
| Eval | 可机读成功谓词结果 | `logs/eval.json`（目标态） | L0 Eval harness / L1 谓词引擎 |
| manifest | 汇总与互链 | `manifest.json` | L0；**强制**链到 A/B/L1/L2 产物 |
| **B 学习集** | 训练（混训 / 流式 / 共享） | LeRobot Dataset **v3**（Parquet + MP4 + meta） | L0 Exporter（或 record 时可选双写） |

**互链规则（纪律）**：

1. A 轨是 CTRL-SIM / 真机回归与审计的主证据；B 轨是学习入口。  
2. 经 `lab` 正式产生的 B 轨 Dataset，manifest **必须**含 `lerobot_dataset_path`（或等价字段）与源 `run_id`；无链接不算正式学习数据。  
3. 从历史 A 轨补导出 B 轨时，Exporter 写回 Index，并在源 run manifest 追加导出记录。  
4. Task Pack 的 `scene.yaml` 须声明可映射到 Dataset `meta/info.json` 的字段子集：`fps`、`action_schema`、`cameras`（可为空列表）。

字段映射草案与 CLI 见 [§13.4](#134-可执行借鉴清单)。

---

## 6. Strategy Runtime 内部结构（L1 展开）

```text
Strategy Runtime
├── High Adapter（可缺省）
│     TemplatePlayer | 键切 | 未来 VLM
├── Mid Runtime（共性 · 应平台化）
│     GoalQueue · TOTE/步进 · timeout · HOLD
│     bounded Δpose toward target
│     success predicate engine（ε 可配置）
├── World Context Services
│     state hub ← LowState
│     object hub ← Oracle / perception
│     scene handle ← scene.yaml
├── Skill Library
│     approach / grasp / lift / place / retreat …
├── Policy Backends（可插拔）
│     rules / template | oracle_servo | world_model_* | lerobot_* | …
├── Async Rollout Client（可选）
│     策略出 chunk / 目标；Low 仍按控制频率消费；断流 HOLD
└── Low Client
      publish SkillIntent · subscribe LowStateFeedback
```

**原则**：换 Policy Backend 不改 L0，不改 Low msg；只换 L1 内插件与 Task Pack 配置。

#### 6.1 PolicyBackend 一览（目标态）

| Backend | 来源 | 用途 |
|---------|------|------|
| `rules` / `template` | 现有 m5 | 调通、回归 |
| `oracle_servo` | Scene Oracle | 抓放闭环 |
| `lerobot_act` 等 | LeRobot | 学习基线 |
| `world_model_*` | 研究栈 | 情境 + 预测 |

L1 只稳定三件事：**观测特征、动作特征、步进/HOLD**；算法实现可外挂（含直接调用 LeRobot）。

#### 6.2 异步 action chunk（标准模式）

借鉴 LeRobot「预测与控制解耦」：

- Mid/策略输出短时域动作序列或目标；Low 仍以控制频率（如 ~50 Hz）执行。  
- 允许「策略进程 ≠ 桥接进程」（远端 GPU 可选）。  
- 与 TECH-02「慢环 intent + expire HOLD」同族：**策略频率 ≤ 控制频率；断流必须 HOLD**。  
- Phase-1 不强制复杂聚合函数；先钉死上述纪律即可。

---

## 7. Task Pack 结构（L2 标准骨架）

```text
tasks/tabletop_pickplace_v0/
├── README.md
├── scene.yaml              # 几何/格点/ε/Home；须含 fps / action_schema / cameras
├── scene_pin.md            # 本机 USD/prim 钉扎
├── assets/                 # 或引用 Nucleus/本地 USD 路径
├── profiles/
│   ├── m5_template.yaml    # 空载两步（回归）
│   └── m5_pickplace.yaml   # 抓放序列
└── (optional) nodes/       # 仅本任务需要的节点
```

Task Pack **可以**脱离 L0 单测（直接 `python` / `ros2 run`）；  
**凡要进评测/数据池的正式实验，必须经 L0 入口**，以便强制 `run_id`、录制与 Index。

平台「示范路径」（对标 LeRobot 社区飞轮的最小可跑通）：

> **官方 FR3 Scene v0 + `m5_pickplace` + 一次可导出的 Dataset + 一个 ACT 基线**

---

## 8. 开发者体验（目标）

```bash
# 业务单测（可无 L0）
python3 -m strategy_runtime.mid --profile tasks/.../m5_pickplace.yaml

# 正式控制/回归实验（必须 L0）
lab --data-root ~/embodied-ai-lab-data ctrl-sim run \
  --scene tabletop_pickplace_v0 \
  --profile m5_pickplace \
  --record [--export-lerobot] --keep-launch

# 学习闭环（挂在 L1；由 L0 编排正式实验）
lab data export --run-id <id> --format lerobot-v3
lab policy train --dataset <path|id> --backend act
lab policy rollout --checkpoint <path|id> --scene tabletop_pickplace_v0
lab eval --suite tabletop_pickplace_v0 --run-id <id>
```

制度口令：

> **可以玩（单测）；算数必须走 lab。**

入口分流（SOP 须写清）：

| 入口 | 用途 |
|------|------|
| `lab ctrl-sim run` | 控制回归、场景/Mid 验收、A 轨证据 |
| `lab data export` / `policy train|rollout` | 学习实验；产物仍经 L0 Index / manifest |
| `lab eval` | 可机读谓词 → `eval.json`；类比 LeRobot `lerobot-eval` |

---

## 9. 演进路线（与场景升级衔接）

| 阶段 | 动作 | 层级 |
|------|------|------|
| **P0（当前后）** | 建 `tasks/tabletop_pickplace_v0`；Scene USD + pin；文档级钉死 A/B 轨职责与互链 | L2 + 纪律 |
| **P1** | ObjectPose Oracle；Mid「朝目标有界步进」从脚本收入 Runtime 模块；`low.jsonl`→LeRobot v3 字段映射草案 | L1 + 数据 |
| **P2** | `m5_pickplace` 全序列；成功谓词接 Scene ε → `eval.json` | L1+L2 |
| **P3** | L0 强制 scene.yaml 门禁；默认 `--record`；manifest 互链；`lab data export --format lerobot-v3` | L0 |
| **P4** | 相机观测约定；PolicyBackend 插槽（`lerobot_act` / WM/VLA）；可选异步 rollout | L1+L0 |
| **P5** | 策略/数据集进 Index（私有类 Hub）；M6 SOP：控制回归 vs 学习实验入口分流 | L0 制度 |

M6（SOP）仍是 L0 流程验收，可后置，不阻塞 P0–P2。  
LeRobot 相关能力按 [§13.4](#134-可执行借鉴清单) 的 P0/P1/P2 切分，可与上表并行推进。

---

## 10. 设计原则清单（评审用）

1. **叠放不揉并**：Lab OS 不实现智能；Runtime 不替代实验治理。  
2. **世界模型可选、Runtime 必选**：没有 WM 也要有情境/技能层。  
3. **契约稳定、插件可换**：TECH-02 + MidGoal + scene.yaml 为稳钉。  
4. **正式实验强制 L0**：单测自由，归档不自由。  
5. **Task Pack 可版本化**：对照实验禁止悄悄换桌换物（Scene 规格纪律）。  
6. **CTRL-SIM 同构**：DOMAIN 43；真机 42；禁止混域。  
7. **数据双轨一等公民**：A 评测复盘、B 训练；manifest 强制互链。  
8. **借 LeRobot 学闭环，不借弱治理**：Dataset + PolicyBackend + eval；不替代 ROS 同构与 Lab OS。  

---

## 11. 待决问题（下一轮讨论）

1. L1 代码主仓：长期留在 `external/world_model` 实现，还是在本仓建 `strategy_runtime/` 包？  
2. ObjectPose 用新 msg，还是先 JSON/`PoseStamped` 约定？  
3. Mid 运行时进程：独立 ROS 节点 vs lab 子进程（Phase-1 建议先子进程/节点二选一钉死）。  
4. 「主结论」数据白名单：哪些文件没有 L0 manifest 链接则评测拒收？  
5. B 轨：record 时双写 vs 事后 `lab data export` 为主？Phase-1 建议后者，降低控制路径耦合。  
6. `lab policy train`：本机子进程调用 LeRobot CLI，还是仅登记外部训练作业 + 回填 checkpoint？  

---

## 12. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-08-05 | 首版：L0/L1/L2 叠放；世界模型定位为 L1 组织形态；对齐 PLAN-FUSION 与 M2–M5 现状 |
| v0.2 | 2026-08-05 | 增补与 LeRobot 的关系（借鉴/边界/清单）；双轨数据与 PolicyBackend/eval/DX 对齐 |

---

## 13. 与 LeRobot 的关系：借鉴与边界

### 13.1 定位对照

| 维度 | LeRobot | 本平台（L0 × L1 × L2） |
|------|---------|------------------------|
| 主问题 | 机器人**怎么学**（采数→训→推） | 实验**怎么管** + 具身**怎么控/组织情境** |
| 数据 | LeRobotDataset v3 + Hub | A 轨 jsonl（已有）+ B 轨对接 v3（目标） |
| 策略 | ACT / Diffusion / VLA / WM 策略库 | Mid 薄模板已有；策略后端待平台化 |
| 硬件 | 自有 middleware，偏低成本臂 | ROS2 TECH-02 + FR3 bridge；CTRL-SIM 同构 |
| 实验治理 | 弱（episode / 任务描述为主） | 强方向：run_id、PreFlight、锁、Index |
| 社区 | Hub 共享模型与数据 | 实验室内部复现与审计（Index ≈ 私有 Hub） |

**结论**：借鉴重点在**产品化能力与架构套路**（数据契约、可插拔策略、学闭环、评测入口），不是照搬仓库形态或用学习库吞掉 L0。

### 13.2 值得借鉴（做什么）

| 优先级 | 借鉴点 | 落到本平台 |
|--------|--------|------------|
| **P0** | 数据契约产品化（schema、meta/stats、v3 存储） | A/B 双轨 + manifest 互链；`lab data export --format lerobot-v3`；Task Pack 声明 `fps` / `action_schema` / `cameras` |
| **P0** | 垂直打通的用户路径 `录→存→训→推→评` | 在三层之上补齐 DX：`run --record` → export → `policy train|rollout` → `eval`；train/rollout 挂 L1，由 L0 编排 |
| **P1** | 策略后端可插拔 | L1 `PolicyBackend`：`template` / `oracle_servo` / `lerobot_*` / `world_model_*` |
| **P1** | 统一评测入口 | Scene 成功谓词 → `eval.json`；`lab eval --suite ...`（类比 `lerobot-eval`） |
| **P1** | 推理与控制解耦 | 异步 action chunk；策略频率 ≤ 控制频率；断流 HOLD（§6.2） |
| **P2** | Hub / 注册中心思维 | Index 扩展：`datasets` / `policies` / `scenes`；artifact 含 id、schema 版本、producer `run_id` |
| **P2** | 最小可跑通示范 | FR3 Scene v0 + `m5_pickplace` + 可导出 Dataset + ACT 基线 |

### 13.3 明确不照搬（不做什么）

| LeRobot 做法 | 为何不直接抄 |
|--------------|--------------|
| 自研 robot middleware 替代 ROS | 已押注 ROS2 同构真机；对 LeRobot **适配** Dataset/Policy，不替换 TECH-02 |
| 以 IL/VLA 为中心组织一切 | 仍需 MidGoal / 谓词 / 世界上下文；学习只是 L1 后端之一 |
| 弱 run 治理 | 多用户、审计、安全门禁是 L0 核心价值，不可稀释 |
| 过度绑定低成本臂生态 | 主路径是 FR3；**Dataset 兼容**优先于驱动兼容 |
| 单一巨型学习库吞并平台 | 保持 L0/L1/L2 边界；LeRobot 作为外挂能力，不是第二套 Lab OS |

### 13.4 可执行借鉴清单

**与 Scene 升级同期（文档 / 契约）**

- [ ] 定义 A/B 轨职责与互链规则（本文 §5.4；写入 SOP）  
- [ ] `low.jsonl` → LeRobotDataset v3 字段映射草案（FR3 + 可选相机）  
- [ ] Task Pack 必须声明 `action_schema` / `fps` / `cameras`

**紧随其后（实现）**

- [ ] `lab data export --format lerobot-v3`（主路径；可选 `--export-lerobot` 双写）  
- [ ] L1 `PolicyBackend` 接口 + 首个 `lerobot_act` 适配（可先离线训、在线 rollout）  
- [ ] 评测器：Scene 成功谓词 → `eval.json` 进 run / Index  

**再往后**

- [ ] 策略 / 数据集进 Index（类 Hub）  
- [ ] 异步 rollout 模式（策略机 vs 桥接机）可选  
- [ ] SOP：区分「控制回归实验」与「学习实验」入口  

### 13.5 叠放后的目标形态（一句话）

```text
L0 Lab OS
  run / PreFlight / locks / Index
  Recorder(A) + Exporter(B→LeRobot v3) + Eval harness
           │
L1 Strategy Runtime
  World Context · Mid scheduler · Skill I/O
  PolicyBackend ∈ {template, oracle, lerobot.*, wm.*}
  Async rollout client（可选）
           │
L2 Task Pack + Low
  tabletop_pickplace_v0 · TECH-02 bridge · Isaac/Real
```

**最该借鉴**：数据标准 + 可插拔策略 + 一条学闭环。  
**最不该借鉴**：用学习库吞掉实验治理和 ROS 同构控制。

---

*PLAN-STRUCT-01 v0.2 · 与 PLAN-FUSION-01 配套使用*
