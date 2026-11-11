# depth-occupancy-nav

Simulation only. Synthetic depth only. Not tested on real cameras or real robots.

A portfolio demo by Arpan Bom. An original implementation, inspired by known
methods, turns simulated pinhole depth frames into a 2D occupancy grid and
shows that a planner can run over that grid. The methods are pinhole
back-projection, analytic scene ray casting, a height-band filter that
removes a horizontal ground plane, log-odds occupancy updates, and
8-connected A*. This repository does not invent those methods.

Licence: Apache-2.0. See LICENSE and NOTICE.

Planning is complete. The build contract is in PLAN.md, the task list is in
TASKS.md, and idea sources are in REFERENCES.md. Implementation follows
those documents. A GitHub Pages demo will be published at
https://applycoding.github.io/depth-occupancy-nav/ after the first green
build on main.

A single depth frame marks the visible surface, not the solid volume.
The height filter is a height gate, not a fitted plane. Invalid depth
pixels do not clear to max range.
