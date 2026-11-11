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

"""Unit tests for depth Image format checks in the ROS node."""

from __future__ import annotations

import struct

import numpy as np
from depth_occupancy_nav_ros.camera_contract import locked_camera_info_msg
from depth_occupancy_nav_ros.node import (
    depth_image_format_valid,
    depth_message_acceptable,
    depth_payload_size_valid,
)
from sensor_msgs.msg import CameraInfo, Image

from depth_occupancy_nav.camera import H, W


def _valid_depth_image() -> Image:
    img = Image()
    img.header.frame_id = "camera_optical_frame"
    img.width = W
    img.height = H
    img.encoding = "32FC1"
    img.is_bigendian = 0
    img.step = W * 4
    data = np.zeros((H, W), dtype=np.float32)
    img.data = data.tobytes(order="C")
    return img


def _valid_ci() -> CameraInfo:
    return locked_camera_info_msg("camera_optical_frame")


def test_depth_image_format_valid_locked() -> None:
    assert depth_image_format_valid(_valid_depth_image())


def test_rejects_wrong_encoding() -> None:
    img = _valid_depth_image()
    img.encoding = "16UC1"
    assert not depth_image_format_valid(img)


def test_rejects_big_endian() -> None:
    img = _valid_depth_image()
    img.is_bigendian = 1
    assert not depth_image_format_valid(img)


def test_rejects_wrong_step() -> None:
    img = _valid_depth_image()
    img.step = img.width * 4 + 4
    assert not depth_image_format_valid(img)


def test_payload_size_valid() -> None:
    assert depth_payload_size_valid(_valid_depth_image())


def test_rejects_short_payload() -> None:
    img = _valid_depth_image()
    img.data = img.data[: len(img.data) - 4]
    assert not depth_payload_size_valid(img)


def test_rejects_oversized_payload() -> None:
    img = _valid_depth_image()
    img.data = list(bytes(img.data) + struct.pack("<f", 1.0))
    assert not depth_payload_size_valid(img)


def test_depth_acceptable_locked_pair() -> None:
    assert depth_message_acceptable(_valid_depth_image(), _valid_ci())


def test_rejects_frame_id_mismatch() -> None:
    img = _valid_depth_image()
    img.header.frame_id = "other_frame"
    assert not depth_message_acceptable(img, _valid_ci())


def test_rejects_width_mismatch_with_ci() -> None:
    img = _valid_depth_image()
    ci = _valid_ci()
    img.width = W - 1
    assert not depth_message_acceptable(img, ci)


def test_rejects_height_mismatch_with_ci() -> None:
    img = _valid_depth_image()
    ci = _valid_ci()
    img.height = H - 1
    img.step = (H - 1) * 4
    img.data = np.zeros((H - 1, W), dtype=np.float32).tobytes(order="C")
    assert not depth_message_acceptable(img, ci)


def test_rejects_bad_encoding_via_acceptable() -> None:
    img = _valid_depth_image()
    img.encoding = "16UC1"
    assert not depth_message_acceptable(img, _valid_ci())


def test_rejects_short_payload_via_acceptable() -> None:
    img = _valid_depth_image()
    img.data = img.data[: len(img.data) - 4]
    assert not depth_message_acceptable(img, _valid_ci())
