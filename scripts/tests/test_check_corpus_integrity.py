"""Integrity of both manifests against the tree, on small planted corpora."""

from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL = "lokale-forskrifter"


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def central_record(dataset: str, path: str, slug: str) -> dict:
    return {
        "doc_type": "lov" if dataset == "gjeldende-lover" else "forskrift",
        "markdown_path": path,
        "removed_reason": None,
        "slug": slug,
        "source_dataset": dataset,
        "status": "current",
        "xml_hash": "0" * 64,
    }


def local_record(authority_id: str, slug: str, authority_type: str = "kommune") -> dict:
    return {
        "authority_id": authority_id,
        "authority_type": authority_type,
        "content_hash": "c" * 64,
        "doc_type": "lokal-forskrift",
        "extractor_version": 1,
        "last_seen": "2026-10-03T00:00:00Z",
        "markdown_path": f"{LOCAL}/{authority_id}/{slug}.md",
        "removed_reason": None,
        "renderer_version": 1,
        "slug": slug,
        "source_dataset": "lokale-forskrifter",
        "status": "current",
        "title": "Forskrift om renovasjon",
        "version": 1,
    }


FRONT_MATTER = {
    "id": '"{doc_id}"',
    "slug": '"{slug}"',
    "type": '"lokal-forskrift"',
    "ref_id": '"forskrift/2019-12-12-2077"',
    "title": '"Forskrift om renovasjon"',
    "authority": '{{id: "{authority_id}", type: "kommune", name: "Oslo", klass_version: "2024"}}',
    "hjemmel": '["forurensningsloven § 30"]',
    "vedtatt": '"2019-12-12"',
    "vedtatt_av": '"Oslo bystyre"',
    "ikraft": '"2020-01-01"',
    "ikraft_text": "null",
    "version": "1",
    "content_hash": '"' + "c" * 64 + '"',
    "observed_at_first": '"2026-08-19T15:17:23Z"',
    "source_url": '"https://example.kommune.no/renovasjon"',
    "source_sha256": '"' + "b" * 64 + '"',
    "source_provider": '"Oslo kommune (observed)"',
    "source_license": '"åndsverkloven § 14"',
    "basis": '"observed"',
    "asserted": "false",
    "language": '"no"',
}


def local_document(doc_id: str, authority_id: str, slug: str, **overrides: str | None) -> str:
    fields = {**FRONT_MATTER, **overrides}
    lines = [
        f"{key}: {value.format(doc_id=doc_id, slug=slug, authority_id=authority_id)}"
        for key, value in fields.items()
        if value is not None
    ]
    return "---\n" + "\n".join(lines) + "\n---\n\n# Forskrift om renovasjon\n\n§ 1 Formål\n"


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    """A minimal valid corpus: one act, one regulation, an empty local dataset."""
    (tmp_path / "lover").mkdir()
    (tmp_path / "forskrifter").mkdir()
    (tmp_path / "lover" / "akt.md").write_text("# Akt\n", encoding="utf-8")
    (tmp_path / "lover" / "INDEX.md").write_text("# Index\n", encoding="utf-8")
    (tmp_path / "forskrifter" / "akt.md").write_text("# Akt\n", encoding="utf-8")
    write_json(
        tmp_path / "manifest.json",
        {
            "documents": {
                "nl-20000101-001": central_record("gjeldende-lover", "lover/akt.md", "akt"),
                "sf-20000101-0001": central_record(
                    "gjeldende-sentrale-forskrifter", "forskrifter/akt.md", "akt"
                ),
            },
            "generated_at": "2026-10-02T00:00:00Z",
            "version": 1,
        },
    )
    write_json(
        tmp_path / LOCAL / "manifest.json",
        {"documents": {}, "generated_at": None, "version": 1},
    )
    return tmp_path


