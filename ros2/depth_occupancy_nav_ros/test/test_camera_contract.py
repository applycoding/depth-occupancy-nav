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

"""Unit tests for PLAN.md section 6 CameraInfo acceptance rules."""

from __future__ import annotations

import pytest
from depth_occupancy_nav_ros.camera_contract import (  # noqa: E402
    camera_info_valid,
    locked_camera_info_msg,
)
from sensor_msgs.msg import CameraInfo

from depth_occupancy_nav.camera import CX, CY, FX, FY, H, W


@pytest.fixture
def valid_ci() -> CameraInfo:
    return locked_camera_info_msg("camera_optical_frame")


def test_locked_camera_info_is_valid(valid_ci: CameraInfo) -> None:
    assert camera_info_valid(valid_ci)


def test_rejects_wrong_width(valid_ci: CameraInfo) -> None:
    valid_ci.width = W - 1
    assert not camera_info_valid(valid_ci)


def test_rejects_wrong_height(valid_ci: CameraInfo) -> None:
    valid_ci.height = H - 1
    assert not camera_info_valid(valid_ci)


@pytest.mark.parametrize("binning_x", [2, 3])
def test_rejects_bad_binning_x(valid_ci: CameraInfo, binning_x: int) -> None:
    valid_ci.binning_x = binning_x
    assert not camera_info_valid(valid_ci)


@pytest.mark.parametrize("binning_y", [2, 3])
def test_rejects_bad_binning_y(valid_ci: CameraInfo, binning_y: int) -> None:
    valid_ci.binning_y = binning_y
    assert not camera_info_valid(valid_ci)


def test_accepts_binning_zero_or_one(valid_ci: CameraInfo) -> None:
    valid_ci.binning_x = 0
    valid_ci.binning_y = 0
    assert camera_info_valid(valid_ci)


def test_rejects_nonzero_distortion(valid_ci: CameraInfo) -> None:
    valid_ci.d = [0.01]
    assert not camera_info_valid(valid_ci)


def test_accepts_empty_distortion(valid_ci: CameraInfo) -> None:
    valid_ci.d = []
    assert camera_info_valid(valid_ci)


def test_accepts_all_zero_distortion(valid_ci: CameraInfo) -> None:
    valid_ci.d = [0.0, 0.0, 0.0, 0.0, 0.0]
    assert camera_info_valid(valid_ci)


def test_rejects_bad_fx(valid_ci: CameraInfo) -> None:
    valid_ci.k[0] = FX + 0.1
    assert not camera_info_valid(valid_ci)


def test_uses_k_not_p(valid_ci: CameraInfo) -> None:
    valid_ci.p[0] = FX + 10.0
    assert camera_info_valid(valid_ci)


def test_rejects_roi_offset(valid_ci: CameraInfo) -> None:
    valid_ci.roi.x_offset = 1
    assert not camera_info_valid(valid_ci)
    valid_ci.roi.x_offset = 0
    valid_ci.roi.y_offset = 1
    assert not camera_info_valid(valid_ci)


def test_rejects_roi_size(valid_ci: CameraInfo) -> None:
    valid_ci.roi.width = W - 1
    assert not camera_info_valid(valid_ci)
    valid_ci.roi.width = 0
    valid_ci.roi.height = H - 1
    assert not camera_info_valid(valid_ci)


def test_accepts_roi_zero_size_as_full_frame(valid_ci: CameraInfo) -> None:
    valid_ci.roi.width = 0
    valid_ci.roi.height = 0
    assert camera_info_valid(valid_ci)


def test_rejects_do_rectify(valid_ci: CameraInfo) -> None:
    valid_ci.roi.do_rectify = True
    assert not camera_info_valid(valid_ci)


def test_intrinsics_tolerance(valid_ci: CameraInfo) -> None:
    valid_ci.k[2] = CX + 1e-10
    assert camera_info_valid(valid_ci)
    valid_ci.k[2] = CX + 1e-6
    assert not camera_info_valid(valid_ci)


@pytest.mark.parametrize(
    ("index", "base", "delta_reject", "delta_accept"),
    [
        (0, FX, 2e-9, 5e-10),
        (4, FY, 2e-9, 5e-10),
        (2, CX, 2e-9, 5e-10),
        (5, CY, 2e-9, 5e-10),
    ],
)
def test_intrinsic_offsets_at_tolerance(
    valid_ci: CameraInfo,
    index: int,
    base: float,
    delta_reject: float,
    delta_accept: float,
) -> None:
    valid_ci.k[index] = base + delta_reject
    assert not camera_info_valid(valid_ci)
    valid_ci.k[index] = base + delta_accept
    assert camera_info_valid(valid_ci)
