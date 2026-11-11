# Copyright 2026 Arpan Bom
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
    bad_camera_from_start = DeclareLaunchArgument(
        "bad_camera_from_start",
        default_value="false",
        description="Publish mismatched CameraInfo from the first frame (tests).",
    )
    publish_noisy_depth_with_bad_ci = DeclareLaunchArgument(
        "publish_noisy_depth_with_bad_ci",
        default_value="false",
        description="When bad CameraInfo starts (after threshold), publish seed-1 noisy depth.",
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
                "bad_camera_from_start": LaunchConfiguration("bad_camera_from_start"),
                "publish_noisy_depth_with_bad_ci": LaunchConfiguration(
                    "publish_noisy_depth_with_bad_ci"
                ),
            }
        ],
    )

    return LaunchDescription(
        [
            run_publisher,
            bad_camera_info_after,
            bad_camera_from_start,
            publish_noisy_depth_with_bad_ci,
            depth_node,
            publisher,
        ]
    )
