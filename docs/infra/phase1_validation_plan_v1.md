# Phase 1 验证测试方案 v1.0

| 属性 | 内容 |
|------|------|
| **文档编号** | INFRA-02 |
| **版本** | v1.0 |
| **维护人** | P2 |
| **依据** | [TECH-14 As-Built](../architecture/platform_architecture_as_built_v1.md) · [INFRA-01 环境清单](./env_setup_checklist_v1.md) · [TECH-02 ROS2 接口](../software/ros2_interface_v1.md) |
| **首台设备** | `quadruped-01`（Unitree Go2） |
| **用途** | Phase 1 逐步验收：Walking Skeleton → Go2 sim bringup → ws-02 Sim → 真机 |

---

## 〇、 当前进度（手动更新）

| ID | 场景 | 节点 | 状态 | 完成日 |
|----|------|------|:----:|--------|
| **E0** | 代码仓库 + 网络 | ws-01/02 | ✅ | |
| **E1** | Skeleton 全流程冒烟 | ws-02 | ⬜ | |
| **E2** | ROS2 三包编译 | ws-01 | ✅ | 2026-06-16 |
| **E3** | Go2 sim real_bringup | ws-01 | ✅ | 2026-06-16 |
| **E4** | 跨机 Topic（真机 onboard） | ws-01 + Go2 | ⬜ | |
| **E5** | Isaac train smoke | ws-02 | ⬜ | |
| **E6** | checkpoint 同步 | ws-02 → ws-01 | ⬜ | |
| **E7** | 真机 real_bringup | ws-01 + Go2 | ⬜ | |

**Phase 1 最低交付**：E1 + E2 + E3（ws-01 sim 栈）✅ 已达成 ws-01 侧。  
**Phase 1 完整交付**：E1～E7 全部通过。

---

## 一、 框架骨架：真实 vs 占位（对照表）

### 1.1 Python 框架 `lab_platform/`

| 模块 | 实现 | 状态 | 说明 |
|------|------|:----:|------|
| **RunManager** | `run_manager/manager.py` | **真实** | PreFlight → Lock → 目录 → 执行 → Artifact → Release |
| **IndexService** | `index/service.py` SQLite | **真实** | runs / artifacts / locks / lineage |
| **PreFlightGate** | `preflight/gate.py` | **真实** | PF 子集；读 registry yaml |
| **ResourceScheduler** | `scheduler/locks.py` | **真实** | device_lock；Z-DYN ≤ 2 台 |
| **ArtifactRegistry** | `artifacts/registry.py` | **真实** | Policy / Demo / Eval / Calibration 注册 |
| **Pipeline A 收录** | `pipelines/pipeline_a.py` | **真实** | Isaac 产出扫描与注册逻辑 |
| **IsaacLauncher** | `stubs/isaac_launcher.py` | **Stub** | sleep + 假 checkpoint，未调 Isaac CLI |
| **RealRuntime 主体** | `stubs/real_runtime.py` | **Stub** | collect / deploy / eval / calibrate 均为假 |
| **bringup（sim）** | `pipeline_c/bringup_runner.py` | **真实** | BU-01～06 ROS 真检查（需 launch 已起） |
| **Ros2Bridge** | `pipeline_c/ros2_runtime.py` | **混合** | `--ros` 时真发 `/system/run_context`；否则 Stub 打印 |
| **GapAnalyzer** | `stubs/gap_analyzer.py` | **Stub** | 固定 gap 百分比 |

### 1.2 ROS2 栈 `ros2/`（Go2 首台）

| 包 | 状态 | 说明 |
|----|:----:|------|
| `embodied_lab_msgs` | **真实** | TECH-02 msg/srv；已 colcon 编译 |
| `go2_driver_bridge` | **真实** | sim 100Hz 感知；real 模式 relay Unitree topic |
| `embodied_lab_bringup` | **真实** | launch + safety + limiter + run_context |

**Topic 命名约定**：台账 `device_id` 用 `quadruped-01`；ROS topic 段用 `quadruped_01`（`-` → `_`）。

### 1.3 尚未实现（Phase 2+）

- F6B 慢环（Perception 融合 / SkillIntent 发布）
- F6C 快环（policy_runner_low / WBC）
- 真 RosbagRecorder（mcap）
- Isaac Lab 真子进程
- LabOpsMonitor
- IndexService HTTP 跨机

---

## 二、 验证测试要得到什么（最终产物）

Phase 1 不是「跑通 demo 脚本」本身，而是证明 **Sim2Real 闭环的基础设施可用**：

