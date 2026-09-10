# L1 Strategy Runtime 需求分析 v0（基于开源框架全量调研）

| 属性 | 内容 |
|------|------|
| **文档编号** | RES-L1-REQ-01 |
| **版本** | v0.2.1 |
| **日期** | 2026-08-14 |
| **状态** | working-draft · **S0/并环/LeRobot 身份已确认**（2026-08-14）；供 L1 Framework Design 输入；非实现规格 |
| **上位** | [PLAN-CHARTER-01](../plan/lab_charter_v0.md) · [PLAN-STRUCT-01](../plan/lab_strategy_runtime_structure_v0.md) |
| **依据** | [RES-OSS-01](./oss_framework_survey_v0.md) · [`oss_notes/`](./oss_notes/) · [PLAN-STRUCT-01](../plan/lab_strategy_runtime_structure_v0.md) |
| **问卷** | [`oss_notes/_questions.md`](./oss_notes/_questions.md) |
| **本仓锚点** | `strategy_runtime/` · CTRL-SIM E2E PASS · B 轨 LeRobot v3 · `PolicyBackend` MVP |
| **v0.2** | 对照现码与开源证据下调过满表述；收口切片顺序与成功标准 |

---

## 1. 这份文档要回答什么

STRUCT 已经钉死了三层叠放与 L1 代码落点，但尚未把「L1 框架」从原则推进到可评审的需求表述。开源调研的目的不是挑选一个仓库来 fork，而是回答：

> 在**已经拥有 Lab OS（L0）与 Isaac/ROS 同构（L2-Low）**的前提下，Strategy Runtime 必须稳定哪些运行时能力，才能同时容纳规则 Mid、Oracle、ACT/DP，并在不推翻架构的前提下长出语言条件与世界上下文？

因此本文先做**生态归类与矛盾分析**，再导出需求；需求用「问题 → 证据 → 本仓含义 → 需求陈述」的链条写出，避免变成功能愿望清单。

下游文档应是 **L1 Framework Design v0**（模块、接口、演进切片）。本文不规定目录拆分细节，也不批准立刻开相机/ACT 编码。**四文件夹拆包（PLAN-SR-B 的 B0）不是框架前置。**

### 1.1 相对现码的诚实表（v0.2）

下列名称在 STRUCT / 本文 v0.1 里容易被读成「已有半个框架」。对照 `strategy_runtime/`，目标与现状必须分开：

| 名称 | 目标态（本文需求） | 现状（2026-08-14） |
|------|-------------------|-------------------|
| `PolicyObs` | 带 feature 声明的投影配置（state / images\* / 可选语言） | 8 维 dataclass：`q[7]+gripper_width`；无投影器 |
| World Context | 可替换只读服务；策略面与评测面分离 | `SceneTargets`（YAML）+ 静态 PoseStamped Oracle（**非** Isaac 物体 GT） |
| PolicyBackend | 同一控制环内可切换 | 工厂能识别名字；`template`/`oracle_servo` 的 `act()` 直接 HOLD；真干活的是 `mid_template` |
| 控制环 | Mid 调度器与策略后端可仲裁 | **两条环**：`mid_template` vs `policy_rollout`，无仲裁 |
| chunk | 后端可预测一段；环内切成 intent | `PolicyAction` 单步 `ee_delta`；B 轨 action 亦为 `ee_delta[6]+gripper` |
| 谓词引擎 | 可机读成功；2s hold 等 L2 参数 | `eval_pickplace` 为运动代理 + 几何净空；`success_hold_enforced: false` |
| TaskSpec | 与观测分离的任务条件 | `scene.yaml` 已有 `task_language_default`，Runtime / export **未消费** |
| 相机声明 | Task Pack 单一 schema | `cameras: []` 与顶层 `camera:` 几何块并存 |

Design 若把左列当已实现，会在脚本袋上叠 ACT。v0.2 以下需求按**右列起步**书写。

---

## 2. 开源生态在告诉我们什么（概括）

把 P0/P1 十一份笔记放在一起看，这些项目并不是「十一套互相可替换的 L1」，而是覆盖了四类不同的问题。若把它们都当成「策略框架候选」，设计会立刻失焦。

