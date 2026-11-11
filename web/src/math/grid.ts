// SPDX-License-Identifier: Apache-2.0

import {
  GRID_H,
  GRID_W,
  L_FREE,
  L_MAX,
  L_MIN,
  L_OCC,
  L0,
  ORIGIN_X,
  ORIGIN_Y,
  RESOLUTION,
  Z_MIN_DEFAULT,
  Z_MAX_DEFAULT,
} from "./constants.ts";
import { pixelToMap } from "./backproject.ts";
import { defaultCamera, type Camera } from "./camera.ts";
import { heightKeepPoint } from "./heightFilter.ts";
import { roundHalfEven } from "./rounding.ts";

export interface GridConfig {
  resolution: number;
  originX: number;
  originY: number;
  width: number;
  height: number;
}

export const defaultGridConfig = (): GridConfig => ({
  resolution: RESOLUTION,
  originX: ORIGIN_X,
  originY: ORIGIN_Y,
  width: GRID_W,
  height: GRID_H,
});

export function worldToCell(x: number, y: number, cfg = defaultGridConfig()): [number, number] {
  const ix = Math.floor((x - cfg.originX) / cfg.resolution);
  const iy = Math.floor((y - cfg.originY) / cfg.resolution);
  return [ix, iy];
}

export function inGrid(ix: number, iy: number, cfg = defaultGridConfig()): boolean {
  return ix >= 0 && ix < cfg.width && iy >= 0 && iy < cfg.height;
}

export function logOddsToProb(l: number): number {
  if (l >= 0) {
    return 1 / (1 + Math.exp(-l));
  }
  const ez = Math.exp(l);
  return ez / (1 + ez);
}

export function probToOccupancyValue(p: number, updated: boolean): number {
  if (!updated) {
    return -1;
  }
  if (p >= 0.65) {
    return 100;
  }
  if (p <= 0.35) {
    return 0;
  }
  return roundHalfEven(p * 100);
}

function clipTToGridExit(
  x0: number,
  y0: number,
  x1: number,
  y1: number,
  cfg: GridConfig,
): number {
  const dx = x1 - x0;
  const dy = y1 - y0;
  let tMax = 1.0;
  const pairs: [number, number, number, number][] = [
    [cfg.originX, cfg.originX + cfg.width * cfg.resolution, x0, dx],
    [cfg.originY, cfg.originY + cfg.height * cfg.resolution, y0, dy],
  ];
  for (const [lo, hi, o, d] of pairs) {
    for (const bound of [lo, hi]) {
      if (Math.abs(d) > 1e-15) {
        const t = (bound - o) / d;
        if (0 < t && t < tMax) {
          tMax = t;
        }
      }
    }
  }
  return tMax;
}

export function rayWalk2d(
  x0: number,
  y0: number,
  x1: number,
  y1: number,
  cfg = defaultGridConfig(),
): [number, number][] {
  const res = cfg.resolution;

  if (Math.abs(x0 - x1) < 1e-15 && Math.abs(y0 - y1) < 1e-15) {
    const [ix, iy] = worldToCell(x0, y0, cfg);
    return inGrid(ix, iy, cfg) ? [[ix, iy]] : [];
  }

  const dx = x1 - x0;
  const dy = y1 - y0;
  let [ix, iy] = worldToCell(x0, y0, cfg);
  const [endIx, endIy] = worldToCell(x1, y1, cfg);
  const endIn = inGrid(endIx, endIy, cfg);

  const stepX = Math.abs(dx) < 1e-15 ? 0 : dx > 0 ? 1 : -1;
  const stepY = Math.abs(dy) < 1e-15 ? 0 : dy > 0 ? 1 : -1;

  const boundaryT = (cell: number, origin: number, d: number, o: number): number => {
    if (Math.abs(d) < 1e-15) {
      return Number.POSITIVE_INFINITY;
    }
    const boundary = d > 0 ? (cell + 1) * res + origin : cell * res + origin;
    return (boundary - o) / d;
  };

  let tMaxX = boundaryT(ix, cfg.originX, dx, x0);
  let tMaxY = boundaryT(iy, cfg.originY, dy, y0);
  const tDeltaX = Math.abs(dx) >= 1e-15 ? Math.abs(res / dx) : Number.POSITIVE_INFINITY;
  const tDeltaY = Math.abs(dy) >= 1e-15 ? Math.abs(res / dy) : Number.POSITIVE_INFINITY;

  const tLimit = endIn ? 1.0 : clipTToGridExit(x0, y0, x1, y1, cfg);

  const cells: [number, number][] = [];
  while (true) {
    if (inGrid(ix, iy, cfg)) {
      cells.push([ix, iy]);
    }
    if (ix === endIx && iy === endIy) {
      break;
    }

    const tx = tMaxX;
    const ty = tMaxY;
    if (tx > tLimit + 1e-12 && ty > tLimit + 1e-12) {
      break;
    }
    if (Math.abs(tx - ty) < 1e-12) {
      if (tx <= tLimit + 1e-12) {
        tMaxX += tDeltaX;
        ix += stepX;
      } else {
        break;
      }
    } else if (tx < ty) {
      if (tx > tLimit + 1e-12) {
        break;
      }
      tMaxX += tDeltaX;
      ix += stepX;
    } else {
      if (ty > tLimit + 1e-12) {
        break;
      }
      tMaxY += tDeltaY;
      iy += stepY;
    }

    if (cells.length === 0 && !inGrid(ix, iy, cfg)) {
      break;
    }
  }
  return cells;
}

