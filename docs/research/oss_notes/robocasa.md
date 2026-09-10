# RoboCasa 源码笔记（RES-OSS-NOTE-11）

| 属性 | 内容 |
|------|------|
| **源码** | `~/project/oss_refs/robocasa` |
| **问卷** | [_questions.md](./_questions.md) |
| **commit** | `921c9a5` |
| **结论摘要** | **大规模厨房场景 + 任务 + 演示生态**（基于 robosuite）。借 **任务多样性 / 资产与 dataset registry / 子任务标注** 的组织方式；仿真与资产栈不迁入本仓 Isaac 主路径。 |

---

## A. 架构

```
robocasa/
  environments/kitchen/   # 原子/复合厨房任务
  models/                 # fixtures · scenes · objects · assets
  wrappers/gym_wrapper.py # Gym 注册
  utils/robomimic/        # 与 robomimic 观测/训练对接
  utils/dataset_registry_utils.py
  scripts/                # 资产下载、数据集脚本
```

| 能力 | 本仓 |
|------|------|
| 365 任务 / 场景资产 | **L2 规模化参考**（非直接依赖） |
| dataset registry | **L0** Index/Artifact 对照 |
| gym + robomimic utils | 训练生态旁路 |
| Policy | 外置（DP / π / GR00T 等 leaderboard） |

**A2** obs dict +（新数据）每帧 subtask / 自然语言阶段指令 — **任务级语言上下文**，仍非几何 WM 服务。  
**A4** 下载资产与评测脚本；无本仓式 PreFlight。

### A5

| 能力 | L0 | L1 | L2 |
|------|----|----|-----|
| dataset registry | ✅ 可对照 Index | — | — |
| 子任务+语言帧标注 | export 字段 | PolicyObs / 分层策略远期 | Task 阶段定义 |
| 厨房资产库 | 不迁入 | — | 场景多样性思路 |

---

## B. 数据

- 大规模 human + 自动轨迹；registry 按类型解析路径。  
- 近期强调 **per-frame subtask annotations**（index、atomic skill、stage、NL instruction）。  
- 存储随 robosuite/robomimic HDF5 习惯。  
- B5：主路径仍 LeRobot；若对标分层策略，先在本仓 meta/jsonl **增加可选 subtask 字段**。

---

## C. 策略

- 仓内不以单一 Policy ABC 为核心；对接外部 IL/VLA。  
- 对我们：不增加 ACT 依赖；强化「任务与数据注册和策略解耦」。

---

## D–F

- Gym wrapper 统一 step。  
- **F**：子任务自然语言标注 ≈ 技能层监督信号，可供日后 L1 分层/选项框架，不是 WM。  
- **不抄**：下载整库厨房资产进 lab；用 RoboCasa 替换 `tabletop_pickplace_v0`。

---

## G

| 项 | 优先级 |
|----|--------|
| 数据契约预留 subtask / stage / instruction | **中期（设计）** |
| Index 风格的 dataset registry 对照 | **立即（概念）** |
| 接入 RoboCasa 运行时 | **不做** |
| 场景规模化（自有资产） | **远期** |
