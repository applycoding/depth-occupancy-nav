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
ALLOWLIST_PATH = Path(".github/legacy-trailer-shas.txt")


def _commit_body(sha: str, *, cwd: Path | None = None) -> str:
    return subprocess.check_output(
        ["git", "show", "-s", "--format=%B", sha], text=True, cwd=cwd
    )


def _commit_meta(sha: str, *, cwd: Path | None = None) -> tuple[str, str, str, str]:
    raw = subprocess.check_output(
        ["git", "show", "-s", "--format=%an%x00%ae%x00%cn%x00%ce", sha],
        text=True,
        cwd=cwd,
    )
    parts = raw.rstrip("\n").split("\0")
    if len(parts) != 4:
        raise SystemExit(f"bad meta for {sha}")
    return parts[0], parts[1], parts[2], parts[3]


def check_commit(sha: str, *, check_trailers: bool, cwd: Path | None = None) -> None:
    an, ae, cn, ce = _commit_meta(sha, cwd=cwd)
    if an != AUTHOR_NAME or ae != AUTHOR_EMAIL:
        raise SystemExit(f"bad author on {sha}: {an!r} {ae!r}")
    if cn != AUTHOR_NAME or ce != AUTHOR_EMAIL:
        raise SystemExit(f"bad committer on {sha}: {cn!r} {ce!r}")
    if not check_trailers:
        return
    body = _commit_body(sha, cwd=cwd)
    if CO_AUTHORED.search(body):
        raise SystemExit(f"co-authored trailer on {sha}")
    try:
        trailers = subprocess.check_output(
            ["git", "interpret-trailers", "--parse", "--no-divider"],
            input=body,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        trailers = ""
    if trailers.strip():
        raise SystemExit(f"git trailer on {sha}: {trailers.strip().splitlines()[0]}")


def rev_list(spec: str, *, cwd: Path | None = None) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "rev-list", spec], text=True, cwd=cwd
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"invalid rev-list {spec!r}: {exc}") from exc
    return out.splitlines() if out else []


def load_allowlist() -> set[str]:
    if not ALLOWLIST_PATH.is_file():
        raise SystemExit(f"missing allowlist {ALLOWLIST_PATH}")
    shas: set[str] = set()
    for line in ALLOWLIST_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            shas.add(line)
    if len(shas) != 33:
        raise SystemExit(f"allowlist must have 33 SHAs, found {len(shas)}")
    return shas


def check_push(*, cwd: Path | None = None) -> None:
    for sha in rev_list("HEAD", cwd=cwd):
        check_commit(sha, check_trailers=True, cwd=cwd)
    print("authorship ok mode=push")


def check_pr(head_sha: str, *, cwd: Path | None = None) -> None:
    allowlist = load_allowlist()
    spec = f"origin/main..{head_sha}"
    for sha in rev_list(spec, cwd=cwd):
        exempt = sha in allowlist
        check_commit(sha, check_trailers=not exempt, cwd=cwd)
    print("authorship ok", f"mode=pr range={spec}")


def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        env = {
            "GIT_AUTHOR_NAME": AUTHOR_NAME,
            "GIT_AUTHOR_EMAIL": AUTHOR_EMAIL,
            "GIT_COMMITTER_NAME": AUTHOR_NAME,
            "GIT_COMMITTER_EMAIL": AUTHOR_EMAIL,
        }
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
        good = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True
        ).strip()
        check_commit(good, check_trailers=True, cwd=repo)

        tree = subprocess.check_output(["git", "write-tree"], cwd=repo, text=True).strip()
        trailer_line = "Co-authored" + "-by: x <x@y.com>"
        bad_trailer = subprocess.check_output(
            ["git", "commit-tree", tree, "-p", good],
            cwd=repo,
            input=f"bad trailer\n\n{trailer_line}\n",
            text=True,
            env=env,
        ).strip()
        try:
            check_commit(bad_trailer, check_trailers=True, cwd=repo)
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
        bad_committer = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True
        ).strip()
        try:
            check_commit(bad_committer, check_trailers=True, cwd=repo)
        except SystemExit:
            pass
        else:
            raise SystemExit("self-test: expected bad committer rejection")

        push_repo = Path(td) / "push_repo"
        push_repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=push_repo, check=True)
        subprocess.run(["git", "config", "user.email", AUTHOR_EMAIL], cwd=push_repo, check=True)
        subprocess.run(["git", "config", "user.name", AUTHOR_NAME], cwd=push_repo, check=True)
        for msg in ("push one", "push two"):
            (push_repo / "g").write_text(msg + "\n", encoding="utf-8")
            subprocess.run(["git", "add", "g"], cwd=push_repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", msg, "--author", f"{AUTHOR_NAME} <{AUTHOR_EMAIL}>"],
                cwd=push_repo,
                check=True,
                env=env,
            )
        check_push(cwd=push_repo)
        parent = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=push_repo, text=True
        ).strip()
        tree2 = subprocess.check_output(["git", "write-tree"], cwd=push_repo, text=True).strip()
        bad = subprocess.check_output(
            ["git", "commit-tree", tree2, "-p", parent],
            cwd=push_repo,
            input=f"bad\n\n{trailer_line}\n",
            text=True,
            env=env,
        ).strip()
        subprocess.run(["git", "reset", "--hard", bad], cwd=push_repo, check=True)
        try:
            check_push(cwd=push_repo)
        except SystemExit:
            pass
        else:
            raise SystemExit("self-test: push mode expected trailer rejection")

    print("authorship self-test ok")


def squash_sim() -> None:
    """Simulate post-merge squash on main without build/v1: push mode must pass."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        env = {
            "GIT_AUTHOR_NAME": AUTHOR_NAME,
            "GIT_AUTHOR_EMAIL": AUTHOR_EMAIL,
            "GIT_COMMITTER_NAME": AUTHOR_NAME,
            "GIT_COMMITTER_EMAIL": AUTHOR_EMAIL,
        }
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", AUTHOR_EMAIL], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", AUTHOR_NAME], cwd=repo, check=True)
        subprocess.run(["git", "checkout", "-qb", "main"], cwd=repo, check=True)
        (repo / "README").write_text("main\n", encoding="utf-8")
        subprocess.run(["git", "add", "README"], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "main seed"],
            cwd=repo,
            check=True,
            env=env,
        )
        subprocess.run(["git", "checkout", "-b", "build_v1"], cwd=repo, check=True)
        (repo / "pkg").write_text("feature\n", encoding="utf-8")
        subprocess.run(["git", "add", "pkg"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "feature"], cwd=repo, check=True, env=env)
        subprocess.run(["git", "checkout", "main"], cwd=repo, check=True)
        subprocess.run(
            ["git", "merge", "--squash", "build_v1"],
            cwd=repo,
            check=True,
            env=env,
        )
        subprocess.run(["git", "commit", "-qm", "squashed merge"], cwd=repo, check=True, env=env)
        subprocess.run(["git", "branch", "-D", "build_v1"], cwd=repo, check=True)
        check_push(cwd=repo)
    print("squash-sim ok")


def main() -> None:
    if "--self-test" in sys.argv:
        self_test()
        return
    if "--squash-sim" in sys.argv:
        squash_sim()
        return
    if len(sys.argv) == 2 and sys.argv[1] == "push":
        check_push()
        return
    if len(sys.argv) == 3 and sys.argv[1] == "pr":
        check_pr(sys.argv[2])
        return
    raise SystemExit(
        "usage: check_authorship.py --self-test | --squash-sim | push | pr <head-sha>"
    )


if __name__ == "__main__":
    main()
