# lovverk

lovverk is a Git-versioned Markdown corpus of current Norwegian laws and central regulations, generated from Lovdata's public API. It is intended for AI/RAG, legal research, change tracking, and local MCP-based access from assistants such as Claude. It is not an official legal source and does not replace Lovdata.

## What this is

- Every current Norwegian **lov** (law) and **sentral forskrift** (central regulation) as one Markdown file with YAML front matter.
- Every change in the source data produces a Git commit. `git log` on any file shows when that act was last amended.
- Designed for AI / RAG ingestion, retrieval, and human reading.

## Status

**Production.** Auto-synced daily at 04:00 UTC by the [`lovspor`](https://github.com/bartoszkobylinski/lovspor) engine. The corpus mirrors **781 lover** + **3 741 sentrale forskrifter** = **4 522 acts** total, with per-act change history under `<dataset>/history/<slug>.json` and EU/EEA cross-references in each act's frontmatter `eu_basis` field.

## Structure

```
lovverk/
├── lover/                          # current Norwegian laws (781 acts)
│   ├── INDEX.md                    # generated index of all current acts in this dataset
│   ├── <slug>.md                   # one Markdown file per act, named after Lovdata's kortform
│   └── history/<slug>.json         # per-act change history (date, commit, type, lines added/removed)
├── forskrifter/                    # current central regulations (3 741 acts)
│   ├── INDEX.md
│   ├── <slug>.md
│   └── history/<slug>.json
└── manifest.json                   # SHA256 of normalized source XML per document
```

## How updates work

The [`lovspor`](https://github.com/bartoszkobylinski/lovspor) engine runs on a daily schedule. It downloads the latest tarballs from Lovdata's public-data API, computes hashes against the manifest, and commits only documents whose source XML changed. One commit per changed document.

To verify any commit:
1. Download the same tarball from `https://api.lovdata.no/v1/publicData/get/`
2. Run the `lovspor` engine
3. Compare the resulting Markdown and SHA256 against this commit

## Source and attribution

Data source: Lovdata public-data API
- `https://api.lovdata.no/v1/publicData/get/gjeldende-lover.tar.bz2`
- `https://api.lovdata.no/v1/publicData/get/gjeldende-sentrale-forskrifter.tar.bz2`

> Contains data under the Norwegian licence for Open Government data (NLOD) 2.0, distributed by Lovdata. The data has been converted to Markdown by the [lovspor](https://github.com/bartoszkobylinski/lovspor) project.

License: [NLOD 2.0](https://data.norge.no/nlod/no/2.0/) for derived legal text, [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) for repository structure. See [LICENSE](LICENSE).

## Not affiliated with Lovdata

This is an unofficial derivative produced from publicly licensed data. For authoritative legal text, always consult [Lovdata](https://lovdata.no/) directly.
