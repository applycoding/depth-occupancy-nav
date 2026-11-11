# References

These are ideas and interfaces only, except the dependencies actually imported or installed as declared below. No third-party source is copied or translated. Licences were checked against each project's LICENSE file or package.xml on 2026-11-11.

## Dependencies (imported or installed, not vendored)

| Project | Version | Licence | Use |
| --- | --- | --- | --- |
| [NumPy](https://github.com/numpy/numpy) | 2.5.4 | BSD-3-Clause ([LICENSE.txt](https://raw.githubusercontent.com/numpy/numpy/v2.5.4/LICENSE.txt)) | Arrays, the locked PCG64 generator via `default_rng` |
| [Pillow](https://github.com/python-pillow/Pillow) | 13.0.0 | MIT-CMU ([LICENSE](https://raw.githubusercontent.com/python-pillow/Pillow/13.0.0/LICENSE)) | 16-bit PNG encode and decode, colourised depth preview. Not used for back-projection or occupancy math |
| [pytest](https://github.com/pytest-dev/pytest) | 9.2.0 | MIT ([LICENSE](https://raw.githubusercontent.com/pytest-dev/pytest/9.2.0/LICENSE)) | Core tests |
| [ruff](https://github.com/astral-sh/ruff) | 0.17.4 | MIT ([LICENSE](https://raw.githubusercontent.com/astral-sh/ruff/0.17.4/LICENSE)) | Lint |
| [navigation2](https://github.com/ros-navigation/navigation2) Jazzy (`nav2_planner`, `nav2_navfn_planner`, `nav2_costmap_2d`, and the message or launch packages those nodes require at runtime) | 1.3.14-1 | `nav2_planner` Apache-2.0 ([package.xml](https://raw.githubusercontent.com/ros-navigation/navigation2/jazzy/nav2_planner/package.xml)). `nav2_navfn_planner` Apache-2.0 and BSD-3-Clause ([package.xml](https://raw.githubusercontent.com/ros-navigation/navigation2/jazzy/nav2_navfn_planner/package.xml)). `nav2_costmap_2d` BSD-3-Clause and Apache-2.0 ([package.xml](https://raw.githubusercontent.com/ros-navigation/navigation2/jazzy/nav2_costmap_2d/package.xml)); this package is a required runtime dependency of launch test B, not a hypothetical transitive. The repo-root [LICENSE](https://raw.githubusercontent.com/ros-navigation/navigation2/jazzy/LICENSE) lists mixed licences; use only the Apache-2.0 and BSD-3-Clause packages | Launch test B: official Navfn on the published grid, with a static-only costmap. Not used as a source of copied code |
| ROS 2 Jazzy (`rclpy`, `sensor_msgs`, `nav_msgs`, `tf2_ros`, `launch_testing` or `launch_pytest`) | distro packages in the pinned `ros:jazzy-ros-base` image | The ROS 2 core is Apache-2.0. The job records the exact Debian package versions on every run | Node, messages, launch tests |
| Node 26.13.0, TypeScript 7.0.2, Vite 8.3.8, Vitest 5.1.0, @playwright/test 1.65.0, @types/node 26.6.6 | as pinned in PLAN.md | MIT / Apache-2.0 / MIT / MIT / Apache-2.0 / MIT | Viewer and tests |

If an extra direct package is added during the build (for example `launch_ros` or `nav2_msgs`), list it in NOTICE at the version actually installed. Do not list packages that are not used. Do not list OpenCV or opencv-python.

## Idea sources (read for concepts, not copied)

| Source | Licence or citation | What we take from it |
| --- | --- | --- |
| Thrun, Burgard and Fox, *Probabilistic Robotics*, MIT Press, 2005, Chapter 9 | Book | The standard log-odds inverse sensor model (free along a ray, occupied at the endpoint, prior 0.5) |
| Moravec and Elfes, "High resolution maps from wide angle sonar", IEEE ICRA, 1985 | Paper | Early occupancy-grid mapping as background |
| Hornung, Wurm, Bennewitz, Stachniss and Burgard, "OctoMap: An Efficient Probabilistic 3D Mapping Framework Based on Octrees", *Autonomous Robots*, 2013; author PDF [hornung13auro.pdf](https://www.arminhornung.de/Research/pub/hornung13auro.pdf); DOI 10.1007/s10514-012-9321-0; listed on [octomap.github.io](https://octomap.github.io/) | Paper. The OctoMap library itself is BSD-3-Clause ([LICENSE.txt](https://raw.githubusercontent.com/OctoMap/octomap/devel/octomap/LICENSE.txt)) and is **not** a dependency | The 3D form of ray-based log-odds updates. This repo uses a 2D walk and does not vendor or link OctoMap |
| Nav2 `nav2_costmap_2d` obstacle and voxel layers (Jazzy) | BSD-3-Clause and Apache-2.0 per package.xml | The idea of feeding a 2D costmap from range or depth observations. Not copied. The StaticLayer is used at runtime as an apt package in launch test B |
| `depth_image_proc` (ROS image_pipeline, Jazzy) | BSD per [package.xml](https://raw.githubusercontent.com/ros-perception/image_pipeline/jazzy/depth_image_proc/package.xml) | The idea of turning a depth image and CameraInfo into 3D points. Not copied; back-projection here is authored |
| Hartley and Zisserman, *Multiple View Geometry in Computer Vision* | Book | The pinhole camera model |
| OpenCV pinhole / `projectPoints` convention | Apache-2.0 library, **not a dependency** | Pixel centre at (0, 0) and the camera matrix layout. Official Python wheels are not used, because they ship LGPLv2.1 FFmpeg |
| ROS REP-103 | https://www.ros.org/reps/rep-0103.html | Map and optical frame conventions |
| Amanatides and Woo, "A Fast Voxel Traversal Algorithm for Ray Tracing", Eurographics, 1987 | Paper | The 2D grid walk |

## Not used

- **`nav2_amcl`.** LGPL-2.1-or-later. Do not depend on it, link it, or read it for implementation.
- **OpenCV / opencv-python / opencv-python-headless as a dependency.** Idea-only camera convention. Official wheels ship LGPLv2.1 FFmpeg ([licensing note](https://github.com/opencv/opencv-python/blob/4.x/README.md#licensing)).
- **OctoMap as a library or source tree.** Idea only.
- **Gazebo, slam_toolbox, full `nav2_bringup`.** Not part of v1 CI.
- GPL or other LGPL robotics code is not read for implementation.

## Sibling portfolio repos (contrast)

- `ros2-nav2-slam-sim`: Gazebo Classic, slam_toolbox, Nav2 waypoint mission.
- `nav2-coverage-planner-compare`: compares planners on already-made costmaps.
- `nav2-behavior-trees`: a BehaviorTree.CPP mission executive.
- `lidar-shape-classifier-ros2`: LiDAR cluster shapes.
- `ros2-vision-tracking-demo`: YOLO detections and a Kalman / IoU tracker.

This repo is the synthetic depth-to-occupancy pipeline that those repositories are not.
