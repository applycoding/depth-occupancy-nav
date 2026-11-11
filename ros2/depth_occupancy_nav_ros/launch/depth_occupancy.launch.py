# SPDX-License-Identifier: Apache-2.0
"""Depth occupancy node and optional locked-scene publisher."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    run_publisher = DeclareLaunchArgument(
        "run_publisher",
        default_value="false",
        description="Publish locked-scene synthetic depth for demos and tests.",
    )
    bad_camera_info_after = DeclareLaunchArgument(
        "bad_camera_info_after",
        default_value="0",
        description="After N depth frames, publish mismatched CameraInfo (tests).",
    )

    depth_node = Node(
        package="depth_occupancy_nav_ros",
        executable="depth_occupancy_node",
        name="depth_occupancy_nav",
        output="screen",
        parameters=[
            {
                "depth_topic": "depth/image",
                "camera_info_topic": "depth/camera_info",
                "map_topic": "map",
                "camera_optical_frame": "camera_optical_frame",
            }
        ],
    )

    publisher = Node(
        package="depth_occupancy_nav_ros",
        executable="locked_scene_publisher",
        name="locked_scene_publisher",
        output="screen",
        condition=IfCondition(LaunchConfiguration("run_publisher")),
        parameters=[
            {
                "frame_id": "camera_optical_frame",
                "publish_rate_hz": 5.0,
                "bad_camera_info_after": LaunchConfiguration("bad_camera_info_after"),
            }
        ],
    )

    return LaunchDescription(
        [
            run_publisher,
            bad_camera_info_after,
            depth_node,
            publisher,
        ]
    )
