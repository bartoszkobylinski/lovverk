# lovverk

lovverk is a Git-versioned Markdown corpus of current Norwegian laws and central regulations, generated from Lovdata's public-data API by the open-source [`lovspor`](https://github.com/bartoszkobylinski/lovspor) engine. It is intended for AI/RAG ingestion, legal research, change tracking, and MCP-based access from assistants such as Claude. It is an unofficial derivative and does not replace Lovdata.

## What this repository is

- Every current Norwegian **lov** (law) and **sentral forskrift** (central regulation) as one Markdown file with YAML front matter — the **Published Rendering** of the source document, deterministically rendered from Lovdata's XML.
- Every change in the source data lands as a Git commit. This repository's Git history is the authoritative record of **published corpus states** — what the corpus said, and when. It is not an authoritative record of Norwegian law; for legal content, Lovdata is authoritative.
- Per-document change history, per-section embedding vectors, and dataset indexes are published alongside the documents.

This repository contains only generated artifacts and control metadata. The code that produces it — ingestion, rendering, sync, embedding generation, search, and the MCP server — lives in `lovspor`. There is no application code here, and nothing here is written by hand.

**Production.** Auto-synced daily at 04:00 UTC. The corpus tracks every current *lov* and *sentral forskrift* — 5,880 documents (759 lover + 5,121 sentrale forskrifter) as of 2026-08-04. Counts change daily; each dataset's `INDEX.md` carries its live count, and `manifest.json` is the authoritative statement of current corpus membership.

## Repository contents

```
lovverk/
├── lover/                          # current Norwegian laws
│   ├── INDEX.md                    # generated index of current acts (live count)
│   ├── <slug>.md                   # one document per act: the Published Rendering
│   ├── history/<slug>.json         # per-document change history — structured source of truth
│   ├── history/<slug>.md           # the same history as a human-readable derived view
│   └── embeddings/<slug>.bin       # per-section embedding vectors (LSPE v1, int8-quantized)
├── forskrifter/                    # current central regulations (same layout)
└── manifest.json                   # authoritative corpus membership + per-document metadata
```

- **`<slug>.md`** — the rendered legal text with YAML front matter (identity, title, retrieval provenance, EU/EEA basis, NLOD attribution).
- **`history/<slug>.json`** — structured per-document event history (added / updated / renamed / removed, with dates and commits). The structured source of truth for generated history.
- **`history/<slug>.md`** — a human-readable view derived from the JSON. If they ever disagree, the JSON wins.
- **`embeddings/<slug>.bin`** — per-section vectors for semantic search. Derived artifacts, regenerable from the Markdown; never a legal source.
- **`manifest.json`** — one record per document; see below.
- History files for repealed documents are deliberately kept: they are the audit trail that an act existed and was removed.

## Authority and versioning

Four things are authoritative for four different questions, and they do not substitute for each other:

- **Lovdata** is authoritative for Norwegian legal source text.
- **This repository's Git history** is authoritative for published corpus states — it is the corpus's version store, not housekeeping. Historical states are intentionally retained, `lovspor`'s temporal tools (`get_law_at`, `list_law_versions`, `diff_law_versions`) answer directly from it, and canonical history is never force-pushed or rewritten; doing so would break the version model, so recovery from a bad sync is `git revert`, never a rewrite. The generated `history/` files are derived projections of this history, convenient to read but never a replacement for it.
- **`manifest.json`** is authoritative for current corpus membership and per-document control metadata. File presence alone never determines membership.
- **The Published Renderings** are evidence of what this project published — a lossy, unofficial derivative, not canonical legal text.

Nothing derived — an embedding, a search result, a rendered Markdown file, a manifest field — independently establishes what the law legally means.

## Manifest

`manifest.json` holds one record per document, current and removed. The fields that matter most to a consumer:

- **`status`** — `"current"` or `"removed"`. A removed record is a **tombstone**: the document's identity, path, title and source hash are preserved, `removed_reason` says why (`null` = it left the upstream dataset; `"upstream_placeholder"` = Lovdata still lists it but serves an error notice instead of legal text, so the corpus withholds it), and its history files remain on disk as the audit trail. Tombstones are not current, searchable legal documents.
- **`xml_hash`** — SHA-256 of the document's *normalized source XML*. Change detection keys on this hash, never on the rendered Markdown.
- **`renderer_version`** — which renderer produced the on-disk Markdown bytes.
- **`embedding_hash`** — the `xml_hash` the document's `.bin` was built from; a mismatch means the vectors are stale and get rebuilt on the next keyed sync.
- **`embedding_space`** / **`embedding_space_id`** — the Embedding Space Identity of the sidecar (see below).

