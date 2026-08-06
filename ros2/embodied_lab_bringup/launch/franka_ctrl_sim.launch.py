"""CTRL-SIM bringup：franka_sim_bridge（TECH-02 ↔ Isaac 官方 JointStates）。

Isaac Sim 本身须按 INFRA-02 §6.7 在终端 A 单独启动（官方 FR3 USD + ros2.bridge）。
本 launch 只起实验室侧 Low 适配节点。
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    device_id = LaunchConfiguration("device_id")
    backend = LaunchConfiguration("backend")
    joint_states_topic = LaunchConfiguration("joint_states_topic")
    joint_command_topic = LaunchConfiguration("joint_command_topic")
    frame_id = LaunchConfiguration("frame_id")

    bridge = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("franka_sim_bridge"), "launch", "franka_sim_bridge.launch.py"]
            )
        ),
        launch_arguments={
            "device_id": device_id,
            "backend": backend,
            "joint_states_topic": joint_states_topic,
            "joint_command_topic": joint_command_topic,
            "frame_id": frame_id,
        }.items(),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("device_id", default_value="franka-01"),
            DeclareLaunchArgument("backend", default_value="isaac_sim"),
            DeclareLaunchArgument(
                "joint_states_topic",
                default_value="/joint_states",
                description="Isaac official OmniGraph publish topic",
            ),
            DeclareLaunchArgument(
                "joint_command_topic",
                default_value="/joint_command",
                description="Isaac official OmniGraph subscribe topic",
            ),
            DeclareLaunchArgument("frame_id", default_value="fr3_link0"),
            LogInfo(
                msg=[
                    "CTRL-SIM: ensure Isaac Sim is playing official FR3 USD with ",
                    "isaacsim.ros2.bridge JointStates (see franka_sim_bridge README / INFRA-02 §6.7).",
                ]
            ),
            bridge,
        ]
    )