### 2.1 四类角色，而不是一张排行榜

**（1）学习栈与策略插件母本 — LeRobot，辅以 robomimic / Diffusion Policy / RDT**

这一类解决的是：演示如何变成可训练样本、策略如何以统一接口训练与推理、动作以何种时间结构（单步 vs chunk）交给控制环。  
LeRobot 把 Dataset v3、Processor、`PreTrainedPolicy`（`predict_action_chunk` / `select_action`）和可选远程推理绑在一起，是当前与本仓 B 轨**契约最近**的母本。robomimic/DP 证明 modality 分解与 horizon 三角（`n_obs_steps` / `horizon` / `n_action_steps`）是 IL 的长期稳定语义；RDT 把同一语义推到「语言 + 多图 + state → 扩散 chunk」，说明 chunk 族后端会长期存在，不只是 ACT 特例。

对 L1 的含义是：Runtime 的策略边界应长成**可插拔后端**，而不是长成「再实现一个 LeRobot」。训练可以外挂官方 CLI，但**推理期的观测投影、chunk 消费、与 Mid/HOLD 的衔接**必须是本仓一等公民。

**（2）仿真 Env / 任务注册底座 — robosuite、ManiSkill、Isaac Lab、RoboCasa**

这一类解决的是：场景如何实例化、观测/动作空间如何声明、成功与终止如何定义、（可选）大规模并行与资产库。  
它们内部往往把「世界」和「任务」揉在同一个 `Env.step` 里。Isaac Lab 的 Manager 化（Observation/Action/Recorder）是这条路线的精致形态：仿真进程内完成观测组装、动作施加与录制钩子。

对本仓的含义是双重的。一方面，CTRL-SIM **刻意**走了另一条轴——Isaac ↔ ROS2 桥 ↔ 外部 Mid——因此不能把 `ManagerBasedRLEnv` 嵌进 `strategy_runtime` 当作「有了框架」。另一方面，这些仓共同强调的**声明式任务元数据**（obs_mode、control_mode、max steps、成功条件、相机键）必须在 L2 Task Pack 与 L1 消费契约上有对应物，否则策略与场景会靠口头约定耦合。

**（3）语言—多任务与通才条件 — LIBERO、OpenVLA、Octo（及 RoboCasa 的帧级指令标注）**

这一类把「任务」从隐式环境名推到**可条件化的输入**：语言嵌入、goal image、或逐帧 subtask 指令。策略签名从 `obs → action` 扩展为 `obs + task → action`（Octo 的 `create_tasks` 是最干净的表述之一；OpenVLA 则极简为 `image + instruction`）。

对 L1 的含义不是「现在就上 VLA」，而是：若 Framework 把观测字典写死成「只有 proprio」，语言与目标条件将只能以破坏性改接口的方式进入。需求层必须现在就承认 **TaskSpec / 条件槽位**，哪怕第一期取值为空。

**（4）数据供给与扩增 — MimicGen，以及 RoboCasa/Isaac Mimic 的规模化采数**

这一类不定义在线智能，却定义「特权状态」（物体位姿、子任务边界）如何服务于离线生成。它提醒我们：Oracle/GT 与策略观测不是同一个接口；A 轨可以拥有 B 轨训练时不可用的字段。L1 需要能**消费**经治理的上下文，而不是把 SDG 管道自身做成 Runtime 核心。

### 2.2 跨项目反复出现的稳定语义

剔除商标与物理引擎差异后，真正反复出现、且与本仓路径相容的语义只有少数几条：

1. **观测是结构化字典，且按模态声明**（rgb / low_dim / language…），而不是一个隐式向量。  
2. **策略与执行频率解耦**：学习后端常预测一段（ACT/DP/RDT）；控制环按自身频率消费。对本仓这是 TECH-02 纪律（慢环 intent + 快环执行），不是「所有开源都输出 chunk」（OpenVLA 为单步 token）。单步 = 长度为 1 的可执行段。  
3. **归一化 / 相对—绝对动作 / processor 与权重同版本**：否则「能 load 不能复现」。  
4. **任务条件与场景资产可分离声明**：语言、goal、成功谓词不应写死在网络类里。  
5. **几乎没有仓提供可与本仓对等的实验治理**（run_id、PreFlight、Index、DOMAIN）。开源强在智能与数据，弱在「算数」。这反证 STRUCT 的分层是正确压力，而不是额外负担。

