"""Check that no change writes both the Lovdata datasets and the local one.

ADR-0016 Decision 4a gives each dataset exactly one writer: the daily Lovdata
sync owns ``manifest.json``, ``lover/`` and ``forskrifter/``; local-regulation
promotion owns ``lokale-forskrifter/`` and never touches the rest. A change
that crosses that line is how a local record ends up in the root manifest —
and an engine already installed from PyPI raises on any ``source_dataset`` it
does not know, so that one change would break search for every existing user.

The check is therefore on the diff, not on the tree: for every non-merge
commit in ``BASE..HEAD`` (and, with ``--aggregate``, for the range as a whole,
as a pull request is reviewed), a change that touches ``lokale-forskrifter/``
must leave the root ``manifest.json``, ``lover/`` and ``forskrifter/``
byte-identical.

Usage: check_dataset_separation.py BASE HEAD [--aggregate]
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_PREFIX = "lokale-forskrifter/"
CENTRAL_FILES = {"manifest.json"}
CENTRAL_PREFIXES = ("lover/", "forskrifter/")
NULL_SHA = "0" * 40


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
    return result.stdout


def is_commit(repo: Path, rev: str) -> bool:
    if not rev or rev == NULL_SHA:
        return False
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{rev}^{{commit}}"],
        cwd=repo,
        capture_output=True,
    )
    return result.returncode == 0


def changed_paths(repo: Path, old: str | None, new: str) -> list[str]:
    if old is None:
        output = git(repo, "diff-tree", "--root", "--no-commit-id", "-r", "--name-only", new)
    else:
        output = git(repo, "diff", "--name-only", old, new)
    return [line for line in output.splitlines() if line]


def crossing(paths: list[str]) -> tuple[list[str], list[str]]:
    """The central and local paths of a change, when it touches both."""
    local = [p for p in paths if p.startswith(LOCAL_PREFIX)]
    central = [p for p in paths if p in CENTRAL_FILES or p.startswith(CENTRAL_PREFIXES)]
    return (central, local) if local and central else ([], [])


def commits_in(repo: Path, base: str | None, head: str) -> list[str]:
    span = head if base is None else f"{base}..{head}"
    limit = ["-1"] if base is None else []
    return git(repo, "rev-list", "--no-merges", *limit, span).split()


def check(repo: Path, base: str, head: str, aggregate: bool = False) -> list[str]:
    # A new branch or a rewritten one has no usable base: check the head commit.
    start = base if is_commit(repo, base) else None
    problems: list[str] = []
    for commit in commits_in(repo, start, head):
        parent = f"{commit}^" if is_commit(repo, f"{commit}^") else None
        central, local = crossing(changed_paths(repo, parent, commit))
        if local:
            problems.append(
                f"commit {commit[:12]} touches {LOCAL_PREFIX} and the Lovdata "
                f"datasets: {central[:5]}"
            )
    if aggregate and start is not None:
        central, local = crossing(changed_paths(repo, start, head))
        if local:
            problems.append(
                f"{start[:12]}..{head[:12]} touches {LOCAL_PREFIX} and the "
                f"Lovdata datasets: {central[:5]}"
            )
    return problems


def main(argv: list[str]) -> int:
    args = [a for a in argv if a != "--aggregate"]
    if len(args) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    problems = check(REPO_ROOT, args[0], args[1], aggregate="--aggregate" in argv)
    if problems:
        print("DATASET SEPARATION FAILURE", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print("dataset separation holds: no change writes both datasets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
