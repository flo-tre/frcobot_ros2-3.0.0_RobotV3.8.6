from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share = get_package_share_directory("fairino_bringup")

    urdf_file = os.path.join(pkg_share, "config", "robot_description.urdf.xacro")
    controller_config = os.path.join(pkg_share, "config", "ros2_controllers.yaml")

    use_sim_time = LaunchConfiguration("use_sim_time")
    start_command_server = LaunchConfiguration("start_command_server")
    trajectory_controller_name = LaunchConfiguration("trajectory_controller_name")

    with open(urdf_file, "r", encoding="utf-8") as urdf_handle:
        robot_description_content = urdf_handle.read()

    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            {"robot_description": robot_description_content, "use_sim_time": use_sim_time},
            controller_config,
        ],
        output="screen",
    )

    fairino_driver = Node(
        package="fairino_hardware",
        executable="ros2_cmd_server",
        condition=IfCondition(start_command_server),
        output="screen",
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
            "--param-file",
            controller_config,
            "--controller-manager-timeout",
            "120",
        ],
        output="screen",
    )

    joint_trajectory_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            trajectory_controller_name,
            "--controller-manager",
            "/controller_manager",
            "--param-file",
            controller_config,
            "--controller-manager-timeout",
            "120",
        ],
        output="screen",
    )

    delayed_joint_state_broadcaster_spawner = TimerAction(
        period=6.0,
        actions=[joint_state_broadcaster_spawner],
    )

    delayed_joint_trajectory_controller_spawner = TimerAction(
        period=8.0,
        actions=[joint_trajectory_controller_spawner],
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        DeclareLaunchArgument("start_command_server", default_value="false"),
        DeclareLaunchArgument("trajectory_controller_name", default_value="fairino10_controller"),
        control_node,
        fairino_driver,
        delayed_joint_state_broadcaster_spawner,
        delayed_joint_trajectory_controller_spawner,
    ])
