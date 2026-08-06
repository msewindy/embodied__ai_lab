# embodied_lab ROS2 工作区

Ubuntu 24.04 + ROS2 Jazzy：Go2 栈 + FR3 CTRL-SIM（DOMAIN 43）适配。

## 包清单

| 包 | 部署 | 说明 |
|----|------|------|
| `embodied_lab_msgs` | ws-01 + onboard + ws-02 | TECH-02 自定义 msg/srv（含 FR3 `ee_delta` / `LowStateFeedback`） |
| `go2_driver_bridge` | **onboard** | 宇树 Go2 Driver Bridge 插件 |
| `franka_sim_bridge` | **lab-ws-02** | FR3 CTRL-SIM Low：TECH-02 ↔ Isaac 官方 `/joint_states`·`/joint_command` |
| `embodied_lab_bringup` | ws-01 / ws-02 | Go2 bringup + `franka_ctrl_sim.launch.py` |

## 快速构建

```bash
cd ros2
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

colcon build --symlink-install
source install/setup.bash
```

## FR3 CTRL-SIM（M2 · DOMAIN 43）

物理侧用 **Isaac 官方 FR3 USD + ros2.bridge JointStates**（见 `franka_sim_bridge/README.md`），不要自研场景。

```bash
export ROS_DOMAIN_ID=43
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source /opt/ros/jazzy/setup.bash
cd ros2 && colcon build --symlink-install --packages-up-to franka_sim_bridge embodied_lab_bringup
source install/setup.bash

# 终端 A：Isaac Sim 打开官方 fr3.usd，启用 JointStates，Play
# 终端 B：
ros2 launch embodied_lab_bringup franka_ctrl_sim.launch.py \
  device_id:=franka-01 backend:=isaac_sim

# 终端 C：
python3 ../lab_platform/scripts/m2_franka_hello.py --dx 0.05 --domain 43
```

## Go2 real_bringup（仿真硬件，无真机）

```bash
# 终端 1：启动 bridge + safety + run_context（sim）
ros2 launch embodied_lab_bringup go2_bringup.launch.py \
  device_id:=quadruped-01 sim:=true

# 终端 2：lab 框架触发 bringup Run（会调用 bringup_checker）
cd ../lab_platform
lab --data-root data ops bringup --device quadruped-01 --ros --sim
```

## Go2 real_bringup（真机 onboard）

```bash
# onboard：Driver Bridge 连 Unitree SDK
ros2 launch go2_driver_bridge go2_bridge.launch.py \
  device_id:=quadruped-01 sim:=false \
  unitree_lowstate_topic:=/lf/lowstate

# ws-01：run_context + bringup
ros2 launch embodied_lab_bringup go2_bringup.launch.py \
  device_id:=quadruped-01 sim:=false
```

## 与 lab_platform 集成

`lab ops bringup --device quadruped-01 --ros [--sim]` 会：

1. PreFlight → 创建 `real_bringup` Run  
2. 发布 `/system/run_context`（`run_context_node` 或 lab 内 rclpy）  
3. 执行 BU-01..06 检查（`bringup_checker_node`）  
4. 写 `bringup_report.json`，Bridge → L1  

无 ROS2 环境时自动回退 Stub（Walking Skeleton 行为不变）。
