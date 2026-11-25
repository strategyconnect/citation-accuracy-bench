#!/usr/bin/env python3
"""Build the seed dataset from seed/bases.tsv, seed/sources.json, sources/*.txt and seed/fabricated.json.

Every label follows from how the item is constructed, and every construction is checked against the source
text here, so a build that would produce a wrong label stops with an error instead.

usage: build_seed.py [--out data/seed-v0.jsonl]
Standard library only; no network (fabricated references are verified separately by verify_fabricated.py).
"""

import argparse
import csv
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = 20261125
STOP = {"not", "no", "never", "only", "first", "last", "most", "least", "the", "and", "was", "were", "that",
        "with", "which", "from", "this", "have", "been", "shall", "who", "whose"}
NUMBER_WORDS = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "twelve", "twenty",
                "thirty", "forty", "fifty", "hundred", "thousand", "million", "billion", "percent", "score"}


def norm(s):
    return re.sub(r"\s+", " ", s.replace("’", "'").replace("‘", "'")).strip().lower()


def paragraph_of(text, quote):
    for i, para in enumerate(text.split("\n\n")):
        if quote in para:
            return i, para
    raise SystemExit(f"quote not found verbatim: {quote[:80]}")


def fail(msg):
    raise SystemExit(f"build check failed: {msg}")


def replace_once(s, old, new, what):
    if s.count(old) != 1:
        fail(f"{what}: '{old}' must occur exactly once in: {s}")
    return s.replace(old, new)


def drop_word(quote, rng):
    words = quote.split(" ")
    # never drop a number word, a unit next to a figure, or a word that changes polarity
    idx = [i for i, w in enumerate(words) if 0 < i < len(words) - 1 and w.isalpha() and len(w) >= 4
           and w.lower() not in STOP and w.lower() not in NUMBER_WORDS
           and not re.search(r"\d", words[i - 1] + words[i + 1])]
    if not idx:
        fail(f"no droppable word in: {quote}")
    i = rng.choice(idx)
    return " ".join(words[:i] + words[i + 1:]), words[i]


def citation(src):
    return {"title": src["title"], "url": src["url"],
            "publisher": "Wikipedia" if src["site"] == "wikipedia" else "Wikisource"}


def source_ref(src, para_index=None):
    ref = {"key": src["key"], "url": src["url"], "revision": src["revid"], "licence": src["licence"],
           "licence_url": src["licence_url"], "snapshot": f"sources/{src['key']}.txt", "sha256": src["sha256"]}
    if para_index is not None:
        ref["paragraph"] = para_index
    return ref


def item(**kw):
    return kw


