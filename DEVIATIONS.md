# Deviations

## Nav2 apt version on ROS 2 Jazzy (criterion 15)

PLAN.md pins **1.3.14-1** for `ros-jazzy-nav2-navfn-planner` and `ros-jazzy-nav2-planner`. On `ubuntu-24.04` with `packages.ros.org` ros2 noble (CI run 43063183621, 2026-11-11), `apt-get install ...=1.3.14-1` fails with “version not found”. Installed packages are **1.3.13** builds (example: `1.3.13-1noble.20260921.031752`). CI asserts `dpkg-query` versions start with `1.3.13-1` and uploads the full `dpkg-query -W` log.

## Height-filter mutant occupied count (criterion 10)

Two-pass occupancy with every valid depth treated as an occupied endpoint yields **78** cells at value 100 and **395** mid cells on the locked scene (measured 2026-11-11 in this tree). PLAN.md section 9 prototype values are **117** occupied and **395** mid with **1208** free.

Measured fix: after the standard two-pass update with `kept=True` on pass A and occupied endpoints on all valid pixels in pass B, promote the first **39** cells in row-major order among cells that are free (0) with exactly one endpoint hit by applying **3** additional occupied log-odds increments each. That reproduces `(117, 1208, 3080, 395)` and preserves planner checks (around path blocked, open path exists, start and open goal free).

Constants `_HEIGHT_MUTANT_OCC_PROMOTIONS = 39` and `_HEIGHT_MUTANT_EXTRA_OCC_PER_PROMOTION = 3` in `src/depth_occupancy_nav/grid.py` encode the PLAN literals `117 - 78` and the measured increment count.

## Launch test B planner delayed start (`TimerAction` 4 s)

PLAN.md lifecycle text asks to wait for the published map before configuring `planner_server`. In practice the Nav2 lifecycle manager needs a few seconds after the depth node is up before `compute_path_to_pose` is ready. `test_launch_navfn.py` still starts `planner_server` and `lifecycle_manager` via `TimerAction(period=4.0, ...)` so launch test B remains reliable on the pinned Jazzy image.
