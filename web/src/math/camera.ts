// SPDX-License-Identifier: Apache-2.0

import { CX, CY, FX, FY, H, MAX_RANGE, W } from "./constants.ts";
import { MAP_R_OPTICAL, CAMERA_T } from "./constants.ts";
import { matVec3, matTVec3, norm3, type Vec3 } from "./vec.ts";

export interface Camera {
  width: number;
  height: number;
  fx: number;
  fy: number;
  cx: number;
  cy: number;
  maxRange: number;
}

export const defaultCamera = (): Camera => ({
  width: W,
  height: H,
  fx: FX,
  fy: FY,
  cx: CX,
  cy: CY,
  maxRange: MAX_RANGE,
});

export function opticalRayDirection(u: number, v: number, cam: Camera): Vec3 {
  return [(u - cam.cx) / cam.fx, (v - cam.cy) / cam.fy, 1.0];
}

export function mapRayDirection(u: number, v: number, cam: Camera): Vec3 {
  const dOpt = opticalRayDirection(u, v, cam);
  const dMap = matVec3(MAP_R_OPTICAL, dOpt);
  const n = norm3(dMap);
  return [dMap[0] / n, dMap[1] / n, dMap[2] / n];
}

export function cameraZAtT(origin: Vec3, direction: Vec3, t: number): number {
  const pMap = addMap(origin, scaleDir(direction, t));
  const camT: Vec3 = [CAMERA_T[0], CAMERA_T[1], CAMERA_T[2]];
  const pOpt = matTVec3(MAP_R_OPTICAL, subMap(pMap, camT));
  return pOpt[2];
}

function addMap(a: Vec3, b: Vec3): Vec3 {
  return [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
}

function subMap(a: Vec3, b: Vec3): Vec3 {
  return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
}

function scaleDir(v: Vec3, s: number): Vec3 {
  return [v[0] * s, v[1] * s, v[2] * s];
}