| 层级 | 验收产物 | 含义 |
|------|----------|------|
| **L0 编排** | E1：`smoke_test.py` ALL PASSED | Run 生命周期 + 索引 + 锁 + Stub 全链路可重复 |
| **L1 通信** | E3：`bringup_report.json` overall=pass；Bridge **L1** | ws-01 ROS 域内 Go2 栈 + BU 检查通过（sim） |
| **L1 真机** | E7：同上，`--no-sim` | onboard Driver Bridge 接真机 SDK |
| **Sim 策略源** | E5：PolicyArtifact 入库 | ws-02 Isaac 训练产出可被框架登记 |
| **跨机数据** | E6：policy 目录 ws-02→ws-01 可读 | deploy 前置的文件同步通路 |
| **跨机 DDS** | E4：ws-01 收到 onboard joint_states ≥50Hz | 局域网 ROS2 域连通 |

**E3 已通过时你应已有**（ws-01）：

```text
~/embodied-ai-lab-data/runs/real_bringup/rb_*/results/bringup_report.json  # BU-01..06 pass
~/embodied-ai-lab-data/registry/bridge_maturity.yaml                       # quadruped-01: L1
~/embodied-ai-lab-data/index.db                                           # run 已索引
```

---

## 三、 逐步执行手册

> 环境安装细节见 [INFRA-01](./env_setup_checklist_v1.md)。本节只写**验证步骤**与**通过标准**。

### 步骤 E1 — ws-02 Skeleton 冒烟

**目的**：确认 Python 框架在 ws-02 可独立运行（无需 ROS2）。

```bash
cd ~/project/embodied__ai_lab/lab_platform
python3 -m venv .venv && source .venv/bin/activate   # 若尚未建 venv
pip install -U pip && pip install -e .

# 可选：清空后全量测
python scripts/smoke_test.py
```

**通过**：最后一行 `=== ALL SMOKE TESTS PASSED ===`

**失败排查**：看 PreFlight / 并发测试输出；确认 `data/` 可写。

---

### 步骤 E2 — ws-01 ROS2 编译（已完成可跳过）

```bash
deactivate 2>/dev/null || true   # 勿在 venv 里 colcon
cd ~/project/embodied__ai_lab/ros2
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash

ros2 pkg list | grep -E 'embodied_lab|go2_driver'
```

**通过**：三包可见；`ros2 interface show embodied_lab_msgs/msg/RunContext` 含 `operator_id`。

---

### 步骤 E3 — ws-01 Go2 sim bringup（已完成可跳过）

**终端 1**（系统 ROS，不进 venv）：

```bash
source /opt/ros/jazzy/setup.bash
source ~/project/embodied__ai_lab/ros2/install/setup.bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

ros2 launch embodied_lab_bringup go2_bringup.launch.py \
  device_id:=quadruped-01 sim:=true
```

**预检**（终端 2，可选）：

```bash
ros2 topic hz /perception/quadruped_01/joint_states --qos-reliability best_effort
ros2 service call /go2_driver_bridge/quadruped_01/smoke embodied_lab_msgs/srv/BridgeSmoke {}
```

**终端 2**（venv + ROS）：

```bash
source ~/project/embodied__ai_lab/.venv/bin/activate
source /opt/ros/jazzy/setup.bash
source ~/project/embodied__ai_lab/ros2/install/setup.bash
export ROS_DOMAIN_ID=42
pip install numpy   # 若 import embodied_lab_msgs 报缺 numpy

lab --data-root ~/embodied-ai-lab-data ops bringup --device quadruped-01 --ros --sim
```

**通过**：

- 输出含 `[Go2Bringup] quadruped-01 → L1 overall=pass`（**无** `[StubReal]`）
- `bringup_report.json` → `"overall": "pass"`
- `bridge_maturity.yaml` → `quadruped-01: level: L1`

---

### 步骤 E5 — ws-02 Isaac train smoke

**前置**：NVIDIA 驱动 ≥560；Isaac Sim 6.0 + Isaac Lab 3.0 已装（见 INFRA-01 §二）。

```bash
cd ~/project/embodied__ai_lab/lab_platform
source .venv/bin/activate
pip install -e .

lab init --data-root ~/embodied-ai-lab-data   # 若 ws-02 尚未 init

lab --data-root ~/embodied-ai-lab-data isaac run \
  --kind train --task velocity_rough_go2
```

> **注意**：当前 `StubIsaacLauncher` 仍会假跑；E5 完整通过需替换为真 Isaac CLI（Phase 2 P0）。  
> 过渡验收：确认 Run 登记 + 目录结构 + index.db 有 `isaac_job` 记录即可标记「框架通路 OK」。

**完整 E5 通过标准**（真 Isaac 接入后）：

- Run status `completed`
- `data/artifacts/policies/pol_*/policy_manifest.yaml` 存在
- `data/runs/isaac_jobs/isaac_*_train/` 有 native 日志与 checkpoint

---

### 步骤 E6 — checkpoint 同步 ws-02 → ws-01

