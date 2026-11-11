// SPDX-License-Identifier: Apache-2.0

import { describe, expect, it } from "vitest";
import golden from "../../tests/fixtures/golden.json";
import { pixelToMap } from "../src/math/backproject.ts";
import { CX, CY, FX, START_XY, GOALS, W, H } from "../src/math/constants.ts";
import { rayWalk2d, updateGridFromDepth } from "../src/math/grid.ts";
import { roundHalfEven } from "../src/math/rounding.ts";
import { astar } from "../src/math/planner.ts";
import { renderDepth } from "../src/math/render.ts";
import { L_OCC, L_FREE } from "../src/math/constants.ts";

describe("golden vs Python core", () => {
  it("locked constants", () => {
    expect(FX).toBeCloseTo(golden.fx, 12);
    expect(L_OCC).toBeCloseTo(golden.l_occ, 12);
    expect(L_FREE).toBeCloseTo(golden.l_free, 12);
  });

  it("28-cell ray walk", () => {
    const walk = rayWalk2d(0, 0, 2.75, 0);
    expect(walk).toHaveLength(28);
    expect(walk).toEqual(golden.walk_28);
  });

  it("optical axis and neighbor back-projections", () => {
    const axis = pixelToMap(CX, CY, 2.75);
    for (let i = 0; i < 3; i++) {
      expect(axis[i]).toBeCloseTo(golden.optical_axis[i]!, 12);
    }
    const { depth } = renderDepth();
    for (const nb of golden.neighbors) {
      const z = depth[nb.v * W + nb.u]!;
      expect(z).toBeCloseTo(nb.z, 12);
      const pt = pixelToMap(nb.u, nb.v, z);
      for (let i = 0; i < 3; i++) {
        expect(pt[i]).toBeCloseTo(nb.map[i]!, 12);
      }
    }
  });

  it("occupancy cells, probes, and counts", () => {
    const { depth } = renderDepth();
    const grid = updateGridFromDepth(depth);
    const vals = grid.occupancyValues();
    const occupied = [];
    for (let iy = 0; iy < H; iy++) {
      for (let ix = 0; ix < W; ix++) {
        if (vals[iy * W + ix] === 100) {
          occupied.push([ix, iy, 100]);
        }
      }
    }
    expect(occupied).toEqual(golden.occupied_cells);
    expect(grid.counts()).toEqual(golden.counts);
    for (const [key, expected] of Object.entries(golden.probes)) {
      const [xs, ys] = key.split(",");
      const v = grid.valueAtWorld(parseFloat(xs!), parseFloat(ys!));
      expect(v).toBe(expected);
    }
  });

  it("planner open and around paths", () => {
    const { depth } = renderDepth();
    const grid = updateGridFromDepth(depth);
    const occ = grid.occupancyValues();
    const open = astar(occ, W, H, START_XY, GOALS.open);
    expect(open.cells).toEqual(golden.open_path_cells);
    expect(open.cost).toBeCloseTo(golden.open_path_cost, 12);

    const around = astar(occ, W, H, START_XY, GOALS.around);
    expect(around.cells?.length).toBe(golden.around_path_len);
    expect(around.cells?.[0]).toEqual(golden.around_first);
    expect(around.cells?.[around.cells.length - 1]).toEqual(golden.around_last);
    expect(around.cost).toBeCloseTo(golden.around_cost, 10);
  });

  it("half-even rounding at ties", () => {
    expect(roundHalfEven(0.5)).toBe(0);
    expect(roundHalfEven(1.5)).toBe(2);
    expect(roundHalfEven(2.5)).toBe(2);
    expect(roundHalfEven(22.5)).toBe(22);
  });
});
