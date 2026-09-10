# CTRL-SIM 端到端验证手册（M6 手动验收）

| 属性 | 内容 |
|------|------|
| **文档编号** | SOP-CTRL-SIM-E2E-01 |
| **版本** | v0.1 |
| **日期** | 2026-08-07 |
| **状态** | **PASS**（手动验收完成 · 2026-08-07） |
| **用途** | 按清单**手动**跑通控制回归 + 学习闭环；留下 `run_id` 与勾选纪要 |
| **日常操作** | 精简版见 [SOP-CTRL-SIM-01](sop_franka_ctrl_sim_v0.md) |
| **进度看板** | [INFRA-02 §1 / §12](phase1_validation_plan_v1.md) |
| **下一阶段** | [真机 FR3 E2E 计划](phase2_franka_real_e2e_plan_v0.md) |
| **主机** | lab-ws-02 · Isaac Sim 6 · `ROS_DOMAIN_ID=43` |

---

## 0. 验证目标与范围

### 0.1 要通过什么

| 线 | 目标 | 最短成功判据 |
|----|------|--------------|
| **A. 控制回归** | L0 编排 + Mid 抓放 + A 轨 | `status=completed`；`eval.json` success；`low.jsonl` 有帧 |
| **B. 学习闭环** | A→B→policy→rollout + Index | `ds_*`/`pol_*` 在 Index；rollout 有 `policy_id`；`lineage` 可解释 |

### 0.2 不在本次范围

- 真机 DOMAIN 42、围栏急停  
- ACT / 视觉 / 相机 B 轨  
- 非作者交叉签字（可另日；本次可自验并填纪要）  
- 重训到最优（可用已有 `pol_state_p4_mvp`；可选短训确认注册）

### 0.3 预计耗时

| 模式 | 时间 |
|------|------|
| 完整（含 assemble 确认 + pickplace + export + 可选短训 + rollout + lineage） | **45–90 min** |
| 加速（场景已开、政策已训：只跑 pickplace + rollout + lineage） | **20–35 min** |

### 0.4 记录表（边跑边填）

| 字段 | 填写 |
|------|------|
| 日期 / 操作者 | |
| 主机 | lab-ws-02 |
| `DATA` | `~/embodied-ai-lab-data` |
| git commit（可选） | `git -C ~/project/embodied__ai_lab rev-parse --short HEAD` |
| 控制回归 `run_id` | |
| export `dataset_id` | |
| 训练/使用 `policy_id` | `pol_state_p4_mvp`（或新建） |
| rollout `run_id` | |
| 结论 | PASS / FAIL（附失败步骤号） |

---

## 1. 前置条件（开跑前一次检查）

### 1.1 软件与域

在**同一个**终端（或每个新终端都重复）：

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=43
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source ~/project/embodied__ai_lab/ros2/install/setup.bash

cd ~/project/embodied__ai_lab/lab_platform
source .venv/bin/activate
export PYTHONPATH=$PWD:$(cd .. && pwd)/strategy_runtime:$PYTHONPATH

