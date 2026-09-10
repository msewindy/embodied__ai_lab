# 实验室运行平台 × 世界模型控制运行时：融合规划 v0

| 属性 | 内容 |
|------|------|
| **文档编号** | PLAN-FUSION-01 |
| **版本** | v0.4.3 |
| **日期** | 2026-08-14 |
| **维护人** | R1 |
| **状态** | **working-baseline**（工作基线 · 指导 INFRA-02 / TECH-02 / TECH-04 / TECH-09） |
| **关联** | [PLAN-CHARTER-01](./lab_charter_v0.md)（目的） · [PLAN-STRUCT-01](./lab_strategy_runtime_structure_v0.md)（结构） · INFRA-02 · SOP |
| **进度** | 不复述长表 → 见 [INFRA-02 §1](../infra/phase1_validation_plan_v1.md) |

---

## 0. 一句话定调

**叠放，不揉并。**  
实验室继续建 **Lab Operating Framework（实验室运行平台）**；世界模型三层架构作为第一个 **Agent Control Runtime（控制运行时）** 接入。  
工业 Pilot 用于验证平台托举能力；世界模型路线承载中长期场景突破。  
**Phase-1 目标**：在 FR3 + Isaac 上跑通「平台编排 + 三层最小闭环」，而非一次证完 H1–H5 或交付跨夹具工位。

本地资料挂载（**不进本仓库 / 无 Submodule**）：见 [`external/README.md`](../../external/README.md) → `external/world_model/`。

---

## 0.1 工作基线效力（v0.2）

本文自 v0.2 起作为 **Phase-1 工程与文档修订的工作基线**：

| 效力 | 说明 |
|------|------|
| **约束** | INFRA-02 主验收路径、TECH-02 manipulation 扩展、TECH-04 Isaac/FR3 钉扎以本文 §2 / §4 为准 |
| **不替代** | L0「框架优先」宪法；不把研究 H1–H5 写成框架 Go |
| **变更** | 修订分层或 Phase-1 出口须走 CR，升本文小版本 |
| **已落地配套** | INFRA-02 **v1.4.6** · STRUCT **v0.3.1** · TECH-02/04/09 双模式 · CTRL-SIM/P5 |

---

## 1. 背景与问题

| 现状 | 问题 |
|------|------|
| 战略首 Pilot = Franka 跨夹具 | 业务锚点在臂 |
| Walking Skeleton / ros2 主路径偏 Go2 | 工程验收本体与战略不一致 |
| 世界模型侧已冻结 FR3 + Isaac + 数据契约 | 研究栈在仓库外，未接入平台编排 |
| 两套文档各自称「框架」 | 易被误解为同一层架构 |

**要解决的不是「选业务 Demo」**，而是：  
让平台有第一条真实 manipulation 负载，同时让世界模型验证有可审计的实验操作系统，且两者目标函数分离。

---

## 2. 分层架构（融合宪法）

```text
[ L0 Lab Operating Framework — 本仓库 ]
  场地/安全/资产/制度 · RunManager · PreFlight · run_id
  Pipeline A/B/C · Artifact · 版本矩阵 · 设备能力矩阵
              |  编排实验 / 锁资源 / 归档产物
              v
[ L1 Agent Control Runtime — Strategy Runtime ]
  High(薄) · Mid(厚) · 世界上下文（策略面/评测面）· PolicyBackend
  代码落点：本仓 strategy_runtime/（见 STRUCT）
              |  SkillIntent / LowStateFeedback（TECH-02 同一 msg）
              v
[ L2 本体与场景 + Low 桥 ]
  FR3 + Hand · Scene tabletop_pickplace_v0 · 虚拟相机
  WorldBackend ∈ {isaac_sim, franka_real}  ← 仿真/真机桥，属 L2-Low，不属 L1
  控制仿真(CTRL-SIM): ROS2 同构 · DOMAIN=43 · lab-ws-02
  真机: ROS2 · DOMAIN=42 · ws-01 + 臂（Phase-2 暂缓）
```

> **v0.4.3：** 废止「WorldBackend 画在 L1 框内」的旧图。Isaac/真机桥是 L2-Low；L1 不拥有 sim step。结构细节以 STRUCT 为准。

### 2.0 lab-ws-02 双模式（v0.3 修正）

| 模式 | ROS2 | DOMAIN | 用途 |
|------|:----:|--------|------|
| **CTRL-SIM** | **开** | **43** | Phase-1 主路径：与真机控制图同构 |
| **BATCH** | 可不启 | — | 大规模训练/数据工厂 |

