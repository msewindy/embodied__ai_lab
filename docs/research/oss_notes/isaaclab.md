# Isaac Lab 源码笔记（RES-OSS-NOTE-04）

| 属性 | 内容 |
|------|------|
| **源码** | `~/IsaacLab`（`oss_refs/IsaacLab` 软链） |
| **问卷** | [_questions.md](./_questions.md) |
| **commit** | `e0d9f94116`（浅） |
| **结论摘要** | Isaac Lab = **仿真侧 Manager 化 Env 框架**（L2-Low / WorldBackend 对标），**不是 L1**。可借鉴 Observation/Action/Recorder Manager 的「声明式 term」；本仓 CTRL-SIM 已用自定义桥 + Task Pack，**不要**把整仓 `ManagerBasedRLEnv` 嵌进 `strategy_runtime`。 |

---

## 0. 源码地图（与本仓相关的切片）

```
source/
  isaaclab/                 # 核心：envs、managers、sensors、assets
    isaaclab/envs/          # ManagerBasedEnv / ManagerBasedRLEnv
    isaaclab/managers/      # Observation / Action / Reward / Termination / Recorder…
  isaaclab_tasks/           # 任务配置（manager_based/manipulation…）
  isaaclab_mimic/           # 示教/数据生成（Mimic、运动规划相关）
  isaaclab_rl/              # RL 库对接
  isaaclab_teleop/          # 遥操作
```

本仓现状：Isaac Sim 6 + `franka_sim_bridge` + `tasks/tabletop_pickplace_v0`，**未**以 Isaac Lab 任务为运行时主路径。

---

## A. 架构切分

### A1 Manager-based 核心思想

`ManagerBasedEnv` 把一步仿真拆成可配置 Manager：

| Manager | 职责 |
|---------|------|
| `ObservationManager` | 按 group/term 算观测；支持 history buffer |
| `ActionManager` | `process_action` → `apply_action` |
| `RecorderManager` | pre/post reset/step 录制钩子 |
| （RL）Reward / Termination / Command / Curriculum | 训练信号 |

→ **场景世界 + 传感器 + 控制** 全在仿真进程内组合。这与本仓「Isaac + ROS2 桥 + 外部 Mid」是**另一条架构轴**。

### A2 上下文？

观测 history（`CircularBuffer` / `history_length`）是 **Manager 内的短时窗**，仍非跨任务的 World Model Context。对 L1：「历史窗」可在 Obs 组装层做，不必引入全套 Manager。

### A3–A4

- 策略通常在 **外层 RL/IL 库**（rl_games、rsl_rl、或外部 IL），Env 只暴露 obs/action。  
- 生命周期：`gym`/`AppLauncher` 进程；与我们的 `run_id` 无交集。  
- Mimic（`isaaclab_mimic`）偏 **数据生成**，属采数扩展，不是策略运行时。

### A5 映射本仓（关键）

| Isaac Lab 概念 | 本仓落点 | 注意 |
|----------------|----------|------|
| ManagerBasedEnv | **不**进 L1；对照 L2-Low | CTRL-SIM 保持桥接架构 |
| Observation terms/groups | L2 profile + L0 录制字段；L1 `PolicyObs` | 可抄「声明式 term」文档形态 |
| Action terms | L0 命令接口 / 控制器模式 | 与 ROS topic 对齐 |
| RecorderManager | L0 recorder | 已有自研；可对标钩子时机 |
| isaaclab_tasks | L2 Task Pack | USD/配置自建 |
| isaaclab_mimic | 远期采数 | Phase 后置 |

---

## B. 数据

- RecorderManager + Mimic 数据生成链路：示教 → 轨迹 →（可再）训练。  
- 格式与 LeRobot v3 **不自动等同**；若用 Mimic，需 **L0 转换**。  
- 观测 history 在 Manager 内完成，导出时要明确是否展开。

---

## C. 策略接口

- Env：`step(action)` 批次向量。  
- **无**统一 `PreTrainedPolicy`；IL 常在外部或 Mimic 流程。  
- 对我们：PolicyBackend 继续对标 LeRobot/ACT，**不**对标 Isaac Lab Env API。

---

## D. 控制环

- 仿真内：`action_manager.process_action` → 物理子步 `apply_action` → `observation_manager.compute`。  
- 与 ROS2 桥模式对比：Lab 是 **同进程闭环**；我们是 **DOMAIN + bridge 跨进程**。  
- 安全：仿真侧限幅可在 action term；真机另议。

---

## E. 任务

- `isaaclab_tasks/.../manager_based/manipulation`：配置类拼装场景与 MDP terms。  
- 成功/终止：`TerminationManager` 等。  
- 对我们：Task Pack 可用「配置拼装」思想，但资产与运行时走现有 Isaac+桥。

---

## F. 世界模型

- ObservationManager 的 group（如 actor/critic 不对称观测）≈ **多视图 Obs**，不是语义世界模型。  
- 预留：L1 `ContextView` 将来可订阅「与 Obs group 类似的投影」；实现仍在 Mid，不在 IsaacLab 包内。

### F3 不抄

- 将 CTRL-SIM 整体改造成 `ManagerBasedRLEnv` 应用（成本高、与 ROS 同构冲突）  
- L1 依赖 `isaaclab` Python 包  
- 用 Mimic 替代当前 Oracle/A 轨（可后期并行研究）

---

## G. 对本仓含义

### G1 对 L1（少而精）

1. **Obs 分组思想**：同一世界状态 → 多种 PolicyObs 投影（state-only / +cam / teacher）。  
2. **历史窗作为 Obs 配置**，不是 Policy 私有魔法。  
3. 明确边界：**L1 不拥有 sim step**。

### G2 对 L0

- recorder 钩子时机可对照 pre/post step（已有则文档化对齐）。  
- 若未来嵌 Lab 任务：DOMAIN、PreFlight、export 仍归 L0。  

### G3 对 L2

- Task Pack：声明式列出 observation terms / action 模式 / 终止条件（即使实现是 YAML+脚本而非 Lab Cfg 类）。  
- 场景 pin、USD 组装保持现状。

### G4 优先级

| 项 | 优先级 |
|----|--------|
| 边界裁定写入 L1 Framework（Lab≠L1） | **立即** |
| Task Pack「声明式 term」文档模板 | **立即** |
| Observation history 配置 | **中期（随相机/ACT）** |
| 切换主路径到 isaaclab_tasks | **不做（当前）** |
| Mimic 采数 | **远期** |

---

## 与 CTRL-SIM 架构对照（备忘）

```text
Isaac Lab 典型：
  [ManagerBasedEnv 内] sensors → obs_manager → (external policy) → action_manager → physx

本仓 CTRL-SIM：
  [Isaac] ↔ [franka_sim_bridge ROS2] ↔ [lab Mid / Policy 子进程]
                 ↓
            L0 recorder / export / Index
```

L1 Framework 必须承认第二种，并定义跨进程 Obs/Action 契约。

---

*P0 四份笔记完成。下一步：汇总「L1 需求清单」草案，再开 L1 Framework Design v0。*
