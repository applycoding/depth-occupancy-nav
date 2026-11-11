# Copyright 2026 Arpan Bom

# Licensed under the Apache License, Version 2.0
# SPDX-License-Identifier: Apache-2.0
"""Static transforms for locked map / base_link / camera_optical_frame."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    camera_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="map_to_camera_optical_tf",
        arguments=[
            "0",
            "0",
            "0.80",
            "0.5",
            "-0.5",
            "0.5",
            "-0.5",
            "map",
            "camera_optical_frame",
        ],
    )
    base_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="map_to_base_link_tf",
        arguments=["0", "0", "0", "0", "0", "0", "1", "map", "base_link"],
    )
    return LaunchDescription([camera_tf, base_tf])
