<!-- SPDX-License-Identifier: Apache-2.0 -->
# Deviations

## Nav2 apt version on ROS 2 Jazzy (criterion 15)

PLAN.md pins **1.3.14-1** for `ros-jazzy-nav2-navfn-planner` and `ros-jazzy-nav2-planner`. On **2026-11-11**, on `ubuntu-24.04` with `packages.ros.org` ros2 noble, `apt-get install ...=1.3.14-1` fails with:

```
E: Version '1.3.14-1' for 'ros-jazzy-nav2-navfn-planner' was not found
```

CI installs and asserts exact noble Debian builds (**Navigation2 1.3.13** upstream):

- `ros-jazzy-nav2-navfn-planner` **1.3.13-1noble.20260921.031752**
- `ros-jazzy-nav2-planner` **1.3.13-1noble.20260921.031801**
- `ros-jazzy-nav2-costmap-2d` **1.3.13-1noble.20260921.024946**

Rosdistro `jazzy/distribution.yaml` still lists the navigation2 release as **1.3.14-1**; the main apt repo at the pin date served the 1.3.13 builds above. See PLAN Amendment 1 (2026-11-11).

## Launch test B negative goal error codes (criterion 15)

On Nav2 **1.3.13**, `nav2_navfn_planner/src/navfn_planner.cpp` (tag 1.3.13, about line 155) throws `GoalOccupied` (**206**) only when `tolerance_ == 0` and the goal cell is lethal. With `tolerance: 0.05` in `planner_server.yaml`, the face goal `(2.75, 0.00)` falls through to `makePlan`, which fails and returns `NoValidPathCouldBeFound` (**208**). Shadow `(5.50, 0.00)` also returns **208**. Launch test B asserts both negative goals yield **208**. Nav2 **1.3.13** `planner_server` sets `error_code` but leaves the action `error_msg` string empty; launch test B prints and asserts non-empty planner diagnostics from that field when set, otherwise from `/rosout` WARN lines on `planner_server`.

## Height-filter mutant counts (criterion 10)

The PLAN's **117 / 1208** occupied and free counts came from the throwaway prototype and could not be reproduced with the locked Amanatides-Woo walk. The measured values at this commit are **78 / 1247 / 3080 / 395**. Mid **395** matches the PLAN. The behavioural assertions are unchanged (around path `None`, open path exists, start and open goal free; ground-only cells `(28, 30)`, `(29, 30)`, `(30, 30)` are 100).

## Launch test B planner delayed start (`TimerAction` 4 s)

PLAN.md lifecycle text asks to wait for the published map before configuring `planner_server`. In practice the Nav2 lifecycle manager needs a few seconds after the depth node is up before `compute_path_to_pose` is ready. `test_launch_navfn.py` still starts `planner_server` and `lifecycle_manager` via `TimerAction(period=4.0, ...)` so launch test B remains reliable on the pinned Jazzy image. Costmap readiness is also asserted before goals are sent (see launch test B).
