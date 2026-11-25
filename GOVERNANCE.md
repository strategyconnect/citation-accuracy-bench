# Governance

## Who maintains it

Webcite (operated by StrategyConnect) maintains this repository. Webcite builds and sells a verification product, so it has a commercial interest in how this benchmark is designed and scored. The rules below exist because of that interest.

Contact: open a GitHub issue, or write to support@webcite.co.

## Rules that apply to the maintainer's own product

1. Webcite's product is scored with the same data, the same script and the same tolerance as every other submission.
2. Its row is marked `publisher_entry: true` and is left out of the main tables. It appears in a separate section labelled "publisher's own system, self-run".
3. It moves into the main table only after at least one reviewer with no commercial tie to Webcite has re-run it from the published instructions and matched the reported numbers within the tolerance.
4. Its raw outputs are published like everyone else's.
5. A Webcite score that is lower than another system's is published as it is. Webcite does not withhold, delay or re-run a result because it lost.
6. Write-ups lead with what the benchmark shows about the field, not with Webcite's rank.
7. No item's label is produced or pre-filled by Webcite's API or any system under test.

## Outside reviewers

The benchmark is looking for two or three reviewers (academics or practitioners) with no commercial tie to Webcite, to approve protocol changes and reproduce publisher entries. None is named yet. When they are, their names and any relationship to Webcite will be listed here.

## Disputes and corrections

- Anyone can dispute a label by opening an issue that names the item id and quotes the evidence.
- The maintainers reply within 10 working days.
- An accepted correction is recorded in `ERRATA.md` with the item id, the old and new label and the reason. Every accepted submission is then re-scored, and the dataset version is bumped.
- A rejected dispute stays public with the reason.

## Submissions and removal

- Any vendor, lab or individual can submit (see [SUBMITTING.md](SUBMITTING.md)).
- A vendor may ask for a row about its own product to be removed, or may submit its own run of its product. Both requests and their outcome are logged in the pull request or issue that made them.

## Versions and refresh

- Version 0 (this seed) is a public development split only.
- Version 1 is planned to add independent double annotation with agreement statistics, harder items (scanned and table-heavy PDFs, wrong periods, conflicting figures across documents, citations given as title or author and year), more languages built by native annotators, and a private test split whose hash is published at release. Custody of the private split is to move to an independent host when one agrees.
- Leaderboard entries are dated. Results older than one dataset version are marked as such.

## No automation on GitHub

This repository has no GitHub Actions. Submissions are re-scored by a maintainer running `tools/verify_submission.py` locally, and the command output is posted on the pull request.
