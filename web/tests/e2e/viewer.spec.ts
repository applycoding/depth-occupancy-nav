// SPDX-License-Identifier: Apache-2.0

import { test, expect } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DEPTH_VARIANCE_MIN = 50;

test.describe("viewer (criterion 16)", () => {
  test("honesty labels and non-flat canvases", async ({ page }) => {
    await page.goto("./");
    await expect(page.locator("text=simulation only")).toBeVisible();
    await expect(page.locator("text=synthetic depth")).toBeVisible();

    const depth = page.locator("#depth-canvas");
    const occ = page.locator("#occ-canvas");
    await expect(depth).toBeVisible();

    const depthVar = await depth.evaluate((canvas: HTMLCanvasElement) => {
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
    });
    expect(depthVar).toBeGreaterThan(DEPTH_VARIANCE_MIN);

    const occVar = await occ.evaluate((canvas: HTMLCanvasElement) => {
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
    });
    expect(occVar).toBeGreaterThan(DEPTH_VARIANCE_MIN);
  });

  test("default data-occupied from grid", async ({ page }) => {
    await page.goto("./");
    const metric = page.locator("#occupied-metric");
    await expect(metric).toHaveAttribute("data-occupied", "22");
    await expect(metric).toHaveText("22");
  });

  test("around path length 51 and screenshot", async ({ page }) => {
    await page.goto("./");
    await page.getByRole("button", { name: "Around goal" }).click();
    const pathMetric = page.locator("#path-metric");
    await expect(pathMetric).toHaveAttribute("data-path-length", "51");
    await expect(pathMetric).toHaveAttribute("data-has-path", "true");

    const demoPath = path.resolve(__dirname, "../../../docs/demo.png");
    await page.screenshot({ path: demoPath, fullPage: true });
  });

  test("shadow goal reports no path", async ({ page }) => {
    await page.goto("./");
    await page.getByRole("button", { name: "Shadow goal" }).click();
    const pathMetric = page.locator("#path-metric");
    await expect(pathMetric).toHaveAttribute("data-has-path", "false");
    await expect(pathMetric).toContainText("No path");
  });

  test("sliders change occupied count and occupancy canvas", async ({ page }) => {
    await page.goto("./");
    const metric = page.locator("#occupied-metric");
    await expect(metric).toHaveAttribute("data-occupied", "22");

    const occ = page.locator("#occ-canvas");
    const before = await occ.screenshot();

    await page.locator("#noise").evaluate((el: HTMLInputElement) => {
      el.value = "1";
      el.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await expect(metric).not.toHaveAttribute("data-occupied", "22");

    const afterNoise = await occ.screenshot();
    expect(afterNoise.equals(before)).toBe(false);

    await page.goto("./");
    await page.locator("#zmin").evaluate((el: HTMLInputElement) => {
      el.value = "1";
      el.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await expect(metric).not.toHaveAttribute("data-occupied", "22");
    await expect(metric).toHaveAttribute("data-occupied", "10");
  });
});
