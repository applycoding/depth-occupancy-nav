# SPDX-License-Identifier: Apache-2.0
"""8-connected A* with corner-cutting forbidden."""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass

import numpy as np

from depth_occupancy_nav.grid import GridConfig, world_to_cell

SQRT2 = math.sqrt(2)


@dataclass
class PathResult:
    cells: list[tuple[int, int]] | None
    cost: float


def _is_free(grid: np.ndarray, iy: int, ix: int) -> bool:
    h, w = grid.shape
    if not (0 <= ix < w and 0 <= iy < h):
        return False
    return int(grid[iy, ix]) == 0


def _neighbors(ix: int, iy: int) -> list[tuple[int, int, float]]:
    out: list[tuple[int, int, float]] = []
    for dix, diy in [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1),
    ]:
        nix, niy = ix + dix, iy + diy
        step = SQRT2 if dix != 0 and diy != 0 else 1.0
        out.append((nix, niy, step))
    return out


def _can_step(grid: np.ndarray, ix: int, iy: int, nix: int, niy: int) -> bool:
    if not _is_free(grid, niy, nix):
        return False
    dix, diy = nix - ix, niy - iy
    if dix != 0 and diy != 0:
        if not (_is_free(grid, iy, nix) and _is_free(grid, niy, ix)):
            return False
    return True


def astar(
    grid: np.ndarray,
    start_xy: tuple[float, float],
    goal_xy: tuple[float, float],
    cfg: GridConfig | None = None,
) -> PathResult:
    c = cfg or GridConfig()
    sx, sy = world_to_cell(start_xy[0], start_xy[1], c)
    gx, gy = world_to_cell(goal_xy[0], goal_xy[1], c)

    if not _is_free(grid, sy, sx):
        return PathResult(None, math.inf)
    if sx == gx and sy == gy:
        return PathResult([(sx, sy)], 0.0)
    if not _is_free(grid, gy, gx):
        return PathResult(None, math.inf)

    def h(ix: int, iy: int) -> float:
        return math.hypot(gx - ix, gy - iy)

    open_set: list[tuple[float, int, int]] = []
    heapq.heappush(open_set, (h(sx, sy), sx, sy))
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    g_score: dict[tuple[int, int], float] = {(sx, sy): 0.0}

    while open_set:
        _, ix, iy = heapq.heappop(open_set)
        if ix == gx and iy == gy:
            path = [(ix, iy)]
            while (ix, iy) in came_from:
                ix, iy = came_from[(ix, iy)]
                path.append((ix, iy))
            path.reverse()
            return PathResult(path, g_score[(gx, gy)])

        for nix, niy, step_cost in _neighbors(ix, iy):
            if not _can_step(grid, ix, iy, nix, niy):
                continue
            tentative = g_score[(ix, iy)] + step_cost
            key = (nix, niy)
            if key not in g_score or tentative < g_score[key]:
                g_score[key] = tentative
                came_from[key] = (ix, iy)
                f = tentative + h(nix, niy)
                heapq.heappush(open_set, (f, nix, niy))

    return PathResult(None, math.inf)


def inflate_grid(grid: np.ndarray, robot_radius: float, resolution: float) -> np.ndarray:
    """Circular inflation in cell units."""
    r = int(math.ceil(robot_radius / resolution))
    out = grid.copy()
    occ = np.argwhere(grid == 100)
    h, w = grid.shape
    for iy, ix in occ:
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    ny, nx = iy + dy, ix + dx
                    if 0 <= nx < w and 0 <= ny < h:
                        out[ny, nx] = 100
    return out


def path_enters_aabb(
    path: list[tuple[int, int]] | None,
    cfg: GridConfig,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
) -> bool:
    if not path:
        return False
    for ix, iy in path:
        x = cfg.origin_x + (ix + 0.5) * cfg.resolution
        y = cfg.origin_y + (iy + 0.5) * cfg.resolution
        if xmin <= x <= xmax and ymin <= y <= ymax:
            return True
    return False
