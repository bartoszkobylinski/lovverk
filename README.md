# lovverk

lovverk is a Git-versioned Markdown corpus of current Norwegian laws and central regulations, generated from Lovdata's public-data API by the `lovspor` engine. It is intended for AI/RAG ingestion, legal research, change tracking, and MCP-based access from assistants such as Claude. It is an unofficial derivative and does not replace Lovdata.

## What this is

- Every current Norwegian **lov** (law) and **sentral forskrift** (central regulation) as one Markdown file with YAML front matter — the **Published Rendering** of the source document, deterministically rendered from Lovdata's XML.
- Every change in the source data lands as a Git commit. This repository's Git history is the authoritative record of **published corpus states** — what the corpus said, and when. It is not an authoritative record of Norwegian law; for legal content, Lovdata is authoritative.
- Per-document change history, per-section embedding vectors, and dataset indexes are published alongside the documents.

## Status

**Production.** Auto-synced daily at 04:00 UTC. The corpus tracks every current Norwegian *lov* and *sentral forskrift* — 5,878 documents (759 lover + 5,119 sentrale forskrifter) as of the 2026-08-02 sync. Counts change daily; each dataset's `INDEX.md` carries its live count, and `manifest.json` is the authoritative statement of current corpus membership.

## Structure

```
lovverk/
├── lover/                          # current Norwegian laws
│   ├── INDEX.md                    # generated index of current acts (live count)
│   ├── <slug>.md                   # one document per act: the Published Rendering
│   ├── history/<slug>.json         # per-document change history — structured source of truth
│   ├── history/<slug>.md           # the same history as a human-readable derived view
│   └── embeddings/<slug>.bin       # per-section embedding vectors (int8-quantized)
├── forskrifter/                    # current central regulations (same layout)
│   ├── INDEX.md
│   ├── <slug>.md
│   ├── history/<slug>.json
│   ├── history/<slug>.md
│   └── embeddings/<slug>.bin
└── manifest.json                   # authoritative corpus membership + SHA256 of each
                                    # document's normalized source XML
```

- **`<slug>.md`** — the rendered legal text with YAML front matter (identity, title, retrieval provenance, EU/EEA basis, NLOD attribution).
- **`history/<slug>.json`** — structured per-document event history (added / updated / renamed / removed, with dates and commits). This is the source of truth for generated history.
- **`history/<slug>.md`** — a human-readable view derived from the JSON. If they ever disagree, the JSON wins.
- **`embeddings/<slug>.bin`** — per-section vectors used for semantic search over the corpus.
- **`manifest.json`** — one record per document: current-or-removed status, file path, and the SHA256 of the *normalized source XML*. Change detection keys on that hash, never on the rendered Markdown.
- History files for repealed documents are deliberately kept: they are the audit trail that an act existed and was removed.

## How updates work

The `lovspor` engine runs on a daily schedule. It downloads the current tarballs from Lovdata's public-data API, normalizes and hashes each document's XML, compares against `manifest.json`, and commits only documents whose source content changed — one commit per changed document, plus index/manifest bookkeeping. Renderer-only migrations are committed under `migration:` subjects and are deliberately excluded from per-document change history.

## Verification and reproducibility

Every document records the SHA256 of its normalized source XML in `manifest.json`, and every published state of the corpus is a Git commit. What you can verify **today**:

- integrity of the corpus against its own manifest (paths, hashes, membership);
- the full provenance of any line of any document via `git log`/`git blame`;
- the upstream source itself, by downloading the same public tarballs from `https://api.lovdata.no/v1/publicData/get/`.

The intended long-term contract is stronger: `lovspor` — the processing engine — is being developed as open infrastructure (MIT), so that a third party can obtain the upstream Lovdata data, run the engine independently, and compare the generated artifacts and hashes against this repository. **The engine repository is currently private** while that publication is prepared, so independent re-rendering is not yet possible; this paragraph will be updated when the engine is public. The corpus itself, including this repository's full history, is already public and verifiable as described above.

## Source and attribution

Data source: Lovdata public-data API
- `https://api.lovdata.no/v1/publicData/get/gjeldende-lover.tar.bz2`
- `https://api.lovdata.no/v1/publicData/get/gjeldende-sentrale-forskrifter.tar.bz2`

> Contains data under the Norwegian licence for Open Government data (NLOD) 2.0, distributed by Lovdata. The data has been converted to Markdown by the [lovspor](https://github.com/bartoszkobylinski/lovspor) project (repository currently private — see Verification above).

License: [NLOD 2.0](https://data.norge.no/nlod/no/2.0/) for the derived legal text (including the generated history files), [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) for the repository structure, manifest schema and README. See [LICENSE](LICENSE).

## Not affiliated with Lovdata

This is an unofficial derivative produced from publicly licensed data. For authoritative legal text, always consult [Lovdata](https://lovdata.no/) directly.
