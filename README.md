# Citation accuracy benchmark

Webcite builds and sells a verification product and maintains this benchmark. Its own product is listed under the same rules as everyone else and can lose.

This benchmark asks three questions about a citation:

1. **Is the reference real?** Does the cited document exist at the cited location?
2. **Is the quote in the source?** Is the quoted passage present in the cited document verbatim (`exact`), present with changes (`altered`), or absent (`fabricated`)?
3. **Does the source support the claim?** Does the cited passage `support`, `partially_support`, `contradict` or say nothing about (`unrelated`) the claim?

Every label can be checked by a person: each item links to a fixed revision of a freely licensed or public-domain page, and a snapshot of that page's text is in [`sources/`](sources/).

## Status: seed version 0

`data/seed-v0.jsonl` has **448 items** built from 56 passages taken from 47 pages; 51 pages are cited in all (45 Wikipedia articles under CC BY-SA 4.0 and 6 public-domain texts on Wikisource), all pinned to the revision fetched on 25 November 2026.

Read these limits before using a number from it:

- **All items are constructed.** Positive items pair a real passage with a claim the maintainers wrote to match it. Negative items are deliberately constructed (a changed figure, a dropped word, a wrong source, an unrelated claim, a reference that does not exist) and are labelled as such in `kind` and `constructed`.
- **Labels follow from the construction rules and are checked by script** (`tools/build_seed.py` stops if, for example, a changed figure already appears in the passage). They have not yet been double-annotated by independent people. That is planned for version 1 (see [GOVERNANCE.md](GOVERNANCE.md)).
- **The quote task is easy on this seed.** A fuzzy string matcher with no model scores 99.55% on it. The support task is not: the same baseline scores 67.60%. Harder quote cases (scanned and table-heavy PDFs, paraphrased "quotes", wrong periods) are the main work for version 1.
- **There is no private test split yet.** Everything here is a public development split. A held-out split with a published hash comes with version 1.

## Quick start

Python 3.9 or later, standard library only.

```bash
python3 baselines/quote_match.py fuzzy > my-predictions.jsonl
python3 tools/score.py my-predictions.jsonl
```

To check whether references resolve against the live services instead of the snapshot cache, add `--resolve online` (it queries the public MediaWiki API and the DOI handle service; no key).

## Item format

```json
{
  "id": "cab-0001",
  "kind": "faithful",
  "constructed": false,
  "input": {
    "claim": "By mass, Jupiter's atmosphere is 76% hydrogen.",
    "quote": "Jupiter's atmosphere consists of 76% hydrogen and 24% helium by mass, with a denser interior.",
    "citation": {"title": "Jupiter", "url": "https://en.wikipedia.org/w/index.php?title=Jupiter&oldid=1384572050", "publisher": "Wikipedia"}
  },
  "gold": {"reference_exists": true, "quote": "exact", "support": "supports"},
  "evidence": {"url": "...", "revision": 1384572050, "paragraph": 1, "licence": "CC BY-SA 4.0", "snapshot": "sources/wp-jupiter.txt", "sha256": "..."},
  "rationale": "The quote appears verbatim in the cited paragraph, which states the claim."
}
```

A system receives only `input`. The task definition, including how support is judged, is in [docs/TASK.md](docs/TASK.md); composition and sources are in [docs/DATASHEET.md](docs/DATASHEET.md).

## Results

See [RESULTS.md](RESULTS.md). Two baselines that need no model and no paid service:

| Baseline | Reference exists | Quote | Support (95% interval) |
|---|---:|---:|---:|
| Exact quote match | 100.00 | 75.00 | 28.57 (24.23 to 33.16) |
| Fuzzy quote match | 100.00 | 99.55 | 67.60 (62.76 to 72.19) |

Reference existence is 100% for both because every citation in the seed has a URL and the fabricated ones fail to resolve; a lookup settles it. It will matter when version 1 adds citations given only as titles or author and year.

## Submitting a result

Any vendor, lab or individual can submit by pull request: predictions, raw outputs and a short metadata file. The maintainers re-score every submission with `tools/verify_submission.py` and accept it only if each reported number is within 0.5 points. See [SUBMITTING.md](SUBMITTING.md).

## Rebuilding the dataset

```bash
python3 tools/fetch_sources.py seed/sources.json sources/   # pinned revisions; network
python3 tools/verify_fabricated.py                          # confirms fabricated references do not exist; network
python3 tools/build_seed.py                                 # deterministic; no network
```

## Licences

Code and the maintainers' annotations: MIT ([LICENSE](LICENSE)). Text reproduced from sources keeps the source's licence, recorded on every item and every snapshot: Wikipedia text is CC BY-SA 4.0 (attribution: Wikipedia contributors, at the linked revision), Wikisource texts used here are in the public domain. Files that contain CC BY-SA text (`sources/wp-*.txt` and the items quoting them) are shared under CC BY-SA 4.0.

## Citation

```bibtex
@misc{citation_accuracy_bench_2026,
  title  = {Citation accuracy benchmark, seed version 0},
  author = {{Webcite}},
  year   = {2026},
  url    = {https://github.com/strategyconnect/citation-accuracy-bench}
}
```
