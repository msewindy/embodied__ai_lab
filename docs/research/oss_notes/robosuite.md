# robosuite 源码笔记（RES-OSS-NOTE-05）

| 属性 | 内容 |
|------|------|
| **源码** | `~/project/oss_refs/robosuite` |
| **问卷** | [_questions.md](./_questions.md) |
| **commit** | `5ce6643` |
| **结论摘要** | **MuJoCo 操作仿真底座**：Env 注册、机器人/夹爪/控制器/相机/示教 wrapper。属 **L2-Low 对标**，不是 L1。与 robomimic/RoboCasa/MimicGen/LIBERO 生态咬合；**不替代**本仓 Isaac CTRL-SIM。 |

---

## A. 架构

| 模块 | 职责 | 本仓映射 |
|------|------|----------|
| `environments/` | `MujocoEnv` → `RobotEnv` → `ManipulationEnv`；`@register` + `make()` | L2 任务形态对照 |
| `robots/` · `models/` | 机器人、arena、物体 XML | L2 资产（概念） |
| `controllers/` | OSC/关节等 part + composite | L0 控制模式命名对照 |
| `devices/` | SpaceMouse 等示教设备 | 采数工具对照 |
| `wrappers/` | Gym、数据采集、域随机 | L0 recorder 对照 |
| **无**独立 Policy / Dataset 核心 | 策略在 robomimic 等 | L1 不从此长出 |

**A2** 上下文 = `env._get_observations()` 字典。无 World Context。  
**A3** Policy 通常在外；Env 直接 `step(action)`。  
**A4** 生命周期 = 单次 Env 会话；无 run_id。

### A5 映射

| 能力 | L0 | L1 | L2 |
|------|----|----|-----|
| Env 注册 / make | — | — | Task Pack 注册名 |
| controller 配置 | 桥命令空间 | — | profile `control_mode` |
| DataCollectionWrapper | recorder 钩子对照 | — | — |
| MuJoCo 运行时 | **不做主路径** | — | — |

---

## B–C. 数据与策略

- 演示数据多由 wrapper → HDF5，交 robomimic。  
- **无** Policy 基类；ACT 不在此仓。  
- 多相机：Env 配置 `camera_names` / 渲染。

---

## D–F

- 控制频率 `control_freq` 与仿真子步耦合。  
- 任务成功在各 `ManipulationEnv` 子类。  
- **无**世界模型。  
- **不抄**：用 robosuite 替换 Isaac；把 MuJoCo env 塞进 `strategy_runtime`。

---

## G. 对本仓

1. **L1**：几乎无直接借；确认 Policy 与仿真解耦。  
2. **L0**：示教/采集 wrapper 的「步进钩子」可作文档对照。  
3. **L2**：任务类分层（RobotEnv / ManipulationEnv）可对照 Task Pack 文档结构。  
4. **优先级**：对照文档 **立即**；接入运行时 **不做**。

---

*生态下游笔记：LIBERO / MimicGen / RoboCasa。*
