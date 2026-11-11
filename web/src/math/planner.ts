// SPDX-License-Identifier: Apache-2.0

import { defaultGridConfig, worldToCell, type GridConfig } from "./grid.ts";

const SQRT2 = Math.sqrt(2);

export interface PathResult {
  cells: [number, number][] | null;
  cost: number;
}

function isFree(grid: Int32Array, w: number, h: number, iy: number, ix: number): boolean {
  if (ix < 0 || ix >= w || iy < 0 || iy >= h) {
    return false;
  }
  return grid[iy * w + ix] === 0;
}

const NEIGHBOR_OFFSETS: [number, number, number][] = [
  [-1, 0, 1],
  [1, 0, 1],
  [0, -1, 1],
  [0, 1, 1],
  [-1, -1, SQRT2],
  [-1, 1, SQRT2],
  [1, -1, SQRT2],
  [1, 1, SQRT2],
];

function canStep(
  grid: Int32Array,
  w: number,
  h: number,
  ix: number,
  iy: number,
  nix: number,
  niy: number,
): boolean {
  if (!isFree(grid, w, h, niy, nix)) {
    return false;
  }
  const dix = nix - ix;
  const diy = niy - iy;
  if (dix !== 0 && diy !== 0) {
    if (!isFree(grid, w, h, iy, nix) || !isFree(grid, w, h, niy, ix)) {
      return false;
    }
  }
  return true;
}

interface HeapItem {
  f: number;
  ix: number;
  iy: number;
}

export function astar(
  grid: Int32Array,
  gridW: number,
  gridH: number,
  startXy: { x: number; y: number },
  goalXy: { x: number; y: number },
  cfg: GridConfig = defaultGridConfig(),
): PathResult {
  const [sx, sy] = worldToCell(startXy.x, startXy.y, cfg);
  const [gx, gy] = worldToCell(goalXy.x, goalXy.y, cfg);

  if (!isFree(grid, gridW, gridH, sy, sx)) {
    return { cells: null, cost: Number.POSITIVE_INFINITY };
  }
  if (sx === gx && sy === gy) {
    return { cells: [[sx, sy]], cost: 0 };
  }
  if (!isFree(grid, gridW, gridH, gy, gx)) {
    return { cells: null, cost: Number.POSITIVE_INFINITY };
  }

  const h = (ix: number, iy: number) => Math.hypot(gx - ix, gy - iy);

  const open: HeapItem[] = [{ f: h(sx, sy), ix: sx, iy: sy }];
  const cameFrom = new Map<string, [number, number]>();
  const gScore = new Map<string, number>();
  const key = (ix: number, iy: number) => `${ix},${iy}`;
  gScore.set(key(sx, sy), 0);

  const popMin = (): HeapItem | undefined => {
    let best = 0;
    for (let i = 1; i < open.length; i++) {
      const a = open[i]!;
      const b = open[best]!;
      if (a.f < b.f || (a.f === b.f && (a.ix < b.ix || (a.ix === b.ix && a.iy < b.iy)))) {
        best = i;
      }
    }
    return open.splice(best, 1)[0];
  };

  while (open.length > 0) {
    const current = popMin()!;
  const { ix, iy } = current;
    if (ix === gx && iy === gy) {
      const path: [number, number][] = [[ix, iy]];
      let cx = ix;
      let cy = iy;
      while (cameFrom.has(key(cx, cy))) {
        const prev = cameFrom.get(key(cx, cy))!;
        cx = prev[0];
        cy = prev[1];
        path.push([cx, cy]);
      }
      path.reverse();
      return { cells: path, cost: gScore.get(key(gx, gy)) ?? Number.POSITIVE_INFINITY };
    }

    for (const [dix, diy, stepCost] of NEIGHBOR_OFFSETS) {
      const nix = ix + dix;
      const niy = iy + diy;
      if (!canStep(grid, gridW, gridH, ix, iy, nix, niy)) {
        continue;
      }
      const tentative = (gScore.get(key(ix, iy)) ?? 0) + stepCost;
      const nk = key(nix, niy);
      if (!gScore.has(nk) || tentative < (gScore.get(nk) ?? Infinity)) {
        gScore.set(nk, tentative);
        cameFrom.set(nk, [ix, iy]);
        open.push({ f: tentative + h(nix, niy), ix: nix, iy: niy });
      }
    }
  }
  return { cells: null, cost: Number.POSITIVE_INFINITY };
}
