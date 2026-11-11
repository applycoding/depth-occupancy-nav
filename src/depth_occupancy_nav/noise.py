# SPDX-License-Identifier: Apache-2.0
"""Locked multiplicative-additive depth noise model."""

from __future__ import annotations

import numpy as np

from depth_occupancy_nav.camera import MAX_RANGE

SIGMA_REL = 0.01
SIGMA_ABS = 0.01


def add_depth_noise(depth: np.ndarray, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n1 = rng.standard_normal(depth.shape)
    n2 = rng.standard_normal(depth.shape)
    mask = depth > 0
    noisy = np.where(mask, depth * (1.0 + SIGMA_REL * n1) + SIGMA_ABS * n2, 0.0)
    noisy = np.where((noisy > 0.0) & (noisy <= MAX_RANGE), noisy, 0.0)
    return noisy


def depth_rmse(clean: np.ndarray, noisy: np.ndarray) -> tuple[float, int]:
    mask = (clean > 0) & (noisy > 0)
    dropped = int(np.sum((clean > 0) & ~(noisy > 0)))
    if not np.any(mask):
        return 0.0, dropped
    diff = noisy[mask] - clean[mask]
    rmse = float(np.sqrt(np.mean(diff * diff)))
    return rmse, dropped
