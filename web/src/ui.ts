// SPDX-License-Identifier: Apache-2.0

import { drawDepth, drawOccupancy, drawTopDown } from "./draw.ts";
import { defaultPipelineOptions, runPipeline, type GoalId, type PipelineOptions } from "./pipeline.ts";
import { W, H, Z_MIN_DEFAULT, Z_MAX_DEFAULT } from "./math/constants.ts";

export function initApp(root: HTMLElement): void {
  const opts: PipelineOptions = defaultPipelineOptions();

  root.innerHTML = `
    <header class="banner">
      <h1>depth-occupancy-nav</h1>
      <p class="honesty">Simulation only. Synthetic depth. Not validated on real cameras or robots.</p>
    </header>
    <section class="metrics" aria-label="Pipeline metrics">
      <span>Occupied cells: <strong id="occupied-metric" data-occupied="22">22</strong></span>
      <span id="path-metric" data-path-length="0" data-has-path="true">Path length: 0</span>
    </section>
    <section class="controls">
      <label>Noise scale
        <input type="range" id="noise" min="0" max="3" step="0.05" value="0" />
        <span id="noise-val">0</span>
      </label>
      <label>z_min (m)
        <input type="range" id="zmin" min="0" max="1.2" step="0.01" value="${Z_MIN_DEFAULT}" />
        <span id="zmin-val">${Z_MIN_DEFAULT}</span>
      </label>
      <label>z_max (m)
        <input type="range" id="zmax" min="1" max="2" step="0.01" value="${Z_MAX_DEFAULT}" />
        <span id="zmax-val">${Z_MAX_DEFAULT}</span>
      </label>
      <motion class="goals">
        <button type="button" data-goal="open" class="active">Open goal</button>
        <button type="button" data-goal="around">Around goal</button>
        <button type="button" data-goal="shadow">Shadow goal</button>
      </motion>
    </section>
    <section class="views">
      <figure>
        <figcaption>Depth (camera-Z)</figcaption>
        <canvas id="depth-canvas"></canvas>
      </figure>
      <figure>
        <figcaption>Top-down points</figcaption>
        <canvas id="points-canvas"></canvas>
      </figure>
      <figure>
        <figcaption>Occupancy grid</figcaption>
        <canvas id="occ-canvas"></canvas>
      </figure>
    </section>
  `.replace("<motion", "<div").replace("</motion>", "</div>");

  const depthCanvas = root.querySelector<HTMLCanvasElement>("#depth-canvas")!;
  const pointsCanvas = root.querySelector<HTMLCanvasElement>("#points-canvas")!;
  const occCanvas = root.querySelector<HTMLCanvasElement>("#occ-canvas")!;
  const occupiedEl = root.querySelector<HTMLElement>("#occupied-metric")!;
  const pathEl = root.querySelector<HTMLElement>("#path-metric")!;
  const noiseInput = root.querySelector<HTMLInputElement>("#noise")!;
  const zminInput = root.querySelector<HTMLInputElement>("#zmin")!;
  const zmaxInput = root.querySelector<HTMLInputElement>("#zmax")!;

  const recompute = (): void => {
    const state = runPipeline(opts);
    drawDepth(depthCanvas, state.depth, W, H);
    drawTopDown(pointsCanvas, state.mapPoints, state.path);
    drawOccupancy(occCanvas, state.occupancy, state.path);

    occupiedEl.textContent = String(state.counts.occupied);
    occupiedEl.dataset.occupied = String(state.counts.occupied);

    const pathLen = state.path?.length ?? 0;
    const hasPath = state.path !== null && Number.isFinite(state.pathCost);
    pathEl.textContent = hasPath && pathLen > 0 ? `Path length: ${pathLen}` : "No path";
    pathEl.dataset.pathLength = String(pathLen);
    pathEl.dataset.hasPath = hasPath && pathLen > 0 ? "true" : "false";
  };

  const bindRange = (
    input: HTMLInputElement,
    labelId: string,
    onChange: (v: number) => void,
  ): void => {
    const label = root.querySelector<HTMLElement>(`#${labelId}`)!;
    input.addEventListener("input", () => {
      const v = parseFloat(input.value);
      label.textContent = String(v);
      onChange(v);
      recompute();
    });
  };

  bindRange(noiseInput, "noise-val", (v) => {
    opts.noiseScale = v;
  });
  bindRange(zminInput, "zmin-val", (v) => {
    opts.zMin = v;
  });
  bindRange(zmaxInput, "zmax-val", (v) => {
    opts.zMax = v;
  });

  for (const btn of root.querySelectorAll<HTMLButtonElement>("[data-goal]")) {
    btn.addEventListener("click", () => {
      opts.goal = btn.dataset.goal as GoalId;
      for (const b of root.querySelectorAll<HTMLButtonElement>("[data-goal]")) {
        b.classList.toggle("active", b === btn);
      }
      recompute();
    });
  }

  document.title = "depth-occupancy-nav (simulation only, synthetic depth)";
  recompute();
}
