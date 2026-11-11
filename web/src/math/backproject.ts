// SPDX-License-Identifier: Apache-2.0

import { CAMERA_T } from "./constants.ts";
import { defaultCamera, type Camera } from "./camera.ts";
import { mapFromOptical, type Vec3 } from "./vec.ts";

export function pixelToMap(u: number, v: number, z: number, cam: Camera = defaultCamera()): Vec3 {
  const xOpt = ((u - cam.cx) / cam.fx) * z;
  const yOpt = ((v - cam.cy) / cam.fy) * z;
  const pOpt: Vec3 = [xOpt, yOpt, z];
  return mapFromOptical(pOpt, [CAMERA_T[0], CAMERA_T[1], CAMERA_T[2]]);
}
