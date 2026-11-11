// SPDX-License-Identifier: Apache-2.0

import { Z_MIN_DEFAULT, Z_MAX_DEFAULT } from "./constants.ts";
import type { Vec3 } from "./vec.ts";

export function heightKeep(z: number, zMin = Z_MIN_DEFAULT, zMax = Z_MAX_DEFAULT): boolean {
  return z >= zMin && z <= zMax;
}

export function heightKeepPoint(pt: Vec3, zMin = Z_MIN_DEFAULT, zMax = Z_MAX_DEFAULT): boolean {
  return heightKeep(pt[2], zMin, zMax);
}
