#!/usr/bin/env python3
"""Create one fabricated reference per base and verify, over the network, that it does not exist.

Even-numbered bases get a Wikipedia article title that the MediaWiki API reports as missing; odd-numbered
bases get a DOI that the DOI handle service reports as unregistered (responseCode 100). The result and the
check date are written to seed/fabricated.json; a reference that turns out to exist stops the script.
usage: verify_fabricated.py
"""

import csv
import datetime
import json
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "citation-accuracy-bench/0.1 (https://github.com/strategyconnect/citation-accuracy-bench)"
WIKI_PATTERNS = ["{t} measurement dispute of 1911", "List of {t} restoration contracts (1952)",
                 "{t} Commission report on visitor numbers", "Second {t} survey expedition (1934)"]
DOI_TITLES = ["{t}: a quantitative review of published figures", "Revisiting the {t} record: an archival audit",
              "Why the standard {t} figures are wrong", "{t} in numbers, 1850 to 2000"]


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def main():
    bases = list(csv.DictReader(open(ROOT / "seed" / "bases.tsv"), delimiter="\t"))
    rng = random.Random(20261125)
    today = datetime.date.today().isoformat()
    out = []
    for i, b in enumerate(bases):
        t = b["topic"]
        if i % 2 == 0:
            title = WIKI_PATTERNS[i // 2 % len(WIKI_PATTERNS)].format(t=t)
            api = ("https://en.wikipedia.org/w/api.php?action=query&format=json&formatversion=2&titles="
                   + urllib.parse.quote(title))
            _, data = get_json(api)
            exists = not data["query"]["pages"][0].get("missing", False)
            ref = {"title": title, "publisher": "Wikipedia",
                   "url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")),
                   "check": f"MediaWiki API query for the title returns 'missing': {api}",
                   "checked": {"date": today, "exists": exists}}
        else:
            doi = f"10.5281/zenodo.{rng.randrange(98000000, 99999999)}"
            status, data = get_json("https://doi.org/api/handles/" + doi)
            exists = data.get("responseCode") != 100
            ref = {"title": DOI_TITLES[i // 2 % len(DOI_TITLES)].format(t=t), "publisher": "Zenodo",
                   "url": f"https://doi.org/{doi}",
                   "check": f"DOI handle lookup https://doi.org/api/handles/{doi} returns responseCode 100 "
                            "(handle not found)",
                   "checked": {"date": today, "exists": exists, "http_status": status}}
        if exists:
            sys.exit(f"fabricated reference exists, choose another pattern: {ref['url']}")
        out.append(ref)
        time.sleep(0.3)
    json.dump(out, open(ROOT / "seed" / "fabricated.json", "w"), indent=1, ensure_ascii=False)
    print(f"{len(out)} fabricated references verified as non-existent on {today}", file=sys.stderr)


if __name__ == "__main__":
    main()
