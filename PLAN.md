<!-- SPDX-License-Identifier: Apache-2.0 -->
# depth-occupancy-nav: plan

Date: 2026-11-11. Author: Arpan Bom. Licence: Apache-2.0. Status: decision-complete. Numeric gates were measured on a throwaway prototype of the locked scene on 2026-11-11. Versions and licence files were checked on the same date (PyPI, npm, Docker Hub, rosdistro, and upstream LICENSE files). See "Verification record".

## 1. Goal

This is a public portfolio demo of a **depth-to-occupancy pipeline for simulated cameras**. An analytic pinhole renderer casts rays against a known scene (a horizontal ground plane and two axis-aligned boxes) and writes a camera-Z depth image. An original implementation then back-projects valid pixels, applies a height-band filter that removes the ground at z = 0, and updates a 2D log-odds occupancy grid with a two-pass inverse sensor model. An 8-connected A* planner, with unknown and occupied cells blocked and with corner cutting forbidden, proves that the grid is planable around the visible obstacle. A ROS 2 Jazzy node performs the same conversion on a live graph, and a GitHub Pages viewer runs a TypeScript port of the same math.

The methods are well known. This repository is an original implementation **inspired by** pinhole back-projection, ray casting, log-odds occupancy updates, ground-plane removal by a height gate, and A*. It does not invent those methods, and it does not copy or translate third-party source.

The project is **simulation only / synthetic depth only**. It makes no claim about real cameras, real robots, calibrated hardware, or production use.

Skills shown: Python, NumPy, ROS 2, Nav2 interfaces, occupancy grids, simulated depth cameras, TypeScript. The camera model follows the OpenCV pinhole convention (pixel centre at (0, 0), camera matrix K). The repository does not depend on the OpenCV library; 16-bit PNG I/O uses Pillow, because official opencv-python wheels ship LGPLv2.1 FFmpeg.

It differs from the sibling applycoding repositories (checked with `gh repo list applycoding` on 2026-11-11; there is no existing `applycoding/depth-occupancy-nav`):

| Repo | What it is | How this repo differs |
| --- | --- | --- |
| `ros2-nav2-slam-sim` | Gazebo Classic, slam_toolbox, Nav2 waypoint mission | No Gazebo, no SLAM, no lidar, no waypoint FSM. The artifact is a grid built from synthetic depth. |
| `nav2-coverage-planner-compare` | Planner bake-off on already-made Nav2-style costmaps | The artifact here is depth-to-grid. A* is only a planability proof, not a planner comparison. |
| `nav2-behavior-trees` | BehaviorTree.CPP mission executive | Different problem. |
| `lidar-shape-classifier-ros2` | LiDAR cluster shape classification | LiDAR clusters, not depth-to-costmap. |
| `ros2-vision-tracking-demo` | YOLO detections with a Kalman and IoU tracker | Object tracking, not occupancy. |
| `edge-vision-detector`, `edge-yolo-tensorrt` | Learned detectors | Not a depth occupancy grid. |

Do not depend on, submodule, or copy any of those repositories.

Git author and committer for every commit: **Arpan Bom <applycoding@gmail.com>**. No co-author trailers, and no assistant or tool attribution in commits, code, comments, the README, or the docs.

## 2. Scope

**In v1 (CI-gated):**

- `depth_occupancy_nav`: a ROS-free Python package with the renderer, back-projection, height filter, two-pass log-odds grid, A* planner, noise model, and Pillow 16-bit PNG helpers.
- pytest gates for every numeric criterion in section 9, including mutants.
- ROS 2 Jazzy package `depth_occupancy_nav_ros`: a node that subscribes to `sensor_msgs/Image` (32FC1 depth, metres) and `sensor_msgs/CameraInfo` and publishes `nav_msgs/OccupancyGrid`, with a real launch test in a digest-pinned official ROS container.
- A Nav2 planner proof in that same ROS job: official `nav2_planner` and `nav2_navfn_planner` (apt) consume the published grid. If that test is green, the README says that CI ran Navfn on the published map. If a pin or a genuine failure prevents it, keep the core A* gate, do not weaken it, and the README must say that CI did not start Nav2.
- Vite + TypeScript + Canvas viewer at base `/depth-occupancy-nav/`, with Vitest goldens and a Playwright test that is a real gate. Playwright writes `docs/demo.png`. Commit that screenshot once from a local run; CI uploads a screenshot and must not commit it.

**Manual only (documented, not gated):** a launch file that runs the same node against a user-supplied bag or a local simulator.

**Out of scope:**

- Real cameras, real robots, calibrated physical intrinsics, distortion, rolling shutter.
- RANSAC or non-horizontal ground planes; IMU-fused poses; multi-sensor fusion.
- 3D volumetric maps. OctoMap is an idea reference only, not a dependency.
- Learned depth, stereo, NeRF, Gaussian splats, neural occupancy.
- Gazebo or other simulators in CI.
- Full Nav2 bringup, AMCL, slam_toolbox, voxel-layer source, or costmap plugins copied from Nav2.
- Copying `depth_image_proc` or `nav2_costmap_2d`.
- GPU, CUDA, ROS 1, or Humble as the CI distro.
- Publishing to apt or ROS Index.
- A WASM build of the Python core (the web demo is a TypeScript port).

## 3. Pinned stack (verified 2026-11-11)

