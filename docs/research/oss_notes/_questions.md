# 开源框架调研问题清单（带着问题读代码）

| 属性 | 内容 |
|------|------|
| **用途** | L1 Framework Design 前的统一问卷；每仓笔记按本题作答 |
| **上位** | [RES-OSS-01](../oss_framework_survey_v0.md) · [STRUCT](../../plan/lab_strategy_runtime_structure_v0.md) |
| **本仓现状锚点** | L0=`lab_platform` · L1=`strategy_runtime` · L2=`tasks/` · CTRL-SIM DOMAIN 43 · B 轨 LeRobot v3 · PolicyBackend |

---

## A. 架构切分（对标 L0 / L1 / L2）

| ID | 问题 |
|----|------|
| A1 | 顶层模块如何划分？哪些对应「实验治理 / 数据 / 策略 / 机器人·仿真 / 任务」？ |
| A2 | 有无显式的「运行时上下文 / World Context」模块？还是观测字典即全部上下文？ |
| A3 | 策略与机器人/仿真之间隔了几层？有无 Processor / Bridge / EnvWrapper？ |
| A4 | 训练入口、采集入口、评测入口是否分离？谁拥有「一次实验」的生命周期？ |
| A5 | 若映射到本仓：哪些能力应进 **L0**、哪些进 **L1**、哪些进 **L2-Low/Task Pack**？（必填表） |

## B. 数据与契约（对标 A/B 轨、Dataset）

| ID | 问题 |
|----|------|
| B1 | Episode / 帧级数据对象长什么样？关键字段名（obs/action/state/images）？ |
| B2 | 视觉如何存与对齐时间（mp4 + parquet？hdf5？）？ |
| B3 | 多相机 / 多模态如何在 schema 里声明？ |
| B4 | 归一化、delta 动作、相对/绝对动作在何处完成？ |
| B5 | 与我们现有 `low.jsonl` → LeRobot v3 export 的差距是什么？L0 要补什么？ |

## C. 策略接口（对标 PolicyBackend / ACT）

| ID | 问题 |
|----|------|
| C1 | Policy 基类方法集（reset / forward / select_action / predict_chunk…）？ |
| C2 | 动作是单步还是 **chunk**？推理时如何队列消费？失败时有无 HOLD 类语义？ |
| C3 | 观测历史（n_obs_steps）如何进入模型？ |
| C4 | 新后端如何注册（factory / registry）？ |
| C5 | ACT（或等价）在该仓的最小依赖路径是什么？我们接入时适配层应多厚？ |

## D. 控制环与异步（对标同构 / 未来 C）

| ID | 问题 |
|----|------|
| D1 | 默认同进程同步 rollout，还是支持策略机 / 机器人机分离？ |
| D2 | 控制频率与策略频率如何解耦？ |
| D3 | 安全限幅、标定、断流停机落在哪一层？ |

## E. 任务与场景（对标 Task Pack）

| ID | 问题 |
|----|------|
| E1 | 「任务」是代码类、配置文件还是数据集属性？ |
| E2 | 场景资产 / 成功判据是否与策略库解耦？ |
| E3 | 对我们 `tabletop_pickplace_v0`：可直接复用的模式 vs 必须自建的部分？ |

## F. 时空上下文 / 世界模型（对标研究设想 · 轻量回答）

| ID | 问题 |
|----|------|
| F1 | 是否存在超越「当前帧 obs dict」的记忆、对象槽位、预测头、兴趣感知？ |
| F2 | 若无：缺口如何描述？我们 L1 设计应预留哪些挂钩（仅接口，不实现）？ |
| F3 | 明确**不抄**什么（弱治理、自研总线替代 ROS、把仿真 env 塞进 L1 等）？ |

## G. 对本仓的变更含义（每仓必答）

| ID | 问题 |
|----|------|
| G1 | 对 **L1** 的 3 条可借鉴设计点 |
| G2 | 对 **L0** 的可能变更（若有） |
| G3 | 对 **L2** 的可能变更（若有） |
| G4 | 优先级：立即借鉴 / 中期 / 不做 |

---

*分析顺序：LeRobot → robomimic+DP → ManiSkill → Isaac Lab → robosuite → LIBERO → OpenVLA → Octo → RDT → MimicGen → RoboCasa（P0+P1 已全部成文于本目录）。*