DATA=~/embodied-ai-lab-data
echo "DOMAIN=$ROS_DOMAIN_ID RMW=$RMW_IMPLEMENTATION"
which lab || python -c "import lab_platform; print('ok', lab_platform.__file__)"
```

| # | 检查 | 期望 | ☐ |
|---|------|------|---|
| P1 | `echo $ROS_DOMAIN_ID` | `43` | ☐ |
| P2 | `echo $RMW_IMPLEMENTATION` | `rmw_cyclonedds_cpp` | ☐ |
| P3 | `ros2 pkg prefix franka_sim_bridge` | 有路径、无报错 | ☐ |
| P4 | `python -c "import embodied_lab_msgs"` | 无 ImportError | ☐ |
| P5 | `$DATA` 可写 | `mkdir -p "$DATA" && touch "$DATA/.write_test" && rm "$DATA/.write_test"` | ☐ |

若 `lab` 命令不存在，下文一律用：

```bash
alias lab='python -m lab_platform.cli'
# 或每次：python -m lab_platform.cli --data-root "$DATA" ...
```

### 1.2 Task Pack / 场景文件

```bash
PACK=~/project/embodied__ai_lab/tasks/tabletop_pickplace_v0
ls "$PACK/scene.yaml" "$PACK/assets/tabletop_pickplace_v0.usda"
# 若改过 scene.yaml / 脚本，重组装：
# python "$PACK/scripts/assemble_scene_usd.py"
```

| # | 检查 | 期望 | ☐ |
|---|------|------|---|
| P6 | USDA 存在且较新 | `tabletop_pickplace_v0.usda` | ☐ |
| P7 | `scene.yaml` 含 `q_home_rad` | `[0, -0.785, 0, -2.356, 0, 1.571, 0.785]` | ☐ |
| P8 | 政策权重（加速模式） | `ls $DATA/artifacts/policies/pol_state_p4_mvp/policy.npz` | ☐ |

### 1.3 Isaac Sim

1. 启动 **Isaac Sim 6**。  
2. **File → Open** 打开：

   `~/project/embodied__ai_lab/tasks/tabletop_pickplace_v0/assets/tabletop_pickplace_v0.usda`

   （不要只开裸 `frankaFR3.usd` 做本验收。）  
3. 确认 ROS2 bridge / JointStates 按本机 M2 钉扎可用（见 `lab_platform/scripts/m2_env_pin.md`）。  
4. **Play**。  
5. 目视关节 Home：约 `joint2≈-45°`、`joint4≈-135°`；EE 名义 ≈ **`(0.31, 0, 0.49)`**（相对 `fr3_link0`）。  
6. 若刚 **Reset**：必须在下一步 **杀掉并重启** bridge（见 §2），不要沿用旧 HOLD。

| # | 检查 | ☐ |
|---|------|---|
| P9 | Stage 已 Play，臂在 Home 姿态 | ☐ |
| P10 | 未残留「上次 lab 已退出但 bridge 仍 HOLD」的未知状态（不确定则重启 bridge） | ☐ |

---

## 2. Bridge 就绪（两种方式选一）

### 方式 A — 交给 Lab 自动 launch（推荐）

不手动 launch。后面 `ctrl-sim run` **不加** `--no-launch`，加 `--keep-launch` 以便连续跑多条。

### 方式 B — 手动 launch（便于观察 topic）

**新终端**（同样 source 环境，DOMAIN=43）：

```bash
ros2 launch embodied_lab_bringup franka_ctrl_sim.launch.py \
  device_id:=franka-01 backend:=isaac_sim
```

另开终端检查：

```bash
export ROS_DOMAIN_ID=43 RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source /opt/ros/jazzy/setup.bash
source ~/project/embodied__ai_lab/ros2/install/setup.bash
ros2 topic list | grep -E 'joint_states|skill/franka|low_state|run_context'
```

| # | Topic（应出现） | ☐ |
|---|----------------|---|
| B1 | `/joint_states` | ☐ |
| B2 | `/joint_command` | ☐ |
| B3 | `/skill/franka_01/intent` | ☐ |
| B4 | `/perception/franka_01/low_state` | ☐ |

可选冒烟（不计入正式 `run_id`）：

```bash
cd ~/project/embodied__ai_lab/lab_platform
python3 scripts/m2_franka_hello.py --dx 0.05 --domain 43
```

期望：脚本 PASS；停发后 HOLD。

**铁律：** Isaac Reset / 重新 Open 场景后 → **Ctrl+C 掉 launch → 再 launch**（或让下次 `lab` 重新拉起）。

---

## 3. 线 A — 控制回归（`m5_pickplace`）

### 3.1 执行

在 lab 终端：

```bash
lab --data-root "$DATA" ctrl-sim run \
  --scene tabletop_pickplace_v0 \
  --profile m5_pickplace \
  --keep-launch
