# LeRobot 源码笔记（RES-OSS-NOTE-01）

| 属性 | 内容 |
|------|------|
| **源码** | `~/project/oss_refs/lerobot`（本仓 `external/oss_refs` 软链） |
| **问卷** | [_questions.md](./_questions.md) |
| **本地 commit** | `22bd7a2`（浅克隆；以目录为准） |
| **上位** | [RES-OSS-01](../oss_framework_survey_v0.md) |
| **结论摘要** | 最值得借：**Dataset v3 契约 + Policy 抽象（chunk/queue）+ Processor 管线**。不借：实验治理、ROS 替代、把 Robot/Env 当 L1 核心。 |

---

## 0. 源码地图（读这些就够）

```
src/lerobot/
  datasets/          # LeRobotDataset / writer / reader / video — B 轨事实标准
  policies/          # PreTrainedPolicy + act/diffusion/… + factory
  processor/         # DataProcessorPipeline / PolicyProcessorPipeline
  robots/            # 真机 ABC：get_observation / send_action
  envs/              # 仿真/gym 侧配置与特征映射
  async_inference/   # gRPC PolicyServer / robot client（可选远程推理）
  scripts/           # train / record / eval / rollout CLI
  configs/           # PreTrainedConfig、TrainPipelineConfig
```

CLI 入口（包 entry）：`lerobot_train` / `lerobot_record` / `lerobot_eval` / `lerobot_rollout` 等。

---

## A. 架构切分

### A1 顶层划分

| 模块 | 职责 | 对本仓映射直觉 |
|------|------|----------------|
| `datasets` | Episode 存储、读写、Hub、stats | **L0** 数据契约 / export 目标 |
| `policies` + `processor` | 模型、归一化、相对/绝对动作 | **L1** PolicyBackend + 适配层 |
| `robots` / `envs` | 真机与仿真观测-动作接口 | **L0 桥 + L2 场景**；不是 L1 本体 |
| `scripts` / train config | 训练与采集 CLI | 部分进 **L0 lab CLI**，训练循环可挂 L1 |
| 无独立 Index/run_id | 实验治理弱 | **必须自建 L0**（已有） |

### A2 运行时上下文？

**没有**独立 World Context / 对象槽位模块。上下文 ≈ flat `RobotObservation` dict +（训练时）`EnvTransition` 里的 `complementary_data`。时空记忆若存在，藏在具体 policy 内部（如队列、chunk），不是一等公民。

### A3 策略与机器人之间的层

典型路径：

```
Robot.get_observation()  →  RobotObservation (dict)
        ↓ PolicyProcessorPipeline (preprocess)
batch: dict[str, Tensor]
        ↓ PreTrainedPolicy.select_action / predict_action_chunk
PolicyAction (Tensor)
        ↓ PolicyProcessorPipeline (postprocess)
RobotAction (dict) → Robot.send_action()
```

另有 `policy_robot_bridge`：motor 名 ↔ tensor 维映射。  
**层数清晰：Robot/Env | Processor | Policy** — 这是我们 L1 应保留的形状。

### A4 入口与生命周期

- **采集**：`lerobot_record` + Dataset writer  
- **训练**：`lerobot_train` + `TrainPipelineConfig`  
- **评测/rollout**：`lerobot_eval` / `lerobot_rollout`  
- **远程推理**：`async_inference.policy_server`（gRPC）

「一次实验」的权威身份在 LeRobot 侧偏 **dataset repo_id / checkpoint 目录**，不是我们的 `run_id` + Index。生命周期由各自 CLI 拥有，**无统一 PreFlight / ArtifactHub**。

### A5 映射到本仓（必填）

| 能力 | L0 | L1 | L2 |
|------|----|----|-----|
| LeRobot v3 目录布局 / export | ✅ 已有 `lerobot_export`；继续对齐 | 消费 Dataset | 任务元数据进 features |
| `run_id` / PreFlight / Index | ✅ 自建，不抄 | 只读契约 | — |
| Policy 训练/推理抽象 | CLI 编排可挂 lab | ✅ `PolicyBackend` + ACT 适配 | — |
| Processor（norm / rel-abs） | 可选落盘 stats | ✅ 管线归属 L1 | — |
| Robot ABC / 标定 | ✅ 真机/桥（未来 Phase-2） | 不实现 Robot | — |
| 相机进录制 | ✅ recorder / bridge | PolicyObs 用图 | Task 声明相机 |
| 场景 USD / 成功判据 | launcher / eval 钩子 | Oracle/eval 逻辑 | ✅ Task Pack |

