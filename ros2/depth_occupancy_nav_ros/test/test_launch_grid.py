# Copyright 2026 Arpan Bom

# Licensed under the Apache License, Version 2.0
# SPDX-License-Identifier: Apache-2.0
"""Launch test A: OccupancyGrid gates and bad CameraInfo rejection."""

from __future__ import annotations

import os
import time

import launch_pytest
import launch_testing.actions
import pytest
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


def _stack_launch(run_publisher: str, bad_after: str) -> IncludeLaunchDescription:
    launch_dir = os.path.join(_pkg_share(), "launch")
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, "depth_occupancy.launch.py")),
        launch_arguments={
            "run_publisher": run_publisher,
            "bad_camera_info_after": bad_after,
        }.items(),
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
            _stack_launch("true", "5"),
            launch_testing.actions.ReadyToTest(),
        ]
    )


def _wait_for_map(timeout: float = 30.0) -> OccupancyGrid:
    rclpy.init()
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
                rclpy.shutdown()
                return snap
    node.destroy_node()
    rclpy.shutdown()
    raise AssertionError("Timed out waiting for OccupancyGrid from depth node")


@pytest.mark.launch(fixture=launch_description_valid)
def test_launch_a_valid_camera_matches_criterion5() -> None:
    msg = _wait_for_map()
    assert_criterion5_grid(msg)


@pytest.mark.launch(fixture=launch_description_bad_ci)
def test_launch_a_bad_camera_info_does_not_mutate_grid() -> None:
    rclpy.init()
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
    rclpy.shutdown()
