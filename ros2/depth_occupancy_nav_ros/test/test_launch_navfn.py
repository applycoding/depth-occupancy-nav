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

"""Launch test B: Navfn planner on static-layer costmap fed by published /map."""

from __future__ import annotations

import math
import os
import time

import pytest

pytest.importorskip("launch_pytest")
import launch_pytest
import launch_testing.actions
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
from conftest import spin_create_node

from depth_occupancy_nav_ros.grid_checks import (
    assert_path_poses_in_bounds,
    assert_path_samples_free,
    grid_value_at_world,
    occupancy_counts,
)

MAP_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
)

START = (0.50, 0.00)
GOAL_AROUND = (5.50, -1.50)
GOAL_SHADOW = (5.50, 0.00)
GOAL_FACE = (2.75, 0.00)
POSE_TOL = 0.15

# nav2_msgs/action/ComputePathToPose.action result codes (Nav2 1.3.x)
ERR_NONE = 0
ERR_NO_VALID_PATH = 208
ERR_GOAL_OCCUPIED = 206


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
    delayed_nav = TimerAction(period=4.0, actions=[planner, lifecycle])
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


def _wait_for_global_costmap(node: RclpyNode, timeout: float) -> OccupancyGrid:
    holder: list[OccupancyGrid] = []

    def cb(msg: OccupancyGrid) -> None:
        if msg.info.width > 0 and msg.info.height > 0:
            holder.append(msg)

    node.create_subscription(OccupancyGrid, "global_costmap/costmap", cb, MAP_QOS)
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        rclpy.spin_once(node, timeout_sec=0.1)
        if not holder:
            continue
        msg = holder[-1]
        if (
            msg.info.width == 80
            and msg.info.height == 60
            and abs(msg.info.resolution - 0.1) < 1e-6
            and abs(msg.info.origin.position.x - (-1.0)) < 1e-6
            and abs(msg.info.origin.position.y - (-3.0)) < 1e-6
            and occupancy_counts(msg).get("occupied", 0) >= 1
        ):
            return msg
    raise AssertionError("global_costmap/costmap not populated with locked grid")


def _assert_locked_costmap_probes(costmap: OccupancyGrid) -> None:
    probes = {
        (2.75, 0.0): 100,
        (2.95, 0.0): -1,
        (5.5, -1.5): 0,
    }
    for (x, y), want in probes.items():
        got = grid_value_at_world(costmap, x, y)
        assert got == want, f"costmap probe ({x}, {y}) expected {want}, got {got}"


def _pose(x: float, y: float) -> PoseStamped:
    msg = PoseStamped()
    msg.header.frame_id = "map"
    msg.pose.position.x = x
    msg.pose.position.y = y
    msg.pose.orientation.w = 1.0
    return msg


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _wait_for_action(node: RclpyNode, client: ActionClient, timeout: float) -> None:
    assert client.wait_for_server(timeout_sec=timeout), "compute_path_to_pose action missing"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.2)
        if client.server_is_ready():
            break
    settle = time.monotonic() + 10.0
    while time.monotonic() < settle:
        rclpy.spin_once(node, timeout_sec=0.2)


def _plan_to(
    node: RclpyNode, client: ActionClient, start: tuple[float, float], goal: tuple[float, float]
) -> tuple[int, int, ComputePathToPose.Result]:
    stamp = node.get_clock().now().to_msg()
    req = ComputePathToPose.Goal()
    req.use_start = True
    req.start = _pose(*start)
    req.start.header.stamp = stamp
    req.goal = _pose(*goal)
    req.goal.header.stamp = stamp
    req.planner_id = "GridBased"

    future = client.send_goal_async(req)
    rclpy.spin_until_future_complete(node, future, timeout_sec=60.0)
    goal_handle = future.result()
    assert goal_handle is not None and goal_handle.accepted

    result_future = goal_handle.get_result_async()
    rclpy.spin_until_future_complete(node, result_future, timeout_sec=60.0)
    result_wrap = result_future.result()
    return goal_handle.status, result_wrap.result.error_code, result_wrap.result


@pytest.mark.launch(fixture=launch_description_navfn)
def test_launch_b_global_costmap_matches_map() -> None:
    node = spin_create_node("launch_test_b_costmap")
    _wait_for_locked_map(node, 45.0)
    costmap = _wait_for_global_costmap(node, 60.0)
    _assert_locked_costmap_probes(costmap)
    node.destroy_node()


@pytest.mark.launch(fixture=launch_description_navfn)
def test_launch_b_navfn_negative_goals() -> None:
    node = spin_create_node("launch_test_b_negative")
    client = ActionClient(node, ComputePathToPose, "compute_path_to_pose")
    _wait_for_locked_map(node, 45.0)
    _wait_for_global_costmap(node, 60.0)
    _wait_for_action(node, client, 90.0)

    shadow_status, shadow_code, shadow_result = _plan_to(node, client, START, GOAL_SHADOW)
    assert shadow_status != GoalStatus.STATUS_SUCCEEDED
    assert shadow_code == ERR_NO_VALID_PATH, shadow_result.error_msg
    assert len(shadow_result.path.poses) == 0

    face_status, face_code, face_result = _plan_to(node, client, START, GOAL_FACE)
    assert face_status != GoalStatus.STATUS_SUCCEEDED
    assert face_code == ERR_GOAL_OCCUPIED, face_result.error_msg
    assert len(face_result.path.poses) == 0

    node.destroy_node()


@pytest.mark.launch(fixture=launch_description_navfn)
def test_launch_b_navfn_around_path() -> None:
    node = spin_create_node("launch_test_b_client")
    client = ActionClient(node, ComputePathToPose, "compute_path_to_pose")

    map_msg = _wait_for_locked_map(node, 45.0)
    _wait_for_global_costmap(node, 60.0)
    _wait_for_action(node, client, 90.0)

    status, error_code, result = _plan_to(node, client, START, GOAL_AROUND)
    assert status == GoalStatus.STATUS_SUCCEEDED
    assert error_code == ERR_NONE, f"planner error_code {error_code}"

    path = result.path
    assert len(path.poses) >= 2, "Empty or trivial path"

    assert_path_poses_in_bounds(path, map_msg)
    assert_path_samples_free(path, map_msg, step=0.05)

    p0 = path.poses[0].pose.position
    p1 = path.poses[-1].pose.position
    assert _dist((p0.x, p0.y), START) <= POSE_TOL
    assert _dist((p1.x, p1.y), GOAL_AROUND) <= POSE_TOL

    node.destroy_node()