---

## B. 数据与契约

### B1 Episode / 帧对象

`LeRobotDataset`（`datasets/lerobot_dataset.py`）封装：

- **meta**：`info.json`（shapes、keys、fps）、`stats.json`、`tasks.parquet`、`episodes/`  
- **data**：chunked **parquet**（帧级数值）  
- **videos**：按相机 key 分目录的 **mp4**，与 parquet 时间对齐  

帧在训练侧变成 `batch: dict[str, Tensor]`；约定键含 `observation.state`、`observation.images.*`、`action`、`action_is_pad` 等（见 `utils.constants`）。

### B2 视觉存取

- 视频：`videos/observation.images.<cam>/chunk-*/file-*.mp4`  
- 与 parquet 同步；支持 streaming encode、多种 video backend  
- **不是**把每帧 PNG 塞进 hdf5（与 robomimic 路线不同）

### B3 多相机 / 多模态

- Schema 由 `info` + feature 字典声明；多相机 = 多个 `observation.images.*` key  
- ACT 配置要求：至少一张图 **或** `observation.environment_state`；多图须同 shape  

### B4 归一化 / 相对绝对动作

落在 **`processor`**（`PolicyProcessorPipeline`），而非硬编码进每个 Policy：

- 归一化映射：`NormalizationMode` × `FeatureType`（STATE/VISUAL/…）  
- `RelativeActionsProcessorStep` / `AbsoluteActionsProcessorStep` 成对；从 checkpoint 反序列化后需 `_reconnect_relative_absolute_steps`  

**设计点**：pre/post processor 与权重一起版本化 — 我们 ArtifactHub 应考虑「权重 + processor 配置」同登记。

### B5 与本仓 `low.jsonl` → v3 的差距

| 已有 | 仍可能缺（进 L0 相机/ACT 时） |
|------|------------------------------|
| v3 目录、parquet、基本 state/action | 真实 `observation.images.*` 多路视频轨 |
| 训练用 `lerobot_state` MVP | `stats.json` 与 ACT 所需 VISUAL/STATE norm 一致 |
| | `tasks` / language 条件（中期） |
| | `delta_timestamps` / `n_obs_steps` 历史窗 |

---

## C. 策略接口

### C1 基类 `PreTrainedPolicy`（`policies/pretrained.py`）

抽象核心（概念上）：

- `forward(batch) -> (loss, loss_dict)` — 训练  
- `predict_action_chunk(batch) -> Tensor` — 整段 chunk  
- `select_action(batch) -> Tensor` — 环境一步（内部可队列）  
- `from_pretrained` / Hub 保存；可选 FSDP2 / PEFT  

子类必须声明 `config_class`、`name`。

### C2 Chunk 与队列（ACT）

`ACTPolicy`（`policies/act/modeling_act.py`）：

- `chunk_size`：模型一次预测的动作长度  
- `n_action_steps`：实际执行步数（≤ chunk）；队列耗尽再推理  
- 可选 `temporal_ensemble_coeff`：每步重推理并指数加权融合（此时 `n_action_steps` 须为 1）  
- **无**本仓式显式 `HOLD` 失败语义；异常即抛 / 停。安全停机在 Robot 层或调用方。

### C3 观测历史

`ACTConfig.n_obs_steps`：把「当前 + 回溯」步数的观测送入策略。Dataset 侧可用 `delta_timestamps` 对齐多时刻特征。  
**含义**：相机/state 录制必须保证时间戳足够支撑历史窗 — L0 recorder 契约。

### C4 注册

- `@PreTrainedConfig.register_subclass("act")`  
- `get_policy_class(name)`：约定从 `configuration_*` 推到 `modeling_*` 的 `*Policy`（懒加载，插件友好）  
- `make_pre_post_processors(...)` 与 policy 成对构造  

我们可对齐：**字符串 backend 名 → 类**，但登记进本仓 `policy_registry` / ArtifactHub，而非 HF Hub 独占。

### C5 接入 ACT 的最小依赖路径

**训练路径（理想）**：本仓 export 合格 v3 → 直接调 `lerobot_train --policy.type=act`（或薄封装）→ checkpoint。  

**推理路径（本仓 CTRL-SIM）**：

