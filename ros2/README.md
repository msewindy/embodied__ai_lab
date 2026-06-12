# embodied_lab ROS2 工作区

Ubuntu 24.04 + ROS2 Jazzy 上构建与运行 Go2 首台设备栈。

## 包清单

| 包 | 部署 | 说明 |
|----|------|------|
| `embodied_lab_msgs` | ws-01 + onboard | TECH-02 自定义 msg/srv |
| `go2_driver_bridge` | **onboard** | 宇树 Go2 Driver Bridge 插件 |
| `embodied_lab_bringup` | ws-01 | run_context、bringup 检查、launch |

## 快速构建

```bash
cd ros2
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

colcon build --symlink-install
source install/setup.bash
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
