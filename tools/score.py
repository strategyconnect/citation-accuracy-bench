#!/usr/bin/env python3
"""Score predictions against the gold labels.

usage: score.py <predictions.jsonl> [--data data/seed-v0.jsonl] [--json out.json]

A prediction line is {"id", "reference_exists": true|false|null, "quote": "exact"|"altered"|"fabricated"|null,
"support": "supports"|"partially_supports"|"contradicts"|"unrelated"|null}. null (or a missing id) is an
abstention: it counts against accuracy and lowers the answer rate. Items whose gold support is
"not_applicable" are left out of the support task. Intervals are 95% percentile bootstrap intervals over
items (2,000 resamples, fixed seed). Standard library only.
"""

import argparse
import json
import random
import sys
from collections import Counter, defaultdict

TASKS = {
    "reference_exists": [True, False],
    "quote": ["exact", "altered", "fabricated"],
    "support": ["supports", "partially_supports", "contradicts", "unrelated"],
}


def load(path):
    return [json.loads(line) for line in open(path) if line.strip()]


def macro_f1(pairs, labels):
    f1s = []
    for lab in labels:
        tp = sum(1 for g, p in pairs if g == lab and p == lab)
        fp = sum(1 for g, p in pairs if g != lab and p == lab)
        fn = sum(1 for g, p in pairs if g == lab and p != lab)
        f1s.append(0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    return sum(f1s) / len(f1s)


def interval(values, rng, n=2000):
    k = len(values)
    stats = sorted(sum(values[rng.randrange(k)] for _ in range(k)) / k for _ in range(n))
    return [round(100 * stats[int(0.025 * n)], 2), round(100 * stats[int(0.975 * n) - 1], 2)]


def score(gold_items, preds):
    rng = random.Random(20261125)
    out = {"items": len(gold_items), "tasks": {}}
    for task, labels in TASKS.items():
        rows = [(it, preds.get(it["id"], {}).get(task)) for it in gold_items
                if it["gold"][task] != "not_applicable"]
        pairs = [(it["gold"][task], p) for it, p in rows]
        correct = [1 if g == p else 0 for g, p in pairs]
        answered = sum(1 for _, p in pairs if p is not None)
        by_kind = defaultdict(list)
        for (it, p), c in zip(rows, correct):
            by_kind[it["kind"]].append(c)
        confusion = Counter(f"{g}->{p}" for g, p in pairs)
        out["tasks"][task] = {
            "n": len(pairs),
            "accuracy": round(100 * sum(correct) / len(pairs), 2),
            "accuracy_95ci": interval(correct, rng),
            "macro_f1": round(100 * macro_f1(pairs, labels), 2),
            "answer_rate": round(100 * answered / len(pairs), 2),
            "accuracy_by_kind": {k: round(100 * sum(v) / len(v), 2) for k, v in sorted(by_kind.items())},
            "confusion": dict(sorted(confusion.items())),
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("predictions")
    ap.add_argument("--data", default="data/seed-v0.jsonl")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    gold = load(args.data)
    preds = {p["id"]: p for p in load(args.predictions)}
    unknown = set(preds) - {it["id"] for it in gold}
    if unknown:
        sys.exit(f"predictions for unknown ids: {sorted(unknown)[:5]}")
    result = score(gold, preds)
    if args.json:
        json.dump(result, open(args.json, "w"), indent=1)
    for task, r in result["tasks"].items():
        print(f"{task:<17} accuracy {r['accuracy']:6.2f} [{r['accuracy_95ci'][0]:.2f}, {r['accuracy_95ci'][1]:.2f}]"
              f"  macro-F1 {r['macro_f1']:6.2f}  answered {r['answer_rate']:6.2f}%  (n={r['n']})")


if __name__ == "__main__":
    main()