1. L0：相机 + state 写入与 export 对齐 feature 名  
2. L1：`PolicyBackend` 实现：`load(ckpt)` → preprocess → `select_action` → 映射为 Franka 命令（关节/笛卡儿以 Task 为准）  
3. **不要**把整个 `Robot` ABC 搬进 Isaac；用现有 bridge topic / Mid 进程。

适配层厚度：**中等** — 主要是 feature 名、归一化 stats、动作空间与控制接口三处胶水，而不是重写 ACT。

---

## D. 控制环与异步

### D1 默认同进程；可选远程

- 常见：record/eval 与 policy 同机同进程  
- `async_inference`：gRPC `PolicyServer` + robot client；obs 队列 `maxsize=1`（最新帧覆盖），有 fps / latency 配置  

对我们：Phase-1 保持 **lab 子进程 Mid**；远程推理是 C 轨以后选项，接口可预留「Obs in / Action chunk out」。

### D2 频率解耦

Server 侧 `fps`、`inference_latency`、`obs_queue_timeout`；chunk 执行在 client/控制环。  
**借鉴**：策略 Hz ≠ 控制 Hz 时用队列 + 超时，而不是阻塞 Isaac 主循环。

### D3 安全 / 标定

落在 `robots.Robot`：`calibrate`、`send_action` 可裁剪返回「实际下发动作」。  
仿真桥路径我们已有自己的安全叙事；**不要**用 LeRobot 标定体系替换 ROS/Franka。

---

## E. 任务与场景

### E1–E3

- 任务更多是 **dataset `tasks` + 配置**，不是重型 Task Pack  
- 成功判据 / USD 场景 **不在** LeRobot 核心  
- 对我们：`tabletop_pickplace_v0` **继续自建**；只对齐 feature 命名与 fps，不引进 LeRobot 任务 DSL  

---

## F. 时空上下文 / 世界模型

### F1–F2

- 基线：**无**对象级记忆、无显式 world model API  
- 仓内有个别研究向 policy（如 VLA / JEPA 相关目录），**不是**统一 Context 层  
- L1 设计预留挂钩（仅接口）：  
  - `ContextView` / `WorldState`：只读，由 Mid 组装  
  - `PolicyObs`：可从 Context 投影（state-only → +images → +memory）  
  - 禁止 Policy 直接读 USD/Index  

### F3 明确不抄

- 用 LeRobot 替代 ROS / run_id / PreFlight  
- 把 `robots/` 或 Isaac Env 塞进 `strategy_runtime` 核心  
- 为对齐而做完整 HF Hub 发布流程（本地 registry 足够）

---

## G. 对本仓的变更含义

### G1 对 L1 的 3 条可借鉴

1. **Policy 双入口**：`predict_action_chunk` + `select_action`（队列/ensemble 在后端内聚）  
2. **Processor 与权重同版本**：normalize / rel-abs 不散落在 train 脚本  
3. **Feature 声明驱动**：`input_features` / `output_features` 决定能否加载 ACT，而不是隐式 tensor 形状  

### G2 对 L0（相机/ACT 阶段）

- recorder / export：多相机视频轨 + 与 parquet 时间对齐  
- stats 导出与训练一致  
- rollout CLI 继续编排进程；不把 LeRobot Robot 当运行时  

### G3 对 L2

- `scene.yaml` / profile 声明相机 key、fps、动作空间，与 LeRobot feature 名一致  
- 成功判据仍在 Task Pack / Oracle  

### G4 优先级

| 项 | 优先级 |
|----|--------|
| v3 契约与 ACT feature 对齐 | **立即**（设计写入 L1 Framework，实现跟 B 阶段） |
| Processor 版本化进 ArtifactHub | **立即（设计）** / 实现随 ACT |
| async gRPC 推理 | **中期** |
| 替换本仓治理或 Robot 栈 | **不做** |

---

## 附录：与本仓现有代码的接点

| 本仓 | LeRobot 对应 |
|------|----------------|
| `lab_platform/.../lerobot_export.py` | `LeRobotDataset` 布局 |
| `strategy_runtime` PolicyBackend / `lerobot_state` | 简化版 policy 适配；ACT 应对齐 `PreTrainedPolicy` 语义 |
| Mid 子进程 | 类似 record/eval 循环，但总线是 ROS2 |
| ArtifactHub + Index | 强于 LeRobot 的实验侧；保持 |

---

*下一份笔记：`robomimic.md` + `diffusion_policy.md`（IL 经典管线与 DP 对照）。*
