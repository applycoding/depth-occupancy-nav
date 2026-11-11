# SPDX-License-Identifier: Apache-2.0
"""Height-band filter (ground removal gate, not plane fitting)."""

from __future__ import annotations

import numpy as np

Z_MIN = 0.15
Z_MAX = 1.50


def height_keep_mask(points: np.ndarray, z_min: float = Z_MIN, z_max: float = Z_MAX) -> np.ndarray:
    """Inclusive z bounds in map frame."""
    z = points[:, 2]
    return (z >= z_min) & (z <= z_max)


def filter_by_height(
    us: np.ndarray,
    vs: np.ndarray,
    points: np.ndarray,
    z_min: float = Z_MIN,
    z_max: float = Z_MAX,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return kept pixel indices and points."""
    keep = height_keep_mask(points, z_min, z_max)
    return us[keep], vs[keep], points[keep]
