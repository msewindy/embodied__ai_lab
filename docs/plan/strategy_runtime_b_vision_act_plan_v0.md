# 实施方案：strategy_runtime 包整理 + 学能力 B（相机 / 视觉 / ACT）v0

| 属性 | 内容 |
|------|------|
| **文档编号** | PLAN-SR-B-01 |
| **版本** | v0.2 |
| **日期** | 2026-08-14 |
| **状态** | **暂停编码**（服从 [RES-L1-REQ-01](../research/l1_framework_requirements_v0.md) v0.2；**确认需求并完成 L1 Framework Design 评审前不得开工**） |
| **前置调研** | [RES-OSS-01](../research/oss_framework_survey_v0.md) · [RES-L1-REQ-01](../research/l1_framework_requirements_v0.md) |
| **上位** | [PLAN-STRUCT-01](./lab_strategy_runtime_structure_v0.md) §6.0 / §9 / §11 |
| **前置** | L1 落点已钉死 `strategy_runtime/`；Phase-1 E2E PASS；真机暂缓 |
| **范围** | **仅仿真 DOMAIN 43** |

---

## 0. 结论：方案仍可用作「学能力 B」切片草案，但顺序已改

v0.1 把 **B0 目录整理**当成第一刀。v0.2 明确：**四文件夹 ≠ L1 框架**；拆包是 Design 的结果，不是前置。编码顺序改为：

1. 确认 RES-L1-REQ-01 v0.2  
2. L1 Framework Design 评审通过（S0：投影配置、TaskSpec、可执行段+HOLD、Context 两面、**Mid 与 Policy 同一控制环**）  
3. 再按 Design 映射本方案的 B1–B3（相机轨 → PolicyObs 图像 → ACT）  
4. 目录整理仅在 Design 指定新模块边界之后做，且不得单独冒充完成

其余仍成立：不一次上完整 ACT 训练闭环；LeRobot 可选；无 GPU 时 state MLP 不得回归；L0 只编排。

| 路径 | v0.2 态度 |
|------|-----------|
| 包整理 `mid/` `policy/` `world/` | **后置于 Design**；禁止当开工第一步 |
| Isaac RGB → A 旁路 → B `videos/` | Design 后的 L0/L2 主风险项（与 ACT 动作空间并列） |
| `PolicyObs` 带 image | 服从「投影配置」；state-only 仍可只投影 state |
| `lerobot_act` 训/rollout | Design 后；训练不进 `strategy_runtime` 核心 |
| 异步 chunk / 多机 | **不做**（属更后切片） |
| 真机相机 | **不做** |

---

## 1. 目标与非目标

### 1.1 目标（验收口径）

| ID | 出口 |
|----|------|
| **G-pkg** | 仅当 Design 指定新模块边界后迁移；**不是**本方案验收主目标 |
| **G-cam** | Task Pack 声明 1 路相机；正式 run 落盘图像序列；`lab data export` 产出含 `videos/`（或等价 mp4）+ meta features |
| **G-obs** | `PolicyObs` 可携带图像；`lerobot_state` 仍可只吃 state（向后兼容） |
| **G-act** | `create_backend("lerobot_act", checkpoint=…)` 可加载；CTRL-SIM 上低速 rollout 冒烟（允许成功率低于 Oracle） |

### 1.2 非目标

- 一次达到仿真 pickplace 高成功率 ACT  
- 多相机标定精密 SSOT  
- record 时双写 B（仍事后 export）  
- 把 LeRobot 训练塞进 RunManager 核心  

---

## 2. 总体切片与依赖

> **v0.2：** 下图保留为「Design 之后」的学能力切片；**B0 不再是开工第一步。** 当前阻塞在 REQ 确认 + Framework Design。

```text
[阻塞] 确认 REQ v0.2 → L1 Framework Design（S0 并环）
        │
        ▼
（可选）按 Design 拆包 / 迁移 import     ──非验收项──►  不得单独宣称框架完成
        │
        ▼
B1  相机采数 + B 轨 videos/                 ──3–5d──►  export 含图像；DATA-MAP 升版
        │
        ├────────► B2  PolicyObs 投影含图像（state-only 仍可用）
        │
        ▼
B3  lerobot_act 适配（train 外包/子进程 + rollout） ──1–2w──►  Index 注册 pol_act_*；rollout 冒烟
```

