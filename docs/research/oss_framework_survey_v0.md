# 开源具身 / 机器人学习框架调研索引 v0

| 属性 | 内容 |
|------|------|
| **文档编号** | RES-OSS-01 |
| **版本** | v0.5 |
| **日期** | 2026-08-14 |
| **L1 需求分析** | [RES-L1-REQ-01](./l1_framework_requirements_v0.md)（**v0.2 审视修订**；确认后再开 Design） |
| **用途** | L1 框架设计前的对标清单；**源码级分析入口**（非采购/建设依据） |
| **统一问卷** | [`oss_notes/_questions.md`](./oss_notes/_questions.md) |
| **笔记目录** | [`docs/research/oss_notes/`](./oss_notes/) |
| **源码根（本机）** | `~/project/oss_refs/`（仓库外） |
| **仓库内挂载** | `external/oss_refs` → 上述目录（symlink，**不进 Git**） |
| **纪律** | 同 [`external/README.md`](../../external/README.md)：禁止 Submodule / 禁止把大仓拷进本仓库 |

---

## 0. 与 L0 / L1 的关系（读源码时带着问题）

本调研服务 **L1 Strategy Runtime 框架设计**，但读代码时必须同时标记：

| 对标能力 | 更可能落在我们的哪一层 |
|----------|------------------------|
| Dataset / 训练 CLI / Hub | L0 数据轨 + 适配，或 L1 Policy 训练入口 |
| Env / Simulator / Robot driver | L2-Low / WorldBackend（Isaac、真机桥） |
| Policy / ACT / Diffusion / VLA | L1 PolicyBackend |
| Demo 采集、评测循环 | L0 编排挂载 + L1 监控/谓词 |
| 任务定义 / 场景资产 | L2 Task Pack |

**结论预案：** L1 设计**不会**与 L0 绝缘；凡涉及 `run_id`、落盘、PreFlight、Index、DOMAIN、录制/导出，**必须在 L0 改**，不能在 L1「私自实现第二套实验 OS」。

---

## 1. 优先级分层

### P0 — 必读（与当前 FR3 / ACT / 数据闭环最相关）

