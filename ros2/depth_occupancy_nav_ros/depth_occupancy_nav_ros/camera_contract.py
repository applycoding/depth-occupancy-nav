# Copyright 2026 Arpan Bom
# SPDX-License-Identifier: Apache-2.0
"""Validate sensor_msgs/CameraInfo against the locked synthetic camera."""

from __future__ import annotations

import math

from sensor_msgs.msg import CameraInfo

from depth_occupancy_nav.camera import CX, CY, FX, FY, H, W

INTRIN_TOL = 1e-9

LOCKED_INTRINSICS = (FX, FY, CX, CY)


def _d_is_zero(d: list[float] | tuple[float, ...]) -> bool:
    return len(d) == 0 or all(abs(x) < 1e-12 for x in d)


def camera_info_valid(msg: CameraInfo) -> bool:
    """Return True iff msg matches the locked undistorted contract from PLAN.md section 6."""
    if msg.width != W or msg.height != H:
        return False
    if msg.binning_x not in (0, 1) or msg.binning_y not in (0, 1):
        return False
    if not _d_is_zero(msg.d):
        return False
    k = msg.k
    if len(k) < 6:
        return False
    fx, fy, cx, cy = k[0], k[4], k[2], k[5]
    for got, want in zip((fx, fy, cx, cy), LOCKED_INTRINSICS, strict=True):
        if abs(got - want) > INTRIN_TOL:
            return False
    roi = msg.roi
    if roi.x_offset != 0 or roi.y_offset != 0:
        return False
    if roi.width not in (0, W) or roi.height not in (0, H):
        return False
    if roi.do_rectify:
        return False
    return True


def locked_camera_info_msg(frame_id: str) -> CameraInfo:
    """Build a valid CameraInfo for tests and publishers."""
    msg = CameraInfo()
    msg.header.frame_id = frame_id
    msg.width = W
    msg.height = H
    msg.distortion_model = "plumb_bob"
    msg.d = []
    msg.k = [FX, 0.0, CX, 0.0, FY, CY, 0.0, 0.0, 1.0]
    msg.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
    msg.p = [FX, 0.0, CX, 0.0, 0.0, FY, CY, 0.0, 0.0, 0.0, 1.0, 0.0]
    msg.binning_x = 1
    msg.binning_y = 1
    msg.roi.x_offset = 0
    msg.roi.y_offset = 0
    msg.roi.height = H
    msg.roi.width = W
    msg.roi.do_rectify = False
    return msg


def locked_camera_info_msg_bad_fx(frame_id: str) -> CameraInfo:
    msg = locked_camera_info_msg(frame_id)
    msg.k[0] = FX + 1.0
    msg.p[0] = FX + 1.0
    return msg
