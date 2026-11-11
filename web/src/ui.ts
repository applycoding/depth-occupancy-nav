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
      <span>Occupied cells: <strong id="occupied-metric">–</strong></span>
      <span>Map points: <strong id="points-metric" data-points="">–</strong></span>
      <span id="path-metric" data-path-length="0" data-has-path="false">Path length: –</span>
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
      <div class="goals">
        <button type="button" data-goal="open" class="active">Open goal</button>
        <button type="button" data-goal="around">Around goal</button>
        <button type="button" data-goal="shadow">Shadow goal</button>
      </div>
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
    <footer class="footer" id="report-footer">Loading report…</footer>
  `;

  const depthCanvas = root.querySelector<HTMLCanvasElement>("#depth-canvas")!;
  const pointsCanvas = root.querySelector<HTMLCanvasElement>("#points-canvas")!;
  const occCanvas = root.querySelector<HTMLCanvasElement>("#occ-canvas")!;
  const occupiedEl = root.querySelector<HTMLElement>("#occupied-metric")!;
  const pointsEl = root.querySelector<HTMLElement>("#points-metric")!;
  const pathEl = root.querySelector<HTMLElement>("#path-metric")!;
  const footerEl = root.querySelector<HTMLElement>("#report-footer")!;
  const noiseInput = root.querySelector<HTMLInputElement>("#noise")!;
  const zminInput = root.querySelector<HTMLInputElement>("#zmin")!;
  const zmaxInput = root.querySelector<HTMLInputElement>("#zmax")!;

  const recompute = (): void => {
    const state = runPipeline(opts);
    drawDepth(depthCanvas, state.depth, W, H);
    depthCanvas.style.width = "320px";
    depthCanvas.style.height = "240px";
    depthCanvas.style.imageRendering = "pixelated";
    drawTopDown(pointsCanvas, state.mapPoints, state.path);
    drawOccupancy(occCanvas, state.occupancy, state.path);

    occupiedEl.textContent = String(state.counts.occupied);
    occupiedEl.dataset.occupied = String(state.counts.occupied);
    pointsEl.textContent = String(state.mapPoints.length);
    pointsEl.dataset.points = String(state.mapPoints.length);

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

  const base = import.meta.env.BASE_URL;
  fetch(`${base}report.json`)
    .then((r) => r.json())
    .then((rep: { git_sha: string; sample: boolean }) => {
      const short = rep.git_sha.slice(0, 7);
      footerEl.textContent = `Build ${short} · sample=${rep.sample}`;
    })
    .catch(() => {
      footerEl.textContent = "report.json unavailable (run build)";
    });

  recompute();
}
