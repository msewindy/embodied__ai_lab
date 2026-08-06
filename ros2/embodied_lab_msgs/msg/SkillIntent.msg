std_msgs/Header header
string device_id
string run_id
string source                  # teleop | policy_high | plan | mid
string skill_mode              # idle | teleop | policy | hold | task_space
float32[] target_joint_pos     # 与 policy_manifest.action_schema 对齐
float32[] target_joint_vel
float32[] target_joint_torque
float32[] kp
float32[] kd
geometry_msgs/Twist cmd_vel    # locomotion 时使用
# --- v1.2：manipulation / FR3（TECH-02 · 与世界模型 TaskSpaceCommand 对齐）---
float32[6] ee_delta            # dx,dy,dz,droll,dpitch,dyaw；基座系相对增量
float32 gripper                # [0,1]；0=开 1=闭（宽度映射见设备契约）
uint8 control_mode             # 0=UNUSED 1=POSE 2=IMPEDANCE
uint32 expire_ms               # 无新令时 Low HOLD；默认 150–200
string frame_id                # 默认 fr3_link0 / 臂基座
