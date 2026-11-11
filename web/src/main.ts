// SPDX-License-Identifier: Apache-2.0

import "./style.css";
import { initApp } from "./ui.ts";

const root = document.querySelector<HTMLElement>("#app");
if (root) {
  initApp(root);
}
