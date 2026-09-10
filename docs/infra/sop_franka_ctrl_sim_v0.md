# SOP：Franka CTRL-SIM（v0）

| 属性 | 内容 |
|------|------|
| **文档编号** | SOP-CTRL-SIM-01 |
| **版本** | v0.1 |
| **日期** | 2026-08-07 |
| **角色** | M6 操作手册 · DOMAIN **43** · lab-ws-02 |
| **结构** | [PLAN-STRUCT-01](../plan/lab_strategy_runtime_structure_v0.md) |
| **进度** | [INFRA-02](phase1_validation_plan_v1.md) §1 / §十 |

本 SOP 把入口拆成两条：**控制回归** vs **学习实验**。两条都经 L0（`lab`），禁止绕过 `run_id` 做正式归档。

---

## 0. 入口分流（先选路径）

| 你要做的事 | 入口 | 产物 |
|------------|------|------|
| Mid / Scene / 桥接冒烟；不关心训练 | `lab ctrl-sim run --profile m2_hello\|m5_*` | A 轨 `logs/low.jsonl` + `manifest.json` |
| 抓放闭环验收 | `lab ctrl-sim run --profile m5_pickplace` | A 轨 + `eval.json` |
| 导出学习集 | `lab data export --run-id … --format lerobot-v3` | B 轨 dataset + Index `ds_*`（默认注册） |
| 训 state MLP | `lab policy train --dataset …` | `policy.npz` + Index `pol_*`（默认注册） |
| 策略上机 rollout | `lab policy rollout --checkpoint <path\|policy_id>` 或 `ctrl-sim run --profile m5_policy_rollout` | 新 run；manifest 写 `policy_id` |

默认 **注册 Index**；仅本地试跑加 `--no-register`。

---

## 1. 环境（每次开跑）

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=43
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source ~/project/embodied__ai_lab/ros2/install/setup.bash

cd ~/project/embodied__ai_lab/lab_platform
source .venv/bin/activate
export PYTHONPATH=$PWD:$(cd .. && pwd)/strategy_runtime:$PYTHONPATH

# 数据根（按本机约定）
export LAB_DATA_ROOT=~/embodied-ai-lab-data   # 若 CLI 支持；否则始终传 --data-root
DATA=~/embodied-ai-lab-data
```

检查：`echo $ROS_DOMAIN_ID` → `43`。真机域是 42，禁止混域。

---

## 2. 启动顺序

1. **Isaac Sim 6**：加载 Task Pack 场景（`tabletop_pickplace_v0` 组装后的 USDA）。  
2. **不要**手动长期 HOLD 旧 bridge；Isaac Reset 后 **必须重启** `franka_ctrl_sim` / bridge，否则关节被旧 HOLD 锁死。  
3. Lab 可自动 launch：`lab … ctrl-sim run …`（缺 topic 时拉起 bringup）。仅附着已有栈时加 `--no-launch`。  
4. 需要保留 lab 拉起的 launch：加 `--keep-launch`。

期望 Home EE 约 `(0.31, 0, 0.49)`；异常先查 bridge HOLD，再查场景 pin。

---

## 3. 控制回归（推荐日检）

```bash
lab --data-root "$DATA" ctrl-sim run \
  --scene tabletop_pickplace_v0 \
  --profile m5_pickplace \
  --keep-launch
```

看终端 JSON：`run_id`、`status`、`recorded`、`manifest`。

落盘：

- `$DATA/runs/ctrl_sim/<run_id>/manifest.json`
- `$DATA/runs/ctrl_sim/<run_id>/logs/low.jsonl`
- `$DATA/runs/ctrl_sim/<run_id>/logs/eval.json`（pickplace）

回放 A 轨：

```bash
lab --data-root "$DATA" ctrl-sim replay --run-id <run_id> --keep-launch
```

冒烟可用 `m2_hello`；薄 Mid 用 `m5_template` / `m5_approach_target`。

---

## 4. 学习实验（A→B→policy→rollout）

### 4.1 导出 B 轨（默认注册）

```bash
lab --data-root "$DATA" data export \
  --run-id <run_id> \
  --format lerobot-v3 \
  --overwrite
```

得到 `dataset_id`（形如 `ds_<run_id>`）与 `datasets/lerobot_v3/<run_id>/`。源 run manifest `tracks.B` 含互链。

### 4.2 训练（默认注册）

```bash
lab --data-root "$DATA" policy train \
  --dataset ds_<run_id_a> \
  --dataset ds_<run_id_b> \
  --policy-id pol_state_p4_mvp \
  --epochs 80
```

也可用相对路径：`--dataset datasets/lerobot_v3/<run_id>`。

### 4.3 Rollout

```bash
lab --data-root "$DATA" policy rollout \
  --checkpoint pol_state_p4_mvp \
  --keep-launch
```

或 `--checkpoint $DATA/artifacts/policies/pol_state_p4_mvp/policy.npz`。

### 4.4 列表与血缘

```bash
lab --data-root "$DATA" list --artifacts
lab --data-root "$DATA" list --artifacts --artifact-type dataset
lab --data-root "$DATA" list --artifacts --artifact-type policy
lab --data-root "$DATA" lineage <run_id>
```

期望链：`collect run` → `dataset (ds_*)` → `policy (pol_*)` → `rollout run`（upstream=policy）。

---

## 5. 正常停止与软件急停

- 正常结束：等 `lab` 退出；未加 `--keep-launch` 时 lab 会停自己拉起的 bringup。  
- 软件急停：停 Isaac 播放 / kill bridge launch；勿在 DOMAIN 43 上同时跑第二套互抢关节命令。  
- 清理僵尸：`ros2 daemon stop`（按需）后确认 `ROS_DOMAIN_ID=43` 再开。

---

## 6. 常见故障（短表）

| 现象 | 先查 |
|------|------|
| EE 不在 Home / 乱动 | Isaac Reset 后未重启 bridge；旧 HOLD `/joint_command` |
| PreFlight 拒 scene | 场景 pin / `action_schema` / cameras；勿用遗留 min scene |
| 无 `low.jsonl` | 正式 run 勿加 `--no-record` |
| `rclpy` / msgs 缺失 | 未 source jazzy + `ros2/install` |
| topic 全空 | DOMAIN 不是 43，或 CycloneDDS 未设 |
| dataset/policy 找不到 | 是否 `--no-register`；`lab list --artifacts` |
| rollout 找不到 checkpoint | 传 `policy_id` 或绝对 `policy.npz` |

更细故障表见 INFRA-02 §六.9。

---

## 7. M6 验收勾选

**手动端到端详细清单：**  
[`sop_franka_ctrl_sim_e2e_validation_v0.md`](sop_franka_ctrl_sim_e2e_validation_v0.md) → **PASS（2026-08-07）**

- [x] **控制回归**（`m5_pickplace`）  
- [x] **学习路径**（export / train 或已有 policy → rollout → lineage）  
- [x] 入口分流与 `--no-register` 含义确认  

下一阶段真机：[`phase2_franka_real_e2e_plan_v0.md`](phase2_franka_real_e2e_plan_v0.md)。

---

*sop_franka_ctrl_sim_v0 · M6 · 与 STRUCT P5 / Index 默认注册对齐*
