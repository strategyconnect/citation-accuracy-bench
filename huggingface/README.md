---
license: cc-by-sa-4.0
language:
- en
pretty_name: Citation accuracy benchmark (seed v0)
size_categories:
- n<1K
task_categories:
- text-classification
tags:
- citations
- fact-checking
- attribution
- benchmark
- evaluation
configs:
- config_name: default
  data_files:
  - split: dev
    path: data/seed-v0.jsonl
---

# Citation accuracy benchmark, seed version 0

Webcite builds and sells a verification product and maintains this benchmark. Its own product is listed under the same rules as everyone else and can lose.

This is a copy of the dataset from the canonical repository, **https://github.com/strategyconnect/citation-accuracy-bench**, which holds the scorer, baselines, submission rules, governance and the build scripts. Report issues and submit results there. This copy is published from a maintainer's personal Hugging Face account until the dataset moves to a Webcite organisation; Hugging Face redirects a moved dataset to its new name.

## Task

For each item a system gets a claim, a quoted passage and a citation, and answers three questions:

1. `reference_exists`: does the cited document exist? (true or false)
2. `quote`: is the quoted passage in the cited document? (`exact`, `altered`, `fabricated`)
3. `support`: does the cited passage support the claim? (`supports`, `partially_supports`, `contradicts`, `unrelated`; `not_applicable` when the reference does not exist)

The full definition, including how support is judged, is in [docs/TASK.md](https://github.com/strategyconnect/citation-accuracy-bench/blob/main/docs/TASK.md).

## Contents

- `data/seed-v0.jsonl`: 448 items, development split. A system should read only the `input` field.
- `sources/`: plain-text snapshots of the 51 cited pages at pinned revisions, with `seed/sources.json` giving each page's URL, revision id, licence and SHA-256.

Label counts. quote: exact 224, altered 112, fabricated 112. support: supports 112, contradicts 112, unrelated 112, partially supports 56, not applicable 56. reference exists: true 392, false 56.

## Limits

- All items are constructed: real passages from Wikipedia and public-domain Wikisource texts, paired with claims written by the maintainers; negatives (changed figures, dropped words, wrong sources, unrelated claims, references that do not exist) are deliberately made and labelled by `kind`.
- Labels follow from construction rules checked by script. They have not yet been double-annotated by independent people; that is planned for version 1, along with harder items and a private test split.
- A fuzzy string matcher with no model scores 99.55% on the quote task and 67.60% on the support task.
- No label was produced or pre-filled by Webcite's API or any system that could be evaluated here.

## Licence

Items and snapshots reproduce Wikipedia text (CC BY-SA 4.0, attribution: Wikipedia contributors, at the revision linked on each item) and public-domain Wikisource texts, so this copy of the dataset is shared under CC BY-SA 4.0. The scorer and tools in the GitHub repository are MIT.