**目的**：ws-02 训练的 policy 能被 ws-01 读取（deploy 前置）。

```bash
# ws-02 上（示例 rsync）
rsync -av ~/embodied-ai-lab-data/artifacts/policies/ \
  ljqy@lab-ws-01:~/embodied-ai-lab-data/artifacts/policies/

# ws-01 验证
ls ~/embodied-ai-lab-data/artifacts/policies/
cat ~/embodied-ai-lab-data/artifacts/policies/pol_*/policy_manifest.yaml
```

**通过**：ws-01 可读 policy 目录与 manifest。

---

### 步骤 E4 + E7 — 真机 Go2

#### E4-0 onboard 环境

1. Go2 onboard 接入与 ws-01 同网段；`/etc/hosts` 互 ping
2. onboard 安装 ROS2 Jazzy + colcon 编译同一仓库 `ros2/`
3. 安装 Unitree SDK / `unitree_ros2`；确认 `/lf/lowstate` 等 topic

#### E4-1 onboard 启动 Bridge

```bash
source /opt/ros/jazzy/setup.bash
source ~/project/embodied__ai_lab/ros2/install/setup.bash
export ROS_DOMAIN_ID=42

ros2 launch go2_driver_bridge go2_bridge.launch.py \
  device_id:=quadruped-01 sim:=false \
  sdk_version:=unitree_go2_sdk_1.0 \
  unitree_lowstate_topic:=/lf/lowstate
```

#### E4-2 ws-01 跨机验证

```bash
ros2 topic hz /perception/quadruped_01/joint_states --qos-reliability best_effort
# ≥ 50 Hz
```

#### E7 真机 bringup

ws-01 终端 2（**不用** sim bringup launch，或 launch 设 `sim:=false`）：

```bash
lab --data-root ~/embodied-ai-lab-data ops bringup --device quadruped-01 --ros --no-sim
```

**通过**：同 E3，且 BU-04 匹配真机 `sdk_version`；P3 确认 BU-05 实机 ESTOP。

---

## 四、 ws-02 与真机：下一步清单

### lab-ws-02（本周优先）

| 序号 | 任务 | 验收 |
|:----:|------|------|
| 1 | `git clone` + `lab init --data-root ~/embodied-ai-lab-data` | registry 文件存在 |
| 2 | **E1** `python scripts/smoke_test.py` | ALL PASSED |
| 3 | 装 NVIDIA + Isaac（若未装） | `nvidia-smi` OK |
| 4 | **E5** Isaac train（Stub 或真 CLI） | Policy Run 入库 |
| 5 | 定 **E6** 同步方式（rsync cron / NFS） | ws-01 能读 policy |

**ws-02 禁止**：日常 shell 设 `ROS_DOMAIN_ID`；不跑 ROS2 节点。

### 真机 Go2（E4 + E7）

| 序号 | 任务 | 负责人 |
|:----:|------|--------|
| 1 | onboard Ubuntu + ROS2 + 同仓库 `ros2/` colcon | P2 |
| 2 | Unitree SDK smoke（lowstate Hz） | P2 |
| 3 | 仅 onboard 起 `go2_bridge`（sim:=false） | P2 |
| 4 | ws-01 跨机 topic（**E4**） | P2 |
| 5 | `lab ops bringup --ros --no-sim`（**E7**） | P2 |
| 6 | BU-05 实机 ESTOP 签字 | P3 |

---

## 五、 常见问题（验证阶段）

| 现象 | 处理 |
|------|------|
| `[StubReal]` 而非 `[Go2Bringup]` | venv 缺 numpy/rclpy；未 source ros2/install；终端1 launch 未起 |
| `ros2 topic hz` 为 0 | 加 `--qos-reliability best_effort`；检查 topic 名为 `quadruped_01` |
| colcon 报 `No module named 'em'` | deactivate venv 后重编 |
| BU-03 fail | QoS 不匹配或 launch 未起 |
| BU-04 fail | 更新 `data/vendor/unitree_go2/plugin.yaml` 的 `sdk_version` |

---

## 六、 相关文档

| 文档 | 用途 |
|------|------|
| [INFRA-01 环境安装清单](./env_setup_checklist_v1.md) | 三节点 OS/ROS/Isaac **安装** |
| [TECH-14 As-Built](../architecture/platform_architecture_as_built_v1.md) | 架构与 Gap List |
| [framework_skeleton_design_v1](../modules/framework_skeleton_design_v1.md) | 骨架设计意图 |
| [ros2/README.md](../../ros2/README.md) | ROS2 包构建与 launch 速查 |

---

## 七、 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v1.0** | 2026-06-16 | 首版；E2/E3 ws-01 已通过；补 E1/E5/E6/E7 逐步手册 |

---

*INFRA-02 | Phase 1 验证方案 · 配合 INFRA-01 使用*