### 2.3 开源普遍不提供、必须由本仓自持的部分

调研中的「缺口」同样构成需求边界：

- **跨进程、同构安全的控制语义**（intent + expire + HOLD）——LeRobot Robot / Isaac Lab Manager 默认同进程假设与此不同。  
- **World Context 作为一等运行时服务**——开源多为「当前 obs dict」；对象槽位、谓词、约束若存在，往往散落在任务代码或离线 `datagen_info` 里。  
- **A/B 双轨互链的实验 OS**——必须继续留在 L0；L1 只能产生可被 L0 挂载的证据（`mid_steps`、谓词结果），不能私建第二套归档。

这三点决定了：L1 框架的「完整性」不来自复刻某一开源仓的目录树，而来自**在开源已验证的策略/数据语义之上，补上情境与控制纪律**。

---

## 3. 从调研到本仓问题的张力

需求不是从笔记条目直接翻译，而是从下列张力中挤压出来的。

### 张力 A：学习栈的「胖」与 Runtime 的「瘦」

LeRobot 同时包含 Dataset、Robot、Env、Train、Async Server。若 L1 为了「好用」把这些全部吸入 `strategy_runtime`，会重新制造一个弱治理的小 LeRobot，并与 ROS 同构冲突。  
若 L1 瘦到只剩「调一下 `select_action`」，则 chunk 队列、观测投影、与 MidGoal/HOLD 的关系会再度散落在脚本里——这正是 STRUCT 要消灭的私造。

**化解方向：** L1 拥有**推理期编排与情境投影**；Dataset 布局与正式 export/Index 属 L0；训练循环允许外挂，但 checkpoint 的特征契约由 L1/L0 共同登记。

### 张力 B：Env 内闭环 vs 桥接闭环

ManiSkill / Isaac Lab / robosuite 证明 Env 内闭环工程效率高。本仓 Phase-1 已用桥接闭环换取真机同构与 DOMAIN 治理，且 E2E 已 PASS。  
因此 L1 需求必须假设：**世界步进不在 L1 进程内**；L1 通过 LowState / 图像话题 / Oracle 话题阅读世界，通过 SkillIntent 写回。Isaac Lab 的 ObservationManager「分组投影」值得借鉴的是**思想**，不是把 Manager 搬进 Python 包依赖。

### 张力 C：现在的 state MVP vs 必然到来的视觉 / 语言 / chunk

`lerobot_state` 证明了 Backend 插槽可用，但所有 P0/P1 视觉与 VLA 笔记都表明：下一步特征面会变宽。若 Framework 以「MLP 的输入维」为中心建模，ACT/RDT/OpenVLA 每一家都要打补丁。  
若以 **PolicyObs（投影配置）+ TaskSpec（条件）+ 可执行段（长度 1 或 N）** 为中心，当前 8 维 dataclass 只是一种投影实例，必须换表示，而不是往上加两个可选字段。

### 张力 D：World Context 研究愿景 vs 开源可借实现极少

STRUCT §3 描述了状态/物体/约束/谓词/记忆/前向。开源几乎不提供对等运行时；MimicGen 的物体位姿是离线特权。  
需求分析不能假装「先抄一个 WM 框架」，也不能把静态 YAML Oracle **自称**为世界模型。应要求 L1 **先把 Context 建成可替换的只读服务界面，并分成策略面 / 评测面**；第一期实现 = `LowState` + `SceneTargets` + 可选 Oracle 位姿。感知/学习 WM 后挂。R10 的覆盖面不得一次铺满 STRUCT §3（记忆/前向仍属 R12）。

### 张力 E：任务成功判据放在哪

Env 库喜欢把成功写在任务类里；学习库往往只关心 reward/demo。本仓需要可机读 `eval.json` 与场景 ε，且正式实验走 L0。  
因此成功谓词引擎属于 **L1 共性能力**，判据参数与几何目标属于 **L2**，是否算进 Index 的「正式结论」属于 **L0 挂载**。

---

