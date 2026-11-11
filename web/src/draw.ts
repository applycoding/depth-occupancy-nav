// SPDX-License-Identifier: Apache-2.0

import { FRONT_BOX, SIDE_BOX, ORIGIN_X, ORIGIN_Y, RESOLUTION, GRID_W, GRID_H } from "./math/constants.ts";
import type { Vec3 } from "./math/vec.ts";

function depthColor(z: number, zMax = 10): [number, number, number] {
  if (z <= 0) {
    return [20, 20, 30];
  }
  const t = Math.min(1, z / zMax);
  const r = Math.floor(255 * t);
  const g = Math.floor(128 * (1 - Math.abs(t - 0.5) * 2));
  const b = Math.floor(255 * (1 - t));
  return [r, g, b];
}

export function drawDepth(canvas: HTMLCanvasElement, depth: Float64Array, w: number, h: number): void {
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    return;
  }
  canvas.width = w;
  canvas.height = h;
  const img = ctx.createImageData(w, h);
  for (let i = 0; i < depth.length; i++) {
    const [r, g, b] = depthColor(depth[i]!);
    const p = i * 4;
    img.data[p] = r;
    img.data[p + 1] = g;
    img.data[p + 2] = b;
    img.data[p + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
}

export function drawTopDown(
  canvas: HTMLCanvasElement,
  points: Vec3[],
  path: [number, number][] | null,
): void {
  const scale = 40;
  const pad = 20;
  const mapWm = GRID_W * RESOLUTION;
  const mapHm = GRID_H * RESOLUTION;
  const cw = mapWm * scale + pad * 2;
  const ch = mapHm * scale + pad * 2;
  canvas.width = cw;
  canvas.height = ch;
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    return;
  }
  ctx.fillStyle = "#1a1a2e";
  ctx.fillRect(0, 0, cw, ch);

  const toCanvas = (x: number, y: number): [number, number] => {
    const px = pad + ((x - ORIGIN_X) / mapWm) * mapWm * scale;
    const py = pad + mapHm * scale - ((y - ORIGIN_Y) / mapHm) * mapHm * scale;
    return [px, py];
  };

  ctx.strokeStyle = "#444";
  ctx.strokeRect(pad, pad, mapWm * scale, mapHm * scale);

  ctx.fillStyle = "rgba(80,80,120,0.5)";
  for (const box of [FRONT_BOX, SIDE_BOX]) {
    const [x0, y0] = toCanvas(box.xmin, box.ymin);
    const [x1, y1] = toCanvas(box.xmax, box.ymax);
    ctx.fillRect(x0, y1, x1 - x0, y0 - y1);
  }

  ctx.fillStyle = "#6cf";
  for (const p of points) {
    const [cx, cy] = toCanvas(p[0], p[1]);
    ctx.fillRect(cx - 0.5, cy - 0.5, 1, 1);
  }

  ctx.fillStyle = "#ff0";
  const [camX, camY] = toCanvas(0, 0);
  ctx.beginPath();
  ctx.arc(camX, camY, 3, 0, Math.PI * 2);
  ctx.fill();

  if (path && path.length > 0) {
    ctx.strokeStyle = "#0f0";
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < path.length; i++) {
      const [ix, iy] = path[i]!;
      const x = ORIGIN_X + (ix + 0.5) * RESOLUTION;
      const y = ORIGIN_Y + (iy + 0.5) * RESOLUTION;
      const [px, py] = toCanvas(x, y);
      if (i === 0) {
        ctx.moveTo(px, py);
      } else {
        ctx.lineTo(px, py);
      }
    }
    ctx.stroke();
  }
}

export function drawOccupancy(
  canvas: HTMLCanvasElement,
  occ: Int32Array,
  path: [number, number][] | null,
): void {
  const cell = 6;
  const w = GRID_W * cell;
  const h = GRID_H * cell;
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    return;
  }
  for (let iy = 0; iy < GRID_H; iy++) {
    for (let ix = 0; ix < GRID_W; ix++) {
      const v = occ[iy * GRID_W + ix]!;
      let color: string;
      if (v === -1) {
        color = "#2a2a3a";
      } else if (v === 0) {
        color = "#1e4d2b";
      } else if (v === 100) {
        color = "#c33";
      } else {
        const t = v / 100;
        color = `rgb(${Math.floor(200 * t)},${Math.floor(100 * (1 - t))},80)`;
      }
      ctx.fillStyle = color;
      ctx.fillRect(ix * cell, (GRID_H - 1 - iy) * cell, cell, cell);
    }
  }
  if (path) {
    ctx.strokeStyle = "#0ff";
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < path.length; i++) {
      const [ix, iy] = path[i]!;
      const px = (ix + 0.5) * cell;
      const py = (GRID_H - 0.5 - iy) * cell;
      if (i === 0) {
        ctx.moveTo(px, py);
      } else {
        ctx.lineTo(px, py);
      }
    }
    ctx.stroke();
  }
}

export function occupancyCanvasVariance(canvas: HTMLCanvasElement): number {
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    return 0;
  }
  const { data, width, height } = ctx.getImageData(0, 0, canvas.width, canvas.height);
  let sum = 0;
  let sumSq = 0;
  const n = width * height;
  for (let i = 0; i < data.length; i += 4) {
    const lum = data[i]! + data[i + 1]! + data[i + 2]!;
    sum += lum;
    sumSq += lum * lum;
  }
  const mean = sum / n;
  return sumSq / n - mean * mean;
}