```

**不要**加 `--no-record`（正式验收要 A 轨）。

### 3.2 终端 JSON 验收

记下输出中的 `run_id`，记入 §0.4 表。

| # | 字段 | 期望 | ☐ |
|---|------|------|---|
| A1 | `status` | `completed` | ☐ |
| A2 | `recorded` | `true` | ☐ |
| A3 | `record_frames` | ≥ 1（典型 200+） | ☐ |
| A4 | `ros_domain_id` | `43` | ☐ |
| A5 | `manifest` | 路径存在 | ☐ |

失败：看同目录 `logs/` 下 profile / mid / preflight 日志；常见原因见 §7。

### 3.3 落盘验收

```bash
RID=<填入控制回归 run_id>
RUN="$DATA/runs/ctrl_sim/$RID"
ls -la "$RUN/manifest.json" "$RUN/logs/low.jsonl" "$RUN/logs/eval.json" "$RUN/logs/mid_steps.json"
wc -l "$RUN/logs/low.jsonl"
python3 - <<PY
import json
from pathlib import Path
run = Path("$RUN")
man = json.loads((run/"manifest.json").read_text())
ev = json.loads((run/"logs/eval.json").read_text())
print("tracks.A frames:", (man.get("tracks") or {}).get("A", {}).get("num_frames"))
print("eval.success:", ev.get("success"))
print("predicates:", ev.get("predicates"))
print("scene:", man.get("task_pack", {}).get("scene_id") or man.get("scene_id"))
PY
```

| # | 检查 | 期望 | ☐ |
|---|------|------|---|
| A6 | `logs/low.jsonl` | 行数 ≥ 50 | ☐ |
| A7 | `logs/eval.json` → `success` | `true` | ☐ |
| A8 | predicates | 含 place 相关 ok（如 `place_horizontal_ok` / `place_clearance_ok`） | ☐ |
| A9 | `logs/mid_steps.json` | 六步 mid 大体 success | ☐ |
| A10 | manifest 含 task_pack / scene 快照引用 | 有 `task_pack` 或 `logs/scene.yaml` | ☐ |

### 3.4（推荐）A 轨回放

Isaac 仍 Play、bridge 仍在：

```bash
lab --data-root "$DATA" ctrl-sim replay --run-id "$RID" --keep-launch
```

| # | 检查 | ☐ |
|---|------|---|
| A11 | replay 退出码 0 / 无明显 topic 错误 | ☐ |

### 3.5 线 A 通过门

**A1–A8 全勾** → 线 A PASS。A9–A11 强烈建议。

---

## 4. 线 B — 学习闭环

> 加速模式：若 Index 里已有三跑 dataset + `pol_state_p4_mvp`，可跳过 §4.1–4.2，从 §4.3 rollout 开始；仍建议做一次 `list --artifacts` 确认。

### 4.1 Export（A→B，默认注册）

```bash
lab --data-root "$DATA" data export \
  --run-id "$RID" \
  --format lerobot-v3 \
  --overwrite
```

| # | 检查 | 期望 | ☐ |
|---|------|------|---|
| B1 | JSON `registered` | `true` | ☐ |
| B2 | `dataset_id` | `ds_<run_id 中 - 变 _>` | ☐ |
| B3 | 目录 | `$DATA/datasets/lerobot_v3/$RID/data/...` 存在 | ☐ |
| B4 | 源 manifest `tracks.B.dataset_id` | 与 B2 一致 | ☐ |

```bash
python3 - <<PY
import json
from pathlib import Path
man = json.loads(Path("$RUN/manifest.json").read_text())
print(man.get("tracks", {}).get("B"))
PY
```

### 4.2 训练（可选；验证注册链路）

**选项 B2a — 使用已有政策（加速）**

```bash
ls "$DATA/artifacts/policies/pol_state_p4_mvp/policy.npz"
PID=pol_state_p4_mvp
```

**选项 B2b — 短训冒烟注册（5 epoch 即可，仅验 Index）**

```bash
lab --data-root "$DATA" policy train \
  --dataset "ds_${RID//-/_}" \
  --policy-id pol_e2e_smoke \
  --epochs 5
