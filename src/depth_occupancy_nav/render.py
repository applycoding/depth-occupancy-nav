# SPDX-License-Identifier: Apache-2.0
"""Analytic pinhole depth renderer (camera-Z, metres)."""

from __future__ import annotations

import numpy as np

from depth_occupancy_nav.camera import CAMERA_T, MAP_R_OPTICAL, Camera
from depth_occupancy_nav.scene import (
    FRONT_BOX,
    SIDE_BOX,
    HitKind,
    classify_hit,
    ground_plane_hit,
)


def _camera_z_at_t(origin: np.ndarray, direction: np.ndarray, t: float) -> float:
    p_map = origin + t * direction
    p_opt = MAP_R_OPTICAL.T @ (p_map - CAMERA_T)
    return p_opt[2]


def render_depth(
    camera: Camera | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Render noise-free depth image and per-pixel hit kinds.

    Returns depth (H, W) float64, kinds (H, W) object array of HitKind strings.
    """
    cam = camera or Camera()
    depth = np.zeros((cam.height, cam.width), dtype=np.float64)
    kinds = np.full((cam.height, cam.width), "none", dtype=object)

    origin = CAMERA_T.copy()

    for v in range(cam.height):
        for u in range(cam.width):
            direction = cam.map_ray_direction(float(u), float(v))
            best_t = np.inf
            best_kind: HitKind = "none"

            for box, kind in ((FRONT_BOX, "front_box"), (SIDE_BOX, "side_box")):
                t0, t1 = box.ray_intersect(origin, direction, 0.0, cam.max_range)
                if t0 <= t1 and t0 > 0 and t0 < best_t:
                    z = _camera_z_at_t(origin, direction, t0)
                    if 0 < z <= cam.max_range:
                        best_t = t0
                        best_kind = kind

            gt = ground_plane_hit(origin, direction)
            if gt is not None and gt <= cam.max_range and gt < best_t:
                z = _camera_z_at_t(origin, direction, gt)
                if 0 < z <= cam.max_range:
                    best_t = gt
                    best_kind = "ground"

            if best_t < np.inf:
                p_map = origin + best_t * direction
                depth[v, u] = _camera_z_at_t(origin, direction, best_t)
                kinds[v, u] = classify_hit(p_map) if best_kind == "ground" else best_kind

    return depth, kinds
