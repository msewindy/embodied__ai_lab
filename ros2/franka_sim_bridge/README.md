# franka_sim_bridge

CTRL-SIM Low 适配层：把实验室 TECH-02 `SkillIntent` / `LowStateFeedback` 接到 **Isaac Sim 官方 ROS2 JointStates** 通路。

## 官方依赖（不要自研替代）

| 层 | 使用官方什么 | 文档 |
| --- | --- | --- |
| 机器人资产 | Nucleus `FrankaRobotics/FrankaFR3/fr3.usd` | [Robot Assets](https://docs.isaacsim.omniverse.nvidia.com/6.0.0/assets/usd_assets_robots.html) |
| ROS2 桥 | Extension `isaacsim.ros2.bridge` + **Tools → ROS 2 OmniGraphs → JointStates** | [ROS2 Joint Control](https://docs.isaacsim.omniverse.nvidia.com/6.0.0/ros2_tutorials/tutorial_ros2_manipulation.html) |
| 命令消息形态 | `sensor_msgs/JointState` on `/joint_command` | IsaacSim-ros_workspaces `isaac_tutorials/ros2_publisher.py` |
| 真机对照（非本包运行时） | `franka_ros2` Jazzy：`franka_bringup` / example controllers | [franka_ros2 Jazzy](https://frankarobotics.github.io/docs/doc/franka_ros2_jazzy/docs/index.html) |

本包**不**重新实现 Isaac 物理或 Franka FCI；只做：

1. `task_space` Δpose → 关节目标（DLS，对齐 Isaac Lab `DifferentialIKController` / franka IK 示例族）
2. 发布 `/joint_command`（与官方 demo 同 topic）
3. 订阅 `/joint_states`，填 `LowStateFeedback`
4. `expire_ms` → HOLD

## Isaac 侧（终端 A）最小步骤

1. 启动 Isaac Sim 6，打开官方 `fr3.usd`
2. 启用 `isaacsim.ros2.bridge`
3. JointStates OmniGraph：`targetPrim` / `robotPath` 指向 Stage 中 FR3 Articulation Root
4. Play；确认 `ros2 topic echo /joint_states --once` 有数据
5. 再启动本 bridge（见 bringup launch）

若 Stage 关节名不是默认 `fr3_joint*`，用参数覆盖：

```bash
ros2 launch franka_sim_bridge franka_sim_bridge.launch.py \
  device_id:=franka-01 \
  --ros-args \
  -p arm_joint_names:="['j1','j2',...]"   # 以 Stage 为准
```

（或在 launch/parameters 文件中声明。）

## 真机（Phase-2）

改用官方：

```bash
ros2 launch franka_bringup franka.launch.py robot_type:=fr3 robot_ip:=<fci-ip>
# 笛卡尔示例：
ros2 launch franka_bringup example.launch.py controller_names:=cartesian_impedance_example_controller
```

届时另建 `franka_driver_bridge`，语义仍走同一套 TECH-02 msg。
