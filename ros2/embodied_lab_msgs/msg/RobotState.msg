std_msgs/Header header
string device_id
float32[3] base_lin_vel
float32[3] base_ang_vel
float32[3] projected_gravity
float32[] joint_pos
float32[] joint_vel
float32[] joint_torque
# --- manipulation 最小集（locomotion 可填 0）---
float32[7] ee_pose             # xyz + quat(xyzw)
float32[6] wrench_ee
float32 gripper_width
