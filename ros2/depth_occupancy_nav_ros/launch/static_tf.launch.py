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
        arguments=["0.5", "0", "0", "0", "0", "0", "1", "map", "base_link"],
    )
    return LaunchDescription([camera_tf, base_tf])
