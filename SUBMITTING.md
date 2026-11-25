# Submitting a result

1. Run your system on every item in `data/seed-v0.jsonl`, giving it only the `input` field of each item.
2. Write `predictions.jsonl`, one line per item:

   ```json
   {"id": "cab-0001", "reference_exists": true, "quote": "exact", "support": "supports"}
   ```

   Allowed values: `reference_exists` true, false or null; `quote` "exact", "altered", "fabricated" or null; `support` "supports", "partially_supports", "contradicts", "unrelated" or null. null means the system abstained.
3. Score it: `python3 tools/score.py predictions.jsonl --json score.json`.
4. Open a pull request adding `submissions/<system-name>/` with:
   - `predictions.jsonl`
   - `raw/`: the system's raw responses (or a link to them if they are large), so others can check how predictions were derived
   - `submission.json`:

   ```json
   {
     "system": "Example verifier",
     "version": "2026-11-20",
     "submitter": "Example Inc.",
     "track": "system",
     "run_date": "2026-11-25",
     "dataset": "seed-v0",
     "publisher_entry": false,
     "how_run": "Endpoint, settings and prompt used, enough for someone else to repeat the run",
     "cost_and_latency": "Optional: total cost at public prices and median seconds per item",
     "reported": {
       "reference_exists": {"accuracy": 0.0, "macro_f1": 0.0},
       "quote": {"accuracy": 0.0, "macro_f1": 0.0},
       "support": {"accuracy": 0.0, "macro_f1": 0.0}
     }
   }
   ```

   `track` is `model` for a model given the claim, quote and source text with a prompt, `system` for a product or pipeline called as its vendor documents, and `baseline` for methods with no model.

A maintainer runs `python3 tools/verify_submission.py submissions/<system-name>` and accepts the entry only if every reported number is within 0.5 points of the re-score, then regenerates `RESULTS.md` with `python3 tools/leaderboard.py`. Models and products are never ranked in the same table.

Submitting a run of a competitor's product is allowed only if its terms of service permit publishing benchmark results; the submitter is responsible for checking.