**建议开工顺序（v0.2）：Design 评审通过 →（可选、按 Design 拆包）→ B1 相机轨 → B2 投影含图像 → B3 ACT。**  
禁止：未 Design 先 B0；未并控制环先 ACT。ACT 第一风险是动作空间与相机数据轨（见 REQ R8），不是网络。

---

## 3. B0 — 包内目录整理（详细 · **后置于 Design，非开工第一步**）

本节保留为拆包清单，供 Design 指定模块边界后对照；**单独完成 B0 不算框架验收。**

### 3.1 目标树

```text
strategy_runtime/
├── pyproject.toml
├── README.md
└── strategy_runtime/
    ├── __init__.py                 # 稳定公共 API 再导出
    ├── mid/
    │   ├── __init__.py
    │   └── template.py             # ← mid_template.py
    ├── policy/
    │   ├── __init__.py
    │   ├── backend.py              # ← policy_backend.py
    │   ├── lerobot_state.py        # ← lerobot_state_policy.py
    │   ├── train.py                # ← policy_train.py
    │   └── rollout.py              # ← policy_rollout.py
    ├── world/
    │   ├── __init__.py
    │   ├── scene_targets.py
    │   └── oracle_gt.py
    └── eval/
        ├── __init__.py
        └── pickplace.py            # ← eval_pickplace.py
```

### 3.2 兼容策略（两层）

| 层 | 做法 |
|----|------|
| **包内旧路径** | 根下保留 `mid_template.py` 等 **1 个小版本周期** 的 re-export，标 `Deprecated` |
| **L0 shim** | `lab_platform.ctrl_sim.*` 继续转发到 **新路径**（或经旧路径） |

公共 API（建议 `__init__.py` 钉死）：

```python
from strategy_runtime.mid.template import MidTemplate, run_mid_template
from strategy_runtime.policy.backend import PolicyObs, PolicyAction, create_backend
from strategy_runtime.policy.train import train_lerobot_state
from strategy_runtime.policy.rollout import run_policy_rollout
from strategy_runtime.world.scene_targets import SceneTargets, bounded_ee_delta
```

### 3.3 步骤清单

1. 建目录，`git mv` 文件并改内部 import。  
2. 根模块留 shim（可选，降低一次改全脚本成本）。  
3. 更新 `strategy_runtime/README.md`、STRUCT §4.1 树图。  
4. 验收：

```bash
export PYTHONPATH=$REPO/lab_platform:$REPO/strategy_runtime:$PYTHONPATH
python -c "from strategy_runtime.mid.template import run_mid_template; from strategy_runtime.policy.backend import create_backend"
python -c "from lab_platform.ctrl_sim import MidTemplate, create_backend"
# 可选：无 Isaac 的 import-only；有机时跑一次 m5_template 或 m5_pickplace
```

### 3.4 风险

- 循环 import：`mid` → `world` → 勿再 import `mid`；`policy.rollout` 勿 import `mid`。  
- 脚本路径：`lab_platform/scripts/m5_*.py` 可暂走 shim，B0 不强制改。

**B0 完成定义：** 新目录为唯一实现位置；冒烟 import PASS；shim 不增加业务逻辑。

---

## 4. B1 — 相机进 A/B 轨（B 的主价值）

### 4.1 架构分工

```text
Isaac Camera prim
  → (采图器：L0 挂载 or L1 world.camera 辅助)
  → run_dir/logs/cameras/<key>/*.jpg   # A 旁路（可审计）
  → lab data export
  → datasets/.../videos/<key>/episode-000.mp4 + meta features
```

| 层 | 职责 |
|----|------|
| L2 Task Pack | `scene.yaml` `cameras[]`：key / prim / fps / resolution / encoding |
| L0 | run 时挂载 recorder 旁路；export 读旁路写 LeRobot v3；Index meta 记 `has_videos` |
| L1 | 不负责落盘根；rollout 时按需读最新帧或订阅图像 topic |