| Item | Pin | Licence (from the project's LICENSE or package.xml) |
| --- | --- | --- |
| Python (core CI) | 3.12 on `ubuntu-24.04` via `actions/setup-python` | PSF |
| NumPy | 2.5.4 | BSD-3-Clause (`LICENSE.txt` on tag `v2.5.4`; the copyright line there still says 2005-2025) |
| Pillow | 13.0.0 | MIT-CMU ([LICENSE](https://raw.githubusercontent.com/python-pillow/Pillow/13.0.0/LICENSE)). Requires Python >= 3.11, so it is fine on the 3.12 core and Jazzy interpreters. Used only for 16-bit PNG encode and decode and a colourised depth preview. Official `opencv-python` wheels are **not** used: they ship LGPLv2.1 FFmpeg, which this repository's licence policy does not allow to be linked. |
| pytest | 9.2.0 | MIT (`LICENSE` on tag 9.2.0) |
| ruff | 0.17.4 | MIT (`LICENSE` on tag 0.17.4) |
| ROS 2 | Jazzy. Official image `ros:jazzy-ros-base` / `ros:jazzy-ros-base-noble`, index digest `sha256:8eed0a4669bbf43ee331878a4c39bd8ebddea8e3312a58b4fae8edb14526b617`, linux/amd64 manifest `sha256:c26c86a28e1addf9d10a81232869791974a3f7907943d5634742b58b2f26e1a3` (registry-1.docker.io, 2026-11-11) | n/a |
| navigation2 | 1.3.14-1 (rosdistro, 2026-11-11) | Mixed. Use only the Apache-2.0 and BSD-3-Clause packages listed in REFERENCES.md. `nav2_navfn_planner` package.xml: Apache-2.0 and BSD-3-Clause. `nav2_planner`: Apache-2.0. `nav2_costmap_2d`: BSD-3-Clause and Apache-2.0. `nav2_amcl` is LGPL-2.1-or-later and is **not** used. |
| Node.js | 26.13.0 LTS Lithium (2026-10-28), npm from that release, committed `package-lock.json` | MIT |
| TypeScript | 7.0.2 | Apache-2.0 |
| Vite | 8.3.8 | MIT |
| Vitest | 5.1.0 | MIT |
| @playwright/test | 1.65.0 (install Chromium with `npx playwright install --with-deps chromium`) | Apache-2.0 |
| @types/node | 26.6.6 | MIT |

**Why Jazzy, not Humble.** The core pin is NumPy 2.5.4, which requires Python >= 3.12. Humble's official container Python is 3.10. Jazzy on Ubuntu Noble is a supported LTS (supported until May 2029) with Python 3.12, matching the core CI interpreter. Lyrical, released 2026-05-22, is a newer LTS (until May 2031) but ships Python 3.14 in the official image; this repo stays on Jazzy to keep one Python 3.12 pin across core CI and the ROS job. State this in the README.

Hash-pin Python requirements (`pip-compile` or a hashed `requirements.txt`). npm uses `package-lock.json`. Record every Actions version in `.github/workflow-pins.md` with the full SHA and a version comment.

GitHub Actions (the tag object is a commit; SHAs verified 2026-11-11):

| Action | Version | SHA |
| --- | --- | --- |
| `actions/checkout` | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| `actions/setup-node` | v7.1.0 | `949feb2413d6458794dcd2491c4babbbce0c15c1` |
| `actions/setup-python` | v7.1.0 | `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` |
| `actions/upload-artifact` | v7.0.2 | `cf430e030ddbb5b0abf93d22962f4752f3646cd9` |
| `actions/download-artifact` | v8.0.2 | `9000827ccba6bdab643e8b6fd33ac0654aef8333` |
| `actions/configure-pages` | v6.0.0 | `45bfe0192ca1faeb007ade9deae92b16b8254a0d` |
| `actions/upload-pages-artifact` | v5.0.0 | `fc324d3547104276b827a68afc52ff2a11cc49c9` |
| `actions/deploy-pages` | v5.0.1 | `368f82528645a54fb793d4d04e342629a3f51346` |

The core runner is `ubuntu-24.04`. Never `ubuntu-latest`. The job prints the Python, NumPy, and Pillow versions.

## 4. Architecture

```
 scene + camera  ->  analytic ray caster  ->  depth image (camera-Z, metres)
                                              |                |
                                              v                v
                                      height-band filter   OpenCV 16UC1 PNG
                                              |
                                              v
                            two-pass log-odds grid  ->  OccupancyGrid-shaped array
                                              |
                                              +--> 8-connected A* (core proof)
                                              |
                         ROS node (Jazzy) publishes nav_msgs/OccupancyGrid
                                              |
                                              +--> launch test A (grid gates)
                                              +--> launch test B (Navfn on /map)
                                              |
                         TypeScript port of the same math -> Pages viewer
```

- **Core is ROS-free.** `depth_occupancy_nav` must not import `rclpy`. Core pytest runs with no ROS, no Node, and no Docker.
- **The ROS package imports the core.** It must not reimplement back-projection, the height filter, log-odds, or A*.
- **The web demo is a TypeScript port of the same locked constants and algorithms**, checked against compact Python goldens. The README must not describe two inventions.
- **Image I/O is Pillow, not OpenCV.** Core math is authored NumPy and Python. A 16-bit unsigned PNG in millimetres (`round(z * 1000)` with Python half-even rounding, 0 invalid) and a colourised depth preview are written and read with Pillow. The camera model follows the OpenCV pinhole convention, but the OpenCV library is not a dependency.

## 5. Locked algorithm

### 5.1 Frames and camera

- Map frame: z up, x forward, y left (REP-103 style). Ground is the plane z = 0.
- Camera optical frame: x right, y down, z forward.
- Camera position in map: `t = (0, 0, 0.80)` m.
- Rotation `map_R_optical` (columns are the optical basis expressed in the map):

```
[[ 0,  0,  1],
 [-1,  0,  0],
 [ 0, -1,  0]]
```

  so map x = optical z, map y = -optical x, map z = -optical y. `p_map = map_R_optical @ p_optical + t`.

- Image: width W = 80, height H = 60.
- Horizontal FOV = 60 degrees. `fx = fy = (W/2) / tan(FOV/2) = 40 / tan(pi/6) = 69.2820323027551`.
- Principal point `(cx, cy) = (39.5, 29.5)`. The optical axis is at the image centre, between four pixels.
- Pixel convention (OpenCV `projectPoints` style): the centre of the top-left pixel is `(0, 0)`. The ray for integer pixel `(u, v)` uses those integers with no 0.5 offset.
- Depth is **camera-Z in metres** (the Z of the hit in the optical frame), not the Euclidean range along the ray. Invalid or out-of-range pixels are `0.0`. Valid depths lie in `(0, max_range]` with `max_range = 10.0` m.
- Back-projection of a valid pixel `(u, v)` with depth Z: `X = (u - cx) / fx * Z`, `Y = (v - cy) / fy * Z`, `p_optical = (X, Y, Z)`, then `p_map` as above.

### 5.2 Scene (analytic, not a mesh file)

- Front box AABB `(xmin, xmax, ymin, ymax, zmin, zmax) = (2.75, 3.15, -0.45, 0.45, 0.0, 1.20)` m. The visible face is the plane x = 2.75, which is the centre of grid cell ix = 37.
- Side box = `(4.05, 4.45, 1.25, 2.15, 0.0, 1.00)` m.
- Ground: infinite plane z = 0.
- Renderer: for each pixel, shoot the pinhole ray, intersect the two AABBs (slabs method) and the ground plane, keep the closest hit with t > 0 and t <= max_range, and convert to camera-Z.
- This is analytic scene ray casting, not a rasteriser and not a game engine.

### 5.3 Noise

- Default tests are noise-free.
- When enabled, the locked draw schedule (reproduces the prototype RMSE) is: `rng = numpy.random.default_rng(seed)` (PCG64); `n1 = rng.standard_normal(depth.shape)` and `n2 = rng.standard_normal(depth.shape)`, each a float64 array of shape `(H, W)` = `(60, 80)`, drawn for every pixel including invalid ones, in that call order; `mask = depth > 0`; `noisy = np.where(mask, depth * (1.0 + sigma_rel * n1) + sigma_abs * n2, 0.0)` with `sigma_rel = 0.01` and `sigma_abs = 0.01` m, so originally invalid pixels stay 0 and do not become positive from the additive term; then `noisy = np.where((noisy > 0.0) & (noisy <= max_range), noisy, 0.0)`. RMSE is computed only on pixels that were originally valid and remain valid.
- No dropout in v1 (`p_drop = 0`).
- Seed 1 is the numeric RMSE case. Do not treat a single-seed RMSE as a bit-identical golden across future NumPy versions. Use a tight check against the prototype value, plus an in-process determinism check (same seed, two calls, bit-identical arrays). If a future NumPy PCG change breaks the tight value, record it in `DEVIATIONS.md` and keep the bound in criterion 9.

### 5.4 Height filter

- Keep a point iff `z_min <= z_map <= z_max`, with `z_min = 0.15` m and `z_max = 1.50` m. The bounds are inclusive: a point at exactly 0.15 or 1.50 is kept.
- This removes the horizontal ground at z = 0. It is a height gate, **not a fitted plane and not RANSAC**. The README must say so.
- Invalid pixels (depth 0) do not update the grid and do not clear to max range. The README must say so.

### 5.5 Occupancy (two-pass, occupied wins in-frame)

- Grid: resolution 0.10 m, origin `(origin_x, origin_y) = (-1.0, -3.0)` m, width 80 cells (x from -1 to 7 m), height 60 cells (y from -3 to 3 m). Cell `(ix, iy)` covers `[origin + i * res, origin + (i + 1) * res)`. `world_to_cell` uses `floor`. The camera `(0, 0)` lies on a boundary and maps to `(ix, iy) = (10, 30)`.
- Each cell stores log-odds `l`, prior `l0 = 0` (p = 0.5).
- `l_occ = ln(0.70/0.30) = 0.8472978603872037`.
- `l_free = ln(0.35/0.65) = -0.6190392084062235`.
- Clamp to `[l_min, l_max] = [-2.0, 3.5]` after every increment.
- Inverse: `p = 1 / (1 + exp(-l))` with the usual numerically stable form.
- OccupancyGrid values: never updated => -1; p >= 0.65 => 100; p <= 0.35 => 0; else `round(p * 100)`.
- Ray traversal: Amanatides-Woo 2D grid walk from the camera `(x, y)` to the endpoint `(x, y)`, inclusive of start and end when they lie in the grid. A unit test must require the exact cell list for `(0, 0) -> (2.75, 0)`: `(10, 30), (11, 30), ..., (37, 30)` (28 cells).
- Traversal details (locked): when the parametric crossing times `t_max_x` and `t_max_y` are equal, step in x first. A zero-length ray (start equals end, and the point is inside the grid) yields the single start cell. If the true endpoint lies outside the finite grid, the walk includes in-grid cells until the ray leaves and does **not** treat the last in-grid cell as an occupied endpoint; an occupied mark is applied only when the height-kept endpoint itself maps to a cell inside the grid. Add tiny literal cell-list tests for a zero-length ray, an axis-parallel negative-x ray, a diagonal that crosses x and y at the same time (tie: x first), and an endpoint outside the grid on the +x side.
- Renderer rays: the optical direction is the unnormalized vector `((u-cx)/fx, (v-cy)/fy, 1)`, normalised to unit length in the map frame for intersection. The intersection parameter `t` is Euclidean metres along that unit map direction. A hit is rejected if `t > max_range` or if the resulting camera-Z is not in `(0, max_range]`.
- **Two-pass per frame** (locked). Pass A: apply `l_free` along each ray; for height-kept (obstacle) rays, exclude the end cell; for filtered (ground or ceiling) rays, include the end cell as free. Pass B: apply `l_occ` at every height-kept endpoint. This ordering means free updates do not run after occupied updates in the same frame. It does **not** guarantee that every endpoint is classified 100: a cell already saturated at `l_min = -2.0` receives only `l_occ = 0.8472978603872037` and stays below the 0.65 occupied threshold. On the locked scene the visible faces receive many endpoints, and the prototype measured 22 cells at 100 and mid = 0. A conflicting-evidence unit test on a tiny hand-built grid must document that one occupied increment after a free-saturated cell does not reach 100. A one-pass update that later frees a cell already marked occupied can clear a visible surface; see criterion 12 for the locked mutant schedules and measured results (zero occupied cells, value 0 at `(37, 30)`).
- A single depth frame marks the **visible surface, not the solid volume**. Cells behind a surface stay unknown unless some other ray observes them. The README must say this.
- Incremental updates across frames are supported by the same log-odds API. v1 CI gates use a single noise-free frame plus one noisy-frame case.

### 5.6 Planner (core, no ROS)

- 8-connected A*. Only occupancy value 0 is traversable. Unknown and any non-zero value are blocked.
- Corner cutting is forbidden: a diagonal step requires both orthogonal adjacent cells to be free.
- No inflation in the default proof. A second inflated grid uses robot radius 0.15 m, cell radius `r = ceil(0.15 / 0.10) = 2`, and marks a cell occupied if `dx^2 + dy^2 <= r^2` from an occupied cell. The inflated path must not step on a cell that was 100 in the uninflated grid.
- Start: `(0.50, 0.00)` m = cell `(15, 30)`, free.
- Open goal: `(1.50, 0.00)` m = cell `(25, 30)`. Path: the 11 cells `(15, 30)` through `(25, 30)`, cost 10.0 (10 orthogonal steps).
- Around goal: `(5.50, -1.50)` m = cell `(65, 15)`, observed free via ground rays beside the front box. Path length 51 cells (50 steps), cost `35 + 15*sqrt(2)` (15 diagonal and 35 orthogonal). The path must not enter the front-box AABB in x,y. This is the "grid is planable around the obstacle" proof.
- Shadow goal: `(5.50, 0.00)` m = cell `(65, 30)`, unknown (occluded behind the front box). A* must return no path.
- Inside goal: `(2.95, 0.00)` m = cell `(39, 30)`, unknown (volume behind the visible face). A* must return no path.
- Height-filter mutant: treat every valid depth as an occupied endpoint. The floor becomes a wall. Prototype: 117 occupied cells, start and the open goal remain free, the around path is None, the open path still exists.

## 6. ROS 2 package

- Image pin: `docker run --rm --init --platform linux/amd64 -v "$GITHUB_WORKSPACE:/ws" -w /ws ros:jazzy-ros-base@sha256:8eed0a4669bbf43ee331878a4c39bd8ebddea8e3312a58b4fae8edb14526b617`. Also record the linux/amd64 manifest digest in `workflow-pins.md`. Never a floating tag. Never a GHA `container:` job. Never `ubuntu-latest`. Host runner: `ubuntu-24.04`.
- The ROS job records `dpkg-query -W` on `ros-jazzy-nav2-navfn-planner` and `ros-jazzy-nav2-planner` and asserts that the upstream version starts with `1.3.14`. If the assertion fails, the job fails. No silent fallback that still exits 0.
- The ROS job is a pinned base image plus a version-checked apt install, not a fully frozen apt universe. It records a full `dpkg-query` log as an artifact, and it asserts that `ros-jazzy-nav2-navfn-planner` and `ros-jazzy-nav2-planner` are exactly version `1.3.14-1` (parse the Debian version, not a `startswith("1.3.14")` prefix). Transitive packages may drift; a change in an asserted package fails the job until a recorded pin bump.
- Node contract (v1 accepts only the locked undistorted synthetic camera). Subscribe to depth `Image` and `CameraInfo`. Accept a frame only when: encoding is `32FC1`; `is_bigendian = 0`; `step == width * 4`; `Image.header.frame_id` equals `CameraInfo.header.frame_id`; `CameraInfo` width and height match the image; distortion `D` is empty or all zeros; `binning_x` and `binning_y` are 0 or 1; ROI is full-frame (unrectified); intrinsics come from `K[0], K[4], K[2], K[5]` (`fx, fy, cx, cy`), not from `P`; each of those four values matches the locked camera within `1e-9`. Reject (no grid mutation, no occupancy publish) if CameraInfo is missing or fails any of those checks, or if the payload cannot be decoded as a tightly packed little-endian float32 buffer of shape `(H, W)`. NaN, infinity, and non-positive or above-`max_range` depths are treated as invalid (0) and do not update the grid. The node uses **pose parameters** equal to the locked camera pose for back-projection; it does not look up TF for the projection in v1. Launch still publishes static TF for Nav2 and visualisation: `map` -> `camera_optical_frame` at translation `(0, 0, 0.80)` and quaternion `(x, y, z, w) = (0.5, -0.5, 0.5, -0.5)`, which is the locked `map_R_optical`, and `map` -> `base_link` at the identity, with `base_link` at the origin of `map`. OccupancyGrid: `frame_id = map`, `resolution = 0.10`, `width = 80`, `height = 60`, `origin.position = (-1.0, -3.0, 0)`, identity orientation, row-major `data[iy * width + ix]` matching core `grid[iy, ix]`.
- **Launch test A (required):** `launch_testing` or `launch_pytest` starts the node and the static TF, publishes the locked-scene noise-free depth and a valid `CameraInfo`, waits for `OccupancyGrid`, and asserts the occupancy counts and cell probes from criterion 5. A second case publishes a mismatched `CameraInfo` (wrong `fx`) and asserts that the grid is not mutated and no new OccupancyGrid with the bad frame is published. This is a real ROS graph test, not an offline replay that never constructs the node.
- **Launch test B (Nav2 planner proof, required CI gate).** Start only `planner_server` with `NavfnPlanner` and a global costmap that loads **only** the StaticLayer plugin (no obstacle layer, no voxel layer, no lidar). Do not start Gazebo, `nav2_amcl`, or full `nav2_bringup`. Locked settings: `use_sim_time: false` (system clock); map topic QoS reliable and transient-local; `robot_base_frame: base_link`; footprint a point robot; `inflation_radius: 0.0`; Navfn `allow_unknown: false` (unknown is blocked, as in the core planner); Navfn `default_tolerance: 0.05` m; `ComputePathToPose.use_start: true` so the supplied start is used. Lifecycle: activate the depth node, wait until this map has been received and the costmap is populated (non-zero size, origin matching the locked grid), then configure and activate `planner_server`, then send the goal. Start `(0.50, 0.00)`, goal `(5.50, -1.50)`. Assert: action status succeeded, result error code is the success code, all path poses are finite and in the map bounds, the first pose is within 0.15 m of the start, the last pose is within 0.15 m of the goal, and every segment, sampled at 0.05 m, snaps only to published cells with value 0 (not 100, not -1, not mid). This is a Navfn proof on the published map, not a claim that Navfn returns the same path as core A*. `nav2_costmap_2d` is a required runtime dependency and must appear in NOTICE. Launch test B is a required green job. Do not skip it, do not `continue-on-error`, and do not make CI green by writing `DEVIATIONS.md`. If a first integration attempt proves a pin unworkable, amend this plan in a reviewed deviation **before merge**; once B is in the tree, a failure fails CI.
- A documented manual launch file may show the same node against a bag or a simulator, under the same acceptance contract (undistorted 32FC1 depth and a matching CameraInfo). It is not a CI gate.

## 7. Web demo

- Vite + TypeScript + Canvas 2D, base `/depth-occupancy-nav/`, `import.meta.env.BASE_URL` for assets.
- UI must work: colourised depth image, top-down projected points, occupancy grid, planned path; controls for noise sigma, `z_min`, `z_max`, and a goal click or preset buttons (open / around / shadow). Changing a control recomputes. The document title or a visible header contains "simulation only" and "synthetic depth".
- Playwright (Chromium, with OS deps) is a real gate on the **built** site: honesty phrases are present; the depth canvas is not a flat field (pixel variance above a fixture threshold on the depth canvas pixels); a DOM metric `data-occupied` (or a visible labelled count) equals 22 on the default scene, and that metric is computed from the grid array, not from canvas pixel counting alone; the occupancy canvas is not a flat field; selecting the around goal draws a path and a DOM path-length metric equals 51, and selecting the shadow goal reports no path; moving the noise or `z_min` slider changes `data-occupied` from 22 and the occupancy canvas updates. Write `docs/demo.png` after the around-path state. Do not assert only that the page title equals a string the test itself just set.
- Vitest checks the TypeScript math against a compact JSON golden produced by the Python core. The golden includes the 28-cell walk, the optical-axis and four-pixel back-projections, the exact 22 occupied cells and the cell probes (not counts alone), the open-path cell list, and the around-path cell count, endpoints and cost. Generate or commit numbers, not a huge image. The TypeScript occupancy conversion must use Python-style half-even rounding (`round` half to even) when mid values appear, because JavaScript `Math.round` differs at ties. On the noise-free locked scene mid = 0, so the default fixture does not depend on a tie.

## 8. File layout

```
LICENSE
NOTICE
README.md
PLAN.md
TASKS.md
REFERENCES.md
DEVIATIONS.md          # only if a pin or test forces a change
pyproject.toml
requirements.txt       # hashed
src/depth_occupancy_nav/
  __init__.py
  camera.py
  scene.py
  render.py
  backproject.py
  height_filter.py
  grid.py
  planner.py
  noise.py
  io_png.py            # Pillow 16-bit PNG
tests/
fixtures/              # compact JSON scene and goldens, not large images
ros2/depth_occupancy_nav_ros/
  package.xml
  setup.py or setup.cfg
  resource/
  depth_occupancy_nav_ros/
    __init__.py
    node.py
  launch/
  test/
web/
  package.json
  package-lock.json
  tsconfig.json
  vite.config.ts
  index.html
  src/
docs/demo.png
.github/workflows/ci.yml          # orchestrator: jobs core, ros, web, pages
.github/workflow-pins.md
```

SPDX headers on authored source: `SPDX-License-Identifier: Apache-2.0`.

NOTICE must include: copyright Arpan Bom 2026; every direct runtime dependency (NumPy, Pillow); every direct dev tool (pytest, ruff, TypeScript, Vite, Vitest, Playwright, `@types/node`, Node); ROS and Nav2 apt packages actually used, including `nav2_costmap_2d`; idea references or a pointer to REFERENCES.md. No over-credits. No under-credits. Do not list OpenCV as a dependency.

Do not commit large generated artifacts (depth images, occupancy dumps, `node_modules`). Generate them at test or build time from the locked scene. `docs/demo.png` is the one allowed committed screenshot, produced once locally.

## 9. Success criteria

The implementation tests must assert these values (exact where given as exact; bounded where given as a range). Never weaken a threshold to make CI green.

**1. Licence.** `LICENSE` is byte-identical to the official Apache-2.0 text. `sha256sum LICENSE` equals `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.

**2. Optical-axis geometry and back-projection.** Virtual sample at `(cx, cy) = (39.5, 29.5)`, noise-free: direction in optical is `(0, 0, 1)`, in map is `(1, 0, 0)`; hit the front box at world `(2.75, 0, 0.80)` m; camera-Z = 2.75 m; back-projection recovers that world point with error < 1e-12. The four neighbour pixels `(39, 29)`, `(40, 29)`, `(39, 30)`, `(40, 30)` each have camera-Z = 2.75 within 1e-12, hit the front face, have map x = 2.75 within 1e-12, and back-project with error < 1e-12. Prototype and analytic world points:

- `(39, 29)`: `(2.75,  0.0198464155033934, 0.8198464155033934)`
- `(40, 29)`: `(2.75, -0.0198464155033934, 0.8198464155033934)`
- `(39, 30)`: `(2.75,  0.0198464155033934, 0.7801535844966067)`
- `(40, 30)`: `(2.75, -0.0198464155033934, 0.7801535844966067)`

These literals are the analytic values from the locked `fx` and `Z = 2.75`. Tests may use them as expected numbers with tolerance `1e-12`.

Also assert `fx = fy = 69.2820323027551`, `l_occ = 0.8472978603872037`, `l_free = -0.6190392084062235`, `p(l_occ) = 0.7` and `p(l_free) = 0.35` within 1e-15.

**3. Renderer counts.** Noise-free locked scene: 2434 valid depth pixels out of 4800. Hit kinds: `front_box` 660, `ground` 1471, `side_box` 303 (sum 2434). After the height filter: kept 823, filtered 1611, of which `front_pts` 572 and `side_pts` 251 (sum 823).

**4. Ray walk.** `(0, 0) -> (2.75, 0)` equals the 28 cells `(10, 30), (11, 30), ..., (37, 30)`.

**5. Occupancy, noise-free, one frame, two-pass.** occupied (100) = 22, free (0) = 1698, unknown (-1) = 3080, mid (1..99) = 0, and 22 + 1698 + 3080 + 0 = 4800. The 10 front occupied cells, as `(ix, iy, centre x, centre y)`, are exactly:

`(37, 25, 2.75, -0.45)`, `(37, 26, 2.75, -0.35)`, `(37, 27, 2.75, -0.25)`, `(37, 28, 2.75, -0.15)`, `(37, 29, 2.75, -0.05)`, `(37, 30, 2.75, 0.05)`, `(37, 31, 2.75, 0.15)`, `(37, 32, 2.75, 0.25)`, `(37, 33, 2.75, 0.35)`, `(37, 34, 2.75, 0.45)`.

The 12 side occupied cells are exactly:

`(50, 42, 4.05, 1.25)`, `(52, 42, 4.25, 1.25)`, `(54, 42, 4.45, 1.25)`, `(50, 43, 4.05, 1.35)`, `(50, 44, 4.05, 1.45)`, `(50, 45, 4.05, 1.55)`, `(50, 46, 4.05, 1.65)`, `(50, 47, 4.05, 1.75)`, `(50, 48, 4.05, 1.85)`, `(50, 49, 4.05, 1.95)`, `(50, 50, 4.05, 2.05)`, `(50, 51, 4.05, 2.15)`.

No other occupied cells. Cell probes:

| world (x, y) | cell (ix, iy) | value |
| --- | --- | --- |
| (2.65, 0) | (36, 30) | 0 |
| (2.75, 0) | (37, 30) | 100 |
| (2.95, 0) | (39, 30) | -1 |
| (3.50, 0) | (45, 30) | -1 |
| (0.50, 0) | (15, 30) | 0 |
| (1.50, 0) | (25, 30) | 0 |
| (5.50, -1.50) | (65, 15) | 0 |
| (4.05, 1.70) | (50, 47) | 100 |

Face cell `(37, 30)` log-odds is clamped at `l_max = 3.5`.

**6. Height filter unit.** 1611 points removed on the locked scene. A point with z = 0 is dropped. A point with z = 0.80 is kept. A point with z = 1.60 is dropped. Inclusive bounds: z = 0.15 and z = 1.50 are kept; z just below 0.15 and just above 1.50 are dropped.

**7. Planner, noise-free.** Open path: 11 cells, cost 10.0, cells `(15, 30)` through `(25, 30)` inclusive, does not enter the front-box AABB. Around path: 51 cells, first `(15, 30)`, last `(65, 15)`, cost `35 + 15*sqrt(2)` with `abs(cost - (35 + 15*math.sqrt(2))) < 1e-12`, does not enter the front-box AABB. Shadow and inside goals: no path.

**8. Inflation.** Radius 0.15 m: occupied cells become 130. A path to the around goal still exists, length 51, same cost `35 + 15*sqrt(2)`, does not step on a cell that was 100 in the uninflated grid, and every path cell is free (value 0) in the inflated grid. A tiny independent fixture with a one-cell-wide corridor that inflation closes must return no path. A tiny fixture must also fail a path that would cut a corner, succeed the same query when the orthogonal cells are free, treat start equals goal as a one-cell path of cost 0, and reject an out-of-bounds or occupied start.

**9. Noise, seed 1, using the locked draw schedule in section 5.3.** All 2434 originally valid pixels remain valid (dropped 0). RMSE = 0.0364728080413652; assert `abs(rmse - 0.0364728080413652) < 1e-9`. If a future NumPy PCG change breaks that tight value, record it in `DEVIATIONS.md` and keep the bound `0.033 <= rmse <= 0.040` together with the theoretical RMSE 0.0363097701532491. Noisy occupancy: occupied 41, free 1684, unknown 3062, mid 13 (13 = 4800 - 41 - 1684 - 3062, from the measured three counts and the fixed grid size). The around path still exists, length 51, cost `35 + 15*sqrt(2)`. Two calls with seed 1 in one process produce bit-identical noisy images. Two noise-free renders are bit-identical, and two occupancy arrays from that depth are equal.

**10. Height-filter mutant.** **Measured gates** (see **PLAN Amendment 1 (2026-11-11)**): occupied **78**, free **1247**, unknown **3080**, mid **395** (78 + 1247 + 3080 + 395 = 4800). The original throwaway prototype recorded **117 / 1208 / 3080 / 395**; the occupied and free counts could not be reproduced with the locked Amanatides-Woo walk. Around path is None. Open path still exists. Start and the open goal remain free. Ground-only cells `(28, 30)`, `(29, 30)`, `(30, 30)` are 100.

**11. Pillow PNG round trip.** Encode the locked-scene depth as a 16-bit unsigned PNG in millimetres (`round(z * 1000)` with half-even rounding, 0 invalid) and decode it. Every originally valid pixel recovers camera-Z within 0.5 mm. Invalid pixels remain 0.

**12. One-pass mutants (both required).** Rays are collected in the same order as the renderer: row `v` from 0 to H-1, column `u` from 0 to W-1, skipping invalid depths. Mutant M1 applies, for each ray in that order, the free mid-cells and then the occupied endpoint immediately, so a later ray can free an earlier endpoint; measured occupancy is occupied 0, free 1709, unknown 3080, mid 11, and `(37, 30) == 0`. Mutant M2 is the product two-pass followed by an extra free pass over the same mid-cells; measured occupancy is occupied 0, free 1714, unknown 3080, mid 6, and `(37, 30) == 0`. The product two-pass implementation must still have value 100 at `(37, 30)` and 22 occupied cells. These mutants show sensitivity to those two schedules; they are not a theorem about every possible one-pass implementation.

**13. Core CI.** pytest and ruff are clean on `ubuntu-24.04` with Python 3.12. A `grep -P` hygiene job fails if GNU `grep -P` is unavailable (probe it first) and fails if any tracked authored file contains U+2014, U+2013, or U+2212. A second scan uses a committed pattern list that lives only in the workflow file and is not repeated here, covering development-tool names, assistant names, a generated-by phrase, co-author trailers, and local host paths. The workflow file is excluded from the tool-word scan so that the list can exist; `package-lock.json`, `*.png`, and `LICENSE` are excluded from both scans. Every other tracked file, including this plan, must stay clean. The job includes a fixture that must fail the scanner, and it fails if the scan file list is empty. An authorship job fetches full history, and on `pull_request` events it inspects `github.event.pull_request.head.sha` (the branch head, not GitHub's synthetic merge commit); on `push` it inspects the pushed commits. Every such commit has author and committer `Arpan Bom <applycoding@gmail.com>` and no co-author trailer. A pin-check step requires every workflow `uses:` value to be either `owner/repo@` plus a 40-character lowercase hex SHA that matches `workflow-pins.md`, or a local `./` action, or a digest-pinned container. Refs such as `@vN`, `@main`, or a short SHA fail. No `continue-on-error` on required jobs. Never `ubuntu-latest`.

**14. ROS launch test A.** The published `OccupancyGrid` matches criterion 5: counts 22 / 1698 / 3080 / 0 and the cell probes, including `(37, 30) == 100` and `(65, 15) == 0`. The test starts the node on a ROS graph. A mismatched CameraInfo case does not mutate the grid.

**15. ROS launch test B.** Required. With the locked Navfn and static-only costmap settings in section 6, the action succeeds, the result error code is success, the path is finite and in bounds, the first pose is within 0.15 m of `(0.50, 0.00)`, the last pose is within 0.15 m of `(5.50, -1.50)`, and every 0.05 m sample along each segment snaps only to published cells of value 0. The core A* gates still pass independently. A failure of B fails CI.

**16. Web.** TypeScript goldens match the Python 28-cell walk, optical-axis and four-pixel back-projections, the exact 22 occupied cells and probes, the open-path cell list, and the around-path length, endpoints and cost. `tsc --noEmit` is clean. Playwright meets the checks in section 7, including `data-occupied == 22`, around path length 51, and shadow goal reports no path, and writes `docs/demo.png`.

**17. Pages.** `pages.yml` deploys the tested `web/dist` from `main` only after the required checks of that SHA have completed green. The live demo document title or header contains "simulation only" and "synthetic depth". Pages source is GitHub Actions (`build_type: workflow`). Base `/depth-occupancy-nav/`.

**18. README.** Says simulation only / synthetic depth; contrasts the sibling repos; maps criteria to tests; does not claim real-camera or real-robot validation or that the project invented the methods, while still including the required simulation-only disclaimers; states that a single frame marks the visible surface, not the solid volume; states that the height filter is a height gate, not a fitted plane; states that invalid pixels do not clear to max range; states that CI ran Nav2 Navfn on the published map (criterion 15). Numbers in the README match these criteria or a named CI log. NOTICE is finished at the merge commit.

**19. NOTICE and licence hygiene.** NOTICE is complete as specified in section 8. No GPL or LGPL code is copied, linked, or translated. `nav2_amcl` is not a dependency. No vendored Nav2, OctoMap, or `depth_image_proc` source. No `third_party/`, `vendor/`, or `external/` directories.

**20. Repository size.** No huge committed generated artifacts. Fixtures are compact JSON. `docs/demo.png` is the only committed screenshot.

## 10. CI layout

Use **one orchestrating workflow**, `.github/workflows/ci.yml`, with jobs `core`, `ros`, `web`, and `pages` in the same run. Do not use `workflow_run` to chain separate workflows: that event fires when any listed workflow finishes, does not wait for all of them, and its `GITHUB_SHA` is not necessarily the tested head. Optional reusable workflow files may implement `core`, `ros`, and `web`, but `pages` must be a job in the orchestrator with `needs: [core, ros, web]`, and it must deploy the `web` job's `dist` artifact from **this same run**.

- `core`: pytest, ruff, `grep -P` hygiene, authorship and pin checks, on `ubuntu-24.04`.
- `ros`: `docker run` of the pinned Jazzy image; install the declared ROS and Nav2 apt packages; colcon or an equivalent install of `depth_occupancy_nav_ros` plus the core package; launch tests A and B. Upload the apt log. This job is a merge gate, not optional.
- `web`: Node 26.13.0, `npm ci`, `tsc --noEmit`, Vitest, production build, Playwright, upload `demo.png` and `dist`.
- `pages`: runs only on a `main` push, after `core`, `ros` and `web` of this run have succeeded, and deploys that `dist`. A failed or missing prerequisite skips or fails deploy; it must not publish an older artifact.

Every action is pinned by SHA with the version in a comment.

## 11. Verification record

On 2026-11-11 a throwaway prototype of the locked scene measured the renderer counts, the 22 occupied cells, the planner paths and costs, the inflation count 130, the seed-1 RMSE 0.0364728080413652 under the locked draw schedule, the noisy occupancy 41 / 1684 / 3062 / mid 13, the height-filter mutant prototype literals 117 / 1208 / 3080 / mid 395 (superseded for CI by PLAN Amendment 1), the exact 28-cell walk, the optical-axis and four-pixel back-projections, and both one-pass mutant schedules (M1: 0 / 1709 / 3080 / 11; M2: 0 / 1714 / 3080 / 6; value 0 at `(37, 30)`). Versions and licence files were checked the same day against PyPI, npm, Node release index, Docker Hub / registry-1.docker.io, rosdistro, and upstream LICENSE or package.xml files (NumPy, pytest, ruff, Pillow, Nav2 packages, OctoMap idea-only licence, Apache-2.0 text SHA-256). Official opencv-python wheels were rejected because they ship LGPLv2.1 FFmpeg. The OctoMap paper is cited from the official project site and the author PDF `https://www.arminhornung.de/Research/pub/hornung13auro.pdf` (DOI 10.1007/s10514-012-9321-0); an earlier arXiv identifier was checked only by HTTP status and was the wrong paper, and has been dropped.

## PLAN Amendment 1 (2026-11-11)

This amendment records measured pins and layout changes that differ from the 2026-11-11 decision-complete PLAN text above. Merge gates use these values where they conflict with section 9 literals.

### Nav2 apt (criterion 15)

- **Upstream:** Navigation2 **1.3.13** (not the rosdistro-indexed **1.3.14-1** at the pin date).
- **Exact noble Debian versions** (CI `env` and `dpkg-query` equality): `ros-jazzy-nav2-navfn-planner` **1.3.13-1noble.20260921.031752**; `ros-jazzy-nav2-planner` **1.3.13-1noble.20260921.031801**; `ros-jazzy-nav2-costmap-2d` **1.3.13-1noble.20260921.024946**.
- **Evidence:** `apt-get install ...=1.3.14-1` on noble returns `E: Version '1.3.14-1' for 'ros-jazzy-nav2-navfn-planner' was not found` (2026-11-11). See `DEVIATIONS.md`.

### Height-filter mutant (criterion 10)

- **CI counts:** occupied **78**, free **1247**, unknown **3080**, mid **395** (production path with height gate disabled, or equivalent `height_mutant` mode).
- **Prototype literals** 117 / 1208 are not reproduced with the locked walk; mid **395** matches the PLAN prototype.

### Launch test B readiness

- The published map and **global_costmap/costmap** are asserted before goals (80x60, resolution 0.10, origin (-1.0, -3.0), lethal at `(2.75, 0.00)`, unknown at `(2.95, 0.00)`, free at `(5.50, -1.50)`). Negative goals exercise shadow and face cells.
- **`TimerAction` (4 s)** before `planner_server` and the lifecycle manager remains for reliability; see `DEVIATIONS.md`.

### Pages and CI artifacts (criterion 17)

- **`web` job:** artifact `web-dist` uploads only `web/dist` (includes `report.json` from `scripts/write_report.py`). Artifact `demo-screenshot` uploads `docs/demo.png` separately.
- **`pages` job:** downloads `web-dist` to `dist`, verifies `dist/index.html` and `dist/report.json`, and passes `path: dist` to `upload-pages-artifact` (not `dist/dist`).
