# Octo 源码笔记（RES-OSS-NOTE-08）

| 属性 | 内容 |
|------|------|
| **源码** | `~/project/oss_refs/octo` |
| **问卷** | [_questions.md](./_questions.md) |
| **commit** | `241fb35` |
| **结论摘要** | **通才策略（JAX）**：统一 `observations` + `tasks`（language **或** goal image）→ `sample_actions`。借 **观测字典 / 任务字典 / 历史窗 Gym wrapper** 设计；运行时栈（JAX）与本仓 PyTorch/LeRobot 主路径分离。 |

---

## A. 架构

```
octo/
  model/octo_model.py     # OctoModel：load/save、create_tasks、sample_actions
  data/ · data/oxe/       # 多数据集、OXE
  utils/gym_wrappers.py   # 观测历史堆叠、pad_mask
```

- **无**实验 OS；训练脚本在仓根。  
- Env 通过 Gym wrapper 接历史；策略不拥有仿真。

### A5

| 能力 | L0 | L1 | L2 |
|------|----|----|-----|
| 多源数据集统计 | export / stats 登记 | unnorm 绑 checkpoint | — |
| `tasks`（text/goal） | meta | PolicyObs.task | 任务指令/目标图 |
| history wrapper | recorder 时序 | Obs 组装 | profile `n_obs_steps` |

---

## B. 数据

- 轨迹 dict：`observation`（含 `image_*`、`proprio`）、`actions`、`language_instruction`。  
- `dataset_statistics` 按数据集名存 action 归一化；推理必须指定 unnormalization。  
- 与 LeRobot：概念对齐（多模态 dict），实现为 TF/JAX 管线 — **不合并训练栈**。

---

## C. 策略接口

```python
tasks = model.create_tasks(texts=[...])           # 或 goals={"image_primary": ...}
actions = model.sample_actions(observations, tasks, rng=..., unnormalization_statistics=...)
```

- 动作为 **采样轨迹/chunk**（action head 决定 horizon）。  
- `reset` 语义在 env wrapper；模型侧无本仓 HOLD。  
- **C5**：最小路径是接口对齐，而非依赖 `octo` 包；若要跑权重需 JAX 环境（适配层厚）。

---

## D–F

- Gym history：`horizon` 堆叠 + `timestep_pad_mask`。  
- **F**：goal image / language = 任务条件；无对象槽位 WM。  
- L1 预留：`TaskSpec = language | goal_image | none`，与 Octo `create_tasks` 同构。  
- **不抄**：JAX 训练作为 lab 默认；OXE 全量进本仓数据根。

---

## G

| 项 | 优先级 |
|----|--------|
| L1 `TaskSpec` / PolicyObs 多条件形态 | **立即（设计）** |
| history + pad_mask 约定 | **中期（随相机）** |
| 原生跑 Octo 权重 | **远期 / 可选** |
