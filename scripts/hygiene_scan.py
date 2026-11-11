# SPDX-License-Identifier: Apache-2.0
"""Repository hygiene scan (criterion 13). Exit 0 clean, 1 match, 2 error."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

# Unicode long dash / minus (not expressible in git grep -P on all runners).
UNICODE_DASHES = ("\u2014", "\u2013", "\u2212")

EXCLUDE_RE = re.compile(
    r"^\.github/workflows/ci\.yml$|"
    r"scripts/check_authorship\.py$|"
    r"package-lock\.json$|"
    r"\.png$|^LICENSE$|"
    r"tests/fixtures/hygiene_trap\.txt$"
)

TRAP_MARKER = "SHOULD_FAIL_HYGIENE_FIXTURE"


def tracked_files(repo_root: Path) -> list[str]:
    out = subprocess.check_output(["git", "ls-files"], cwd=repo_root, text=True)
    files: list[str] = []
    for line in out.splitlines():
        if line and not EXCLUDE_RE.search(line):
            files.append(line)
    return files


def _compile_pattern(pattern: str) -> re.Pattern[str]:
    if pattern.startswith("(?i)"):
        return re.compile(pattern)
    return re.compile(f"(?i){pattern}")


def _line_matches(pattern: re.Pattern[str], line: str) -> bool:
    if pattern.search(line):
        return True
    return any(ch in line for ch in UNICODE_DASHES)


def _scan_file_unicode(repo_root: Path, path: str, pattern: re.Pattern[str]) -> list[str]:
    hits: list[str] = []
    full = repo_root / path
    try:
        text = full.read_text(encoding="utf-8", errors="surrogateescape")
    except OSError as exc:
        raise RuntimeError(f"read {path}: {exc}") from exc
    for line_no, line in enumerate(text.splitlines(), start=1):
        if _line_matches(pattern, line):
            hits.append(f"{path}:{line_no}:hygiene")
    return hits


def scan_paths(repo_root: Path, paths: list[str], pattern: str) -> int:
    if not paths:
        return 0
    compiled = _compile_pattern(pattern)
    grep_pat = pattern if pattern.startswith("(?i)") else f"(?i){pattern}"
    cmd = ["git", "grep", "-P", "-i", "-n", grep_pat, "--"]
    cmd.extend(paths)
    proc = subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True)
    if proc.returncode not in (0, 1):
        sys.stderr.write(proc.stderr or f"git grep failed ({proc.returncode})\n")
        return 2
    hits: list[str] = []
    if proc.returncode == 0 and proc.stdout:
        hits.extend(proc.stdout.strip().splitlines())
    for path in paths:
        hits.extend(_scan_file_unicode(repo_root, path, compiled))
    if hits:
        sys.stdout.write("\n".join(hits) + "\n")
        return 1
    return 0


def scan_trap(repo_root: Path, pattern: str) -> int:
    trap = repo_root / "tests/fixtures/hygiene_trap.txt"
    compiled = _compile_pattern(pattern)
    missed: list[str] = []
    for line_no, line in enumerate(trap.read_text(encoding="utf-8").splitlines(), start=1):
        if TRAP_MARKER in line:
            continue
        if not line.strip():
            continue
        if not _line_matches(compiled, line):
            missed.append(f"line {line_no}: {line[:60]!r}")
    if missed:
        sys.stderr.write("trap lines without pattern hits:\n")
        for m in missed:
            sys.stderr.write(f"  {m}\n")
        return 2
    return 1


def pattern_from_env() -> str:
    raw = os.environ.get("HYGIENE_PATTERN", "").strip()
    if not raw:
        raise SystemExit("HYGIENE_PATTERN unset (see .github/workflows/ci.yml)")
    return raw


def main() -> None:
    repo = Path(".").resolve()
    pattern = pattern_from_env()
    if len(sys.argv) >= 2 and sys.argv[1] == "--trap":
        raise SystemExit(scan_trap(repo, pattern))
    files = tracked_files(repo)
    raise SystemExit(scan_paths(repo, files, pattern))


if __name__ == "__main__":
    main()
