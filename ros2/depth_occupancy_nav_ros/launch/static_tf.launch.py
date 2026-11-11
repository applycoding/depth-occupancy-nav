# Copyright 2026 Arpan Bom
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

"""Static transforms for locked map / base_link / camera_optical_frame."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    world_map = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="world_to_map_tf",
        arguments=[
            "--x",
            "0",
            "--y",
            "0",
            "--z",
            "0",
            "--roll",
            "0",
            "--pitch",
            "0",
            "--yaw",
            "0",
            "--frame-id",
            "world",
            "--child-frame-id",
            "map",
        ],
    )
    camera_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="map_to_camera_optical_tf",
        arguments=[
            "--x",
            "0",
            "--y",
            "0",
            "--z",
            "0.80",
            "--qx",
            "0.5",
            "--qy",
            "-0.5",
            "--qz",
            "0.5",
            "--qw",
            "-0.5",
            "--frame-id",
            "map",
            "--child-frame-id",
            "camera_optical_frame",
        ],
    )
    base_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="map_to_base_link_tf",
        arguments=[
            "--x",
            "0",
            "--y",
            "0",
            "--z",
            "0",
            "--roll",
            "0",
            "--pitch",
            "0",
            "--yaw",
            "0",
            "--frame-id",
            "map",
            "--child-frame-id",
            "base_link",
        ],
    )
    return LaunchDescription([world_map, camera_tf, base_tf])
