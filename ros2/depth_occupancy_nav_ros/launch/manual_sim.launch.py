# SPDX-License-Identifier: Apache-2.0
"""
Manual launch: depth node + static TF + locked-scene publisher.

Documented only (not a CI gate). Use the same undistorted 32FC1 + CameraInfo contract
as CI, or a bag replaying those topics.
"""

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
    node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "depth_occupancy.launch.py")),
        launch_arguments={"run_publisher": "true"}.items(),
    )
    return LaunchDescription([tf, node])
