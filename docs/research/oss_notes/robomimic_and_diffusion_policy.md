# robomimic + Diffusion Policy 源码笔记（RES-OSS-NOTE-02）

| 属性 | 内容 |
|------|------|
| **源码** | `~/project/oss_refs/robomimic` · `~/project/oss_refs/diffusion_policy` |
| **问卷** | [_questions.md](./_questions.md) |
| **commit** | robomimic `d309eae` · DP `5ba07ac` |
| **结论摘要** | 经典 IL：**obs dict + modality 编码器 + horizon/chunk**。robomimic=算法库+H5；DP 原版=研究向 Hydra workspace。**B 轨仍以 LeRobot v3 为准**；从二者借「观测模态分解 / action horizon / normalizer 绑定 checkpoint」。 |

---

## 0. 为何绑在一起读

- robomimic v0.5 已**内嵌** Diffusion Policy（`algo/diffusion_policy.py`），环境侧绑 robosuite。  
- 原版 `real-stanford/diffusion_policy` 是论文参考实现：更清晰的 `horizon / n_obs_steps / n_action_steps` 与 `BaseWorkspace`。  
- 对我们：不必双栈训练；对照后固化 **PolicyBackend 语义**，训练可走 LeRobot DP/ACT 或日后薄适配。

---

## A. 架构切分

### A1 顶层

| 仓 | 模块 | 职责 |
|----|------|------|
| robomimic | `algo/` | BC / BC-RNN / DP / offline RL… 统一 `Algo` |
| | `utils/obs_utils.py` · `models/obs_nets` | 模态（rgb/low_dim）编码与预处理 |
| | `utils/dataset.py` | HDF5 演示数据集 |
| | `envs/` | 对 robosuite 等的薄包装 |
| | `config/` · `scripts/` | JSON 配置 + train/rollout |
| DP | `policy/` | `BaseImagePolicy` / `BaseLowdimPolicy` |
| | `dataset/` · `env/` · `env_runner/` | 任务数据与评测 runner |
| | `workspace/` | Hydra 训练生命周期 + checkpoint |
| | `real_world/` | RealSense / 真机环（研究向） |

### A2 上下文？

两者都是 **obs_dict（+ 可选 goal_dict）即全部上下文**。robomimic 有 `goal` / `subgoal` modality 槽，用于目标条件，**不是**时空世界模型。

### A3 分层

```
Env / Dataset  →  obs_dict (by key)
       ↓ ObsUtils / encoder (modality)
latent / features
       ↓ Algo.get_action / Policy.predict_action
action (vector or chunk)
```

无独立 Processor Hub；归一化多在 dataset stats / `LinearNormalizer`（DP）或 algo 配置里。

### A4 生命周期

- robomimic：`train.py` 风格脚本 + JSON；checkpoint `.pth`；评测 `run_trained_agent.py`。  
- DP：`BaseWorkspace.run()` + Hydra；checkpoint 含 `cfg` + `state_dicts` + dill pickles。  
**无** run_id / PreFlight；实验复现靠配置文件路径。

### A5 映射本仓

| 能力 | L0 | L1 | L2 |
|------|----|----|-----|
| HDF5 演示格式 | 不作为主格式；可转换脚本 | — | — |
| modality → encoder | — | PolicyObs 组装 + backend | Task 声明键名 |
| horizon / chunk 语义 | export 时序窗 | ✅ PolicyBackend | — |
| robosuite Env | 不采用为 CTRL-SIM | — | 仅对照任务结构 |
| Workspace/Hydra | 可选训练入口包装 | 训练循环可外置 | — |

---

## B. 数据与契约

### B1–B3

**robomimic HDF5**（典型）：

- `data/demo_*/obs/<key>`、`actions`、`rewards`、`dones`…  
- 图像常直接存数组（或压缩）；多相机 = 多 obs key（如 `agentview_image`）  
- filter_keys 做 train/val 划分  

**DP**：任务 yaml 的 `shape_meta` 声明 obs/action 形状；dataset 类按任务（PushT、robomimic 包装等）实现。

### B4 归一化

- DP：`LinearNormalizer`，`set_normalizer` 进 policy，checkpoint 一并保存。  
- robomimic：dataset 侧 action/obs stats + 配置开关。  

### B5 与本仓差距

- 主路径 **不要** 改回 HDF5；保持 LeRobot v3。  
- 若要用 robomimic 算法：写 **v3 → 训练 batch** 适配，或用 LeRobot 内 DP。  
- 可借鉴：`shape_meta` / modality 列表写进 Task Pack + export meta。

---

## C. 策略接口

### C1 robomimic `Algo` / `PolicyAlgo`

- 训练：`process_batch_for_training` → `train_on_batch`  
- 推理：`get_action(obs_dict, goal_dict=None)`  
- 工厂：`@register_algo_factory_func("diffusion_policy")`  

### C2 DP `predict_action`

- 输入：`obs_dict`，值形状概念上 `B, To, *`  
- 输出：`{'action': B,Ta,Da, 'action_pred': ...}`  
- 参数三角：`horizon`（扩散轨迹长）· `n_obs_steps` · `n_action_steps`  
- 从预测轨迹切 `[To-1 : To-1+n_action_steps]` 作为执行段（与 ACT 队列思想同类）  

robomimic 内嵌 DP 同样用 `observation_horizon` + action horizon + 内部 deque（见 `diffusion_policy.py` 后半）。

### C3–C5

- 观测历史：显式 `To` 维，dataset 采样保证。  
- 注册：字符串 algo 名 / Hydra `_target_`。  
- **对我们 ACT 优先**：接口形状对齐 DP/ACT 的 chunk 语义即可；不必引入 robomimic 全库。

---

## D. 控制环

- 默认同进程 eval runner。  
- DP `real_world/`：共享内存、相机进程 — 真机研究栈，**不替代**我们的 ROS2。  
- 频率解耦靠 action chunk 执行；无统一 HOLD。

---

## E. 任务

- robomimic 任务 ≈ 数据集 + robosuite 环境名。  
- DP 任务 ≈ `config/task/*.yaml` + env_runner。  
- 对我们：继续 Task Pack；只借「shape_meta 写进配置」的习惯。

---

## F. 世界模型

- **无**一等 Context。goal modality ≠ spatiotemporal WM。  
- L1 预留：`PolicyObs` 可含 `goal` 字段（语言/目标位姿），与 WM 记忆分离。

### F3 不抄

- 以 HDF5 替换 LeRobot v3  
- 把 robosuite 当 CTRL-SIM  
- 把 Hydra Workspace 当作实验 OS（Index/run_id 仍属 L0）

---

## G. 对本仓含义

### G1 对 L1（3 条）

1. **统一推理返回 chunk**：`action` 执行窗 + 可选完整 `action_pred`（调试/可视化）。  
2. **Normalizer 与权重同生命周期**（同 LeRobot processor 结论）。  
3. **modality 配置表**（哪些 key 是 rgb / low_dim）驱动编码器，避免硬编码。

### G2 L0

- export meta 增加 shape / modality / horizon 提示字段（供训练）。  
- 不强制 HDF5。

### G3 L2

- profile 声明 obs keys 与控制模式（joint/pose），对齐训练 `shape_meta`。

### G4 优先级

| 项 | 优先级 |
|----|--------|
| chunk / n_obs / n_action 语义写入 L1 设计 | **立即** |
| modality 表 | **立即（设计）** |
| 接入 robomimic 训练栈 | **中期（可选）** |
| DP real_world 栈 | **不做**（ROS2 优先） |

---

*下一份：`maniskill.md`。*