废止旧表述「ws-02 全程禁止 ROS2」。批处理仍可无 ROS；**控制验证必须同构**。真机域 **42** 与仿真域 **43** 禁止混用。

### 2.1 职责边界

| 层 | 负责 | 禁止 |
|----|------|------|
| **Lab OS** | 谁能开跑、资源锁、PreFlight、run 生命周期、日志/数据集落盘路径、安全门禁 | 实现 Mid 情境/前向/对照假说逻辑 |
| **Agent Runtime** | High/Mid/Low 控制语义、对照实验 B0–B5、H1–H5 | 绕过 run_id 私自落「主结论」数据；直改急停策略 |
| **工业 Pilot** | 工装/节拍/换型等成熟能力拼接；验证平台可托举 | 作为 Phase-1 算法突破 KPI |

### 2.2 与现有模块映射

| 本仓库概念 | 世界模型侧 | 融合动作 |
|------------|------------|----------|
| Pipeline A / CTRL-SIM | `WorldBackend=isaac_sim` | FR3 桌面；**ROS2 DOMAIN 43** 与真机同 Topic |
| Pipeline B（Real） | `WorldBackend=franka_real` | DOMAIN 42；消息契约与仿真同构 |
| BATCH 训练 | （可无 ROS） | 不替代 CTRL-SIM 验收 |
| F6 大脑（慢环） | High + Mid | 大脑进程挂 Agent Runtime；**不**把 Mid 拆进 RunManager |
| F6 小脑 / Driver Bridge | Low + 限幅 | 新增 `franka_*` Bridge，实现 Δpose 契约 |
| RunManager | 实验生命周期 | 管 start/stop/pin/archive；不管关节/Δpose |
| LeRobot / Artifact | 数据契约双轨 | A 运行日志 + B 学习集；manifest 互链 |
| TECH-02 SkillIntent | `TaskSpaceCommand` | 补齐 ee_delta / gripper / wrench 反馈（见 TECH-02 v1.2） |
| Go2 栈 | （保留） | **降级**为多本体回归，不再作 Phase-1 主验收 |

### 2.3 成功标准分离（不可混用）

| 轨道 | Phase 内「Go」含义 |
|------|-------------------|
| **平台 Go（框架）** | 可纳管、可审计、可安全按 SOP 跑标准实验（可为仿真） |
| **研究 Go** | H1/H2 等对照成立（世界模型文档定义） |
| **Pilot Go** | 工位指标（节拍/成功率/换型）——默认 Phase-2+ |

---

## 3. 资料与仓库边界

| 内容 | 位置 | 是否进本 Git |
|------|------|:------------:|
| Lab OS 代码/制度/架构 | 本仓库 | ✅ |
| 融合规划、适配说明、索引 | 本仓库 `docs/plan/` 等 | ✅ |
| 世界模型调研/FR3 设计/论文/上游 clone | `D:\project\世界模型`（经 `external/world_model` 挂载） | ❌ |
| Git Submodule 指向世界模型仓库 | — | **禁止** |

阅读入口（挂载后）：

| 主题 | 路径 |
|------|------|
| 世界模型资料总览 | `external/world_model/README.md` |
| 三层理论 | `external/world_model/docs/人类交互与具身智能控制路线分析.md` |
| 验证假说 | `external/world_model/docs/7自由度单臂三层架构验证方案.md` |
| FR3 框架 v0.3 | `external/world_model/docs/FR3验证框架详细设计与阶段计划.md` |
| 模块/数据/Scene | 同目录 `FR3模块级详细设计.md` 等 |

数值 SSOT 纪律沿用世界模型侧：几何/ε → Scene；特征/fps → 数据契约；本融合规划**不复述可漂移数值**。

---

## 4. 分阶段目标

### 4.1 Phase-1｜最小融合闭环（第一阶段目标）

**主题**：平台编排 + Agent Runtime 薄实现 + FR3/Isaac 动起来。  
**对应**世界模型 P-1 → P0 → P1a（仿真）；平台 Walking Skeleton 换锚点。  
**验收条目 SSOT**：[`INFRA-02`](../infra/phase1_validation_plan_v1.md)；分层落地顺序见 [PLAN-STRUCT-01](./lab_strategy_runtime_structure_v0.md) §9。  
**Phase-1 已收口**（M6 E2E PASS 2026-08-07）。**当前工程重心**：真机 FR3（DOMAIN 42）→ [`phase2_franka_real_e2e_plan_v0.md`](../infra/phase2_franka_real_e2e_plan_v0.md)。

