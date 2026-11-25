#!/usr/bin/env python3
"""List candidate quote sentences (they contain a number) per source, for the maintainer to write claims from.
usage: candidates.py seed/sources.json sources/ [per_source]"""
import json, re, sys
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"(])")
def sentences(text):
    for pi, para in enumerate(text.split("\n\n")):
        for s in SENT.split(para):
            yield pi, s.strip()
def main():
    srcs = json.load(open(sys.argv[1])); k = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    for src in srcs:
        text = open(f"{sys.argv[2]}/{src['key']}.txt").read()
        n = 0
        for pi, s in sentences(text):
            if 60 <= len(s) <= 230 and re.search(r"\b\d[\d,.]*\b", s) and '"' not in s and "(" not in s:
                print(f"{src['key']}|p{pi}|{s}"); n += 1
                if n >= k: break
main()
