# SPDX-License-Identifier: Apache-2.0
"""Back-project depth pixels to map-frame 3D points."""

from __future__ import annotations

import numpy as np

from depth_occupancy_nav.camera import CAMERA_T, MAP_R_OPTICAL, Camera


def pixel_to_map(u: float, v: float, z: float, camera: Camera | None = None) -> np.ndarray:
    """Back-project valid pixel (u, v) with camera-Z depth z to map frame."""
    cam = camera or Camera()
    x_opt = (u - cam.cx) / cam.fx * z
    y_opt = (v - cam.cy) / cam.fy * z
    p_opt = np.array([x_opt, y_opt, z], dtype=np.float64)
    return MAP_R_OPTICAL @ p_opt + CAMERA_T


def backproject_depth(
    depth: np.ndarray, camera: Camera | None = None
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Back-project all valid pixels.

    Returns u_indices, v_indices, points (N, 3) map coordinates.
    """
    cam = camera or Camera()
    mask = depth > 0
    vs, us = np.where(mask)
    zs = depth[mask]
    triples = zip(us, vs, zs, strict=True)
    pts = [pixel_to_map(float(u), float(v), float(z), cam) for u, v, z in triples]
    points = np.stack(pts)
    return us.astype(np.float64), vs.astype(np.float64), points
