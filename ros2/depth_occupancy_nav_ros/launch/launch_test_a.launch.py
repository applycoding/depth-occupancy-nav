# Copyright 2026 Arpan Bom
# SPDX-License-Identifier: Apache-2.0
"""Launch graph for launch test A (grid gates)."""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description() -> LaunchDescription:
    pkg = get_package_share_directory("depth_occupancy_nav_ros")
    launch_dir = os.path.join(pkg, "launch")

    tf = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "static_tf.launch.py"))
    )
    stack = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "depth_occupancy.launch.py")),
        launch_arguments={
            "run_publisher": "true",
            "bad_camera_info_after": "0",
        }.items(),
    )
    return LaunchDescription([tf, stack])
