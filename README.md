# lovverk

Versioned Markdown corpus of current Norwegian law, auto-updated from Lovdata's public-data API.

## What this is

- Every current Norwegian **lov** (law) and **sentral forskrift** (central regulation) as one Markdown file with YAML front matter.
- Every change in the source data produces a Git commit. `git log` on any file shows when that act was last amended.
- Designed for AI / RAG ingestion, retrieval, and human reading.

## Status

Bootstrapping. Corpus not yet populated.

## Structure (planned)

```
lovverk/
├── lover/              # current Norwegian laws
│   └── <id>.md
├── forskrifter/        # current central regulations
│   └── <id>.md
└── manifest.json       # SHA256 of source XML per document
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
