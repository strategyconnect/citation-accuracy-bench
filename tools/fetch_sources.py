#!/usr/bin/env python3
"""Download each source page at a fixed revision and save its body paragraphs as plain text.

usage: fetch_sources.py seed/sources.json sources/
seed/sources.json lists {"key", "site", "title", "revid" (optional), "licence", "licence_url"}.
Without a revid the current revision is fetched and its id is written back, so later builds are pinned.
Standard library only. Uses the public MediaWiki API (no key).
"""

import hashlib
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser

UA = "citation-accuracy-bench/0.1 (https://github.com/strategyconnect/citation-accuracy-bench)"
API = {"wikipedia": "https://en.wikipedia.org/w/api.php", "wikisource": "https://en.wikisource.org/w/api.php"}
SKIP_CLASSES = ("reference", "mw-editsection", "noprint", "mw-empty-elt", "IPA", "nowrap-ipa", "metadata",
                "sistersitebox", "navbox", "hatnote", "ws-noexport", "pagenum", "mw-cite-backlink")


class Paragraphs(HTMLParser):
    """Collect the text of top-level <p> and <dd>/<li> blocks, skipping footnote markers and edit links."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.buf, self.depth_skip, self.in_block, self.stack = [], [], 0, 0, []

    def handle_starttag(self, tag, attrs):
        cls = dict(attrs).get("class") or ""
        skip = tag in ("sup", "style", "script", "table") or any(c in cls.split() for c in SKIP_CLASSES)
        self.stack.append((tag, skip))
        if skip:
            self.depth_skip += 1
        if tag in ("p",) and not self.depth_skip:
            self.in_block += 1

    def handle_endtag(self, tag):
        while self.stack:
            t, skip = self.stack.pop()
            if skip:
                self.depth_skip -= 1
            if t == "p" and self.in_block and not self.depth_skip:
                self.in_block -= 1
                text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
                if len(text) > 40:
                    self.out.append(text)
                self.buf = []
            if t == tag:
                break

    def handle_data(self, data):
        if self.in_block and not self.depth_skip:
            self.buf.append(data)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception:  # noqa: BLE001 - retry transient network errors with backoff
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def fetch(src):
    params = {"action": "parse", "prop": "text|revid", "format": "json", "formatversion": "2",
              "disableeditsection": "1", "disabletoc": "1"}
    if src.get("revid"):
        params["oldid"] = str(src["revid"])
    else:
        params["page"] = src["title"]
        params["redirects"] = "1"
    data = get(API[src["site"]] + "?" + urllib.parse.urlencode(params))
    if "error" in data:
        raise RuntimeError(f"{src['key']}: {data['error']}")
    p = Paragraphs()
    p.feed(data["parse"]["text"])
    return data["parse"]["revid"], data["parse"]["title"], [html.unescape(x) for x in p.out]


def main():
    seed_path, out_dir = sys.argv[1], sys.argv[2]
    sources = json.load(open(seed_path))
    for src in sources:
        revid, title, paras = fetch(src)
        src["revid"], src["title"] = revid, title
        base = "https://en.wikipedia.org" if src["site"] == "wikipedia" else "https://en.wikisource.org"
        src["url"] = f"{base}/w/index.php?title={urllib.parse.quote(title.replace(' ', '_'))}&oldid={revid}"
        text = "\n\n".join(paras) + "\n"
        path = f"{out_dir}/{src['key']}.txt"
        open(path, "w").write(text)
        src["sha256"] = hashlib.sha256(text.encode()).hexdigest()
        src["paragraphs"] = len(paras)
        print(f"{src['key']}: rev {revid}, {len(paras)} paragraphs", file=sys.stderr)
        time.sleep(0.3)
    json.dump(sources, open(seed_path, "w"), indent=1, ensure_ascii=False)
    open(seed_path, "a").write("\n")


if __name__ == "__main__":
    main()