## 4. L1 需求分析（带推导）

下列每条需求都绑定调研证据与边界。表述采用「L1 应当…」；涉及 L0/L2 处标明**协作需求**（非把 L0 工作写进 L1）。

### 4.1 定位需求：L1 是「情境 + 技能 + 策略插件」的运行时，不是第二实验 OS，也不是仿真 Env

开源强项分裂为学习栈与仿真栈两端，本仓已用 STRUCT 选择第三条路。调研只是加强了这一判断：没有任何 P0/P1 仓库同时提供「可审计 run」+「ROS 同构 HOLD」+「可插拔 ACT/VLA」。

**R1 — 职责闭合。** L1 必须闭合：世界上下文的组装与查询、MidGoal/技能步进、成功/失败/HOLD 语义、PolicyBackend 的推理期适配。L1 不得拥有：`run_id` 发放、PreFlight、GPU/设备锁、Index 权威、DOMAIN 选择、A/B 轨落盘权威路径。

**R2 — 进程假设。** L1 默认作为 L0 拉起的 lab 子进程运行（已落地），其接口设计必须容忍「策略进程 ≠ 桥接进程」，以便日后异步/远端推理（LeRobot async、OpenVLA deploy 已证明该模式）而不改 Low 消息族。

### 4.2 观测与任务条件：从「向量」升级为「可投影的结构化契约」

LeRobot feature 声明、robomimic modality、Octo observation/task 二分、ManiSkill obs_mode，共同说明：策略输入是**配置出来的**，不是网络 `__init__` 里写死的。

**R3 — PolicyObs 是投影配置，不是当前 8 维 dataclass 的别名。** L1 应定义稳定的投影配置：从 World Context（策略面）与传感器缓冲生成带 feature 名的观测（至少支持 state；images\* / 语言为配置项）。`lerobot_state` 所用 dataclass 是一种实例。Design 必须换表示（配置驱动的 dict / feature 表），禁止在现结构上堆可选字段冒充契约。state-only 必须在增加图像后仍能只投影 state。

**R4 — TaskSpec 契约。** L1 应定义与观测分离的任务条件对象（空 / 语言指令 / goal 位姿或图像引用 / 枚举技能目标）。OpenVLA/Octo/LIBERO 表明条件与观测生命周期不同。**槽位在 L2 已存在**（`task_language_default`）；缺口是 Runtime 与 B 轨 export 尚未消费。第一期允许策略忽略该字段，但挂载点必须打通，而不是「类型还不存在」。

**R5 — 历史窗是 Obs 配置，不是后端私货。** `n_obs_steps` / history 在 DP、ACT、Octo wrapper、Isaac ObservationManager 中反复出现。L1 应在 Obs 组装层支持可配置短历史（含 pad 语义的概念位置），避免每个 Backend 私建 deque 且无法与 export 对齐。第一期可只声明配置项、实现长度为 1。

### 4.3 动作与时间结构：控制环只认 intent + HOLD；chunk 是后端能力

ACT、DP、RDT 将「预测地平线 / 执行地平线」分裂；LeRobot 用队列或 temporal ensemble 消费。OpenVLA 偏单步 token——因此 **chunk 不是跨仓共识，而是本仓控制纪律下的后端能力**。任何后端最终都进入可过期的 intent 流；单步 = 长度为 1 的可执行段。

**R6 — 可执行段推理面（含长度为 1）。** PolicyBackend 应能产出「当前可发给 Low 的一段」（N≥1），并可选保留完整预测供调试。对齐 LeRobot 的 `select_action` / `predict_action_chunk` 或 DP 的 `action` vs `action_pred`。**消费发生在 L1**：切成逐步 `SkillIntent`；策略频率可以低于控制频率。禁止把 chunk 张量直接当 Low 消息。

**R7 — 与 HOLD 合流。** 开源普遍缺少与 TECH-02 同族的断流停机。L1 必须规定：策略无输出、队列耗尽且未刷新、推理超时、或显式失败时，进入 HOLD（或等价安全意图），而不是默发零动作或抛到无人处理的异常路径。现码仅在 `policy_rollout` 路径落实了 HOLD；`mid_template` 有超时/成功语义，两条路径尚未统一。

