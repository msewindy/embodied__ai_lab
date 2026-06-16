from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("device_id", default_value="quadruped-01"),
        DeclareLaunchArgument("sim", default_value="true"),
        DeclareLaunchArgument("sdk_version", default_value="unitree_go2_sim_1.0"),
        DeclareLaunchArgument("unitree_lowstate_topic", default_value=""),
        Node(
            package="go2_driver_bridge",
            executable="bridge_node",
            name="go2_driver_bridge",
            output="screen",
            parameters=[{
                "device_id": LaunchConfiguration("device_id"),
                "sim": LaunchConfiguration("sim"),
                "sdk_version": LaunchConfiguration("sdk_version"),
                "unitree_lowstate_topic": LaunchConfiguration("unitree_lowstate_topic"),
                "publish_hz": 100.0,
                "max_speed_cap": 1.5,
            }],
        ),
    ])
