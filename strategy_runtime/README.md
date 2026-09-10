# Strategy Runtime（L1）

**职责：** MidGoal 调度、世界上下文（Oracle / SceneTargets）、PolicyBackend、成功谓词。  
**非职责：** `run_id` / PreFlight / Index / 录制导出（→ `lab_platform` L0）；场景资产（→ `tasks/` L2）。

**现状（勿把目标当已实现）：** `PolicyObs` 现为 8 维 state；Oracle 为 YAML 名义位姿；`mid_template` 与 `policy_rollout` 仍是两条环。口径见 [RES-L1-REQ-01](../docs/research/l1_framework_requirements_v0.md) §1.1。

结构 SSOT：[PLAN-STRUCT-01](../docs/plan/lab_strategy_runtime_structure_v0.md) §4 / §11。目的：[宪章](../docs/plan/lab_charter_v0.md)。

## 安装 / 路径

```bash
# 推荐：与 lab_platform 一并进 PYTHONPATH
export REPO=~/project/embodied__ai_lab
export PYTHONPATH=$REPO/lab_platform:$REPO/strategy_runtime:$PYTHONPATH

# 或 editable
cd $REPO/strategy_runtime && pip install -e .
```

## 模块

| 模块 | 说明 |
|------|------|
| `mid_template` | MidGoal 播放（相对 / toward / pickplace） |
| `policy_backend` | PolicyBackend 协议与工厂 |
| `lerobot_state_policy` | state MLP 后端 |
| `policy_train` / `policy_rollout` | 训 / 推 |
| `oracle_gt` / `scene_targets` | 世界上下文（仿真 GT / 命名目标） |
| `eval_pickplace` | 抓放成功谓词 |

## 进程形态（已钉死）

- **默认：** 由 L0 `lab ctrl-sim` **子进程**拉起（脚本入口仍在 `lab_platform/scripts/`）。  
- **非默认：** 独立 ROS Mid 节点（后置；接口稳定后再拆）。

## 与 L0 边界

- L0 `lab_platform.ctrl_sim` **只保留** launcher / recorder / replayer / export / task_pack。  
- 旧 import `lab_platform.ctrl_sim.mid_template` 等为 **兼容 shim**，新代码请 `import strategy_runtime…`。
