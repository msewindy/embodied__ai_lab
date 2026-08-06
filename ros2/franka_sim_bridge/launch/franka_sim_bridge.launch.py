from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("device_id", default_value="franka-01"),
            DeclareLaunchArgument("backend", default_value="isaac_sim"),
            DeclareLaunchArgument("joint_states_topic", default_value="/joint_states"),
            DeclareLaunchArgument("joint_command_topic", default_value="/joint_command"),
            DeclareLaunchArgument("control_hz", default_value="50.0"),
            DeclareLaunchArgument("frame_id", default_value="fr3_link0"),
            Node(
                package="franka_sim_bridge",
                executable="bridge_node",
                name="franka_sim_bridge",
                output="screen",
                parameters=[
                    {
                        "device_id": LaunchConfiguration("device_id"),
                        "backend": LaunchConfiguration("backend"),
                        "joint_states_topic": LaunchConfiguration("joint_states_topic"),
                        "joint_command_topic": LaunchConfiguration("joint_command_topic"),
                        "control_hz": LaunchConfiguration("control_hz"),
                        "frame_id": LaunchConfiguration("frame_id"),
                    }
                ],
            ),
        ]
    )