PID=pol_e2e_smoke
```

> 注意：`dataset_id` 里 run_id 的 `-` 已换成 `_`。也可用路径：  
> `--dataset "datasets/lerobot_v3/$RID"`

| # | 检查 | 期望 | ☐ |
|---|------|------|---|
| B5 | train JSON `registered` | `true`（未加 `--no-register`） | ☐ |
| B6 | `policy.npz` 存在 | `$DATA/artifacts/policies/$PID/policy.npz` | ☐ |

**选项 B2c — 正式质量（可选）**  
若要用历史三跑重训 MVP：

```bash
lab --data-root "$DATA" policy train \
  --dataset ds_cs_20260806_174016_p2_franka_01 \
  --dataset ds_cs_20260806_174048_p2_franka_01 \
  --dataset ds_cs_20260806_174118_p2_franka_01 \
  --policy-id pol_state_p4_mvp \
  --epochs 80
PID=pol_state_p4_mvp
```

### 4.3 Index 列表

```bash
lab --data-root "$DATA" list --artifacts
lab --data-root "$DATA" list --artifacts --artifact-type dataset
lab --data-root "$DATA" list --artifacts --artifact-type policy
```

| # | 检查 | ☐ |
|---|------|---|
| B7 | 能看到本次 `ds_*` 与 `$PID` | ☐ |

### 4.4 策略 Rollout

确认 Isaac Play + bridge 健康（Reset 过则先重启 bridge）：

```bash
lab --data-root "$DATA" policy rollout \
  --checkpoint "$PID" \
  --keep-launch
```

记下新的 `run_id` → `RID_RO`。

| # | 检查 | 期望 | ☐ |
|---|------|------|---|
| B8 | `status` | `completed`（或按当前策略能力：有 `n_pub>0` 且无崩溃） | ☐ |
| B9 | JSON `policy_id` | 等于 `$PID` | ☐ |
| B10 | manifest `policy.policy_id` / `policy.checkpoint` | 有值 | ☐ |
| B11 | `logs/policy_steps.json` | 存在；`n_pub` ≥ 1 | ☐ |

```bash
RID_RO=<rollout run_id>
python3 - <<PY
import json
from pathlib import Path
run = Path("$DATA/runs/ctrl_sim/$RID_RO")
man = json.loads((run/"manifest.json").read_text())
steps = json.loads((run/"logs/policy_steps.json").read_text())
print("policy:", man.get("policy"))
print("n_pub:", steps.get("n_pub"), "n_hold:", steps.get("n_hold"), "success:", steps.get("success"))
PY
```

> 说明：state MLP MVP **不保证**每次抓放 `eval.success=true`；本线硬门禁是 **能加载 id、发布动作、落盘可审计**。若 `success=true` 可记为加分。

### 4.5 血缘

```bash
lab --data-root "$DATA" lineage "$RID"
lab --data-root "$DATA" lineage "$RID_RO"
```

| # | 检查 | 期望 | ☐ |
|---|------|------|---|
| B12 | collect lineage | `dataset_id` 有；`downstream` 含 `ds_*`（训练后还可含 `pol_*`） | ☐ |
| B13 | rollout lineage | `policy_id` 有；`upstream` 含 policy **或** manifest.policy 可追溯 | ☐ |

### 4.6 线 B 通过门

**最低：** B7 + B8–B11 + B13（用已有政策）。  
**完整：** 再加上 B1–B6 + B12。

---

## 5. 入口分流口头确认（M6）

操作者应能回答（自检打勾）：

| # | 问题 | ☐ |
|---|------|---|
| C1 | 控制回归入口是什么？ | ☐ `lab ctrl-sim run --profile m5_*` |
| C2 | 学习入口是什么？ | ☐ `data export` / `policy train` / `policy rollout` |
| C3 | `--no-register` 做什么？ | ☐ 不写 Index，仍可落盘 |
| C4 | `--no-record` 做什么？ | ☐ 关闭 A 轨（正式验收禁用） |
| C5 | Isaac Reset 后第一件事？ | ☐ 重启 bridge / 勿沿用旧 HOLD |

---

## 6. 正常收尾

1. 等当前 `lab` 命令退出。  
2. 若需停桥：在 launch 终端 Ctrl+C。  
3. Isaac：Stop / 退出均可。  
4. 可选：`ros2 daemon stop`（下次记得重新 source + DOMAIN=43）。  
5. 把 §0.4 记录表 + 下方签字填进实验笔记或 PR/纪要。

---

## 7. 故障速查（验证现场）

| 步骤 | 现象 | 处理 |
|------|------|------|
| §1 | `embodied_lab_msgs` 导入失败 | `source ros2/install/setup.bash`；必要时 `colcon build --packages-up-to embodied_lab_msgs franka_sim_bridge` |
| §2 | topic 列表空 | 确认 DOMAIN=43；Isaac Play；bridge 进程在 |
| §3 | EE 飞到天上 / 不在 Home | **Reset 后未重启 bridge**；重启 launch 再跑 |
| §3 | PreFlight 失败 | 场景是否 Task Pack；看报错 PF-CS-*；勿用 legacy min scene |
| §3 | `eval.success=false` | 看 mid_steps 哪步失败；碗/杯是否弹飞（USD 防弹）；重开场景再跑一轮 |
| §4 | `dataset not found` | 用 `ds_…`（`-`→`_`）或相对 `datasets/lerobot_v3/...` |
| §4 | rollout 无 checkpoint | `list --artifacts --artifact-type policy`；确认未 `--no-register` |
| §4 | rollout 臂不动 | bridge HOLD / 未 Play / 错 DOMAIN |

更全：INFRA-02 §六.9 · SOP-CTRL-SIM-01 §6。

---

## 8. 验收结论模板（复制填写）

```text
### M6 E2E 验证纪要
日期：
操作者：
DATA：~/embodied-ai-lab-data
git：

