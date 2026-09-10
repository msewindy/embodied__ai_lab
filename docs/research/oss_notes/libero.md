# LIBERO 源码笔记（RES-OSS-NOTE-06）

| 属性 | 内容 |
|------|------|
| **源码** | `~/project/oss_refs/LIBERO` |
| **问卷** | [_questions.md](./_questions.md) |
| **commit** | `8f1084e` |
| **结论摘要** | **语言条件多任务 / 终身学习基准**（BDDL 任务 + 演示 + lifelong algos）。借：**任务套件 + language emb → Policy** 的挂载方式。仿真仍基于 robosuite 系；非本仓主仿真。 |

---

## A. 架构

```
libero/libero/
  benchmark/     # 任务套件索引
  envs/          # 基于 robosuite 的操作 env
  bddl_files/    # 任务逻辑（物体关系/目标）
  assets/
libero/lifelong/
  algos/ · models/ · configs/   # 终身学习 + BC/ViLT 等策略
```

| 能力 | 层直觉 |
|------|--------|
| 任务套件 / BDDL | **L2**（语言-任务声明） |
| lifelong 训练循环 | 研究向；实验治理仍归 **L0** |
| `BasePolicy` + language encoder | **L1** PolicyBackend 远期接口 |

**A2** 上下文 = 图像/state obs + **task embedding（语言）**；非时空 WM。  
**A4** train/eval 脚本分离；无 Index/run_id。

### A5 映射

| 能力 | L0 | L1 | L2 |
|------|----|----|-----|
| 语言指令字段 | export `tasks` / meta | PolicyObs.language | Task Pack 指令表 |
| BDDL 成功逻辑 | — | Oracle 可对标谓词 | 任务定义 |
| lifelong algo | — | 中期研究 | — |
| robosuite env | 不采用 | — | — |

---

## B. 数据

- 人类遥操演示数据集（suite 分包）；HDF5 生态。  
- 任务描述 → `get_task_embs`（BERT 等）进 policy。  
- 与本仓：B 轨可先在 LeRobot `tasks.parquet` 留 language；不必上 BDDL。

---

## C. 策略

- `lifelong/models/base_policy.py`：metaclass 注册；视觉 + language fusion（FiLM / ViLT）。  
- 多为逐步/序列策略，非统一 ACT chunk API。  
- 接入厚度：**厚**（换栈）；更合理是 **抄接口形状**：`obs + language → action`。

---

## D–F

- 评测在 suite env 内。  
- **F**：declarative（物体关系）在 BDDL，接近「任务级语义」，仍非运行时 World Model。  
- L1 预留：`PolicyObs.task_emb` / `instruction`；Context 层将来可提供物体关系，与 LIBERO BDDL 思想对齐但实现自建。  
- **不抄**：整仓 lifelong 训练 OS；MuJoCo 主路径。

---

## G

| 项 | 优先级 |
|----|--------|
| Task Pack / export 支持 language 字段 | **立即（设计）** |
| PolicyBackend 语言条件钩子 | **中期** |
| 跑 LIBERO 基准作主 KPI | **不做（当前 FR3 路径）** |
| BDDL 引擎迁入 | **不做** |

---

*VLA 对照：OpenVLA / Octo / RDT。*
