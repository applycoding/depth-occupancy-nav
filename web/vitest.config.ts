// SPDX-License-Identifier: Apache-2.0
import { defineConfig } from "vitest/config";
import path from "node:path";

const root = import.meta.dirname ?? path.dirname(new URL(import.meta.url).pathname);

export default defineConfig({
  test: {
    include: ["tests/**/*.test.ts"],
  },
  resolve: {
    alias: {
      "@": path.resolve(root, "src"),
    },
  },
});
