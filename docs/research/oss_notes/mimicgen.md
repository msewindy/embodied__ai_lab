# MimicGen 源码笔记（RES-OSS-NOTE-10）

| 属性 | 内容 |
|------|------|
| **源码** | `~/project/oss_refs/mimicgen` |
| **问卷** | [_questions.md](./_questions.md) |
| **commit** | `72bd767` |
| **结论摘要** | **从少量演示合成大规模轨迹**（子任务切分 + 物体位姿变换 + 回放）。属 **L0 采数扩展 / 数据生成**，不是 L1 策略框架。与 robosuite HDF5 深度绑定；Isaac Lab 另有 `isaaclab_mimic` 旁路。 |

---

## A. 架构

```
mimicgen/
  datagen/          # DataGenerator、waypoint、selection_strategy、DatagenInfo
  configs/task_spec # MG_TaskSpec：子任务边界与随机
  env_interfaces/   # 仿真 env 适配
  envs/robosuite/   # 生成用环境
  scripts/          # prepare_src_dataset、生成、导出训练配置
```

| 能力 | 本仓 |
|------|------|
| 演示扩增流水线 | **L0** 远期（或研究脚本外置） |
| TaskSpec 子任务 | L2 任务阶段标注对照 |
| Policy 训练 | 仍交 robomimic / LeRobot |

**A2** 生成时需要 **物体位姿 / 子任务信号**（`DatagenInfo`）— 这是「数据生成用特权状态」，接近 Oracle，**不是**策略运行时 Context API。  
**A4** 生成作业生命周期自管；产出 HDF5。

### A5

| 能力 | L0 | L1 | L2 |
|------|----|----|-----|
| 源演示 prepare（注入 datagen_info） | ✅ 采数工具 | — | 子任务定义 |
| 合成轨迹写盘 | ✅ data-root | — | — |
| 特权物体位姿 | recorder / Oracle GT | 仅 A 轨可用 | 场景目标 |

---

## B. 数据

- 输入/输出：**HDF5**；关键附加键 `datagen_info/{eef_pose,object_poses,subtask_term_signals,target_pose,gripper_action}`。  
- 子任务边界由 `MG_TaskSpec` + term signals 决定。  
- B5：与 `low.jsonl` 差距大；若采用，需 **L0 转换** 或仅在 MuJoCo 生态内生成再 export 到 v3。

---

## C. 策略

- **无**在线 Policy 推理核心；生成器用运动学/waypoint 拼接轨迹。  
- 不回答 ACT 接入；对策略侧是「数据供给侧」。

---

## D–F

- 控制在 env_interface 回放。  
- **F**：`object_poses` 子任务结构对 **世界模型/技能图** 有启发，但实现是离线 SDG，不是 Mid 运行时。  
- L1 挂钩：Oracle/A 轨已有 GT → 将来可标记 subtask；不把 MimicGen 塞进 `strategy_runtime`。  
- **不抄**：强制 HDF5 主格式；用 MimicGen 替换当前 pickplace 人工/Oracle 采数（可后期并行）。

---

## G

| 项 | 优先级 |
|----|--------|
| 子任务/阶段标注字段（设计进数据契约） | **中期** |
| Isaac 侧 SDG（对照 isaaclab_mimic） | **远期** |
| 主路径依赖 MimicGen+robosuite | **不做** |
