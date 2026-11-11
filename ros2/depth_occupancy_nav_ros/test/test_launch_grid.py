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

"""Launch test A: OccupancyGrid gates and bad CameraInfo rejection."""

from __future__ import annotations

import os
import time

import pytest

pytest.importorskip("launch_pytest")
import launch_pytest
import launch_testing.actions
import rclpy
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node as RclpyNode
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)

from depth_occupancy_nav_ros.grid_checks import assert_criterion5_grid, occupancy_counts

MAP_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
)


def _pkg_share() -> str:
    from ament_index_python.packages import get_package_share_directory

    return get_package_share_directory("depth_occupancy_nav_ros")


def _stack_launch(
    run_publisher: str,
    bad_after: str = "0",
    **extra: str,
) -> IncludeLaunchDescription:
    launch_dir = os.path.join(_pkg_share(), "launch")
    args = {
        "run_publisher": run_publisher,
        "bad_camera_info_after": bad_after,
        "bad_camera_from_start": "false",
        "publish_noisy_depth_with_bad_ci": "false",
    }
    args.update(extra)
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "depth_occupancy.launch.py")),
        launch_arguments=args.items(),
    )


@launch_pytest.fixture
def launch_description_valid() -> LaunchDescription:
    launch_dir = os.path.join(_pkg_share(), "launch")
    tf = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "static_tf.launch.py"))
    )
    return LaunchDescription(
        [
            tf,
            _stack_launch("true", "0"),
            launch_testing.actions.ReadyToTest(),
        ]
    )


@launch_pytest.fixture
def launch_description_bad_ci() -> LaunchDescription:
    launch_dir = os.path.join(_pkg_share(), "launch")
    tf = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "static_tf.launch.py"))
    )
    return LaunchDescription(
        [
            tf,
            _stack_launch(
                "true",
                "5",
                publish_noisy_depth_with_bad_ci="true",
            ),
            launch_testing.actions.ReadyToTest(),
        ]
    )


@launch_pytest.fixture
def launch_description_bad_from_start() -> LaunchDescription:
    launch_dir = os.path.join(_pkg_share(), "launch")
    tf = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "static_tf.launch.py"))
    )
    return LaunchDescription(
        [
            tf,
            _stack_launch("true", bad_camera_from_start="true"),
            launch_testing.actions.ReadyToTest(),
        ]
    )


def _wait_for_map(timeout: float = 30.0) -> OccupancyGrid:
    node = RclpyNode("launch_test_a_client")
    holder: list[OccupancyGrid] = []

    def cb(msg: OccupancyGrid) -> None:
        if msg.info.width == 80 and msg.info.height == 60:
            holder.append(msg)

    node.create_subscription(OccupancyGrid, "map", cb, MAP_QOS)
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        rclpy.spin_once(node, timeout_sec=0.1)
        if holder:
            snap = holder[-1]
            counts = occupancy_counts(snap)
            if counts.get("occupied", 0) >= 22:
                node.destroy_node()
                return snap
    node.destroy_node()
    raise AssertionError("Timed out waiting for OccupancyGrid from depth node")


@pytest.mark.launch(fixture=launch_description_valid)
def test_launch_a_valid_camera_matches_criterion5() -> None:
    msg = _wait_for_map()
    assert_criterion5_grid(msg)


@pytest.mark.launch(fixture=launch_description_bad_ci)
def test_launch_a_bad_camera_info_does_not_mutate_grid() -> None:
    node = RclpyNode("launch_test_a_bad_ci")
    good: list[OccupancyGrid] = []
    all_msgs: list[OccupancyGrid] = []

    def cb(msg: OccupancyGrid) -> None:
        all_msgs.append(msg)
        counts = occupancy_counts(msg)
        if counts == {"occupied": 22, "free": 1698, "unknown": 3080, "mid": 0}:
            good.append(msg)

    node.create_subscription(OccupancyGrid, "map", cb, MAP_QOS)
    deadline = time.monotonic() + 30.0
    while time.monotonic() < deadline and not good:
        rclpy.spin_once(node, timeout_sec=0.1)

    assert good, "Never received criterion-5 OccupancyGrid before bad CameraInfo"
    baseline = list(good[-1].data)

    # Wait through bad CameraInfo frames (publisher switches after 5 ticks at 5 Hz).
    while time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        if len(all_msgs) >= 12:
            break

    for msg in all_msgs[len(good) :]:
        assert list(msg.data) == baseline, "Grid mutated after bad CameraInfo"

    node.destroy_node()


@pytest.mark.launch(fixture=launch_description_bad_from_start)
def test_launch_a_bad_camera_from_start_never_updates_grid() -> None:
    node = RclpyNode("launch_test_a_bad_from_start")
    msgs: list[OccupancyGrid] = []

    def cb(msg: OccupancyGrid) -> None:
        if msg.info.width == 80 and msg.info.height == 60:
            msgs.append(msg)

    node.create_subscription(OccupancyGrid, "map", cb, MAP_QOS)
    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)

    for msg in msgs:
        assert all(v == -1 for v in msg.data), "Grid mutated with bad CameraInfo from start"

    node.destroy_node()
