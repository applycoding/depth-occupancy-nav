# Copyright 2026 Arpan Bom

# Licensed under the Apache License, Version 2.0
# SPDX-License-Identifier: Apache-2.0
"""Launch graph for launch test B (Navfn on published /map)."""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description() -> LaunchDescription:
    pkg = get_package_share_directory("depth_occupancy_nav_ros")
    launch_dir = os.path.join(pkg, "launch")
    config_dir = os.path.join(pkg, "config")

    tf = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "static_tf.launch.py"))
    )
    stack = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "depth_occupancy.launch.py")),
        launch_arguments={"run_publisher": "true"}.items(),
    )

    planner = Node(
        package="nav2_planner",
        executable="planner_server",
        name="planner_server",
        output="screen",
        parameters=[
            os.path.join(config_dir, "planner_server.yaml"),
        ],
    )

    lifecycle = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_navigation",
        output="screen",
        parameters=[os.path.join(config_dir, "lifecycle_manager.yaml")],
    )

    delayed_nav = TimerAction(period=2.0, actions=[planner, lifecycle])
    return LaunchDescription([tf, stack, delayed_nav])
