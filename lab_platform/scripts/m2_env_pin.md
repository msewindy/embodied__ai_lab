# M2 环境钉扎（手填）

> 完成 INFRA-02 §6.7 / §6.8 后填写。官方资产与桥方案见 `ros2/franka_sim_bridge/README.md`。

```text
date: 2026-08-04
host: lab-ws-02
isaac_sim: 6.0.0-rc.59+release.41464.5f2772bc.gl   # /home/ljqy/isaacsim/VERSION
isaac_lab: 3.0.0 @ e0d9f94116                         # /home/ljqy/IsaacLab
driver: 595.84 (NVIDIA GeForce RTX 5090 D)
ros: jazzy + rmw_cyclonedds_cpp
ROS_DOMAIN_ID: 43
bridge_option: A          # A=官方 isaacsim.ros2.bridge JointStates；B=进程内 Lab API
isaac_usd_path: /home/ljqy/project/embodied__ai_lab/frankaFR3.usd
  # 官方文档路径（Nucleus）：Isaac/Robots/FrankaRobotics/FrankaFR3/fr3.usd
  # 本机工作副本为仓库根 frankaFR3.usd（USD crate 0.8.0）
isaac_asset_rev: Isaac Sim 6.0 Robot Assets（FR3）
articulation_prim: /fr3   # Stage 以实测为准；joint 名为 fr3_joint*
arm_joint_names: fr3_joint1..7
frame_id_base: fr3_link0
hand_loaded: yes          # /joint_states 含 fr3_finger_joint1/2；low_state grip_w≈0.08
notes: |
  - 2026-08-04 Hello PASS×2：python3 scripts/m2_franka_hello.py --dx 0.05 --domain 43
  - 可见 topic：/joint_states /joint_command /skill/franka_01/intent /perception/franka_01/low_state
  - 发布中 ik=ok、des≈ee+0.05；停发后 ik=hold、safety=none；脚本 PASS field check
  - 复跑：第二次仍 PASS；臂已伸出时位移更小，字段/HOLD 行为可重复
  - HOLD 后仍有约 2–5 cm tracking_error 与轻微爬升，已记录；不挡 M2 字段验收
  - bringup：ros2 launch embodied_lab_bringup franka_ctrl_sim.launch.py device_id:=franka-01 backend:=isaac_sim
```

## 官方参考（勿改写替代）

- FR3 USD: https://docs.isaacsim.omniverse.nvidia.com/6.0.0/assets/usd_assets_robots.html
- Isaac ROS2 Joint Control: https://docs.isaacsim.omniverse.nvidia.com/6.0.0/ros2_tutorials/tutorial_ros2_manipulation.html
- franka_ros2 Jazzy（真机对照）: https://frankarobotics.github.io/docs/doc/franka_ros2_jazzy/docs/index.html