### 4.2 Task Pack 变更（示例）

```yaml
cameras:
  - key: observation.images.third_person
    prim: /World/CameraThirdPerson   # assemble_scene_usd 需保证 prim 存在
    fps: 10
    width: 320
    height: 240
    encoding: mp4
```

USD：在 `assemble_scene_usd.py` 增加第三人称相机（位姿钉在 `scene_pin.md`）。  
PreFlight：`cameras` 非空时检查 prim 声明完整（不必启动 Isaac 才能过 PF 的字段检查）。

### 4.3 采图实现选项（选定一个）

| 方案 | 说明 | 推荐 |
|------|------|------|
| **A. Isaac 复本脚本拉渲染** | 子进程/扩展读 viewport 或 Replicator | 依赖重，后置 |
| **B. ROS Image topic** | Isaac ROS2 camera bridge → `/camera/.../image_raw`；L0 录盘 | **推荐**（与 DOMAIN 43 同构） |
| **C. 仅导出占位黑帧** | 打通目录契约 | 仅开发自测，不算 B1 PASS |

**推荐 B：**  
Isaac 侧启用相机 ROS2 发布（官方桥或 OmniGraph）；L0 `TrajectoryRecorder` 旁路或独立 `CameraRecorder` 按 `record_fps` 写 jpg；manifest `tracks.A.cameras`。

### 4.4 Export（DATA-MAP 升 v1.2）

- 若存在 `logs/cameras/<key>/`：组装 mp4 → `videos/<key>/chunk-…` 或 LeRobot v3 约定路径。  
- `meta/info.json` features 增加图像项；`lab` 段记录 `cameras` 快照。  
- `tracks.B.has_videos: true`。  
- **无相机 run 行为不变**（`cameras: []` 回归）。

### 4.5 B1 验收

| # | 检查 |
|---|------|
| 1 | 新 scene 打开可见相机 prim；topic 或落盘有帧 |
| 2 | pickplace run 后 `logs/cameras/...` 帧数 ≈ A 轨量级（允许 ±20%） |
| 3 | export 后 dataset 含 videos；`lerobot`/自检可读 |
| 4 | 旧无相机 run 仍可 export |

**B1 完成定义：** 视觉进 B 轨契约打通；尚不要求 ACT。

---

## 5. B2 — 观测契约与轻量视觉（可选薄刀）

### 5.1 `PolicyObs` 扩展（兼容）

```python
@dataclass
class PolicyObs:
    q: list[float]
    gripper_width: float
    t: float = 0.0
    ee_pose: list[float] | None = None
    run_id: str = ""
    images: dict[str, Any] = field(default_factory=dict)  # key → HxWxC uint8 / path
```

- `lerobot_state.act`：**忽略** `images`。  
- 新增可选 `lerobot_vision_stub` 或极小 CNN（仅证明管道）；**不**替代 ACT。

### 5.2 Rollout 取图

- 优先订阅与采数相同的 Image topic；失败则 HOLD（纪律与 state 一致）。  
- 不在 L1 读 `data-root` 历史 jpg 做在线控（避免和实时脱节）；历史仅用于 train。

**B2 完成定义：** 带图 obs 能进 backend；state 路径零回归。可与 B3 合并交付。

---

## 6. B3 — ACT（LeRobot 适配）

### 6.1 定位

| 项 | 选择 |
|----|------|
| 实现 | **适配** HuggingFace LeRobot ACT，不自研 transformer |
| 依赖 | `optional-dependencies`: `strategy-runtime[act]` → `lerobot` + `torch` |
| 训练 | `lab policy train --backend lerobot_act …` **子进程**调 LeRobot CLI/API；产物回填 `artifacts/policies/pol_act_*` |
| 推理 | `PolicyBackend` 名：`lerobot_act`；chunk 动作可先 **同步逐步消费**（异步=C，本阶段不做） |
| 数据 | 必须 B1 通过的带 `videos/` dataset |

