# SPDX-License-Identifier: Apache-2.0
"""Generate compact JSON goldens for Vitest."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from depth_occupancy_nav.backproject import pixel_to_map
from depth_occupancy_nav.camera import CX, CY, FX, Camera
from depth_occupancy_nav.grid import L_FREE, L_OCC, ray_walk_2d, update_grid_from_depth
from depth_occupancy_nav.planner import astar
from depth_occupancy_nav.render import render_depth

# constants for TS
assert abs(FX - 69.2820323027551) < 1e-12


def main() -> None:
    depth, _ = render_depth()
    cam = Camera()
    walk = ray_walk_2d(0, 0, 2.75, 0)
    assert len(walk) == 28

    neighbors = []
    for u, v in ((39, 29), (40, 29), (39, 30), (40, 30)):
        z = float(depth[v, u])
        pt = pixel_to_map(u, v, z, cam)
        neighbors.append({"u": u, "v": v, "z": z, "map": pt.tolist()})

    g = update_grid_from_depth(depth)
    vals = g.occupancy_values()
    occupied_cells = [
        [int(ix), int(iy), 100]
        for iy in range(vals.shape[0])
        for ix in range(vals.shape[1])
        if vals[iy, ix] == 100
    ]

    grid = vals
    open_path = astar(grid, (0.5, 0.0), (1.5, 0.0))
    around = astar(grid, (0.5, 0.0), (5.5, -1.5))

    golden = {
        "walk_28": walk,
        "optical_axis": pixel_to_map(CX, CY, 2.75, cam).tolist(),
        "neighbors": neighbors,
        "occupied_cells": occupied_cells,
        "probes": {
            "2.65,0": int(g.value_at_world(2.65, 0)),
            "2.75,0": int(g.value_at_world(2.75, 0)),
            "2.95,0": int(g.value_at_world(2.95, 0)),
            "3.50,0": int(g.value_at_world(3.50, 0)),
            "0.50,0": int(g.value_at_world(0.50, 0)),
            "1.50,0": int(g.value_at_world(1.50, 0)),
            "5.50,-1.50": int(g.value_at_world(5.50, -1.50)),
            "4.05,1.70": int(g.value_at_world(4.05, 1.70)),
        },
        "open_path_cells": [[int(a), int(b)] for a, b in (open_path.cells or [])],
        "open_path_cost": open_path.cost,
        "around_path_len": len(around.cells) if around.cells else 0,
        "around_first": list(around.cells[0]) if around.cells else None,
        "around_last": list(around.cells[-1]) if around.cells else None,
        "around_cost": around.cost,
        "counts": g.counts(),
        "fx": FX,
        "l_occ": L_OCC,
        "l_free": L_FREE,
    }
    out = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "golden.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(golden, indent=2) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