**R8 — 动作空间适配是 L1 胶水，schema 是 L2/L0 元数据；ACT 的第一风险在此。** 后端输出（关节、EE delta、绝对位形、token 反归一化）映射到 SkillIntent 的适配器挂在 L1。`action_schema`、fps、相机键由 Task Pack 声明并由 L0 export 写入 Dataset meta。**接入 ACT 的厚度主要在动作空间与坐标系，不是网络结构**：当前 B 轨为 `ee_delta[6]+gripper`，LeRobot ACT 默认更接近关节或绝对位形。若不一致，必须先改 DATA-MAP / `scene.yaml`（C1），不能只在 L1 里偷偷 remap。

### 4.4 Processor / 统计量：复现性需求，不是训练细节

LeRobot Processor、DP `LinearNormalizer`、OpenVLA `norm_stats`/`unnorm_key`、Octo `dataset_statistics` 都表明：没有与权重绑定的预处理，就没有可复现 rollout。

**R9 — 预处理与 checkpoint 同生命周期。** L1 加载策略时必须能加载对应的 normalize / 相对—绝对动作 / tokenizer 统计（实现上可委托 LeRobot 对象）。L0 ArtifactHub 登记策略资产时，应能指向这些附属物（协作需求）。不允许「只拷 safetensors、在脚本里手写均值方差」。

### 4.5 World Context：把 STRUCT §3 落成可替换服务，而不是一个大 dict

调研显示「上下文」在开源中通常塌缩为当前观测；而本仓已有 Oracle GT、SceneTargets、谓词评估的萌芽。缺口在于它们尚未被收束为稳定服务面，且 **不得把静态 YAML 封装成假世界模型**。

**R10 — Context 分两面，第一期覆盖面收窄。** L1 应提供只读查询界面，分成：

- **策略面**（可进 B 轨 / PolicyObs）：本体关节与 ee、夹爪、run 元数据；图像在 C1 就绪后加入。  
- **评测/特权面**（默认不进训练特征）：命名物体位姿（当前为 scene.yaml 名义值，非 Isaac GT）、谓词所需几何、场景句柄。

Policy 与技能通过投影读策略面，不直接解析 USD、不直接读 Index。第一期**不**要求 Memory / Forward / 完整物体槽位服务（见 R12）。

**R11 — 特权上下文与策略上下文分离。** MimicGen `datagen_info` 与 A 轨 GT 说明：训练不可用的字段可以存在于运行/生成路径。Framework 需允许评测面字段存在，并由 L0 export 过滤（协作）。静态 Oracle 位姿默认走评测面。

**R12 — 前向预测与记忆为可选后端，不为第一期阻塞。** 开源无可直接搬迁的运行时 WM。需求只要求挂钩点（例如 Context 上的 memory 槽、可选 `world_model_*` Backend），不要求第一期实现预测头。P1 笔记（OpenVLA/Octo/RDT 等）为接口级扫描，**不足以为 VLA 适配层定实现规格**。

### 4.6 Mid / 技能 / 谓词：开源最弱、本仓必须最强的共性

Env 库把成功塞进任务类；学习库常忽略技能阶段。本仓已有 template Mid 与 pickplace 谓词，调研反而证明这块**不能外包给开源**。

**R13 — Mid 与 Policy 必须能进同一控制环。** Goal 队列、有界步进、超时、技能切换、与 PolicyBackend 的仲裁（何时听模板、何时听策略）应是 L1 模块。第一期仲裁允许「由 profile 二选一」，但必须是**同一调度入口**（同一 lab 子进程或同一正式 CLI 入口），而不是继续维持 `mid_template` 与 `policy_rollout` 两条互不相认的环。没有本条，成功标准「换 Backend 不换桥」无法验收。各 profile 脚本分叉不得再增加第三条环。

**R14 — 成功谓词引擎。** 谓词计算在 L1；阈值与目标位姿来自 L2；结果以可机读形式交给 L0 挂载为 eval 证据。现码为运动代理，Design 须标明哪些谓词是代理、哪些是物体级（后置）。LIBERO BDDL / ManiSkill evaluate 的启发是「成功与策略网络解耦」，不是引入 BDDL 引擎。

