# Low → Mid 状态反馈（CTRL-SIM / Real 同构 · TECH-02）
std_msgs/Header header
string device_id
string run_id
string frame_id                # 基座 / 任务系，默认 fr3_link0

float32[7] ee_pose_actual      # xyz + quat(xyzw)
float32[7] ee_pose_desired     # xyz + quat(xyzw)
float32[7] q
float32[7] dq
float32[7] tau_ext            # 无则填 0
float32[6] wrench_ee           # 估计外力/力矩；无则填 0
float32 gripper_width
float32 tracking_error
bool contact_flag
string ik_status               # ok | limited | failed | hold | idle
string safety_event            # none | ...
string backend                 # isaac_sim | franka_real
float32 latency_ms
