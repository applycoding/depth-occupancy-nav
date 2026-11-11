# SPDX-License-Identifier: Apache-2.0
"""Fail if tracked source files lack SPDX-License-Identifier (criterion 19)."""

from __future__ import annotations

import subprocess
from pathlib import Path

SPDX = "SPDX-License-Identifier: Apache-2.0"
EXCLUDE_SUFFIX = {".png", ".json", ".lock"}
EXCLUDE_NAMES = {"LICENSE", "requirements.txt", "package-lock.json"}
SCAN_EXTS = {
    ".py",
    ".ts",
    ".tsx",
    ".html",
    ".yaml",
    ".yml",
    ".toml",
    ".cfg",
    ".sh",
    ".md",
    ".xml",
}


def tracked_files() -> list[Path]:
    out = subprocess.check_output(["git", "ls-files"], text=True)
    paths: list[Path] = []
    for line in out.splitlines():
        if not line or line in EXCLUDE_NAMES:
            continue
        p = Path(line)
        if p.suffix in EXCLUDE_SUFFIX:
            continue
        if p.suffix in SCAN_EXTS or p.name in {"NOTICE", "DEVIATIONS.md", "PLAN.md"}:
            paths.append(p)
    return paths


def test_spdx_headers_present() -> None:
    missing: list[str] = []
    for path in tracked_files():
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        head = "\n".join(text.splitlines()[:25])
        if SPDX not in head:
            missing.append(str(path))
    assert not missing, "missing SPDX header:\n" + "\n".join(missing)
