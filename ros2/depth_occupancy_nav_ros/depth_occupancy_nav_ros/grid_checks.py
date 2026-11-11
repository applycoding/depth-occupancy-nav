# Copyright 2026 Arpan Bom

# Licensed under the Apache License, Version 2.0
# SPDX-License-Identifier: Apache-2.0
"""Shared OccupancyGrid assertions for launch tests A and B."""

from __future__ import annotations

import math

from nav_msgs.msg import OccupancyGrid

from depth_occupancy_nav.grid import ORIGIN_X, ORIGIN_Y, RESOLUTION


def grid_value_at_world(msg: OccupancyGrid, x: float, y: float) -> int:
    ix = int(math.floor((x - ORIGIN_X) / RESOLUTION))
    iy = int(math.floor((y - ORIGIN_Y) / RESOLUTION))
    if ix < 0 or iy < 0 or ix >= msg.info.width or iy >= msg.info.height:
        return -1
    return int(msg.data[iy * msg.info.width + ix])


def occupancy_counts(msg: OccupancyGrid) -> dict[str, int]:
    occ = free = unk = mid = 0
    for v in msg.data:
        if v == 100:
            occ += 1
        elif v == 0:
            free += 1
        elif v == -1:
            unk += 1
        elif 0 < v < 100:
            mid += 1
    return {"occupied": occ, "free": free, "unknown": unk, "mid": mid}


def assert_criterion5_grid(msg: OccupancyGrid) -> None:
    counts = occupancy_counts(msg)
    assert counts == {"occupied": 22, "free": 1698, "unknown": 3080, "mid": 0}, counts

    probes = {
        (2.65, 0.0): 0,
        (2.75, 0.0): 100,
        (2.95, 0.0): -1,
        (3.50, 0.0): -1,
        (0.50, 0.0): 0,
        (1.50, 0.0): 0,
        (5.50, -1.50): 0,
        (4.05, 1.70): 100,
    }
    for (x, y), want in probes.items():
        got = grid_value_at_world(msg, x, y)
        assert got == want, f"probe ({x}, {y}) expected {want}, got {got}"


def _map_bounds(msg: OccupancyGrid) -> tuple[float, float, float, float]:
    ox = msg.info.origin.position.x
    oy = msg.info.origin.position.y
    res = msg.info.resolution
    wx = ox + msg.info.width * res
    wy = oy + msg.info.height * res
    return ox, oy, wx, wy


def assert_path_poses_in_bounds(path, msg: OccupancyGrid) -> None:
    ox, oy, wx, wy = _map_bounds(msg)
    for pose in path.poses:
        x = pose.pose.position.x
        y = pose.pose.position.y
        assert math.isfinite(x) and math.isfinite(y), (x, y)
        assert ox <= x <= wx and oy <= y <= wy, (x, y)


def _sample_segment(
    x0: float, y0: float, x1: float, y1: float, step: float
) -> list[tuple[float, float]]:
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return [(x0, y0)]
    n = max(1, int(math.ceil(length / step)))
    pts: list[tuple[float, float]] = []
    for i in range(n + 1):
        t = min(1.0, i * step / length)
        pts.append((x0 + t * dx, y0 + t * dy))
    return pts


def assert_path_samples_free(path, msg: OccupancyGrid, step: float = 0.05) -> None:
    poses = path.poses
    for i in range(len(poses) - 1):
        p0 = poses[i].pose.position
        p1 = poses[i + 1].pose.position
        for x, y in _sample_segment(p0.x, p0.y, p1.x, p1.y, step):
            v = grid_value_at_world(msg, x, y)
            assert v == 0, f"segment sample ({x}, {y}) has cost {v}, expected free (0)"
