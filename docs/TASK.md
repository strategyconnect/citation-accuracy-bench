# Task definition

## Input

Each item gives a system three things:

- `claim`: a sentence someone wants to support with a citation.
- `quote`: the passage the citing text presents as coming from the source.
- `citation`: the reference (title, URL, publisher).

The system may fetch the URL. It may not read `gold`, `evidence`, `rationale` or `kind`.

## Output

One line per item: `{"id", "reference_exists", "quote", "support"}`. Any of the three may be `null` to abstain. An abstention counts as wrong and lowers the answer rate, which is reported next to every accuracy.

## Labels

### reference_exists

`true` if the cited URL resolves to a document. `false` if it does not: in the seed, a Wikipedia title the MediaWiki API reports as missing, or a DOI the DOI handle service reports as unregistered. The check and its date are stored on each item.

### quote

Judged against the whole cited document at the pinned revision, after normalising whitespace and curly quote marks:

- `exact`: the quote appears verbatim.
- `altered`: a passage of the document matches the quote except for a change (in the seed: one figure changed, or one word dropped).
- `fabricated`: no passage of the document matches the quote, or the document does not exist.

### support

Judged only from the **evidence passage**, never from outside knowledge:

- When the quote is `exact` or `altered`, the evidence passage is the paragraph of the cited document that contains the real sentence (given as `evidence.paragraph`). An altered quote is therefore judged by what the source really says, not by what the quote claims it says.
- When the quote is `fabricated` and the document exists, the evidence is the whole cited document.
- When the document does not exist, support is `not_applicable` and the item is left out of the support score.

Classes:

- `supports`: the passage states everything the claim asserts.
- `partially_supports`: the passage states part of the claim; another part (a detail, a cause, an extra figure) is not in it. A detail that is false in the world but absent from the passage is still "not in the passage", so the claim is partially supported, not contradicted.
- `contradicts`: the passage states something incompatible with the claim, such as a different figure for the same quantity.
- `unrelated`: the passage does not address the claim's subject.

## Item kinds in the seed

| Kind | Construction | quote | support |
|---|---|---|---|
| faithful | real sentence, claim written to match it | exact | supports |
| claim_number_changed | claim's figure changed | exact | contradicts |
| quote_number_changed | figure changed in both quote and claim | altered | contradicts |
| quote_word_dropped | one word (never a figure, unit or negation) removed from the quote | altered | supports |
| partial_support | claim adds a detail absent from the paragraph | exact | partially_supports |
| unrelated_claim | real quote paired with another passage's claim on a subject the paragraph never mentions | exact | unrelated |
| wrong_source | real quote cited to a different real page that neither contains it nor mentions the subject | fabricated | unrelated |
| fabricated_reference | citation to a page or DOI that does not exist | fabricated | not applicable |

Each of the 56 passages yields one item of each kind (448 items).

## Scoring

`tools/score.py` reports, per task: accuracy with a 95% bootstrap interval (2,000 resamples over items, fixed seed), macro-F1 over the task's classes, answer rate, accuracy by item kind and a confusion table. Systems whose intervals overlap are read as tied.

Quote presence is meant to be scored deterministically; support is scored against the labels. No language model is used as a judge.
