# 具身智能实验室

**建设目标：** 推进具身在工业场景落地 — 先建可安全运营的**实验室运行框架**，再挂接工业 Pilot 项目。

---

## 从这里开始

| 角色 | 入口 |
|------|------|
| **负责人 / 审批** | [预算报批一页纸](docs/plan/budget_approval_onepager_v1.md) · [W1 评审纪要](docs/meeting/plan_review_w1.md) |
| **所有人** | [文档总索引](docs/org/governance_index_v1.md) · [L0 总体方案](实验室运行框架建设总体方案.md) |
| **工程** | [lab_platform/](lab_platform/) · [Phase 1 验证](docs/infra/phase1_validation_plan_v1.md) |
| **融合规划** | [平台 × 世界模型](docs/plan/platform_wm_fusion_plan_v0.md) · [本地挂载说明](external/README.md) |
| **招聘** | [岗位 JD](docs/org/jd/) |

---

## 仓库结构

```
具身智能实验室搭建/
├── 实验室运行框架建设总体方案.md   # L0 建设总纲（唯一主方案）
├── docs/
│   ├── org/          # 制度索引、RACI、JD
│   ├── plan/         # WBS、预算 v2
│   ├── architecture/ # 架构与 As-Built
│   ├── infra/        # 环境、网络、验证
│   ├── device/       # 设备清单、能力矩阵
│   ├── safety/       # SOP、急停
│   ├── process/      # 实验流程、CR
│   ├── meeting/      # 评审纪要
│   └── research/     # 技术调研（非建设依据）
├── lab_platform/     # Python 实验平台（Walking Skeleton）
├── ros2/             # ROS2 Jazzy 包（Go2 首台）
├── external/         # 本地外部挂载说明（world_model 为 Junction，不进 Git）
└── scripts/          # 含 link_external_world_model.ps1
```

---

## 当前状态（2026-08-03）

- **预算：** 框架 CAPEX 报批 **¥10 万**（[PLAN-BUDGET-02](docs/plan/budget_v2_framework.md)）
- **团队：** 标准编制 4 人（R1–R4），Batch-1 招聘 R2+R3
- **环境：** lab-ws-01 / lab-ws-02 环境安装完成（E0）
- **Phase-1 主路径：** **FR3 CTRL-SIM**（Isaac + ROS2 · DOMAIN **43**）（[INFRA-02 v1.3](docs/infra/phase1_validation_plan_v1.md) M0–M6）；Go2 降为回归
- **融合基线：** [PLAN-FUSION-01 v0.3](docs/plan/platform_wm_fusion_plan_v0.md) · ws-02 **双模式**
- **下一步：** ws-02 **M2** FR3 Hello（ROS2 同构）  
- **物理：** 围栏/急停待采购施工；布局待实测

---

## 关键决策（W1 冻结）

1. 框架期不做完整场景 Demo；首 Pilot = Franka 跨夹具工位  
2. VR/灵巧手/多相机等 **不进框架包**，Pilot 池单独立项  
3. 真机动态实验：**围栏+急停验收前禁止**  
4. 软件基线：Ubuntu 24.04 + ROS2 Jazzy  

详见 [plan_review_w1.md](docs/meeting/plan_review_w1.md)。

---

## 世界模型资料（本地挂载，非本仓库）

世界模型调研与 FR3 设计保留在仓库外目录；本机通过 Directory Junction 挂到 `external/world_model/`（**已 gitignore，禁止 Submodule**）。

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\link_external_world_model.ps1
```

融合方向见 [PLAN-FUSION-01](docs/plan/platform_wm_fusion_plan_v0.md)。

---

*仓库 README · 2026-08-03*