| ID | INFRA-02 | 交付 | 验收出口 |
|----|----------|------|----------|
| F1-0 | M0 | 本机挂载 `external/world_model`；环境钉扎写入 run manifest 模板 | 挂载可读；版本表可填 |
| F1-1 | M3 | RunManager 可发起/归档一次仿真 `run`（FR3 场景标签） | 有 `run_id` + manifest |
| F1-2 | M2 | Low：Δpose 驱动 FR3（Isaac）+ `LowStateFeedback` 字段齐 | 末端按指令动 5cm；可急停/HOLD |
| F1-3 | M4 | 双轨落盘：A=`low.jsonl` 可回放；B=`lab data export --format lerobot-v3` + manifest 互链 | 回放误差可接受；B 有 `lerobot_dataset_path` |
| F1-4 | M5 | Mid：Template / toward-target / `m5_pickplace` + Oracle | Scene 抓放谓词可机读 |
| F1-5 | M6 | PreFlight / 安全策略在仿真规程可走通；文档 SOP 一步通 | **E2E PASS ✅** 2026-08-07 |
| F1-6 | R-Go2 | Go2：保留为回归用例，从「主验收」摘牌 | 主路径改 FR3 |

**Phase-1 明确不做**

- Cosmos / LDA / 完整在线 V-JEPA  
- H1 主结论（需 P1b@S2）与 H2 前向主结论  
- 工业跨夹具完整工位交付  
- 真机相机采购与完整 P0r（另册）  
- 把三层控制 API 写进 RunManager 核心  

**Phase-1 一句话出口**

> 任意成员能按 SOP 启动一次「FR3 桌面抓放仿真实验」：有 `run_id`、有 High/Mid/Low 最小链路、有可回放数据。

### 4.2 Phase-2｜各自完善（平台 ⊥ 研究）

| 轨道 | 内容 |
|------|------|
| **平台** | **真 Franka Bridge（进行中）**；Pipeline C 标定；围栏急停；见 [PHASE2-FR3-REAL](../infra/phase2_franka_real_e2e_plan_v0.md) |
| **研究** | P1b（S2+B2）、P2（薄高层+B3）、P3（前向 WM/H2）；对照矩阵与日志评测闸门 |
| **共享** | 同一 Scene/数据契约/WorldBackend；接口变更走 CR |

### 4.3 Phase-3｜Pilot 与扩展（可选并行）

- 工业跨夹具工位：复用 Low/数据/编排，**另定 KPI**  
- 多本体：Go2 locomotion 回归证明契约未退化  
- 大模型插件：仅在 M0/P0 通过后按需接入  

---

## 5. 对现有计划的增删改（执行状态）

| 对象 | 变更 | 状态 |
|------|------|:----:|
| INFRA-02 / Phase 1 | FR3 CTRL-SIM；M2–M6 详细技术方案；DOMAIN 43 | **v1.4.6**（进度看板 SSOT） |
| PLAN-STRUCT-01 | L0×L1×L2 + Task Pack + 双轨/LeRobot 边界 | **v0.3.1**（结构 SSOT） |
| TECH-02 | TaskSpace + 仿真域说明 | **v1.3 已改** |
| TECH-04 | Isaac 钉扎 + DOMAIN 42/43 + 双模式 | **v1.3 已改** |
| TECH-09 | 废止「ws-02 全程无 ROS2」；改为双模式 | **已改** |
| `ros2/` | `franka_sim_bridge` + bringup；Go2 包保留 | **CTRL-SIM 已通** |
| Task Pack / Scene | `tasks/tabletop_pickplace_v0`；`m5_pickplace` | **Phase-1 ✅** |
| 数据 B 轨 | `lab data export --format lerobot-v3`；manifest 互链 | **P3 已通** |
| Index / P5 | `ArtifactHub`：dataset/policy 默认注册；id 解析 | **P5 已通** |
| M6 SOP / E2E | 成员按清单独立开跑 | **E2E PASS ✅** |
| 真机 FR3 | `franka_driver_bridge` + DOMAIN 42 + L0 | **Phase-2 暂缓** |
| L0 总体方案 | **不改宪法**；增补「首个 Agent Runtime = 三层栈」另 CR | 待定 |
| 预算 Pilot-A | 仍作平台托举验收；不前移为 Phase-1 算法目标 | 维持 |

---

## 6. 建议 WBS 切片（Phase-1，约 4–8 周，可压缩）

