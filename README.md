<!-- SPDX-License-Identifier: Apache-2.0 -->
# depth-occupancy-nav

Simulation only. Synthetic depth only. Not tested on real cameras or real robots.

Portfolio demo by Arpan Bom (Apache-2.0). An **original implementation** of pinhole back-projection, a height gate, Amanatides-Woo 2D grid traversal, a two-pass log-odds occupancy grid, and 8-connected A*, **inspired by** Moravec and Elfes (1985), Thrun, Burgard and Fox (*Probabilistic Robotics*, ch. 9), Amanatides and Woo (1987), and the Nav2 costmap ideas (see [REFERENCES.md](REFERENCES.md)).

**Nav2 Navfn** and the Nav2 costmap **StaticLayer** are unmodified third-party apt packages (Navigation2 **1.3.13** noble debs). They are used **only** in CI launch test B.

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

### Noise (seed 1)

RMSE **0.0364728080413652** (asserted with tolerance `1e-9`). Occupancy: **41** / **1684** / **3062** / **13** mid. Around A* path still length 51 with the same cost.

### Mutants

| Mutant | Occupied / free / unknown / mid | Notes |
| --- | --- | --- |
| Height-filter (all endpoints occupied) | **78 / 1247 / 3080 / 395** | Floor becomes a wall; around goal blocked; see PLAN Amendment 1 |
| One-pass M1 | 0 / 1709 / 3080 / 11 | `(37, 30)` cleared |
| One-pass M2 | 0 / 1714 / 3080 / 6 | `(37, 30)` cleared |

## Nav2 launch test B (criterion 15)

CI runs Navfn on the published `/map` with a static-only global costmap (`allow_unknown: false`).

The **around goal** `(5.50, -1.50)` is reachable on the unobstructed octile-optimal path through free cells beside the obstacle. Evidence that Navfn respects **lethal** and **unknown** cells comes from the **global costmap** probes before planning and from **negative goals** (shadow at `(5.50, 0.00)` and face at `(2.75, 0.00)`), not from the around path alone. With `tolerance: 0.05`, both negative goals return Navfn error code **208** (`NO_VALID_PATH`), not **206** (`GOAL_OCCUPIED`); see `DEVIATIONS.md`.

Nav2 apt pin (2026-11-11): `ros-jazzy-nav2-navfn-planner` **1.3.13-1noble.20260921.031752**, `ros-jazzy-nav2-planner` **1.3.13-1noble.20260921.031801**, `ros-jazzy-nav2-costmap-2d` **1.3.13-1noble.20260921.024946**. Rosdistro lists 1.3.14-1; noble apt served 1.3.13. See DEVIATIONS.md and PLAN Amendment 1.

## How this was verified

| Criterion | Tests / checks |
| --- | --- |
| 1 | `test_criterion_1_license` |
| 2 | `test_criterion_2_optical_axis` |
| 3 | `test_criterion_3_renderer_counts`, `test_criterion_3_height_filter_counts` |
| 4 | `test_criterion_4_ray_walk`, `test_prob_to_occupancy_value_half_even` |
| 5 | `test_criterion_5_occupancy`, `test_conflicting_evidence_after_free_saturation` |
| 6 | `test_criterion_6_height_filter_unit` |
| 7 | `test_criterion_7_planner` |
| 8 | `test_criterion_8_inflation` |
| 9 | `test_criterion_9_noise` |
| 10 | `test_criterion_10_height_mutant` |
| 11 | `test_criterion_11_png_roundtrip` |
| 12 | `test_criterion_12_one_pass_mutants` |
| 13 | CI `core` job: `pytest`, `ruff`, `scripts/hygiene_scan.py`, `scripts/check_authorship.py`, workflow SHA pin check |
| 14 | `test_launch_a_valid_camera_matches_criterion5`, `test_launch_a_bad_camera_info_does_not_mutate_grid`, `test_launch_a_bad_camera_from_start_never_updates_grid`, plus `test_camera_contract.py` and `test_node_validation.py` |
| 15 | `test_launch_b_global_costmap_matches_map`, `test_launch_b_navfn_negative_goals`, `test_launch_b_navfn_around_path` |
| 16 | `web/tests/golden.test.ts`; Playwright `viewer.spec.ts` (`honesty labels…`, `default data-occupied…`, `around path length 51…`, `shadow goal…`, `sliders change…`) |
| 17 | CI `pages` job: `web-dist` artifact, `dist/index.html` and `dist/report.json` |
| 18-20 | This README, NOTICE, SPDX header test |

## Run locally

Core:

```bash
python3 -m pip install --require-hashes -r requirements.txt
python3 -m pip install -e .
pytest
ruff check src tests
```

ROS launch tests (same steps as CI; requires Docker and pre-fetched Nav2 debs in `ros-debs/` as in CI):

```bash
scripts/run_ros_tests.sh
```

The stock `ros:jazzy-ros-base` image does not include Nav2; `pip install -e` on Noble hits PEP 668 without the CI container workflow above.

Viewer (Node 26.13.0):

```bash
cd web && npm ci && npm run typecheck && npm test && npm run build
cd web && npm run test:e2e
```

Playwright downloads Chromium at test time; see NOTICE.

Optional manual launch: `ros2/depth_occupancy_nav_ros/launch/manual_sim.launch.py` (not CI-gated).

## Licence

Apache-2.0. See LICENSE and NOTICE. Idea references are in REFERENCES.md only.