线 A（控制回归）
  run_id：
  eval.success：
  low.jsonl 行数：
  结果：PASS / FAIL

线 B（学习闭环）
  dataset_id：
  policy_id：
  rollout run_id：
  n_pub：
  lineage 可解释：是 / 否
  结果：PASS / FAIL

入口分流口头确认：是 / 否

总评：PASS / FAIL
备注（失败步骤号 / 截图路径）：
```

### 总评门禁

| 级别 | 条件 |
|------|------|
| **PASS** | 线 A PASS + 线 B 最低集 PASS + §5 口头确认 |
| **有条件 PASS** | 线 A PASS；线 B 仅 list/lineage、rollout 因机时未跑（须写明） |
| **FAIL** | 线 A 失败，或无法生成可审计 `run_id` |

---

## 9. 命令速查（单页）

```bash
# 环境
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=43 RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source ~/project/embodied__ai_lab/ros2/install/setup.bash
cd ~/project/embodied__ai_lab/lab_platform && source .venv/bin/activate
export PYTHONPATH=$PWD:$(cd .. && pwd)/strategy_runtime:$PYTHONPATH
DATA=~/embodied-ai-lab-data

# 线 A
lab --data-root "$DATA" ctrl-sim run \
  --scene tabletop_pickplace_v0 --profile m5_pickplace --keep-launch

# 线 B
lab --data-root "$DATA" data export --run-id <RID> --format lerobot-v3 --overwrite
lab --data-root "$DATA" policy train --dataset ds_<…> --policy-id pol_state_p4_mvp --epochs 80
lab --data-root "$DATA" policy rollout --checkpoint pol_state_p4_mvp --keep-launch
lab --data-root "$DATA" list --artifacts
lab --data-root "$DATA" lineage <RID>
lab --data-root "$DATA" lineage <RID_RO>
```

---

## 10. 验收记录（收口）

| 项 | 内容 |
|----|------|
| 总评 | **PASS** |
| 日期 | 2026-08-07 |
| 说明 | 操作者按本清单完成线 A（控制回归）+ 线 B（学习闭环最低集）+ 入口分流确认 |
| 看板 | INFRA-02 v1.4.7 · M6 → ✅ E2E |

（具体 `run_id` 以操作者实验笔记 / §8 模板为准；需要时可回填本表。）

---

*SOP-CTRL-SIM-E2E-01 v0.1 · PASS 2026-08-07 · 下一阶段真机 FR3*
