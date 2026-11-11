# depth-occupancy-nav

Simulation only. Synthetic depth only. Not tested on real cameras or real robots.

Portfolio demo by Arpan Bom (Apache-2.0). An original implementation, inspired by known methods, turns **simulated pinhole depth** into a 2D occupancy grid and shows that a planner can run on that grid. Methods include pinhole back-projection, analytic ray casting, a **height gate** (not plane fitting), two-pass log-odds updates, and 8-connected A* with corner cutting forbidden.

Live demo (after Pages deploy on `main`): https://applycoding.github.io/depth-occupancy-nav/

## What you see

- A single depth frame marks the **visible surface**, not the solid volume.
- The height filter is a **height gate** on map z, not RANSAC or a fitted ground plane.
- **Invalid depth pixels** (0, NaN, out of range) do not clear rays to max range.

## Why ROS 2 Jazzy

Core CI uses **Python 3.12** (NumPy 2.5.4). Jazzy on Ubuntu Noble is an LTS (supported to May 2029) with Python 3.12, so core and ROS jobs share one interpreter. Newer distros (for example Lyrical) ship newer Python; this repo stays on Jazzy for the locked 3.12 pin.

## Sibling repos (contrast)

| Repo | This repo |
| --- | --- |
| `ros2-nav2-slam-sim` (Gazebo, SLAM) | No Gazebo; synthetic depth only |
| `nav2-coverage-planner-compare` | Builds the grid from depth, does not compare planners |
| `lidar-shape-classifier-ros2` | Depth camera, not LiDAR clusters |
| Others (`nav2-behavior-trees`, vision tracking, edge detectors) | Different problem domain |

See PLAN.md for the full table.

## Measured scenario (noise-free, one frame)

Values are asserted in `tests/test_criteria.py` against the locked scene:

| Quantity | Value |
| --- | ---: |
| Valid depth pixels | 2434 |
| After height filter (kept) | 823 |
| Occupied cells (100) | 22 |
| Free cells (0) | 1698 |
| Unknown (-1) | 3080 |
| Mid (1..99) | 0 |
| Open A* path length / cost | 11 / 10.0 |
| Around A* path length / cost | 51 / 35+15*sqrt(2) |
| Inflated occupied cells (r=0.15 m) | 130 |

## Mutants

| Mutant | Shows |
| --- | --- |
| Height-filter mutant (all endpoints occupied) | Floor becomes a wall; around goal blocked |
| One-pass M1 / M2 | Visible face can be cleared if free runs after occupied |

Height-filter mutant counts: occupied 117, free 1208, unknown 3080, mid 395 (see `DEVIATIONS.md` for promotion rule).

## How this was verified

| Criterion | Evidence |
| --- | --- |
| 1-12 | `pytest` (`tests/test_criteria.py`) |
| 13 | CI `core` job (ruff, pytest, hygiene, authorship, pin check) |
| 14-15 | CI `ros` job (`depth_occupancy_nav_ros` launch tests, Navfn on `/map`) |
| 16 | CI `web` job (Vitest goldens, Playwright on built site) |
| 17 | CI `pages` job on `main` after green `core`/`ros`/`web` |
| 18-20 | This README, NOTICE, compact fixtures |

CI runs **Nav2 Navfn** on the published occupancy grid in launch test B (static costmap layer only, `allow_unknown: false`).

## Run locally

```bash
python3 -m pip install --require-hashes -r requirements.txt
python3 -m pip install -e .
pytest
ruff check src tests
```

ROS launch tests (pinned image):

```bash
docker run --rm --init --platform linux/amd64 -v "$PWD:/ws" -w /ws \
  ros:jazzy-ros-base@sha256:8eed0a4669bbf43ee331878a4c39bd8ebddea8e3312a58b4fae8edb14526b617 \
  bash -lc 'source /opt/ros/jazzy/setup.bash && pip install -e /ws && cd /ws/ros2/depth_occupancy_nav_ros && colcon build && . install/setup.bash && pytest'
```

Viewer (Node 26.13.0):

```bash
cd web && npm ci && npm run typecheck && npm test && npm run build
```

Optional manual launch: `ros2/depth_occupancy_nav_ros/launch/manual_sim.launch.py` (not CI-gated).

## Licence

Apache-2.0. See LICENSE and NOTICE. Idea references are in REFERENCES.md only.