### 4.7 后端谱系：用同一套 Runtime 挂载多条算法路

**R15 — Backend 谱系与注册。** 工厂/注册表按稳定字符串挂载：`template` / `oracle_*` / `lerobot_state` /（目标）`lerobot_act` / `lerobot_diffusion` / 远期 `openvla`·`rdt`·`world_model_*`。换后端不改 L0，不改 Low msg（STRUCT §6 原则，调研未提供反例）。

**R16 — 训练入口可外挂；仓内 MLP 只当回归夹具。** 允许 `lerobot_train` 等外部训练器；L1/L0 需要的是特征契约、登记与 rollout 路径。不要求在 L1 内复刻 Hydra/JAX 训练 OS。**裁定草案（待确认）：** `strategy_runtime.policy_train` 的 numpy MLP 仅用于 state 路径回归；ACT 训练不进 `strategy_runtime` 核心（L0 子进程调 LeRobot CLI，或只登记外部作业 + 回填 Index——STRUCT §11.2 #6 在 Design 闭合）。

### 4.8 与 L0/L2 的协作需求（作为 L1 可行性前提）

这些不是 L1 内部功能，但若缺失，上述 R3–R9 无法落地——调研里所有视觉/ACT 路径都卡在数据与任务声明上。

**C1 — L0：** 多相机与视频轨进入 A→B export；stats 与特征名和训练一致；ArtifactHub 支持「权重 + processor/stats」（现有 MLP checkpoint **尚未**满足）；异步/子进程编排保持。ACT 若改 action_schema，DATA-MAP 必须先升版。  
**C2 — L2：** Task Pack 四件套稳定——注册名/scene_id、资产 pin、观测/控制/fps/`action_schema`、成功参数。**须统一** Dataset 用的 `cameras` 列表与场景几何用的 `camera:` 块（现状双轨并存）。`task_language_default` 保留并允许被 TaskSpec 消费。  
**C3 — 明确不做（开源诱感清单）：** 以 LeRobot/robosuite/ManiSkill/Isaac Lab 替换 ROS2 或 run 治理；HDF5 取代 LeRobot v3 主路径；JAX Octo 作为默认训练运行时；将 MimicGen/RoboCasa 资产库作为当前主依赖；把 FUSION 文中的 `WorldBackend∈L1` 当作现行结构（该表述过时，WorldBackend 属 L2-Low / 桥）；以拆 `mid/policy/world` 文件夹冒充框架完成。

---

## 5. 需求的优先级切片（仍是分析，不是排期看板）

若把 R1–R16 一次性工程化，会重蹈「先搭目录再找灵魂」。结合现码落差，**S1（视觉/ACT）不得早于 S0 的调度面**；收束 Mid 不是 ACT 之后的美化工作。

**切片 S0 — Framework 语义 + 同一控制环（文档 + 薄接口，仍不写 ACT）。**  
钉死类型与边界，而不是文件夹：

1. PolicyObs 投影配置（state-only 是一种配置）  
2. TaskSpec（先透传 `task_language_default`）  
3. 可执行段：长度 1 或 N，失败 → HOLD  
4. Context 两通道：策略面 vs 评测面  
5. **Mid 调度器与 PolicyBackend 同一入口**（profile 二选一即可）

对应 R1–R8、R10–R11、R13、R15 的接口级部分。没有 S0，相机与 ACT 会在脚本层分叉。

**切片 S1 — 视觉与 ACT 可加载闭环。**  
仅在投影配置与 **action_schema 风险写清** 之后。补齐图像进入 PolicyObs、`lerobot_act`（或等价）、processor 随 Artifact 加载；L0/L2 履行 C1/C2。ACT 第一风险是动作空间与相机数据轨，不是网络。这是 STRUCT 示范路径「Scene + Dataset + ACT」的缺口变现。

**切片 S2 — Oracle/谓词收束（可与 S1 并行，不得晚于「无调度器就上 ACT」）。**  
把已有 `mid_template` / Oracle / `eval_pickplace` 收进 S0 调度面与 Context 两通道（R13–R14、R11）。标明谓词哪些是代理。

