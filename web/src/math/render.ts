// SPDX-License-Identifier: Apache-2.0

import { CAMERA_T } from "./constants.ts";
import { cameraZAtT, defaultCamera, mapRayDirection, type Camera } from "./camera.ts";
import {
  classifyHit,
  frontBox,
  groundPlaneHit,
  rayIntersectAabb,
  sideBox,
  type HitKind,
} from "./scene.ts";
import type { Vec3 } from "./vec.ts";

export interface RenderResult {
  depth: Float64Array;
  kinds: HitKind[];
}

export function renderDepth(camera: Camera = defaultCamera()): RenderResult {
  const depth = new Float64Array(camera.width * camera.height);
  const kinds: HitKind[] = new Array(camera.width * camera.height).fill("none");
  const origin: Vec3 = [CAMERA_T[0], CAMERA_T[1], CAMERA_T[2]];

  for (let v = 0; v < camera.height; v++) {
    for (let u = 0; u < camera.width; u++) {
      const direction = mapRayDirection(u, v, camera);
      let bestT = Number.POSITIVE_INFINITY;
      let bestKind: HitKind = "none";

      for (const [box, kind] of [
        [frontBox, "front_box"] as const,
        [sideBox, "side_box"] as const,
      ]) {
        const [t0, t1] = rayIntersectAabb(box, origin, direction, 0, camera.maxRange);
        if (t0 <= t1 && t0 > 0 && t0 < bestT) {
          const z = cameraZAtT(origin, direction, t0);
          if (0 < z && z <= camera.maxRange) {
            bestT = t0;
            bestKind = kind;
          }
        }
      }

      const gt = groundPlaneHit(origin, direction);
      if (gt !== null && gt <= camera.maxRange && gt < bestT) {
        const z = cameraZAtT(origin, direction, gt);
        if (0 < z && z <= camera.maxRange) {
          bestT = gt;
          bestKind = "ground";
        }
      }

      const idx = v * camera.width + u;
      if (bestT < Number.POSITIVE_INFINITY) {
        const pMap: Vec3 = [
          origin[0] + bestT * direction[0],
          origin[1] + bestT * direction[1],
          origin[2] + bestT * direction[2],
        ];
        depth[idx] = cameraZAtT(origin, direction, bestT);
        kinds[idx] = bestKind === "ground" ? classifyHit(pMap) : bestKind;
      }
    }
  }
  return { depth, kinds };
}
