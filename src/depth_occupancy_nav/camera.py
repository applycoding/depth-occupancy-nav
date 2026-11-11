# SPDX-License-Identifier: Apache-2.0
"""Locked pinhole camera model (OpenCV convention, no OpenCV dependency)."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

# Locked camera pose in map frame
CAMERA_T = np.array([0.0, 0.0, 0.80], dtype=np.float64)

# map_R_optical: columns are optical basis in map coordinates
MAP_R_OPTICAL = np.array(
    [
        [0.0, 0.0, 1.0],
        [-1.0, 0.0, 0.0],
        [0.0, -1.0, 0.0],
    ],
    dtype=np.float64,
)

W = 80
H = 60
FOV_DEG = 60.0
MAX_RANGE = 10.0

FX = FY = (W / 2.0) / math.tan(math.radians(FOV_DEG / 2.0))  # 69.2820323027551
CX = 39.5
CY = 29.5


@dataclass(frozen=True)
class Camera:
    """Locked undistorted pinhole camera."""

    width: int = W
    height: int = H
    fx: float = FX
    fy: float = FY
    cx: float = CX
    cy: float = CY
    max_range: float = MAX_RANGE

    def optical_ray_direction(self, u: float, v: float) -> np.ndarray:
        """Unnormalized optical direction for pixel (u, v)."""
        return np.array([(u - self.cx) / self.fx, (v - self.cy) / self.fy, 1.0])

    def map_ray_direction(self, u: float, v: float) -> np.ndarray:
        """Unit ray direction in map frame."""
        d_opt = self.optical_ray_direction(u, v)
        d_map = MAP_R_OPTICAL @ d_opt
        norm = np.linalg.norm(d_map)
        return d_map / norm

    def camera_matrix_k(self) -> list[float]:
        """ROS CameraInfo K layout."""
        return [self.fx, 0.0, self.cx, 0.0, self.fy, self.cy, 0.0, 0.0, 1.0]