| 周 | 焦点 | 出口 |
|----|------|------|
| W0 | 挂载、环境钉扎、**P0 文档基线** | F1-0 / M0 |
| W1 | Isaac FR3 Hello + Low 契约 | F1-2 / M2 |
| W2 | RunManager 挂仿真 job + 落盘 | F1-1、F1-3 |
| W3 | Template Mid + Oracle/ stub | F1-4 |
| W4 | PreFlight/SOP、Go2 摘牌、评审 | F1-5、F1-6；Phase-1 Go/No-Go |

人力假设：标准 R1–R4；缺编时优先保 F1-2/F1-3，砍 F1-4 完整度。

---

## 7. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 两套「框架」叙事混乱 | 对外只用「平台 × 控制运行时」；本文 §2 为宪法 |
| 研究被平台工期拖死 | P-1 允许薄路径冒烟；稳定采数后强制挂 run_id |
| 平台被研究接口污染 | Mid 五模块不得进入 `protocols.py` 核心 |
| Isaac/驱动版本漂移 | manifest 钉扎；变更升小版本 |
| 工业 Pilot 被低估 | Pilot Go 单独指标；不与研究 Go 捆绑 |
| 挂载丢失导致「找不到文档」 | `external/README.md` + 建链脚本；CI/新人 onboarding 检查 `Test-Path` |

---

## 8. 基线决策清单（v0.2 已生效）

| # | 决策 | 状态 |
|---|------|:----:|
| 1 | 分层：Lab OS × Agent Runtime，禁止揉并 | **生效** |
| 2 | Phase-1 出口 = §4.1 一句话，而非 H1/跨夹具 | **生效** |
| 3 | 首工程锚点：FR3（Isaac）为主，Go2 为回归 | **生效** |
| 4 | 工业 Pilot = 平台托举验证负载（Phase-2+） | **生效** |
| 5 | 世界模型资料仅本地 Junction，永不 Submodule | **生效** |
| 6 | 立即修订 INFRA-02 / TECH-02 / TECH-04 | **已执行** |
| 7 | ws-02 双模式：CTRL-SIM 用 ROS2（DOMAIN 43）；BATCH 可不启 | **生效（v0.3）** |

正式会签纪要可另附；未会签前工程按本基线执行，冲突以 CR 升级本文为准。

---

## 9. 参考路径速查

| 文档 | 路径 |
|------|------|
| 本文 | `docs/plan/platform_wm_fusion_plan_v0.md` |
| **结构 SSOT（L0×L1×L2）** | `docs/plan/lab_strategy_runtime_structure_v0.md` |
| **目的宪章** | `docs/plan/lab_charter_v0.md` |
| 本地挂载说明 | `external/README.md` |
| INFRA-02（验收 + **进度看板**） | `docs/infra/phase1_validation_plan_v1.md` |
| SOP（操作） | `docs/infra/sop_franka_ctrl_sim_v0.md` |
| A→B 字段映射 | `docs/data/low_jsonl_to_lerobot_v3.md` |
| Policy/Dataset 注册 | `docs/data/policy_registry_spec.md` |
| L0 | `实验室运行框架建设总体方案.md` |
| As-Built | `docs/architecture/platform_architecture_as_built_v1.md` |
| FR3 框架设计 | `external/world_model/docs/FR3验证框架详细设计与阶段计划.md` |

---

## 10. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1-draft | 2026-08-03 | 首稿 |
| v0.2 | 2026-08-03 | 升为工作基线；挂钩 INFRA-02 M 序列 |
| v0.3 | 2026-08-03 | **ws-02 双模式**；CTRL-SIM=ROS2 DOMAIN 43；对齐 INFRA-02 v1.3 |
| **v0.4** | 2026-08-06 | 指向 PLAN-STRUCT-01；**M6 后置**；当前验收=Scene/`m5_pickplace`；B 轨 export |
| v0.4.1 | 2026-08-07 | P5 Index 默认注册；M6 SOP 文档落地；交叉签字可后补 |
| v0.4.2 | 2026-08-07 | Phase-1 E2E PASS 收口；Phase-2 真机 FR3 计划挂载 |
| v0.4.3 | 2026-08-14 | WorldBackend 划回 L2-Low；STRUCT v0.3.1；真机暂缓；对齐 REQ 审视 |
| v0.4.3b | 2026-08-14 | 挂载宪章为目的圣经 |

---

*PLAN-FUSION-01 v0.4.3 · working-baseline · 2026-08-14*