def add_local(root: Path, doc_id: str, record: dict, text: str | None = None) -> None:
    manifest_path = root / LOCAL / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["documents"][doc_id] = record
    write_json(manifest_path, manifest)
    if text is None:
        text = local_document(doc_id, record["authority_id"], record["slug"])
    path = root / record["markdown_path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def problems_mentioning(problems: list[str], needle: str) -> list[str]:
    return [p for p in problems if needle in p]


def test_this_repository_passes(integrity: ModuleType) -> None:
    assert integrity.check(REPO_ROOT) == []


def test_shipped_local_manifest_is_empty_with_the_root_schema(integrity: ModuleType) -> None:
    local = integrity.load_manifest(REPO_ROOT / LOCAL / "manifest.json")
    root = integrity.load_manifest(REPO_ROOT / "manifest.json")
    assert local["documents"] == {}
    assert set(local) == set(root) == {"documents", "generated_at", "version"}
    assert local["version"] == root["version"] == 1


def test_empty_local_dataset_passes(integrity: ModuleType, corpus: Path) -> None:
    assert integrity.check(corpus) == []


def test_missing_local_manifest_fails(integrity: ModuleType, corpus: Path) -> None:
    (corpus / LOCAL / "manifest.json").unlink()
    assert problems_mentioning(integrity.check(corpus), f"{LOCAL}/manifest.json is missing")


def test_check_leaves_root_manifest_bytes_untouched(integrity: ModuleType, corpus: Path) -> None:
    before = (corpus / "manifest.json").read_bytes()
    add_local(corpus, "lk-0301-0123456789ab", local_record("0301", "renovasjon"))
    integrity.check(corpus)
    assert (corpus / "manifest.json").read_bytes() == before


def test_valid_local_document_passes(integrity: ModuleType, corpus: Path) -> None:
    add_local(corpus, "lk-0301-0123456789ab", local_record("0301", "renovasjon"))
    assert integrity.check(corpus) == []


def test_fylkeskommune_document_passes(integrity: ModuleType, corpus: Path) -> None:
    record = local_record("03", "renovasjon", authority_type="fylkeskommune")
    add_local(corpus, "lf-20191212-2077", record)
    assert integrity.check(corpus) == []


def test_same_slug_under_two_authorities_passes(integrity: ModuleType, corpus: Path) -> None:
    add_local(corpus, "lk-0301-0123456789ab", local_record("0301", "renovasjon"))
    add_local(corpus, "lk-4601-0123456789ab", local_record("4601", "renovasjon"))
    assert integrity.check(corpus) == []


def test_planted_orphan_fails(integrity: ModuleType, corpus: Path) -> None:
    orphan = corpus / LOCAL / "0301" / "ingen-post.md"
    orphan.parent.mkdir(parents=True)
    orphan.write_text(local_document("lk-0301-0123456789ab", "0301", "ingen-post"), "utf-8")
    problems = integrity.check(corpus)
    assert problems_mentioning(problems, "no current record claims")
    assert problems_mentioning(problems, f"{LOCAL}/0301/ingen-post.md")


def test_markdown_directly_under_dataset_is_an_orphan(integrity: ModuleType, corpus: Path) -> None:
    (corpus / LOCAL / "stray.md").write_text("# stray\n", encoding="utf-8")
    assert problems_mentioning(integrity.check(corpus), f"{LOCAL}/stray.md")


def test_index_and_history_markdown_are_not_documents(integrity: ModuleType, corpus: Path) -> None:
    (corpus / LOCAL / "INDEX.md").write_text("# Index\n", encoding="utf-8")
    add_local(corpus, "lk-0301-0123456789ab", local_record("0301", "renovasjon"))
    history = corpus / LOCAL / "0301" / "history" / "renovasjon.md"
    history.parent.mkdir()
    history.write_text("# History\n", encoding="utf-8")
    (corpus / LOCAL / "0301" / "INDEX.md").write_text("# Oslo\n", encoding="utf-8")
    assert integrity.check(corpus) == []


def test_missing_document_fails(integrity: ModuleType, corpus: Path) -> None:
    add_local(corpus, "lk-0301-0123456789ab", local_record("0301", "renovasjon"))
    (corpus / LOCAL / "0301" / "renovasjon.md").unlink()
    assert problems_mentioning(integrity.check(corpus), "missing from the tree")


def test_removed_document_still_on_disk_fails(integrity: ModuleType, corpus: Path) -> None:
    record = {**local_record("0301", "renovasjon"), "status": "removed"}
    record["removed_reason"] = "withdrawn_misclassified"
    add_local(corpus, "lk-0301-0123456789ab", record)
    assert problems_mentioning(integrity.check(corpus), "removed document(s) still on disk")


def test_duplicate_authority_and_slug_fails(integrity: ModuleType, corpus: Path) -> None:
    add_local(corpus, "lk-0301-0123456789ab", local_record("0301", "renovasjon"))
    add_local(corpus, "lk-0301-ba9876543210", local_record("0301", "renovasjon"))
    problems = integrity.check(corpus)
    assert problems_mentioning(problems, "(authority_id, slug) claimed by more than one record")


def test_wrong_path_layout_fails(integrity: ModuleType, corpus: Path) -> None:
    record = {**local_record("0301", "renovasjon"), "markdown_path": f"{LOCAL}/renovasjon.md"}
    add_local(corpus, "lk-0301-0123456789ab", record)
    assert problems_mentioning(integrity.check(corpus), "markdown_path must be")


def test_local_record_in_root_manifest_fails(integrity: ModuleType, corpus: Path) -> None:
    manifest = json.loads((corpus / "manifest.json").read_text(encoding="utf-8"))
    manifest["documents"]["lk-0301-0123456789ab"] = local_record("0301", "renovasjon")
    write_json(corpus / "manifest.json", manifest)
    assert problems_mentioning(integrity.check(corpus), "root manifest.json carries 1 local")


def test_id_in_both_manifests_fails(integrity: ModuleType, corpus: Path) -> None:
    manifest = json.loads((corpus / "manifest.json").read_text(encoding="utf-8"))
    manifest["documents"]["lf-20191212-2077"] = central_record(
        "gjeldende-sentrale-forskrifter", "forskrifter/annen.md", "annen"
    )
    write_json(corpus / "manifest.json", manifest)
    (corpus / "forskrifter" / "annen.md").write_text("# Annen\n", encoding="utf-8")
    add_local(corpus, "lf-20191212-2077", local_record("0301", "renovasjon"))
    assert problems_mentioning(integrity.check(corpus), "ids present in both manifests")


@pytest.mark.parametrize("doc_id", ["sf-20191212-2077", "lf-2019-12-12-2077", "lk-0301-XYZ"])
def test_malformed_local_id_fails(integrity: ModuleType, corpus: Path, doc_id: str) -> None:
    add_local(corpus, doc_id, local_record("0301", "renovasjon"))
    assert problems_mentioning(integrity.check(corpus), "is neither lf-")


def test_fallback_id_naming_another_authority_fails(integrity: ModuleType, corpus: Path) -> None:
    add_local(corpus, "lk-4601-0123456789ab", local_record("0301", "renovasjon"))
    assert problems_mentioning(integrity.check(corpus), "lk- id names a different authority")


@pytest.mark.parametrize(
    ("authority_id", "authority_type"),
    [("301", "kommune"), ("0301", "fylkeskommune"), ("0301", "bydel")],
)
def test_authority_id_must_match_type(
    integrity: ModuleType, corpus: Path, authority_id: str, authority_type: str
) -> None:
    record = local_record(authority_id, "renovasjon", authority_type=authority_type)
    add_local(corpus, "lf-20191212-2077", record)
    assert problems_mentioning(integrity.check(corpus), "does not match authority_type")


def test_record_with_xml_hash_fails(integrity: ModuleType, corpus: Path) -> None:
    record = {**local_record("0301", "renovasjon"), "xml_hash": "0" * 64}
    add_local(corpus, "lk-0301-0123456789ab", record)
    assert problems_mentioning(integrity.check(corpus), "has xml_hash")


def test_record_missing_field_fails(integrity: ModuleType, corpus: Path) -> None:
    record = local_record("0301", "renovasjon")
    del record["extractor_version"]
    add_local(corpus, "lk-0301-0123456789ab", record)
    assert problems_mentioning(integrity.check(corpus), "missing ['extractor_version']")


def test_record_with_central_dataset_fails(integrity: ModuleType, corpus: Path) -> None:
    record = {**local_record("0301", "renovasjon"), "source_dataset": "gjeldende-lover"}
    add_local(corpus, "lk-0301-0123456789ab", record)
    assert problems_mentioning(integrity.check(corpus), "must have doc_type")


@pytest.mark.parametrize(
    "case",
    [
        ("source_license", '"NLOD 2.0"', "source_license must be"),
        ("source_license", '"CC0 1.0"', "source_license must be"),
        ("basis", '"asserted"', "basis must be"),
        ("asserted", "true", "asserted must be false"),
        ("type", '"forskrift"', "type must be"),
        ("content_hash", '"' + "d" * 64 + '"', "content_hash disagrees"),
        ("version", "2", "version disagrees"),
        ("id", '"lk-0301-ffffffffffff"', "id disagrees"),
        ("authority", '{{id: "4601", type: "kommune"}}', "authority id disagrees"),
    ],
)
def test_front_matter_value_violations_fail(
    integrity: ModuleType, corpus: Path, case: tuple[str, str, str]
) -> None:
    key, value, needle = case
    doc_id = "lk-0301-0123456789ab"
    text = local_document(doc_id, "0301", "renovasjon", **{key: value})
    add_local(corpus, doc_id, local_record("0301", "renovasjon"), text)
    assert problems_mentioning(integrity.check(corpus), needle)


def test_front_matter_missing_field_fails(integrity: ModuleType, corpus: Path) -> None:
    doc_id = "lk-0301-0123456789ab"
    text = local_document(doc_id, "0301", "renovasjon", source_license=None)
    add_local(corpus, doc_id, local_record("0301", "renovasjon"), text)
    assert problems_mentioning(integrity.check(corpus), "front matter missing ['source_license']")


def test_front_matter_out_of_order_fails(integrity: ModuleType, corpus: Path) -> None:
    doc_id = "lk-0301-0123456789ab"
    text = local_document(doc_id, "0301", "renovasjon").replace(
        'id: "lk-0301-0123456789ab"\nslug: "renovasjon"',
        'slug: "renovasjon"\nid: "lk-0301-0123456789ab"',
    )
    add_local(corpus, doc_id, local_record("0301", "renovasjon"), text)
    assert problems_mentioning(integrity.check(corpus), "out of the fixed order")


@pytest.mark.parametrize("key", ["retrieved_at", "observed_at_last"])
def test_front_matter_forbidden_key_fails(integrity: ModuleType, corpus: Path, key: str) -> None:
    doc_id = "lk-0301-0123456789ab"
    text = local_document(doc_id, "0301", "renovasjon").replace(
        'language: "no"', f'language: "no"\n{key}: "2026-10-03T00:00:00Z"'
    )
    add_local(corpus, doc_id, local_record("0301", "renovasjon"), text)
    assert problems_mentioning(integrity.check(corpus), "forbidden key")


def test_block_style_authority_is_read(integrity: ModuleType, corpus: Path) -> None:
    doc_id = "lk-0301-0123456789ab"
    block = '\n  id: "0301"\n  type: "kommune"\n  name: "Oslo"\n  klass_version: "2024"'
    text = local_document(doc_id, "0301", "renovasjon", authority=block)
    text = text.replace("authority: \n", "authority:\n")
    add_local(corpus, doc_id, local_record("0301", "renovasjon"), text)
    assert integrity.check(corpus) == []


def test_document_without_front_matter_fails(integrity: ModuleType, corpus: Path) -> None:
    add_local(corpus, "lk-0301-0123456789ab", local_record("0301", "renovasjon"), "# Bare\n")
    assert problems_mentioning(integrity.check(corpus), "no front matter")


@pytest.mark.parametrize(
    "relative", ["0301/renovasjon.md", "0301/observations/renovasjon.json", "manifest.json"]
)
def test_any_nlod_mention_in_the_dataset_fails(
    integrity: ModuleType, corpus: Path, relative: str
) -> None:
    add_local(corpus, "lk-0301-0123456789ab", local_record("0301", "renovasjon"))
    path = corpus / LOCAL / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if relative.endswith(".json"):
        data = json.loads(existing) if existing else {}
        data["note"] = "Licensed under Nlod"
        write_json(path, data)
    else:
        path.write_text(existing + "\nNorsk lisens for offentlige data (NLOD)\n", "utf-8")
    assert problems_mentioning(integrity.check(corpus), "mention NLOD")


def test_main_exit_code_follows_problems(
    integrity: ModuleType, corpus: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(integrity, "REPO_ROOT", corpus)
    assert integrity.main() == 0
    (corpus / LOCAL / "stray.md").write_text("# stray\n", encoding="utf-8")
    assert integrity.main() == 1
