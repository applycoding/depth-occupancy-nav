# SPDX-License-Identifier: Apache-2.0
"""Write web/report.json from locked Python core measurements."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from depth_occupancy_nav.grid import update_grid_from_depth
from depth_occupancy_nav.noise import add_depth_noise, depth_rmse
from depth_occupancy_nav.planner import astar
from depth_occupancy_nav.render import render_depth


def _git_sha() -> str:
    env = os.environ.get("GITHUB_SHA", "").strip()
    if env:
        return env
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _apt_versions() -> dict[str, str]:
    path = Path("apt-versions.txt")
    if not path.is_file():
        return {}
    want = {
        "ros-jazzy-nav2-navfn-planner",
        "ros-jazzy-nav2-planner",
        "ros-jazzy-nav2-costmap-2d",
    }
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t", 1)
        if len(parts) == 2 and parts[0] in want:
            out[parts[0]] = parts[1]
    return out


def build_report() -> dict:
    depth, kinds = render_depth()
    valid = int((depth > 0).sum())
    g = update_grid_from_depth(depth)
    base_counts = g.counts()
    grid_vals = g.occupancy_values()
    around = astar(grid_vals, (0.5, 0.0), (5.5, -1.5))
    noisy = add_depth_noise(depth, 1)
    rmse, dropped = depth_rmse(depth, noisy)
    noisy_counts = update_grid_from_depth(noisy).counts()
    hm = update_grid_from_depth(depth, mode="height_mutant").counts()
    m1 = update_grid_from_depth(depth, mode="one_pass_m1").counts()
    m2 = update_grid_from_depth(depth, mode="one_pass_m2").counts()
    in_ci = bool(os.environ.get("GITHUB_SHA"))
    return {
        "schema": 1,
        "git_sha": _git_sha(),
        "sample": not in_ci,
        "ci_run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "valid_pixels": valid,
        "renderer": {
            "front_box": int((kinds == "front_box").sum()),
            "ground": int((kinds == "ground").sum()),
            "side_box": int((kinds == "side_box").sum()),
        },
        "occupancy_clean": base_counts,
        "around_path_length": len(around.cells) if around.cells else 0,
        "around_path_cost": around.cost if around.cells else None,
        "noisy_rmse": rmse,
        "noisy_dropped": dropped,
        "occupancy_noisy": noisy_counts,
        "height_mutant": hm,
        "one_pass_m1": m1,
        "one_pass_m2": m2,
        "nav2_debs": _apt_versions(),
    }


def main() -> None:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("web/public")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "report.json"
    path.write_text(json.dumps(build_report(), indent=2) + "\n", encoding="utf-8")
    print("wrote", path)


if __name__ == "__main__":
    main()
