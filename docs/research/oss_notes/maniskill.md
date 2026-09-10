# ManiSkill 源码笔记（RES-OSS-NOTE-03）

| 属性 | 内容 |
|------|------|
| **源码** | `~/project/oss_refs/ManiSkill` |
| **问卷** | [_questions.md](./_questions.md) |
| **commit** | `62ff3a5` |
| **结论摘要** | 强在 **任务注册 / GPU 并行 Env / obs_mode·control_mode 约定**。属 **L2-Low / 仿真任务侧** 对标，不是 L1 策略框架。CTRL-SIM 主仿真仍是 Isaac；ManiSkill 用来校准「Task 如何声明观测与成功」。 |

---

## 0. 源码地图

```
mani_skill/
  envs/           # BaseEnv(sapien) + tasks/* + @register_env
  agents/         # 机器人与 controllers
  sensors/        # Camera / depth…
  trajectory/     # 轨迹 IO / 回放相关
  vector/         # 向量化与 SB3/Gymnasium 包装
  utils/registration.py
```

物理后端：**SAPIEN/PhysX**（非 Isaac）。可作算法基准，不替换本仓 Isaac 主路径。

---

## A. 架构切分

### A1–A4

| 模块 | 职责 | 本仓映射 |
|------|------|----------|
| `BaseEnv` + tasks | Gymnasium Env、奖励、成功 | **L2 Task Pack**（逻辑对标，实现不同） |
| `agents` / controllers | 控制模式与动作空间 | L0 桥 + L2 profile |
| `sensors` | 相机等 | L0 传感器 / Isaac 侧 |
| `trajectory` | 演示轨迹 | L0 数据轨对照 |
| 几乎无独立 Policy 库 | IL/RL 在 examples / 外部 | **L1 不从这里长出来** |

生命周期：`gym.make(uid)` / 向量 env；**无**实验治理层。

### A2 上下文

`obs_mode` 决定观测内容（`state` / `rgb` / `rgbd` / `pointcloud`…）。仍是 **当前（并行）步进的 obs**，无持久 World Context 服务。

### A5 映射

| 能力 | L0 | L1 | L2 |
|------|----|----|-----|
| `@register_env` 任务注册 | — | — | ✅ 可对标「Task Pack 注册名」 |
| obs_mode / control_mode | 桥与 recorder 配置 | PolicyObs 投影 | ✅ scene/profile |
| GPU 并行千万 env | 非当前目标 | — | 研究向 |
| SAPIEN 场景资产 | 不迁入 | — | 概念对照 |

---

## B. 数据

- 轨迹工具在 `trajectory/`；生态常见导出到各类 IL 格式（含社区 → LeRobot）。  
- 观测键随 `obs_mode` 与传感器配置变化。  
- **对我们**：继续自研 recorder → `low.jsonl` / LeRobot；借鉴「模式枚举」减少隐式约定。

---

## C. 策略接口

- Env 侧标准：`reset` / `step(action)`。  
- Policy 不在核心库；examples 接随机动作、运动规划、外部 RL。  
- **无** ACT 级 `select_action` 标准 — 不作为 PolicyBackend 母本。

---

## D. 控制环

- `control_mode` 选择控制器；动作空间随之变。  
- 向量化 `num_envs`；单 env 可走 CPU backend。  
- 安全/标定非重点（仿真基准库）。

---

## E. 任务与场景（本仓最有用的部分）

### E1 任务 = 注册的 Env 类

```python
@register_env("PickSingleYCB-v1", max_episode_steps=50, asset_download_ids=["ycb"])
class ...
```

- uid、步数上限、资产依赖显式声明。  
- 成功/奖励在任务类内（`evaluate` / reward_mode）。

### E2–E3 对我们 `tabletop_pickplace_v0`

| 可借鉴 | 必须自建 |
|--------|----------|
| 任务 uid + 最大步数 + 资产 pin | USD/Isaac 场景与 Franka 桥 |
| obs_mode / control_mode 写进 profile | ROS2 Mid / Oracle |
| 成功判据与策略代码分离（在 Env） | 判据挂 L1 Oracle 或 L2 script，不进 Isaac 扩展乱绑 |

---

## F. 世界模型

- 无。点云 obs_mode 只是传感器打包。  
- 挂钩：L2 可声明「可用传感器集合」；L1 Context 将来可订阅子集。

### F3 不抄

- 用 ManiSkill 替换 Isaac CTRL-SIM  
- 把 `BaseEnv` 放进 `strategy_runtime`  
- 为对齐而引入 SAPIEN 运行时依赖到 lab 主路径

---

## G. 对本仓含义

### G1 对 L1

1. 少借策略；多借 **「任务成功/终止与策略训练代码分离」**。  
2. Oracle/eval 读 Task 声明的成功定义，不读仿真私有 API 散落逻辑。  
3. `PolicyObs` 的 mode（state / rgb / …）与 Task profile 对齐。

### G2 L0

- launcher profile 字段可对齐命名：`obs_mode`、`control_mode`、`max_episode_steps`。  

### G3 L2

- Task Pack README/scene.yaml：**注册名、资产 pin、观测模式、控制模式、成功条件** 四件套。  

### G4 优先级

| 项 | 优先级 |
|----|--------|
| Task Pack 元数据四件套 | **立即（设计→文档）** |
| 并行仿真扩展 | **远期** |
| 接入 SAPIEN 主路径 | **不做** |

---

*下一份：`isaaclab.md`。*
