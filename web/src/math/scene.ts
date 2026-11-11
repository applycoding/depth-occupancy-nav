// SPDX-License-Identifier: Apache-2.0

import { FRONT_BOX, SIDE_BOX } from "./constants.ts";
import type { Vec3 } from "./vec.ts";

export type HitKind = "front_box" | "side_box" | "ground" | "none";

export interface AABB {
  xmin: number;
  xmax: number;
  ymin: number;
  ymax: number;
  zmin: number;
  zmax: number;
}

export function rayIntersectAabb(
  box: AABB,
  origin: Vec3,
  direction: Vec3,
  tMin: number,
  tMax: number,
): [number, number] {
  let t0 = tMin;
  let t1 = tMax;
  const mins = [box.xmin, box.ymin, box.zmin];
  const maxs = [box.xmax, box.ymax, box.zmax];
  for (let i = 0; i < 3; i++) {
    const o = origin[i]!;
    const d = direction[i]!;
    const lo = mins[i]!;
    const hi = maxs[i]!;
    if (Math.abs(d) < 1e-15) {
      if (o < lo || o > hi) {
        return [Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY];
      }
    } else {
      const inv = 1 / d;
      let tNear = (lo - o) * inv;
      let tFar = (hi - o) * inv;
      if (tNear > tFar) {
        [tNear, tFar] = [tFar, tNear];
      }
      t0 = Math.max(t0, tNear);
      t1 = Math.min(t1, tFar);
      if (t0 > t1) {
        return [Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY];
      }
    }
  }
  return [t0, t1];
}

export function groundPlaneHit(origin: Vec3, direction: Vec3): number | null {
  if (Math.abs(direction[2]) < 1e-15) {
    return null;
  }
  const t = -origin[2]! / direction[2]!;
  if (t <= 0) {
    return null;
  }
  return t;
}

export function classifyHit(point: Vec3): HitKind {
  const tol = 1e-9;
  if (
    Math.abs(point[0] - FRONT_BOX.xmin) < 0.01 &&
    FRONT_BOX.ymin - tol <= point[1]! &&
    point[1]! <= FRONT_BOX.ymax + tol &&
    FRONT_BOX.zmin - tol <= point[2]! &&
    point[2]! <= FRONT_BOX.zmax + tol
  ) {
    return "front_box";
  }
  if (
    SIDE_BOX.xmin - tol <= point[0]! &&
    point[0]! <= SIDE_BOX.xmax + tol &&
    SIDE_BOX.ymin - tol <= point[1]! &&
    point[1]! <= SIDE_BOX.ymax + tol &&
    SIDE_BOX.zmin - tol <= point[2]! &&
    point[2]! <= SIDE_BOX.zmax + tol
  ) {
    return "side_box";
  }
  if (point[2]! <= tol) {
    return "ground";
  }
  return "none";
}

export const frontBox = FRONT_BOX;
export const sideBox = SIDE_BOX;
