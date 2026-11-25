#!/usr/bin/env python3
"""Two baselines that need no model and no paid service.

  exact : the quote is "exact" if it appears in the cited source after whitespace and quote-mark
          normalisation, otherwise "fabricated"; support is "supports" when the quote is found,
          "unrelated" otherwise.
  fuzzy : adds a fuzzy match (best character-level similarity of the quote against every window of the
          source of the same length, difflib) with "altered" at a ratio of 0.85 or more, and a lexical
          support rule: a figure in the claim that the matched paragraph lacks gives "contradicts";
          low word overlap gives "unrelated"; part of the claim's content words missing gives
          "partially_supports"; otherwise "supports".

The citation URL is looked up in the snapshot cache (seed/sources.json and sources/), which stands in for
fetching the page: a URL with no snapshot is a reference that could not be retrieved.
With --resolve online, whether the reference exists is decided by asking the public MediaWiki API (for
Wikipedia and Wikisource URLs) or the DOI handle service (for doi.org URLs), instead of by the cache.
usage: quote_match.py {exact|fuzzy} [--resolve offline|online] [--data data/seed-v0.jsonl] > predictions.jsonl
"""

import argparse
import difflib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
         "ten": 10, "eleven": 11, "twelve": 12, "fourteen": 14, "twenty": 20, "thirty": 30, "forty": 40,
         "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
STOP = set("a an the of in on at to by for and or is was were are be been has had have it its as that this with "
           "from about than more most which who whose their his her they he she after before since until into "
           "under over each per".split())


def norm(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip().lower()


def numbers(s):
    s = norm(s).replace("-", " ")
    found = {re.sub(r"[,]", "", m) for m in re.findall(r"\d[\d,]*(?:\.\d+)?", s)}
    toks = s.split()
    i = 0
    while i < len(toks):  # "twenty five" -> 25, "two hundred and fifty" -> 250, "four score and seven" -> 87
        if toks[i] in WORDS:
            total, cur = 0, WORDS[toks[i]]
            j = i + 1
            while j < len(toks) and (toks[j] in WORDS or toks[j] in ("hundred", "score", "and")):
                t = toks[j]
                if t == "hundred":
                    cur *= 100
                elif t == "score":
                    cur *= 20
                elif t != "and":
                    total, cur = total + cur, WORDS[t]
                j += 1
            found.add(str(total + cur))
            i = j
        else:
            i += 1
    return found


def content(s):
    return {w for w in re.findall(r"[a-z][a-z'-]+", norm(s)) if w not in STOP and len(w) > 2}


def best_ratio(quote, text):
    q, t = norm(quote), norm(text)
    n, best, best_at = len(q), 0.0, 0
    step = max(1, n // 8)
    for start in range(0, max(1, len(t) - n + 1), step):
        r = difflib.SequenceMatcher(None, q, t[start:start + n], autojunk=False).ratio()
        if r > best:
            best, best_at = r, start
    for start in range(max(0, best_at - step), min(len(t), best_at + step) + 1):
        r = difflib.SequenceMatcher(None, q, t[start:start + n], autojunk=False).ratio()
        if r > best:
            best, best_at = r, start
    return best, best_at


def paragraph_at(text, pos_norm):
    """Paragraph of `text` containing the normalised offset (approximate: paragraphs normalised one by one)."""
    offset = 0
    for para in text.split("\n\n"):
        n = len(norm(para)) + 1
        if offset + n > pos_norm:
            return para
        offset += n
    return text


def support_rule(claim, para):
    cn, pn = numbers(claim), numbers(para)
    if cn - pn:
        return "contradicts"
    cw, pw = content(claim), content(para)
    if not cw:
        return "supports"
    overlap = len(cw & pw) / len(cw)
    if overlap < 0.35:
        return "unrelated"
    if overlap < 0.8:
        return "partially_supports"
    return "supports"


UA = "citation-accuracy-bench/0.1 (https://github.com/strategyconnect/citation-accuracy-bench)"


def resolves(url):
    """True if the reference resolves, asking the public services (no key)."""
    u = urllib.parse.urlparse(url)
    if u.netloc == "doi.org":
        api = "https://doi.org/api/handles/" + u.path.lstrip("/")
        req = urllib.request.Request(api, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r).get("responseCode") == 1
        except urllib.error.HTTPError as e:
            return json.loads(e.read() or b"{}").get("responseCode") == 1
    q = urllib.parse.parse_qs(u.query)
    params = {"action": "query", "format": "json", "formatversion": "2"}
    if "oldid" in q:
        params["revids"] = q["oldid"][0]
    else:
        params["titles"] = urllib.parse.unquote(u.path.rsplit("/", 1)[-1]).replace("_", " ")
    api = f"https://{u.netloc}/w/api.php?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(api, headers={"User-Agent": UA}), timeout=30) as r:
        data = json.load(r)
    time.sleep(0.2)
    pages = data.get("query", {}).get("pages", [])
    return bool(pages) and not pages[0].get("missing") and "badrevids" not in data.get("query", {})


def predict(item, cache, mode, online=False):
    url = item["input"]["citation"]["url"]
    text = cache.get(url)
    if online and not resolves(url):
        return {"reference_exists": False, "quote": "fabricated", "support": None}
    if text is None:
        return {"reference_exists": False, "quote": "fabricated", "support": None}
    quote, claim = item["input"]["quote"], item["input"]["claim"]
    if norm(quote) in norm(text):
        para = paragraph_at(text, norm(text).index(norm(quote)))
        found = "exact"
    elif mode == "fuzzy":
        ratio, at = best_ratio(quote, text)
        found = "altered" if ratio >= 0.85 else "fabricated"
        para = paragraph_at(text, at)
    else:
        found, para = "fabricated", ""
    if found == "fabricated":
        support = "unrelated"
    elif mode == "exact":
        support = "supports"
    else:
        support = support_rule(claim, para)
    return {"reference_exists": True, "quote": found, "support": support}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["exact", "fuzzy"])
    ap.add_argument("--resolve", choices=["offline", "online"], default="offline")
    ap.add_argument("--data", default=str(ROOT / "data" / "seed-v0.jsonl"))
    args = ap.parse_args()
    cache = {s["url"]: (ROOT / "sources" / f"{s['key']}.txt").read_text()
             for s in json.load(open(ROOT / "seed" / "sources.json"))}
    for line in open(args.data):
        item = json.loads(line)
        print(json.dumps({"id": item["id"], **predict(item, cache, args.mode, args.resolve == "online")}))


if __name__ == "__main__":
    main()
