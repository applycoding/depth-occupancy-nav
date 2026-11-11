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

"""Publish noise-free locked-scene depth and CameraInfo for launch tests."""

from __future__ import annotations

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import CameraInfo, Image

from depth_occupancy_nav.camera import H, W
from depth_occupancy_nav.noise import add_depth_noise
from depth_occupancy_nav.render import render_depth

from depth_occupancy_nav_ros.camera_contract import (
    locked_camera_info_msg,
    locked_camera_info_msg_bad_fx,
)

LATCHED_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
)


class LockedScenePublisher(Node):
    def __init__(self) -> None:
        super().__init__("locked_scene_publisher")
        self.declare_parameter("frame_id", "camera_optical_frame")
        self.declare_parameter("depth_topic", "depth/image")
        self.declare_parameter("camera_info_topic", "depth/camera_info")
        self.declare_parameter("publish_rate_hz", 5.0)
        self.declare_parameter("bad_camera_info", False)
        self.declare_parameter("bad_camera_info_after", 0)
        self.declare_parameter("bad_camera_from_start", False)
        self.declare_parameter("publish_noisy_depth_with_bad_ci", False)

        frame_id = self.get_parameter("frame_id").get_parameter_value().string_value
        depth_topic = self.get_parameter("depth_topic").get_parameter_value().string_value
        ci_topic = (
            self.get_parameter("camera_info_topic").get_parameter_value().string_value
        )
        rate = self.get_parameter("publish_rate_hz").get_parameter_value().double_value
        self._bad = self.get_parameter("bad_camera_info").get_parameter_value().bool_value
        self._bad_from_start = (
            self.get_parameter("bad_camera_from_start").get_parameter_value().bool_value
        )
        self._bad_after = (
            self.get_parameter("bad_camera_info_after").get_parameter_value().integer_value
        )
        self._publish_noisy_bad_ci = (
            self.get_parameter("publish_noisy_depth_with_bad_ci")
            .get_parameter_value()
            .bool_value
        )
        if self._bad_from_start:
            self._bad = True

        depth_np, _ = render_depth()
        self._depth_f32 = depth_np.astype(np.float32)
        self._frame_id = frame_id
        self._depth_pub = self.create_publisher(Image, depth_topic, 10)
        self._ci_pub = self.create_publisher(CameraInfo, ci_topic, LATCHED_QOS)
        self._tick = 0
        self._timer = self.create_timer(1.0 / max(rate, 0.1), self._publish)

    def _camera_info(self) -> CameraInfo:
        if self._bad or (self._bad_after > 0 and self._tick >= self._bad_after):
            msg = locked_camera_info_msg_bad_fx(self._frame_id)
        else:
            msg = locked_camera_info_msg(self._frame_id)
        msg.header.stamp = self.get_clock().now().to_msg()
        return msg

    def _depth_payload(self) -> np.ndarray:
        use_noisy = (
            self._publish_noisy_bad_ci
            and self._bad_after > 0
            and self._tick >= self._bad_after
        )
        if use_noisy:
            noisy = add_depth_noise(self._depth_f32.astype(np.float64), seed=1)
            return noisy.astype(np.float32)
        return self._depth_f32

    def _publish(self) -> None:
        self._tick += 1
        ci = self._camera_info()
        self._ci_pub.publish(ci)

        depth = self._depth_payload()
        img = Image()
        img.header.stamp = ci.header.stamp
        img.header.frame_id = self._frame_id
        img.height = H
        img.width = W
        img.encoding = "32FC1"
        img.is_bigendian = 0
        img.step = W * 4
        img.data = depth.tobytes(order="C")
        self._depth_pub.publish(img)


def main() -> None:
    rclpy.init()
    node = LockedScenePublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
