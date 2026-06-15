from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    device_id = LaunchConfiguration("device_id")
    sim = LaunchConfiguration("sim")
    sdk_version = LaunchConfiguration("sdk_version")
    unitree_topic = LaunchConfiguration("unitree_lowstate_topic")

    bridge_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("go2_driver_bridge"), "launch", "go2_bridge.launch.py"]
            )
        ),
        launch_arguments={
            "device_id": device_id,
            "sim": sim,
            "sdk_version": sdk_version,
            "unitree_lowstate_topic": unitree_topic,
        }.items(),
    )

    run_context_node = Node(
        package="embodied_lab_bringup",
        executable="run_context_node",
        name="run_context_node",
        output="screen",
        parameters=[{
            "run_id": "debug_bringup",
            "run_type": "real_bringup",
            "device_id": device_id,
            "operator": "p2",
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument("device_id", default_value="quadruped-01"),
        DeclareLaunchArgument("sim", default_value="true"),
        DeclareLaunchArgument("sdk_version", default_value="unitree_go2_sim_1.0"),
        DeclareLaunchArgument("unitree_lowstate_topic", default_value=""),
        bridge_launch,
        Node(
            package="embodied_lab_bringup",
            executable="safety_coordinator",
            name="safety_coordinator",
            output="screen",
            parameters=[{"device_id": device_id}],
        ),
        Node(
            package="embodied_lab_bringup",
            executable="limiter_node",
            name="limiter_node",
            output="screen",
            parameters=[{"device_id": device_id, "max_joint_pos": 2.0}],
        ),
        run_context_node,
    ])
