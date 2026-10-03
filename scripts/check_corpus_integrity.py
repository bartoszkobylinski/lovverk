"""Check that each manifest and the files on disk still describe the same corpus.

This repository is written by a machine — lovspor renders the Markdown and
commits it — so the failure worth guarding against is not a typo but a drift:
a document the manifest promises and the tree does not carry, or a file left
behind after its record was retired. Anything reading this corpus (the lovverk
MCP server, anyone citing a law) trusts that the two agree.

The corpus has two membership files (ADR-0016, option A2):

* the root ``manifest.json`` for the Lovdata datasets ``lover/`` and
  ``forskrifter/``;
* ``lokale-forskrifter/manifest.json`` for local regulations captured from
  municipal and county websites. They live in their own manifest so that an
  engine already installed from PyPI, which rejects any ``source_dataset`` it
  does not know, never sees them.

Invariants for both datasets:

* every ``current`` record's ``markdown_path`` exists;
* every document file belongs to a ``current`` record — except the generated
  INDEX.md files, which are navigation, not law;
* no ``removed`` record still has its file on disk;
* ``markdown_path`` is unique, and so is ``(source_dataset, slug)`` centrally
  and ``(authority_id, slug)`` locally.

Additional invariants for the local dataset:

* documents sit at ``lokale-forskrifter/<authority_id>/<slug>.md``;
* the root manifest carries no local record, and the two manifests share no id;
* every document's front matter has the fields ADR-0016 Decision 3 fixes, in
  that order, states ``source_license: "åndsverkloven § 14"``,
  ``basis: "observed"`` and ``asserted: false``, and agrees with its record;
* no file in the dataset mentions NLOD: these texts are not Lovdata data and
  are not published under Lovdata's licence.

**Slugs are not globally unique, and must not be made so.** `Bergverksordning
for Svalbard` exists twice from 1925 — once as an act, once as a regulation —
and both legitimately slug to `bergverksordning-for-svalbard` in their own
directories. A check that forbade that would be asserting something untrue
about Norwegian law. The same holds for two kommuner each enacting a
`renovasjonsforskrift`.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIRS = ("lover", "forskrifter")
LOCAL_DIR = "lokale-forskrifter"
LOCAL_DATASET = "lokale-forskrifter"
LOCAL_DOC_TYPE = "lokal-forskrift"
LOCAL_LICENSE = "åndsverkloven § 14"
# Generated navigation files, not corpus documents.
NON_DOCUMENT_FILES = {"INDEX.md"}

# ADR-0016 Decision 3: the front matter of a local document, in its fixed order.
LOCAL_FRONT_MATTER_KEYS = (
    "id",
    "slug",
    "type",
    "ref_id",
    "title",
    "authority",
    "hjemmel",
    "vedtatt",
    "vedtatt_av",
    "ikraft",
    "ikraft_text",
    "version",
    "content_hash",
    "observed_at_first",
    "source_url",
    "source_sha256",
    "source_provider",
    "source_license",
    "basis",
    "asserted",
    "language",
)
# `retrieved_at` is Lovdata download time; `observed_at_last` would churn the
# document on every observation. Neither belongs in a local document.
LOCAL_FORBIDDEN_KEYS = ("retrieved_at", "observed_at_last")
LOCAL_FIXED_VALUES = {
    "type": LOCAL_DOC_TYPE,
    "source_license": LOCAL_LICENSE,
    "basis": "observed",
    "asserted": False,
}
LOCAL_RECORD_FIELDS = (
    "doc_type",
    "source_dataset",
    "status",
    "slug",
    "title",
    "markdown_path",
    "renderer_version",
    "last_seen",
    "removed_reason",
    "authority_id",
    "authority_type",
    "content_hash",
    "version",
    "extractor_version",
)
# SSB KLASS codes as the observatory registry holds them: length is the type.
AUTHORITY_ID_PATTERN = {
    "kommune": re.compile(r"^\d{4}$"),
    "fylkeskommune": re.compile(r"^\d{2}$"),
}
LOCAL_ID_PATTERN = re.compile(r"^(lf-\d{8}-\d{4}|lk-(\d{4}|\d{2})-[0-9a-f]{12})$")
NLOD_PATTERN = re.compile(r"nlod", re.IGNORECASE)


def load_manifest(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("documents"), dict):
        raise SystemExit(f"{path.name} has no 'documents' object")
    return data


def markdown_files(root: Path) -> set[str]:
    found: set[str] = set()
    for directory in CORPUS_DIRS:
        for file in (root / directory).glob("*.md"):
            if file.name in NON_DOCUMENT_FILES:
                continue
            found.add(f"{directory}/{file.name}")
    return found


def local_markdown_files(root: Path) -> set[str]:
    """Document files of the local dataset: one level below the authority dir.

    Deeper Markdown (``history/<slug>.md``) is a derived view, not a document.
    Markdown directly under ``lokale-forskrifter/`` other than INDEX.md has no
    authority; it is collected anyway so that it surfaces as an orphan.
    """
    base = root / LOCAL_DIR
    found: set[str] = set()
    for pattern in ("*.md", "*/*.md"):
        for file in base.glob(pattern):
            if file.name not in NON_DOCUMENT_FILES:
                found.add(file.relative_to(root).as_posix())
    return found


def split_by_status(documents: dict) -> tuple[dict, dict]:
    current = {k: v for k, v in documents.items() if v.get("status") == "current"}
    removed = {k: v for k, v in documents.items() if v.get("status") == "removed"}
    return current, removed


def duplicates(values: Iterable) -> list:
    return [value for value, count in Counter(values).items() if count > 1]


def membership_problems(current: dict, removed: dict, on_disk: set[str]) -> list[str]:
    claimed = {v["markdown_path"] for v in current.values() if v.get("markdown_path")}
    problems: list[str] = []

    missing = sorted(claimed - on_disk)
    if missing:
        problems.append(f"{len(missing)} current document(s) missing from the tree: {missing[:5]}")

    orphans = sorted(on_disk - claimed)
    if orphans:
        problems.append(f"{len(orphans)} file(s) no current record claims: {orphans[:5]}")

    resurrected = sorted(
        v["markdown_path"] for v in removed.values() if v.get("markdown_path") in on_disk
    )
    if resurrected:
        problems.append(f"{len(resurrected)} removed document(s) still on disk: {resurrected[:5]}")

    pathless = sorted(k for k, v in current.items() if not v.get("markdown_path"))
    if pathless:
        problems.append(f"{len(pathless)} current record(s) with no path: {pathless[:5]}")

    duplicate_paths = duplicates(
        v["markdown_path"] for v in current.values() if v.get("markdown_path")
    )
    if duplicate_paths:
        problems.append(f"paths claimed by more than one record: {duplicate_paths[:5]}")
    return problems


def check_central(root: Path) -> tuple[dict, list[str]]:
    manifest = load_manifest(root / "manifest.json")
    documents = manifest["documents"]
    current, removed = split_by_status(documents)
    on_disk = markdown_files(root)
    problems = membership_problems(current, removed, on_disk)

    duplicate_keys = duplicates((v.get("source_dataset"), v.get("slug")) for v in current.values())
    if duplicate_keys:
        problems.append(f"(dataset, slug) claimed by more than one record: {duplicate_keys[:5]}")

    # An installed engine raises on any source_dataset it does not know, so a
    # local record in the root manifest breaks search for every existing user.
    leaked = sorted(
        k
        for k, v in documents.items()
        if v.get("source_dataset") == LOCAL_DATASET
        or v.get("doc_type") == LOCAL_DOC_TYPE
        or str(v.get("markdown_path") or "").startswith(f"{LOCAL_DIR}/")
    )
    if leaked:
        problems.append(
            f"root manifest.json carries {len(leaked)} local record(s); they "
            f"belong in {LOCAL_DIR}/manifest.json: {leaked[:5]}"
        )

    print(
        f"manifest.json {manifest.get('version', '?')} generated "
        f"{manifest.get('generated_at', '?')}"
    )
    print(f"  current: {len(current)}  removed: {len(removed)}")
    print(f"  markdown files: {len(on_disk)}")
    return manifest, problems


def parse_front_matter(text: str) -> tuple[list[str], dict[str, str]] | None:
    """Top-level keys (in order) and their raw values; None if there is none.

    Standard library only, so this is not a YAML parser: it reads the keys at
    column 0 and keeps each value's raw text, including indented continuation
    lines, which is all the checks below need.
    """
    lines = text.split("\n")
    if not lines or lines[0] != "---":
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None
    keys: list[str] = []
    raw: dict[str, str] = {}
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):(.*)$", line)
        if match:
            keys.append(match.group(1))
            raw[match.group(1)] = match.group(2).strip()
        elif keys and line.startswith((" ", "\t")):
            raw[keys[-1]] += "\n" + line
    return keys, raw


def scalar(raw: str) -> object:
    """A front-matter scalar as JSON reads it (quoted string, number, bool,
    null), else the raw text, which then never equals an expected value."""
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def authority_id_in(raw: str) -> str | None:
    """The ``id`` of an authority mapping, in flow or block style."""
    match = re.search(r"(?:^|[{,\s])id:\s*\"?([0-9]+)\"?", raw)
    return match.group(1) if match else None


def front_matter_problems(path: str, text: str, doc_id: str, record: dict) -> list[str]:
    parsed = parse_front_matter(text)
    if parsed is None:
        return [f"{path}: no front matter"]
    keys, raw = parsed
    problems: list[str] = []

    missing = [k for k in LOCAL_FRONT_MATTER_KEYS if k not in raw]
    if missing:
        problems.append(f"{path}: front matter missing {missing}")
    elif [k for k in keys if k in LOCAL_FRONT_MATTER_KEYS] != list(LOCAL_FRONT_MATTER_KEYS):
        problems.append(f"{path}: front matter keys out of the fixed order")
    forbidden = [k for k in LOCAL_FORBIDDEN_KEYS if k in raw]
    if forbidden:
        problems.append(f"{path}: front matter carries forbidden key(s) {forbidden}")

    for key, expected in LOCAL_FIXED_VALUES.items():
        if key in raw and scalar(raw[key]) != expected:
            shown = json.dumps(expected, ensure_ascii=False)
            problems.append(f"{path}: {key} must be {shown}")

    expected_values = {
        "id": doc_id,
        "slug": record.get("slug"),
        "content_hash": record.get("content_hash"),
        "version": record.get("version"),
    }
    for key, expected in expected_values.items():
        if key in raw and scalar(raw[key]) != expected:
            problems.append(f"{path}: front matter {key} disagrees with the manifest")
    if "authority" in raw and authority_id_in(raw["authority"]) != record.get("authority_id"):
        problems.append(f"{path}: front matter authority id disagrees with the manifest")
    return problems


def local_record_problems(doc_id: str, record: dict) -> list[str]:
    problems: list[str] = []
    if not LOCAL_ID_PATTERN.match(doc_id):
        problems.append(
            f"local id {doc_id!r} is neither lf-yyyymmdd-nnnn nor lk-<authority_id>-<h12>"
        )
    missing = [f for f in LOCAL_RECORD_FIELDS if f not in record]
    if missing:
        problems.append(f"local record {doc_id} missing {missing}")
    if "xml_hash" in record:
        problems.append(f"local record {doc_id} has xml_hash; a local regulation has no XML")
    if record.get("doc_type") != LOCAL_DOC_TYPE or record.get("source_dataset") != LOCAL_DATASET:
        problems.append(
            f"local record {doc_id} must have doc_type {LOCAL_DOC_TYPE!r} "
            f"and source_dataset {LOCAL_DATASET!r}"
        )
    authority_id = str(record.get("authority_id"))
    pattern = AUTHORITY_ID_PATTERN.get(str(record.get("authority_type")))
    if pattern is None or not pattern.match(authority_id):
        problems.append(
            f"local record {doc_id}: authority_id {authority_id!r} does not match "
            f"authority_type {record.get('authority_type')!r}"
        )
    if doc_id.startswith("lk-") and not doc_id.startswith(f"lk-{authority_id}-"):
        problems.append(f"local record {doc_id}: lk- id names a different authority")
    expected_path = f"{LOCAL_DIR}/{authority_id}/{record.get('slug')}.md"
    if record.get("status") == "current" and record.get("markdown_path") != expected_path:
        problems.append(f"local record {doc_id}: markdown_path must be {expected_path}")
    return problems


def nlod_problems(root: Path) -> list[str]:
    hits = sorted(
        file.relative_to(root).as_posix()
        for file in (root / LOCAL_DIR).rglob("*")
        if file.is_file()
        and NLOD_PATTERN.search(file.read_text(encoding="utf-8", errors="replace"))
    )
    if hits:
        return [
            f"{len(hits)} file(s) in {LOCAL_DIR}/ mention NLOD; local regulations "
            f"are published on the basis of {LOCAL_LICENSE}, not NLOD: {hits[:5]}"
        ]
    return []


def check_local(root: Path, central_ids: set[str]) -> list[str]:
    manifest_path = root / LOCAL_DIR / "manifest.json"
    if not manifest_path.is_file():
        return [f"{LOCAL_DIR}/manifest.json is missing"]
    manifest = load_manifest(manifest_path)
    documents = manifest["documents"]
    current, removed = split_by_status(documents)
    on_disk = local_markdown_files(root)
    problems = membership_problems(current, removed, on_disk)

    duplicate_keys = duplicates((v.get("authority_id"), v.get("slug")) for v in current.values())
    if duplicate_keys:
        problems.append(
            f"(authority_id, slug) claimed by more than one record: {duplicate_keys[:5]}"
        )

    shared_ids = sorted(central_ids & set(documents))
    if shared_ids:
        problems.append(f"ids present in both manifests: {shared_ids[:5]}")

    for doc_id, record in documents.items():
        problems.extend(local_record_problems(doc_id, record))
    for doc_id, record in current.items():
        path = record.get("markdown_path")
        if path in on_disk:
            text = (root / path).read_text(encoding="utf-8")
            problems.extend(front_matter_problems(path, text, doc_id, record))
    problems.extend(nlod_problems(root))

    print(
        f"{LOCAL_DIR}/manifest.json {manifest.get('version', '?')} generated "
        f"{manifest.get('generated_at', '?')}"
    )
    print(f"  current: {len(current)}  removed: {len(removed)}")
    print(f"  markdown files: {len(on_disk)}")
    return problems


def check(root: Path) -> list[str]:
    central, problems = check_central(root)
    problems.extend(check_local(root, set(central["documents"])))
    return problems


def main() -> int:
    problems = check(REPO_ROOT)
    if problems:
        print("\nCORPUS INTEGRITY FAILURE", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print("  manifests and tree agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
