# SPDX-License-Identifier: Apache-2.0
"""Analytic scene: ground plane and two axis-aligned boxes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

HitKind = Literal["front_box", "side_box", "ground", "none"]


@dataclass(frozen=True)
class AABB:
    xmin: float
    xmax: float
    ymin: float
    ymax: float
    zmin: float
    zmax: float

    def ray_intersect(
        self, origin: np.ndarray, direction: np.ndarray, t_min: float, t_max: float
    ) -> tuple[float, float]:
        """Slab method; returns (t_enter, t_exit) or (inf, -inf) if miss."""
        t0 = t_min
        t1 = t_max
        for i, (o, d, lo, hi) in enumerate(
            zip(
                origin,
                direction,
                [self.xmin, self.ymin, self.zmin],
                [self.xmax, self.ymax, self.zmax],
            )
        ):
            if abs(d) < 1e-15:
                if o < lo or o > hi:
                    return (np.inf, -np.inf)
            else:
                inv = 1.0 / d
                t_near = (lo - o) * inv
                t_far = (hi - o) * inv
                if t_near > t_far:
                    t_near, t_far = t_far, t_near
                t0 = max(t0, t_near)
                t1 = min(t1, t_far)
                if t0 > t1:
                    return (np.inf, -np.inf)
        return (t0, t1)


FRONT_BOX = AABB(2.75, 3.15, -0.45, 0.45, 0.0, 1.20)
SIDE_BOX = AABB(4.05, 4.45, 1.25, 2.15, 0.0, 1.00)


def ground_plane_hit(origin: np.ndarray, direction: np.ndarray) -> float | None:
    """Intersection with z=0 ground; t along unit map direction."""
    if abs(direction[2]) < 1e-15:
        return None
    t = -origin[2] / direction[2]
    if t <= 0:
        return None
    return t


def classify_hit(point: np.ndarray) -> HitKind:
    """Classify closest hit point (with tolerance)."""
    tol = 1e-9
    if abs(point[0] - FRONT_BOX.xmin) < 0.01 and (
        FRONT_BOX.ymin - tol <= point[1] <= FRONT_BOX.ymax + tol
        and FRONT_BOX.zmin - tol <= point[2] <= FRONT_BOX.zmax + tol
    ):
        return "front_box"
    if (
        SIDE_BOX.xmin - tol <= point[0] <= SIDE_BOX.xmax + tol
        and SIDE_BOX.ymin - tol <= point[1] <= SIDE_BOX.ymax + tol
        and SIDE_BOX.zmin - tol <= point[2] <= SIDE_BOX.zmax + tol
    ):
        return "side_box"
    if point[2] <= tol:
        return "ground"
    return "none"