def build(bases, sources, fabricated):
    rng = random.Random(SEED)
    texts = {k: (ROOT / "sources" / f"{k}.txt").read_text() for k in sources}
    items = []
    for bi, b in enumerate(bases):
        src = sources[b["key"]]
        text = texts[b["key"]]
        pi, para = paragraph_of(text, b["quote"])
        bid = f"b{bi + 1:03d}"
        q, c = b["quote"], b["claim"]
        if b["claim_from"] not in c:
            fail(f"{bid} claim_from not in claim")
        q_alt = replace_once(q, b["quote_from"], b["quote_to"], f"{bid} quote")
        c_alt = replace_once(c, b["claim_from"], b["claim_to"], f"{bid} claim")
        if norm(q_alt) in norm(text):
            fail(f"{bid} altered quote occurs in source")
        if b["quote_to"] in para or b["claim_to"] in para:
            fail(f"{bid} replacement number already in the paragraph")
        if b["partial_marker"].lower() in para.lower():
            fail(f"{bid} partial marker '{b['partial_marker']}' occurs in the paragraph")
        if b["claim_from"] not in b["partial_claim"] or b["partial_marker"] not in b["partial_claim"]:
            fail(f"{bid} partial claim must keep the supported figure and add the marked detail")
        q_drop, dropped = drop_word(q, rng)
        if norm(q_drop) in norm(text):
            fail(f"{bid} word-dropped quote occurs in source")
        ev = source_ref(src, pi)
        base = {"base": bid, "topic": b["topic"]}

        def add(kind, claim, quote, cit, ref, labels, rationale, constructed):
            items.append({**base, "kind": kind, "constructed": constructed,
                          "input": {"claim": claim, "quote": quote, "citation": cit},
                          "gold": labels, "evidence": ref, "rationale": rationale,
                          "quote_source": source_ref(src, pi)})

        cit = citation(src)
        add("faithful", c, q, cit, ev,
            {"reference_exists": True, "quote": "exact", "support": "supports"},
            "The quote appears verbatim in the cited paragraph, which states the claim.", False)
        add("claim_number_changed", c_alt, q, cit, ev,
            {"reference_exists": True, "quote": "exact", "support": "contradicts"},
            f"The quote is verbatim, but the claim says {b['claim_to']} where the passage says {b['claim_from']}.",
            True)
        add("quote_number_changed", c_alt, q_alt, cit, ev,
            {"reference_exists": True, "quote": "altered", "support": "contradicts"},
            f"The quote changes '{b['quote_from']}' to '{b['quote_to']}'; the real passage contradicts the claim.",
            True)
        add("quote_word_dropped", c, q_drop, cit, ev,
            {"reference_exists": True, "quote": "altered", "support": "supports"},
            f"The quote omits the word '{dropped}' from the real sentence; the passage still states the claim.",
            True)
        add("partial_support", b["partial_claim"], q, cit, ev,
            {"reference_exists": True, "quote": "exact", "support": "partially_supports"},
            f"The passage supports the first part; nothing in it supports '{b['partial_marker']}'.", True)
        # unrelated claim: another base's claim whose topic the paragraph never mentions
        others = [o for o in bases if o["key"] != b["key"] and o["topic"].lower() not in para.lower()]
        other = others[(bi * 7) % len(others)]
        add("unrelated_claim", other["claim"], q, cit, ev,
            {"reference_exists": True, "quote": "exact", "support": "unrelated"},
            f"The quote is verbatim, but the passage is about {b['topic']} and says nothing about the claim.",
            True)
        # wrong source: a real page that neither contains the quote nor mentions the topic
        pool = [k for k in sorted(sources) if k != b["key"] and b["topic"].lower() not in texts[k].lower()
                and norm(q) not in norm(texts[k])]
        wk = pool[(bi * 11) % len(pool)]
        add("wrong_source", c, q, citation(sources[wk]), source_ref(sources[wk]),
            {"reference_exists": True, "quote": "fabricated", "support": "unrelated"},
            f"The cited page ({sources[wk]['title']}) is real but does not contain the quote or mention "
            f"{b['topic']}; the quote comes from {src['title']}.", True)
        fab = fabricated[bi]
        add("fabricated_reference", c, q, {k: fab[k] for k in ("title", "url", "publisher")},
            {"kind": "none", "check": fab["check"], "checked": fab.get("checked")},
            {"reference_exists": False, "quote": "fabricated", "support": "not_applicable"},
            "The cited reference does not exist; see the evidence check.", True)
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "data" / "seed-v0.jsonl"))
    args = ap.parse_args()
    sources = {s["key"]: s for s in json.load(open(ROOT / "seed" / "sources.json"))}
    bases = list(csv.DictReader(open(ROOT / "seed" / "bases.tsv"), delimiter="\t"))
    fabricated = json.load(open(ROOT / "seed" / "fabricated.json"))
    if not all(f.get("checked", {}).get("exists") is False for f in fabricated):
        fail("every fabricated reference must be verified as non-existent (run verify_fabricated.py)")
    items = build(bases, sources, fabricated)
    random.Random(SEED).shuffle(items)
    with open(args.out, "w") as f:
        for n, it in enumerate(items, 1):
            f.write(json.dumps({"id": f"cab-{n:04d}", "split": "dev", **it}, ensure_ascii=False) + "\n")
    print(f"{len(items)} items from {len(bases)} bases -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
