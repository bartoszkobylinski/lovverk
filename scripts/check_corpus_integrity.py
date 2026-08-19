"""Check that manifest.json and the files on disk still describe the same corpus.

This repository is written by a machine — lovspor renders the Markdown and
commits it — so the failure worth guarding against is not a typo but a drift:
a document the manifest promises and the tree does not carry, or a file left
behind after its record was retired. Anything reading this corpus (the lovverk
MCP server, anyone citing a law) trusts that the two agree.

Invariants, and one that deliberately is NOT one:

* every ``current`` record's ``markdown_path`` exists;
* every Markdown file under lover/ and forskrifter/ belongs to a ``current``
  record — except the generated INDEX.md files, which are navigation, not law;
* no ``removed`` record still has its file on disk;
* ``markdown_path`` is unique, and so is ``(source_dataset, slug)``.

**Slugs are not globally unique, and must not be made so.** `Bergverksordning
for Svalbard` exists twice from 1925 — once as an act, once as a regulation —
and both legitimately slug to `bergverksordning-for-svalbard` in their own
directories. A check that forbade that would be asserting something untrue
about Norwegian law.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIRS = ("lover", "forskrifter")
# Generated navigation files, not corpus documents.
NON_DOCUMENT_FILES = {"INDEX.md"}


def load_manifest(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "documents" not in data:
        raise SystemExit("manifest.json has no 'documents' key")
    return data


def markdown_files(root: Path) -> set[str]:
    found: set[str] = set()
    for directory in CORPUS_DIRS:
        for file in (root / directory).glob("*.md"):
            if file.name in NON_DOCUMENT_FILES:
                continue
            found.add(f"{directory}/{file.name}")
    return found


def check(root: Path) -> list[str]:
    manifest = load_manifest(root / "manifest.json")
    documents = manifest["documents"]
    current = {k: v for k, v in documents.items() if v.get("status") == "current"}
    removed = {k: v for k, v in documents.items() if v.get("status") == "removed"}

    on_disk = markdown_files(root)
    claimed = {v["markdown_path"] for v in current.values() if v.get("markdown_path")}
    problems: list[str] = []

    missing = sorted(claimed - on_disk)
    if missing:
        problems.append(
            f"{len(missing)} current document(s) missing from the tree: "
            f"{missing[:5]}"
        )

    orphans = sorted(on_disk - claimed)
    if orphans:
        problems.append(
            f"{len(orphans)} file(s) no current record claims: {orphans[:5]}"
        )

    resurrected = sorted(
        v["markdown_path"]
        for v in removed.values()
        if v.get("markdown_path") in on_disk
    )
    if resurrected:
        problems.append(
            f"{len(resurrected)} removed document(s) still on disk: "
            f"{resurrected[:5]}"
        )

    pathless = sorted(k for k, v in current.items() if not v.get("markdown_path"))
    if pathless:
        problems.append(f"{len(pathless)} current record(s) with no path: {pathless[:5]}")

    duplicate_paths = [
        path
        for path, count in Counter(
            v["markdown_path"] for v in current.values() if v.get("markdown_path")
        ).items()
        if count > 1
    ]
    if duplicate_paths:
        problems.append(f"paths claimed by more than one record: {duplicate_paths[:5]}")

    duplicate_keys = [
        key
        for key, count in Counter(
            (v.get("source_dataset"), v.get("slug")) for v in current.values()
        ).items()
        if count > 1
    ]
    if duplicate_keys:
        problems.append(
            f"(dataset, slug) claimed by more than one record: {duplicate_keys[:5]}"
        )

    print(
        f"manifest {manifest.get('version', '?')} generated "
        f"{manifest.get('generated_at', '?')}"
    )
    print(f"  current: {len(current)}  removed: {len(removed)}")
    print(f"  markdown files: {len(on_disk)}")
    return problems


def main() -> int:
    problems = check(REPO_ROOT)
    if problems:
        print("\nCORPUS INTEGRITY FAILURE", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print("  manifest and tree agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
