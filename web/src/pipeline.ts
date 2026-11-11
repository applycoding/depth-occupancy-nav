// SPDX-License-Identifier: Apache-2.0

import { defaultCamera } from "./math/camera.ts";
import { Z_MAX_DEFAULT, Z_MIN_DEFAULT, GOALS, START_XY, W, H } from "./math/constants.ts";
import { updateGridFromDepth, type LogOddsGrid } from "./math/grid.ts";
import { addDepthNoise } from "./math/noise.ts";
import { astar } from "./math/planner.ts";
import { renderDepth } from "./math/render.ts";
import { pixelToMap } from "./math/backproject.ts";
import type { Vec3 } from "./math/vec.ts";

export type GoalId = keyof typeof GOALS;

export interface PipelineOptions {
  noiseScale: number;
  zMin: number;
  zMax: number;
  goal: GoalId;
}

export interface PipelineState {
  depth: Float64Array;
  mapPoints: Vec3[];
  grid: LogOddsGrid;
  occupancy: Int32Array;
  counts: ReturnType<LogOddsGrid["counts"]>;
  path: [number, number][] | null;
  pathCost: number;
}

const cam = defaultCamera();

export function runPipeline(opts: PipelineOptions): PipelineState {
  const { depth: clean } = renderDepth(cam);
  const depth =
    opts.noiseScale > 0
      ? addDepthNoise(clean, cam.width, cam.height, 1, opts.noiseScale)
      : clean.slice();

  const mapPoints: Vec3[] = [];
  for (let v = 0; v < H; v++) {
    for (let u = 0; u < W; u++) {
      const z = depth[v * W + u]!;
      if (z > 0) {
        mapPoints.push(pixelToMap(u, v, z, cam));
      }
    }
  }

  const grid = updateGridFromDepth(depth, cam, opts.zMin, opts.zMax);
  const occupancy = grid.occupancyValues();
  const counts = grid.counts();

  const goal = GOALS[opts.goal];
  const pathResult = astar(occupancy, W, H, START_XY, goal);

  return {
    depth,
    mapPoints,
    grid,
    occupancy,
    counts,
    path: pathResult.cells,
    pathCost: pathResult.cost,
  };
}

export const defaultPipelineOptions = (): PipelineOptions => ({
  noiseScale: 0,
  zMin: Z_MIN_DEFAULT,
  zMax: Z_MAX_DEFAULT,
  goal: "open",
});
