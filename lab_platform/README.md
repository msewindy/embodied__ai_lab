# Lab Platform（L0 Lab OS）

实验室运行框架：Run 治理、PreFlight、Index、CTRL-SIM 编排、A/B 数据轨与策略注册。

结构 SSOT：[PLAN-STRUCT-01](../docs/plan/lab_strategy_runtime_structure_v0.md)  
操作手册：[SOP-CTRL-SIM](../docs/infra/sop_franka_ctrl_sim_v0.md)  
进度：[INFRA-02](../docs/infra/phase1_validation_plan_v1.md)

## 能力分层

| 层 | 内容 |
|----|------|
| **真实（主路径）** | Index / PreFlight / Locks · `ctrl_sim` · A 轨录制 · B 轨 export · `ArtifactHub` · `lerobot_state` 训/rollout |
| **真实（ROS2）** | `/system/run_context`（CTRL-SIM）· 依赖 `ros2/franka_sim_bridge` |
| **Stub（后置）** | Pipeline A 真 Isaac train · 真机 Real 栈 · gap 分析 |

## CTRL-SIM 快速开始（DOMAIN 43）

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=43 RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source ~/project/embodied__ai_lab/ros2/install/setup.bash

cd ~/project/embodied__ai_lab/lab_platform
source .venv/bin/activate
# L0 + L1（strategy_runtime）须同时在路径中
export PYTHONPATH=$PWD:$(cd .. && pwd)/strategy_runtime:$PYTHONPATH
DATA=~/embodied-ai-lab-data

# 控制回归（抓放）
lab --data-root "$DATA" ctrl-sim run \
  --scene tabletop_pickplace_v0 --profile m5_pickplace --keep-launch

# 学习路径
lab --data-root "$DATA" data export --run-id <cs_…> --format lerobot-v3
lab --data-root "$DATA" policy train --dataset ds_<…> --policy-id pol_state_p4_mvp
lab --data-root "$DATA" policy rollout --checkpoint pol_state_p4_mvp --keep-launch

lab --data-root "$DATA" list --artifacts
lab --data-root "$DATA" lineage <run_id>
```

Isaac Reset 后须重启 bridge（见 SOP）。默认录 A、默认注册 Index；`--no-record` / `--no-register` 退出。

## 骨架冒烟（无 Isaac）

```bash
cd lab_platform
pip install -e .   # 或 PYTHONPATH=$PWD
lab init
lab demo full
lab list
```

## 包结构（摘要）

```text
lab_platform/                 # L0
├── cli.py
├── ctrl_sim/                 # launcher · recorder · export · task_pack（L1 为 shim）
├── artifacts/ · index/ · preflight/ · run_manager/
└── stubs/

strategy_runtime/             # L1（兄弟包）
└── mid_template · policy_* · oracle · eval
```

Task Pack（L2）：`tasks/tabletop_pickplace_v0/`。  
ROS2：`ros2/franka_sim_bridge`、`ros2/embodied_lab_bringup`。  
L1 说明：[`strategy_runtime/README.md`](../strategy_runtime/README.md)。