export interface RayInfo {
  kept: boolean;
  occEndpoint: boolean;
  endCell: [number, number];
  walk: [number, number][];
}

export class LogOddsGrid {
  readonly config: GridConfig;
  readonly logOdds: Float64Array;
  readonly updated: Uint8Array;

  constructor(cfg = defaultGridConfig()) {
    this.config = cfg;
    this.logOdds = new Float64Array(cfg.height * cfg.width).fill(L0);
    this.updated = new Uint8Array(cfg.height * cfg.width);
  }

  idx(iy: number, ix: number): number {
    return iy * this.config.width + ix;
  }

  clampCell(iy: number, ix: number): void {
    const i = this.idx(iy, ix);
    this.logOdds[i] = Math.max(L_MIN, Math.min(L_MAX, this.logOdds[i]!));
  }

  addFree(iy: number, ix: number): void {
    if (!inGrid(ix, iy, this.config)) {
      return;
    }
    const i = this.idx(iy, ix);
    this.logOdds[i] = (this.logOdds[i] ?? 0) + L_FREE;
    this.clampCell(iy, ix);
    this.updated[i] = 1;
  }

  addOcc(iy: number, ix: number): void {
    if (!inGrid(ix, iy, this.config)) {
      return;
    }
    const i = this.idx(iy, ix);
    this.logOdds[i] = (this.logOdds[i] ?? 0) + L_OCC;
    this.clampCell(iy, ix);
    this.updated[i] = 1;
  }

  occupancyValues(): Int32Array {
    const out = new Int32Array(this.config.height * this.config.width).fill(-1);
    for (let iy = 0; iy < this.config.height; iy++) {
      for (let ix = 0; ix < this.config.width; ix++) {
        const i = this.idx(iy, ix);
        if (this.updated[i]) {
          const p = logOddsToProb(this.logOdds[i]!);
          out[i] = probToOccupancyValue(p, true);
        }
      }
    }
    return out;
  }

  counts(): { occupied: number; free: number; unknown: number; mid: number } {
    const vals = this.occupancyValues();
    let occupied = 0;
    let free = 0;
    let unknown = 0;
    let mid = 0;
    for (let i = 0; i < vals.length; i++) {
      const v = vals[i]!;
      if (v === 100) occupied++;
      else if (v === 0) free++;
      else if (v === -1) unknown++;
      else if (v > 0 && v < 100) mid++;
    }
    return { occupied, free, unknown, mid };
  }

  valueAtWorld(x: number, y: number): number {
    const [ix, iy] = worldToCell(x, y, this.config);
    if (!inGrid(ix, iy, this.config)) {
      return -1;
    }
    return this.occupancyValues()[this.idx(iy, ix)]!;
  }
}

export function collectRaysFromDepth(
  depth: Float64Array,
  cam: Camera = defaultCamera(),
  zMin = Z_MIN_DEFAULT,
  zMax = Z_MAX_DEFAULT,
  occAllValid = false,
): RayInfo[] {
  const camXy: [number, number] = [0, 0];
  const rays: RayInfo[] = [];
  for (let v = 0; v < cam.height; v++) {
    for (let u = 0; u < cam.width; u++) {
      const z = depth[v * cam.width + u]!;
      if (z <= 0) {
        continue;
      }
      const pt = pixelToMap(u, v, z, cam);
      const kept = occAllValid || heightKeepPoint(pt, zMin, zMax);
      const endXy: [number, number] = [pt[0], pt[1]];
      const endCell = worldToCell(endXy[0], endXy[1]);
      const walk = rayWalk2d(camXy[0], camXy[1], endXy[0], endXy[1]);
      rays.push({
        kept,
        occEndpoint: occAllValid || kept,
        endCell,
        walk,
      });
    }
  }
  return rays;
}

function twoPassFreeThenOcc(g: LogOddsGrid, rays: RayInfo[]): void {
  for (const ray of rays) {
    const [endIx, endIy] = ray.endCell;
    for (const [ix, iy] of ray.walk) {
      if (ray.kept && ix === endIx && iy === endIy) {
        continue;
      }
      g.addFree(iy, ix);
    }
  }
  for (const ray of rays) {
    if (!ray.occEndpoint) {
      continue;
    }
    const [endIx, endIy] = ray.endCell;
    if (inGrid(endIx, endIy, g.config)) {
      g.addOcc(endIy, endIx);
    }
  }
}

export function updateGridFromDepth(
  depth: Float64Array,
  cam: Camera = defaultCamera(),
  zMin = Z_MIN_DEFAULT,
  zMax = Z_MAX_DEFAULT,
): LogOddsGrid {
  const g = new LogOddsGrid();
  const rays = collectRaysFromDepth(depth, cam, zMin, zMax, false);
  twoPassFreeThenOcc(g, rays);
  return g;
}
