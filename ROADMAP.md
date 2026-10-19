# lovverk — Roadmap

Last reviewed: 2026-10-19 · Reviewed against: 987743f
Product: Lovspor (engine `lovspor` + corpus `lovverk`) · Product roadmap: [lovspor/ROADMAP.md](https://github.com/bartoszkobylinski/lovspor/blob/main/ROADMAP.md)

lovverk is the generated, Git-versioned Markdown corpus of current Norwegian laws and central
regulations that the `lovspor` engine renders from Lovdata's public data, plus a separate
`lokale-forskrifter/` dataset of local regulations (3 current records in its manifest at
987743f). This file covers the corpus repository only: its datasets, integrity checks and
documentation. Engine work (rendering, sync, observatory, promotion, MCP) is tracked in the
lovspor roadmap linked above.

## Now
- (none recorded) — no open pull requests; the only branches besides `main`
  (`ci/corpus-integrity`, `feat/local-regulations-skeleton`) are 0 commits ahead of `main`.
  The daily automated sync is ongoing operation, not a work item (see Done).

## Next
- Integrity check accepts `basis: "received"` local regulation files (ADR-0016 Amendment 1):
  a second front-matter key set, `basis` limited to {observed, received}, observations schema 2,
  manifest `last_seen` equal to `received_at` — needed before the first received regulation
  lands here — source: issue #15 (open)
- Wire the `scripts/tests` pytest suite and `scripts/check_dataset_separation.py` into CI
  (pytest step in the integrity job plus a `dataset-separation` job) — source: PR #11,
  "Pending: CI wiring commit not pushed". At 987743f
  `.github/workflows/corpus-integrity.yml` still runs only `scripts/check_corpus_integrity.py`.

## Later
- (none recorded)

## Done
Local regulations dataset (`lokale-forskrifter/`, ADR-0016):
- Three local regulations migrated to extractor v7, approvals carried, byte-identical — PR #14 (4a1bb58), 2026-10-10
- Orkland (5059): first batch of two regulations; Indre Østfold (3118) regulation migrated to extractor v6 — PR #13 (de973fe), 2026-10-08
- First local regulation promoted: 3118 Indre Østfold, owner-reviewed (ADR-0016 S4) — PR #12 (005d7c6), 2026-10-04
- Empty dataset skeleton with its own manifest; integrity checks for the local dataset
  (layout, membership, id shape, front matter, no NLOD mention); writer-separation check
  `scripts/check_dataset_separation.py`; tests in `scripts/tests/` (ADR-0016 S0) — PR #11 (cdad15e), 2026-10-03

Integrity and CI:
- CI checks that the manifest and the tree describe the same corpus, on push, PR and a daily
  schedule: `.github/workflows/corpus-integrity.yml`, `scripts/check_corpus_integrity.py` — PR #10 (df1bbde), 2026-08-19
- 48 orphaned documents and their embedding sidecars removed — PR #3 (a43a008), 2026-07-14

Documentation:
- README: the engine is AGPL-3.0, not MIT — PR #9 (768b38c), 2026-08-18
- README: the corpus ships LSPE v2 and the sidecar carries its own identity — PR #6 (7a59321), 2026-08-07
- README describes the repository as it exists today — PR #4 (c659916), 2026-08-04
- Docs stop hard-coding a corpus total — PR #2 (60633e4), 2026-07-14
- README moved from "Bootstrapping" to production state — PR #1 (a541cb1), 2026-04-30
- `lover/.gitkeep` placeholder removed — PR #5 (6ec7059), 2026-08-05

Corpus migrations (39 `migration:` commits, 2026-04-27 – 2026-08-05; grouped):
- Embedding sidecars rewritten as LSPE version 2 — 2fa5d12, 2026-08-05
- Embedding identity (ESI) recorded: embeddings regenerated with recorded ESI and identity
  annotated in the manifest — 0054897, 1e80d9c, 2026-08-04
- NLOD attribution backfilled in history Markdown (2580 files) — 0075a22, 2026-08-02
- Re-renders through renderer v1, v3, v4, v5, v6, v7, v8 — afd229b … d5fc99d, 2026-07-10 – 2026-08-02
- Embedding backfills and re-embeds of under-embedded documents — 65a8d4b (2026-06-11) through 6c6733e (2026-08-02)
- `eu_basis` backfilled for 4523 documents — 3d499af, 2026-04-29
- Slug-based filenames and per-document history generated for 4522 documents — 3dddeca, 0c40d0b, 2026-04-27

Automated sync (ongoing since 2026-04-26):
- First sync: 4522 new documents — 57c3052, 2026-04-26
- Daily sync from Lovdata public data: 125 `sync:` bookkeeping commits plus per-document
  `add(...)` / `update(...)` / `remove(...)` / `rename(...)` commits (2,009 at 987743f);
  latest 987743f, 2026-10-17

Repository initialised — 27aef25, 2026-04-22

## Unverified
- README says `lokale-forskrifter/` "is currently an empty skeleton" and that local-regulation
  promotion is "not yet built" — contradicted by PRs #12–#14 and by
  `lokale-forskrifter/manifest.json` (3 current records at 987743f). Whether a README update is
  planned is not recorded anywhere.
- First received regulation (ADR-0016 Amendment 1 "slice I4", named in issue #15) — the
  issue names it as the step that needs #15, but no issue, PR or date for it exists in this
  repository; the promotion itself is engine-side work.

## Sources
- `README.md`, `.github/workflows/corpus-integrity.yml`, `scripts/check_corpus_integrity.py`,
  `scripts/check_dataset_separation.py`, `scripts/tests/` (sparse clone at 987743f)
- `lokale-forskrifter/manifest.json` (read through the GitHub API at `main`)
- `git log` of `main` (2,204 commits)
- `gh issue list -R bartoszkobylinski/lovverk --state all -L 200` (1 issue: #15)
- `gh pr list -R bartoszkobylinski/lovverk --state all -L 200` (12 PRs, all merged); bodies of #10–#14
- Branch list via the GitHub API
- Public product roadmap: https://github.com/bartoszkobylinski/lovspor/blob/main/ROADMAP.md