| 框架 | GitHub | 本机路径 | 浅克隆大小约 | 借鉴焦点 |
|------|--------|----------|-------------:|----------|
| **LeRobot** | [huggingface/lerobot](https://github.com/huggingface/lerobot) | `oss_refs/lerobot` | 163M | Dataset v3、Policy（ACT）、train/eval/robot 入口、配置组织 |
| **Isaac Lab** | [isaac-sim/IsaacLab](https://github.com/isaac-sim/IsaacLab) | `oss_refs/IsaacLab` → `~/IsaacLab` | 本机已有（大） | Manager-based env、传感器、IL/Mimic、与 Isaac Sim 6 对齐 |
| **ManiSkill** | [haosulab/ManiSkill](https://github.com/haosulab/ManiSkill) | `oss_refs/ManiSkill` | ~600M | GPU 并行操作任务、IL/RL baseline 组织、观测/动作约定 |
| **robomimic** | [ARISE-Initiative/robomimic](https://github.com/ARISE-Initiative/robomimic) | `oss_refs/robomimic` | ~110M | 演示学习算法库、obs/action 管道、Diffusion Policy |
| **robosuite** | [ARISE-Initiative/robosuite](https://github.com/ARISE-Initiative/robosuite) | `oss_refs/robosuite` | ~870M | 模块化仿真 env / 控制器 / 示教工具链 |
| **Diffusion Policy** | [real-stanford/diffusion_policy](https://github.com/real-stanford/diffusion_policy) | `oss_refs/diffusion_policy` | ~32M | 经典 IL 代码结构、视觉 obs、chunk 动作 |

### P1 — 强烈建议（数据规模化 / 语言条件 / VLA 接口）

| 框架 | GitHub | 本机路径 | 借鉴焦点 |
|------|--------|----------|----------|
| **LIBERO** | [Lifelong-Robot-Learning/LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO) | `oss_refs/LIBERO` | 终身操作基准、语言-任务套件、与 DP/OpenVLA 对照 |
| **OpenVLA** | [openvla/openvla](https://github.com/openvla/openvla) | `oss_refs/openvla` | VLA 训练/微调代码组织（大模型路径后置） |
| **Octo** | [octo-models/octo](https://github.com/octo-models/octo) | `oss_refs/octo` | 通才策略、多数据集、观测字典设计 |
| **RDT-1B** | [thu-ml/RoboticsDiffusionTransformer](https://github.com/thu-ml/RoboticsDiffusionTransformer) | `oss_refs/RDT` | 双臂/扩散基础模型代码形态 |
| **MimicGen** | [NVlabs/mimicgen](https://github.com/NVlabs/mimicgen) | `oss_refs/mimicgen` | 从少量演示生成大规模数据（对标采数扩展） |
| **RoboCasa** | [robocasa/robocasa](https://github.com/robocasa/robocasa) | `oss_refs/robocasa` | 大规模厨房场景 + robosuite 生态 |

### P2 — 按需（暂不克隆或仅文档跟）

| 框架 | 说明 | 何时深入 |
|------|------|----------|
| robomimic + Isaac Lab Mimic 文档流 | 人形/IL 数据生成 | 人形或大规模 SDG 时 |
| Habitat / AI2-THOR | 导航/具身家居 | 非 FR3 主路径 |
| MuJoCo MJX / mujoco_playground | 轻量物理 | 不替代 Isaac 主仿真 |
| SERL / HIL-SERL | 真机 RL | 真机 RL 阶段 |
| π0 / 闭源或权重受限栈 | 产品参考 | 仅论文级，不强制源码 |

---

## 2. 建议的源码阅读顺序（L1 设计前）

```text
1) LeRobot
   - src/lerobot/datasets/   ← B 轨 / meta / 视频如何组织
   - src/lerobot/policies/   ← ACT 等 Policy 接口
   - 训练/评估入口脚本与配置
2) robomimic + diffusion_policy
   - algo/ · ObsUtils · 训练循环 vs 我们的 PolicyBackend
3) ManiSkill
   - 任务注册、obs/action space、baseline 目录习惯
4) Isaac Lab（对照本机 Isaac 6）
   - managers / sensors / imitation 示例
   - 明确：哪些属于「仿真 env」而非 L1
5) LIBERO / OpenVLA / Octo（扫接口，不深挖训练）
   - 语言条件与多任务如何挂到 obs dict
```

每读一个仓，按 [_questions.md](./oss_notes/_questions.md) 作答，再汇总成「L1 需求清单」。

### 2.1 笔记进度（P0 + P1）

| 层级 | 笔记 | 状态 |
|------|------|------|
| 问卷 | [oss_notes/_questions.md](./oss_notes/_questions.md) | ✅ |
| P0 | [lerobot.md](./oss_notes/lerobot.md) | ✅ |
| P0 | [robomimic_and_diffusion_policy.md](./oss_notes/robomimic_and_diffusion_policy.md) | ✅ |
| P0 | [robosuite.md](./oss_notes/robosuite.md) | ✅ |
| P0 | [maniskill.md](./oss_notes/maniskill.md) | ✅ |
| P0 | [isaaclab.md](./oss_notes/isaaclab.md) | ✅ |
| P1 | [libero.md](./oss_notes/libero.md) | ✅ |
| P1 | [openvla.md](./oss_notes/openvla.md) | ✅ |
| P1 | [octo.md](./oss_notes/octo.md) | ✅ |
| P1 | [rdt.md](./oss_notes/rdt.md) | ✅ |
| P1 | [mimicgen.md](./oss_notes/mimicgen.md) | ✅ |
| P1 | [robocasa.md](./oss_notes/robocasa.md) | ✅ |
| 汇总 | [l1_framework_requirements_v0.md](./l1_framework_requirements_v0.md) | ✅ v0.2 审视修订 |

---

## 3. 本机操作

```bash
# 源码根
ls ~/project/oss_refs

# 仓库内浏览（symlink）
ls ~/project/embodied__ai_lab/external/oss_refs

# 更新某一仓（浅克隆）
cd ~/project/oss_refs/lerobot && git pull --depth 1

# 补克隆示例
cd ~/project/oss_refs
git clone --depth 1 https://github.com/<org>/<repo>.git
```

**说明：** 首次并行克隆曾有部分失败；已顺序重拉。Isaac Lab 使用本机已有 `~/IsaacLab`（勿重复整仓克隆）。

---

## 4. 单仓分析笔记模板（复制用）

```markdown
# <框架名> 源码笔记
- 路径：
- 版本/commit：
## 1. 顶层模块图（目录 → 职责）
## 2. 数据对象（Dataset / Episode / Obs / Action）
## 3. 策略接口（reset/act/train）
## 4. 与仿真/机器人的边界
## 5. 可借鉴到我们的 L0 / L1 / L2（各列 3 条）
## 6. 明确不抄（及原因）
```

落点：`docs/research/oss_notes/<name>.md`；统一题库见 [_questions.md](./oss_notes/_questions.md)。

---

## 5. 下一步（流程共识）

1. ~~P0+P1 源码笔记~~ · ~~L1 需求分析~~ · ~~需求审视修订（v0.2）~~  
2. **待确认 REQ v0.2** → 再启动 **L1 Framework Design v0**  
3. 目录整理 / 相机 / ACT 实现 **不得早于** 设计文档评审；B0 拆包非前置  

---

## 6. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-08-10 | 首版清单；本机浅克隆 P0+P1 完成 |
| v0.2 | 2026-08-10 | 挂载统一问卷；先完成阅读顺序前 4 份笔记 |
| v0.3 | 2026-08-10 | 补全 P0 robosuite + 全部 P1 笔记 |
| v0.4 | 2026-08-10 | 挂载 RES-L1-REQ-01 需求分析 |
| v0.5 | 2026-08-14 | REQ v0.2 审视修订；Design 待确认后启动 |

---

*RES-OSS-01 · 研究参考 · 不驱动采购*
