# Datasheet: seed version 0

## Motivation

Language models and retrieval products attach citations to their answers, and published studies report that a large share of those citations point to sources that do not exist or do not say what is claimed. This benchmark measures three narrow, checkable properties of a citation (does the reference exist, is the quote in it, does it support the claim) so that systems can be compared on the same items with labels a person can verify.

The maintainer, Webcite, sells a verification product. That is a conflict of interest; [GOVERNANCE.md](../GOVERNANCE.md) sets out how it is handled.

## Composition

- 448 items from 56 passages, 8 items per passage (one per kind; see [TASK.md](TASK.md)).
- Sources: 45 English Wikipedia articles (CC BY-SA 4.0) and 6 public-domain texts on English Wikisource (the US Constitution, the Gettysburg Address (Bliss copy), Lincoln's second inaugural address, Washington's Farewell Address, the Fourteen Points speech and Franklin D. Roosevelt's first inaugural address). The 56 passages come from 47 of these pages; the other 4 appear only as wrong sources. All 51 snapshots are included.
- Every source is pinned to a revision id fetched on 25 November 2026. `sources/<key>.txt` holds the page's body paragraphs as plain text; `seed/sources.json` records the URL, revision, licence and SHA-256 of each snapshot.
- 56 fabricated references: 28 Wikipedia titles reported missing by the MediaWiki API and 28 DOIs reported unregistered by the DOI handle service, both checked on 25 November 2026 (`seed/fabricated.json`). No real person is named as an author of a fabricated reference.
- Label counts. quote: exact 224, altered 112, fabricated 112. support: supports 112, contradicts 112, unrelated 112, partially_supports 56, not applicable 56. reference_exists: true 392, false 56.
- Language: English only.

## How it was made

1. The maintainers chose pages and, in each, a sentence containing a figure (`tools/candidates.py` lists candidates).
2. For each sentence they wrote a claim the sentence supports, a changed figure for the quote and the claim, and a claim that adds a detail absent from the paragraph (`seed/bases.tsv`).
3. `tools/build_seed.py` derives the eight items per passage and checks each construction against the snapshot: the quote is present verbatim; the changed figure and the added detail are absent from the paragraph; the altered quotes are absent from the page; the wrong source neither contains the quote nor mentions the subject; the unrelated claim's subject is absent from the paragraph. A failed check stops the build.
4. Items are shuffled with a fixed seed and numbered `cab-0001` to `cab-0448`.

No label was produced or pre-filled by Webcite's API or by any system that could be evaluated on this benchmark.

## Known limitations

- Constructed negatives are simpler than real citation errors. A fuzzy string matcher solves the quote task on this seed (99.55%).
- One passage per item and short paragraphs make the support task easier than real documents.
- Wikipedia text appears in most model training data. Systems may know the facts without reading the source; the support labels deliberately ignore outside knowledge, so a system that uses it can lose points on `partially_supports` items.
- Labels have one author group and script checks, not two independent annotators.
- No scanned PDFs, tables or non-English sources yet.

## Maintenance

See [GOVERNANCE.md](../GOVERNANCE.md) and [CHANGELOG.md](../CHANGELOG.md). Corrections are made through public issues and recorded in `ERRATA.md`.