The full schema with exact semantics is documented in [`lovspor/docs/data-model.md`](https://github.com/bartoszkobylinski/lovspor/blob/main/docs/data-model.md).

## Embeddings and ESI

Each document carries a binary sidecar `embeddings/<slug>.bin` in the **LSPE v1** format: a 16-byte header (magic `LSPE`, version 1, section count, dimension, dequantization scale) followed by one int8-quantized 3072-dimensional vector per `§` section of the act, keyed by section id. Long sections are stored as several chunk records under one id. A document whose rendering yields no embeddable sections legitimately has a header-only sidecar with zero vectors.

**ESI (Embedding Space Identity)** identifies the embedding configuration — provider, model, dimension, endpoint — that produced a corpus artifact. Semantic consumers must only compare query and corpus vectors that belong to the same embedding space: cosine similarity across two spaces returns confident-looking nonsense, not an error. The `lovspor` engine enforces this — its `semantic_search` refuses documents whose recorded identity differs from, or is unknown to, the configured embedder, and reports every exclusion.

Two facts about where identity lives, and they are load-bearing:

- **The LSPE v1 sidecar carries no identity.** A `.bin` read on its own cannot tell you which model produced it.
- **Identity is recorded in the manifest** (`embedding_space` + `embedding_space_id`), stamped at generation time by the embedder that actually produced the vectors. This manifest-mediated model is ADR-0005 **Stage 1**, live in the current corpus: every current record carries its recorded identity, and new or changed documents receive theirs through the normal daily sync.

The exact identity definition, canonical serialization, and compatibility rules are owned by [`lovspor/docs/embeddings.md`](https://github.com/bartoszkobylinski/lovspor/blob/main/docs/embeddings.md).

## Using the corpus

**Direct use** — clone the repository and read it. The Markdown is plain text with YAML front matter; `git log --follow` on any file is that act's publication history; `manifest.json` tells you what is current.

**Programmatic / search / MCP use** — use the `lovspor` engine (Python, [on PyPI](https://pypi.org/project/lovspor/)); it handles corpus parsing, semantic-compatibility enforcement, temporal retrieval, quote verification, and serves it all over MCP:

```bash
uvx lovspor fetch-corpus     # clone the corpus to the local cache
claude mcp add lovverk -- uvx lovspor mcp
```

Sixteen read-only tools: search (keyword and semantic), section-level retrieval, per-act history, point-in-time text, diffs, citation validation, and verbatim-quote verification. See [`lovspor/docs/mcp.md`](https://github.com/bartoszkobylinski/lovspor/blob/main/docs/mcp.md). Semantic search additionally needs an operator-supplied OpenAI key; everything else runs fully local.

What you should **not** infer from this corpus: that a rule does not exist because it is absent here (the corpus covers acts and central regulations only — no circulars, court practice, forarbeider, or municipal regulations); that a retrieval hit answers a legal question (it locates text, nothing more); or that historical corpus states describe when a provision was legally in force (Git history records what the *corpus* held on a date — corpus-retrieval time, not legal-validity time).

## How updates work

The `lovspor` engine runs on a daily schedule. It downloads the current tarballs from Lovdata's public-data API, normalizes and hashes each document's XML, compares against `manifest.json`, and commits only documents whose source content changed — one commit per changed document, plus index/manifest bookkeeping. Renderer-only migrations are committed under `migration:` subjects and are deliberately excluded from per-document change history.

## Verification and reproducibility

Every document records the SHA-256 of its normalized source XML in `manifest.json`, and every published state of the corpus is a Git commit. You can verify:

- integrity of the corpus against its own manifest (paths, hashes, membership);
- the full provenance of any line of any document via `git log` / `git blame`;
- the upstream source itself, by downloading the same public tarballs from `https://api.lovdata.no/v1/publicData/get/`;
- the rendering end-to-end: the engine is public and MIT-licensed, so a third party can obtain the upstream data, run `lovspor` independently, and compare the generated artifacts and hashes against this repository. Rendering is deterministic — same source in, identical bytes out.

## Relationship to lovspor

[`lovspor`](https://github.com/bartoszkobylinski/lovspor) (public, MIT) is the engine; `lovverk` (this repository) is its published output. The only write path into this repository is the engine's scheduled sync. Consuming the corpus never requires the engine — a clone plus `manifest.json` is a complete, self-describing dataset — but everything programmatic (search, MCP, temporal tools, verification) lives on the engine side.

## Source and attribution

Data source: Lovdata public-data API
- `https://api.lovdata.no/v1/publicData/get/gjeldende-lover.tar.bz2`
- `https://api.lovdata.no/v1/publicData/get/gjeldende-sentrale-forskrifter.tar.bz2`

> Contains data under the Norwegian licence for Open Government data (NLOD) 2.0, distributed by Lovdata. The data has been converted to Markdown by the [lovspor](https://github.com/bartoszkobylinski/lovspor) project.

License: [NLOD 2.0](https://data.norge.no/nlod/no/2.0/) for the derived legal text (including the generated history files), [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) for the repository structure, manifest schema and README. See [LICENSE](LICENSE).

## Limitations

This is a generated corpus and tooling project. Source fidelity and retrieval correctness are engineering properties, not legal advice — anyone needing authoritative legal interpretation should verify against [Lovdata](https://lovdata.no/) and qualified counsel. This project is not affiliated with Lovdata.
