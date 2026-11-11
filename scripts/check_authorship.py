# SPDX-License-Identifier: Apache-2.0
"""Verify commit authorship and detect git message trailers (CI gate)."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

AUTHOR_NAME = "Arpan Bom"
AUTHOR_EMAIL = "applycoding@gmail.com"
CO_AUTHORED = re.compile(r"(?im)^co-authored-by:")
TRAILER_BASE = "5fcad2927246fa08150c0db116438e3c9f20a0d3"


def _commit_body(sha: str) -> str:
    return subprocess.check_output(["git", "show", "-s", "--format=%B", sha], text=True)


def _commit_meta(sha: str) -> tuple[str, str, str, str]:
    raw = subprocess.check_output(
        ["git", "show", "-s", "--format=%an%x00%ae%x00%cn%x00%ce", sha],
        text=True,
    )
    parts = raw.rstrip("\n").split("\0")
    if len(parts) != 4:
        raise SystemExit(f"bad meta for {sha}")
    return parts[0], parts[1], parts[2], parts[3]


def check_commit(sha: str, *, check_trailers: bool) -> None:
    an, ae, cn, ce = _commit_meta(sha)
    if an != AUTHOR_NAME or ae != AUTHOR_EMAIL:
        raise SystemExit(f"bad author on {sha}: {an!r} {ae!r}")
    if cn != AUTHOR_NAME or ce != AUTHOR_EMAIL:
        raise SystemExit(f"bad committer on {sha}: {cn!r} {ce!r}")
    body = _commit_body(sha)
    if check_trailers and CO_AUTHORED.search(body):
        raise SystemExit(f"co-authored trailer on {sha}")
    try:
        trailers = subprocess.check_output(
            ["git", "interpret-trailers", "--parse", "--no-divider"],
            input=body,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        trailers = ""
    if check_trailers and trailers.strip():
        raise SystemExit(f"git trailer on {sha}: {trailers.strip().splitlines()[0]}")


def rev_list(spec: str) -> list[str]:
    out = subprocess.check_output(["git", "rev-list", spec], text=True).strip()
    return out.splitlines() if out else []


def check_range(author_range: str, trailer_range: str) -> None:
    for sha in rev_list(author_range):
        is_new = sha in set(rev_list(trailer_range))
        check_commit(sha, check_trailers=is_new)
    print("authorship ok", f"author={author_range}", f"trailers={trailer_range}")


def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        env = {"GIT_AUTHOR_NAME": AUTHOR_NAME, "GIT_AUTHOR_EMAIL": AUTHOR_EMAIL}
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", AUTHOR_EMAIL], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", AUTHOR_NAME], cwd=repo, check=True)
        (repo / "f").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "f"], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "ok", "--author", f"{AUTHOR_NAME} <{AUTHOR_EMAIL}>"],
            cwd=repo,
            check=True,
            env=env,
        )
        good = rev_list("HEAD")[0]
        check_commit(good, check_trailers=True)

        (repo / "f").write_text("y\n", encoding="utf-8")
        subprocess.run(["git", "add", "f"], cwd=repo, check=True)
        bad_msg = "bad trailer\n\n" + "Co-authored" + "-by: x <x@y.com>"
        subprocess.run(
            [
                "git",
                "commit",
                "-qm",
                bad_msg,
                "--author",
                f"{AUTHOR_NAME} <{AUTHOR_EMAIL}>",
            ],
            cwd=repo,
            check=True,
            env=env,
        )
        bad_trailer = rev_list("HEAD")[0]
        try:
            check_commit(bad_trailer, check_trailers=True)
        except SystemExit:
            pass
        else:
            raise SystemExit("self-test: expected trailer rejection")

        (repo / "f").write_text("z\n", encoding="utf-8")
        subprocess.run(["git", "add", "f"], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "bad committer"],
            cwd=repo,
            check=True,
            env={**env, "GIT_COMMITTER_NAME": "Other", "GIT_COMMITTER_EMAIL": "o@e.com"},
        )
        bad_committer = rev_list("HEAD")[0]
        try:
            check_commit(bad_committer, check_trailers=True)
        except SystemExit:
            pass
        else:
            raise SystemExit("self-test: expected bad committer rejection")
    print("authorship self-test ok")


def main() -> None:
    if "--self-test" in sys.argv:
        self_test()
        return
    if len(sys.argv) != 3:
        raise SystemExit("usage: check_authorship.py <author-range> <trailer-range>")
    check_range(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