### 6.2 训练入口（草）

```bash
lab --data-root "$DATA" policy train \
  --backend lerobot_act \
  --dataset ds_… \
  --policy-id pol_act_pickplace_v0 \
  --epochs …          # 透传 LeRobot
```

- 无 `[act]` extra → CLI 明确报错。  
- 注册：TECH-12 增 `backend: lerobot_act`；checkpoint 布局按 LeRobot 输出 + 本仓 `policy_manifest.yaml`。

### 6.3 Rollout

```bash
lab policy rollout --checkpoint pol_act_pickplace_v0 --backend lerobot_act
```

- 动作语义仍 `ee_delta[6]+gripper`（与 Task Pack `action_schema` 对齐）。  
- 失败 / 超时 → HOLD。  
- 成功率：**冒烟级**（有 `n_pub`、不崩）；不与 Oracle pickplace 同比验收。

### 6.4 STRUCT §11.2 相关裁定（B3 开工前钉死）

| # | 问题 | 建议裁定 |
|---|------|----------|
| 6 | train 形态 | **本机子进程调 LeRobot**（登记外部作业后置） |
| 2 | ObjectPose msg | 视觉 ACT **不阻塞**；Oracle 仍 PoseStamped |

### 6.5 B3 验收

| # | 检查 |
|---|------|
| 1 | 无 torch 环境：state 训/推仍 PASS |
| 2 | 有 LeRobot：train 产出可注册 `pol_act_*` |
| 3 | rollout `n_pub>0`，manifest 写 `policy_id` + backend |
| 4 | `lab lineage` 可追溯 dataset → policy → rollout |

---

## 7. 文档与看板同步（随切片）

| 切片 | 文档 |
|------|------|
| B0 | `strategy_runtime/README` · STRUCT §4.1 |
| B1 | DATA-MAP → v1.2 · `scene_pin` 相机 · SOP 学习路径补「带相机 export」 |
| B2–B3 | TECH-12 backend 表 · STRUCT §9 增 **P6（视觉/ACT）** · INFRA §12.2 |

---

## 8. 工作量与人力假设（单人参考）

| 切片 | 估时 | 阻塞 |
|------|------|------|
| B0 | 0.5 天 | 无 |
| B1 | 3–5 天 | Isaac 相机 ROS 桥是否已有经验 |
| B2 | 1–2 天 | 依赖 B1 topic |
| B3 | 5–10 天 | LeRobot 版本钉扎、GPU、数据量 |

**合计到「B1 完成」约一周内可交付可见价值；完整 ACT 冒烟约 2–3 周。**

---

## 9. 风险与缓解

| 风险 | 缓解 |
|------|------|
| Isaac 相机 ROS 难搞 | B1 可先「Replicator/离线刷帧→jpg」保契约，再换 ROS |
| LeRobot API 漂移 | `version_matrix` 钉 commit；适配层隔离 |
| 包整理与 B1 并行冲突 | **禁止并行**；且 B0 不得早于 Design |
| 磁盘爆（jpg） | fps=10、320×240；可选只保留 export 后删 raw |
| 期望过高 | 验收写清：B1=数据契约；B3=冒烟非 SOTA |

---

## 10. 建议立即拍板的 3 件事（延后到 Design 评审）

编码前请先确认 RES-L1-REQ-01 v0.2。下列问题改在 Design 里闭合，不在未确认需求时拍板开工：

1. **采图方案**：ROS Image topic vs 离线刷帧——属 C1，Design 后实施。  
2. **ACT 是否本迭代必达**：REQ 将 ACT 放在 S1，且要求先并环、写清 action_schema。  
3. **LeRobot / torch** 环境：写入 TECH-04，仍不阻塞 S0 接口设计。

---

## 11. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-08-10 | 首版：B0 整理 + B1 相机 + B2 obs + B3 ACT 切片 |
| v0.2 | 2026-08-14 | B0 非前置；服从 REQ v0.2；先 Design 再 B1–B3 |

---

*PLAN-SR-B-01 v0.2 · 暂停编码 · 仿真加深 L1 / 学能力 B*
