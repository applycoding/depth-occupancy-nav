# Copyright 2026 Arpan Bom
# SPDX-License-Identifier: Apache-2.0
"""Subscribe to 32FC1 depth + CameraInfo; publish nav_msgs/OccupancyGrid on /map."""

from __future__ import annotations

import numpy as np
import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import CameraInfo, Image

from depth_occupancy_nav.camera import MAX_RANGE
from depth_occupancy_nav.grid import (
    GRID_H,
    GRID_W,
    ORIGIN_X,
    ORIGIN_Y,
    RESOLUTION,
    LogOddsGrid,
    update_grid_from_depth,
)

from depth_occupancy_nav_ros.camera_contract import camera_info_valid

MAP_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
)


class DepthOccupancyNode(Node):
    """Depth-to-occupancy node (locked synthetic camera; no TF lookup in v1)."""

    def __init__(self) -> None:
        super().__init__("depth_occupancy_nav")
        self.declare_parameter("depth_topic", "depth/image")
        self.declare_parameter("camera_info_topic", "depth/camera_info")
        self.declare_parameter("map_topic", "map")
        self.declare_parameter("camera_optical_frame", "camera_optical_frame")

        self._grid = LogOddsGrid.empty()
        self._camera_info: CameraInfo | None = None
        self._camera_ok = False

        map_topic = self.get_parameter("map_topic").get_parameter_value().string_value
        depth_topic = self.get_parameter("depth_topic").get_parameter_value().string_value
        ci_topic = (
            self.get_parameter("camera_info_topic").get_parameter_value().string_value
        )

        self._map_pub = self.create_publisher(OccupancyGrid, map_topic, MAP_QOS)
        self._last_map: OccupancyGrid | None = None
        self.create_subscription(Image, depth_topic, self._on_depth, 10)
        self.create_subscription(CameraInfo, ci_topic, self._on_camera_info, 10)
        # Keep Nav2 static costmap subscriptions fed after the latched map is built.
        self.create_timer(1.0, self._republish_map)
        self.get_logger().info("depth_occupancy_nav node ready (simulation only)")

    def _on_camera_info(self, msg: CameraInfo) -> None:
        if camera_info_valid(msg):
            self._camera_info = msg
            self._camera_ok = True
        else:
            self._camera_info = None
            self._camera_ok = False
            self.get_logger().warn(
                "Rejected CameraInfo (does not match locked contract)",
                throttle_duration_sec=2.0,
            )

    def _on_depth(self, msg: Image) -> None:
        if not self._camera_ok or self._camera_info is None:
            return
        if msg.header.frame_id != self._camera_info.header.frame_id:
            return
        if not self._depth_image_valid(msg):
            self.get_logger().warn("Rejected depth Image", throttle_duration_sec=2.0)
            return

        depth = self._decode_depth(msg)
        if depth is None:
            return

        self._grid = update_grid_from_depth(depth, grid=self._grid)
        self._publish_map()

    @staticmethod
    def _depth_image_valid(msg: Image) -> bool:
        if msg.encoding != "32FC1":
            return False
        if msg.is_bigendian != 0:
            return False
        if msg.step != msg.width * 4:
            return False
        return True

    def _decode_depth(self, msg: Image) -> np.ndarray | None:
        expected = msg.height * msg.width
        if expected <= 0:
            return None
        buf = np.frombuffer(msg.data, dtype="<f4")
        if buf.size != expected:
            return None
        depth = buf.reshape((msg.height, msg.width)).astype(np.float64, copy=False)
        valid = np.isfinite(depth) & (depth > 0.0) & (depth <= MAX_RANGE)
        out = np.where(valid, depth, 0.0)
        return out

    def _publish_map(self) -> None:
        msg = self._grid_to_occupancy_grid()
        self._last_map = msg
        self._map_pub.publish(msg)

    def _republish_map(self) -> None:
        if self._last_map is not None:
            self._last_map.header.stamp = self.get_clock().now().to_msg()
            self._map_pub.publish(self._last_map)

    def _grid_to_occupancy_grid(self) -> OccupancyGrid:
        msg = OccupancyGrid()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "map"
        msg.info.resolution = RESOLUTION
        msg.info.width = GRID_W
        msg.info.height = GRID_H
        msg.info.origin.position.x = ORIGIN_X
        msg.info.origin.position.y = ORIGIN_Y
        msg.info.origin.position.z = 0.0
        msg.info.origin.orientation.w = 1.0

        vals = self._grid.occupancy_values()
        msg.data = vals.reshape(-1, order="C").astype(np.int8).tolist()
        return msg


def main() -> None:
    rclpy.init()
    node = DepthOccupancyNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
