#!/usr/bin/env python3
"""Re-score a submission and accept it only if every reported number is within the tolerance.

usage: verify_submission.py submissions/<name> [--tolerance 0.5]
A submission folder holds submission.json (metadata and the numbers the submitter reports) and
predictions.jsonl (one line per item, see SUBMITTING.md), plus raw outputs under raw/ when the system
produced any. Exit 0 = accepted; the re-scored result is written to <folder>/score.json.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score import load, score  # noqa: E402

REQUIRED = ["system", "version", "submitter", "track", "run_date", "dataset", "publisher_entry", "reported"]
TRACKS = {"model", "system", "baseline"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--tolerance", type=float, default=0.5)
    args = ap.parse_args()
    folder = Path(args.folder)
    meta = json.load(open(folder / "submission.json"))
    missing = [k for k in REQUIRED if k not in meta]
    if missing:
        sys.exit(f"submission.json is missing: {', '.join(missing)}")
    if meta["track"] not in TRACKS:
        sys.exit(f"track must be one of {sorted(TRACKS)}")
    root = Path(__file__).resolve().parent.parent
    gold = load(root / "data" / f"{meta['dataset']}.jsonl")
    preds = {p["id"]: p for p in load(folder / "predictions.jsonl")}
    result = score(gold, preds)
    problems = []
    for task, numbers in meta["reported"].items():
        for metric, value in numbers.items():
            got = result["tasks"][task][metric]
            if abs(got - value) > args.tolerance:
                problems.append(f"{task}.{metric}: reported {value}, re-scored {got}")
    json.dump(result, open(folder / "score.json", "w"), indent=1)
    if problems:
        print("rejected:\n  " + "\n  ".join(problems))
        return 1
    print(f"accepted: {meta['system']} {meta['version']} (every reported number within {args.tolerance} points)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
