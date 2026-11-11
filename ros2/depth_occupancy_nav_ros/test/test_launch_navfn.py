# Copyright 2026 Arpan Bom
# SPDX-License-Identifier: Apache-2.0
"""Launch test B: Navfn planner on static-layer costmap fed by published /map."""

from __future__ import annotations

import math
import os
import time

import launch_pytest
import launch_testing.actions
import pytest
import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from nav_msgs.msg import OccupancyGrid
from nav2_msgs.action import ComputePathToPose
from rclpy.action import ActionClient
from rclpy.node import Node as RclpyNode
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

from depth_occupancy_nav.grid import ORIGIN_X, ORIGIN_Y, RESOLUTION
from depth_occupancy_nav_ros.grid_checks import (
    assert_path_poses_in_bounds,
    assert_path_samples_free,
    occupancy_counts,
)

MAP_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
)

START = (0.50, 0.00)
GOAL = (5.50, -1.50)
POSE_TOL = 0.15


def _pkg_share() -> str:
    from ament_index_python.packages import get_package_share_directory

    return get_package_share_directory("depth_occupancy_nav_ros")


@launch_pytest.fixture
def launch_description_navfn() -> LaunchDescription:
    pkg = _pkg_share()
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
        parameters=[os.path.join(config_dir, "planner_server.yaml")],
    )
    lifecycle = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_navigation",
        output="screen",
        parameters=[os.path.join(config_dir, "lifecycle_manager.yaml")],
    )
    # Depth /map must exist before planner_server configures the static costmap layer.
    delayed_nav = TimerAction(period=5.0, actions=[planner, lifecycle])
    return LaunchDescription(
        [tf, stack, delayed_nav, launch_testing.actions.ReadyToTest()]
    )


def _wait_for_locked_map(node: RclpyNode, timeout: float) -> OccupancyGrid:
    holder: list[OccupancyGrid] = []

    def cb(msg: OccupancyGrid) -> None:
        if (
            abs(msg.info.resolution - RESOLUTION) < 1e-6
            and abs(msg.info.origin.position.x - ORIGIN_X) < 1e-6
            and abs(msg.info.origin.position.y - ORIGIN_Y) < 1e-6
            and msg.info.width == 80
            and msg.info.height == 60
        ):
            holder.append(msg)

    node.create_subscription(OccupancyGrid, "map", cb, MAP_QOS)
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        rclpy.spin_once(node, timeout_sec=0.1)
        if holder and occupancy_counts(holder[-1]).get("occupied", 0) >= 22:
            return holder[-1]
    raise AssertionError("Locked /map not received")


def _pose(x: float, y: float) -> PoseStamped:
    msg = PoseStamped()
    msg.header.frame_id = "map"
    msg.pose.position.x = x
    msg.pose.position.y = y
    msg.pose.orientation.w = 1.0
    return msg


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


@pytest.mark.launch(fixture=launch_description_navfn)
def test_launch_b_navfn_around_path() -> None:
    rclpy.init()
    node = RclpyNode("launch_test_b_client")
    map_msg = _wait_for_locked_map(node, 45.0)

    client = ActionClient(node, ComputePathToPose, "compute_path_to_pose")
    assert client.wait_for_server(timeout_sec=90.0), "compute_path_to_pose action missing"

    # Extra time for static costmap to ingest transient-local /map.
    deadline = time.monotonic() + 15.0
    while time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.2)

    goal = ComputePathToPose.Goal()
    stamp = node.get_clock().now().to_msg()
    goal.use_start = True
    goal.start = _pose(*START)
    goal.start.header.stamp = stamp
    goal.goal = _pose(*GOAL)
    goal.goal.header.stamp = stamp
    goal.planner_id = "GridBased"

    future = client.send_goal_async(goal)
    rclpy.spin_until_future_complete(node, future, timeout_sec=60.0)
    goal_handle = future.result()
    assert goal_handle is not None and goal_handle.accepted

    result_future = goal_handle.get_result_async()
    rclpy.spin_until_future_complete(node, result_future, timeout_sec=60.0)
    result = result_future.result().result
    assert goal_handle.status == GoalStatus.STATUS_SUCCEEDED
    assert result.error_code == 0, f"planner error_code {result.error_code}"

    path = result.path
    assert len(path.poses) >= 2, "Empty or trivial path"

    assert_path_poses_in_bounds(path, map_msg)
    assert_path_samples_free(path, map_msg, step=0.05)

    p0 = path.poses[0].pose.position
    p1 = path.poses[-1].pose.position
    assert _dist((p0.x, p0.y), START) <= POSE_TOL
    assert _dist((p1.x, p1.y), GOAL) <= POSE_TOL

    node.destroy_node()
    rclpy.shutdown()