**切片 S3 — 条件化与异步。**  
语言/goal TaskSpec 深化、远端推理客户端（R4、R2）；VLA/RDT 仅作 Backend 适配。P1 笔记不够当实现规格。

世界模型预测头、MimicGen 式 SDG、RoboCasa 级场景、**B0 目录大拆**放在更后：拆包是 Design 的结果，不是前置。

---

## 6. 对「L1 框架」成功标准的工作定义（可证伪）

在进入 Design 文档前，用调研校准什么叫「框架做成了」——否则容易用「新建了几个文件夹」冒充完成。下列均相对**现码缺口**书写。

L1 Framework 在本仓语境下成立，当且仅当同时满足：

1. **同一正式入口可切换后端**：同一 Task Pack 下，profile 能在 template / oracle / `lerobot_*` 间切换；Low 话题不变。允许「`lab ctrl-sim run` 为唯一入口」或「第二条正式入口写进 SOP」——但不得再是两条互不相认的脚本环。**现状：不满足。**  
2. **换投影不换 Mid 纪律**：增加图像字段时，`lerobot_state` 仍只投影 state；HOLD / 超时路径不改。  
3. **Context 可替换且分面**：策略代码无 `read_usd` / 写死 prim；物体 GT 走评测面。静态 YAML Oracle 不得自称世界模型。  
4. **学习复现可解释（协作 L0）**：正式 checkpoint 在 Index 能指到特征名、processor/stats、action_schema、源 `run_id`。**现状：MLP 仅有权重文件。** 本条 L1 不能单独闭环。  
5. **不引入第二实验 OS 或第二控制总线**：不依赖 `isaaclab` / `robosuite` 包；LeRobot 仅为可选 extra；不以拆目录冒充完成。

若某设计满足目录美观但破坏 1–5 任一条，则相对本调研而言是失败的。

---

## 7. 结论：Design 文档应优先写清的接口面

综合全文，开源调研把 L1 需求收敛为**五张必须先画清的界面**，而不是一个算法选型结论：

| 界面 | 一侧 | 另一侧 | 调研主要来源 | v0.2 口径 |
|------|------|--------|----------------|-----------|
| PolicyObs / TaskSpec | Context 策略面 + 传感器 | PolicyBackend | LeRobot · Octo · LIBERO · OpenVLA | 投影配置；语言槽位已在 L2 |
| 可执行段 + HOLD | PolicyBackend | **同一** Mid / Low Client | ACT · DP · RDT · TECH-02 | chunk 是后端能力；单步=长度 1 |
| Processor/Stats | Artifact | Backend.load | LeRobot · DP · OpenVLA | 现 MLP 未满足 |
| World Context API | 策略面 / 评测面 | Mid · 投影器 · 谓词 | STRUCT · MimicGen（反例） | 第一期收窄；非假 WM |
| Backend Registry + 调度入口 | 配置/字符串 | 模板 · Oracle · 学习后端 | 全学习栈 + 现码双环 | 先并环，再 ACT |

算法选择（先 ACT 后 VLA、是否上 RDT）属于界面之上的插件决策；**界面本身**才是 Framework Design 的正文。

---

## 8. 下一步

1. ~~确认本文 v0.2~~（2026-08-14：S0、LeRobot 身份、方案 A）。  
2. 撰写 **L1 Framework Design v0**（服从 [宪章 v1.1](../plan/lab_charter_v0.md)：World Context 可替换服务面为正文，不是再包一层 `select_action`）。  
3. Design 评审通过前：不启动 B0 目录大拆、不启动相机/ACT 主开发。

---

## 9. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-08-10 | 首版：基于 P0+P1 全量笔记的概括与需求分析 |
| v0.2 | 2026-08-14 | 审视修订：诚实表；PolicyObs=投影配置；chunk=后端能力；Context 两面；先并环再 ACT；B0 非前置；成功标准可证伪 |
| v0.2.1 | 2026-08-14 | 宪章确认：S0 同意；LeRobot=算法库非内核；单一 `ctrl-sim run`；可开 Design |
| v0.2.2 | 2026-08-14 | 对齐宪章 v1.1：Design 正文=Context 服务面，非策略库外壳 |

---

*RES-L1-REQ-01 · 研究推导 · 不直接驱动采购或编码*
