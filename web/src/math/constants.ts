// SPDX-License-Identifier: Apache-2.0
/** Locked constants from depth_occupancy_nav (PLAN.md section 5). */

export const CAMERA_T = [0.0, 0.0, 0.8] as const;

export const MAP_R_OPTICAL: readonly [readonly number[], readonly number[], readonly number[]] = [
  [0.0, 0.0, 1.0],
  [-1.0, 0.0, 0.0],
  [0.0, -1.0, 0.0],
];

export const W = 80;
export const H = 60;
export const FOV_DEG = 60.0;
export const MAX_RANGE = 10.0;

export const FX = (W / 2) / Math.tan((FOV_DEG / 2) * (Math.PI / 180));
export const FY = FX;
export const CX = 39.5;
export const CY = 29.5;

export const Z_MIN_DEFAULT = 0.15;
export const Z_MAX_DEFAULT = 1.5;

export const L_OCC = Math.log(0.7 / 0.3);
export const L_FREE = Math.log(0.35 / 0.65);
export const L_MIN = -2.0;
export const L_MAX = 3.5;
export const L0 = 0.0;

export const RESOLUTION = 0.1;
export const ORIGIN_X = -1.0;
export const ORIGIN_Y = -3.0;
export const GRID_W = 80;
export const GRID_H = 60;

export const SIGMA_REL = 0.01;
export const SIGMA_ABS = 0.01;

export const FRONT_BOX = {
  xmin: 2.75,
  xmax: 3.15,
  ymin: -0.45,
  ymax: 0.45,
  zmin: 0.0,
  zmax: 1.2,
};

export const SIDE_BOX = {
  xmin: 4.05,
  xmax: 4.45,
  ymin: 1.25,
  ymax: 2.15,
  zmin: 0.0,
  zmax: 1.0,
};

export const GOALS = {
  open: { x: 1.5, y: 0.0 },
  around: { x: 5.5, y: -1.5 },
  shadow: { x: 5.5, y: 0.0 },
  inside: { x: 2.95, y: 0.0 },
} as const;

export const START_XY = { x: 0.5, y: 0.0 };
