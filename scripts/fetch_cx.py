"""Fetch the Content Translation record of the Portuguese to Mirandese translations.

MinT, which offers machine drafts in Content Translation, arrived in 2023. The script writes gold/cx_mint_era.tsv,
the translations published from 2023 on with the share of machine text Content Translation recorded, and a JSON
file with their final Mirandese text, which scripts/make_gold.py reads to drop the pairs that come from them.

    python scripts/fetch_cx.py <output.json>
"""
import csv
import json
import sys
import time
import urllib.request

API = "https://mwl.wikipedia.org/w/api.php?format=json&action=query&"
HEADERS = {"User-Agent": "TigreGotico pt2mirandese (jarbasai@mailfence.com)"}
MINT_FROM = "2023"


def get(query):
    with urllib.request.urlopen(urllib.request.Request(API + query, headers=HEADERS), timeout=60) as r:
        return json.load(r)["query" if "contenttranslationcorpora" in query else "result"]


def main():
    published, offset = [], ""
    while True:
        page = get(f"list=cxpublishedtranslations&from=pt&to=mwl&limit=500{offset}")["translations"]
        published += page
        if len(page) < 500:
            break
        offset = f"&offset={len(published)}"
    late = [t for t in published if t["publishedDate"][:4] >= MINT_FROM]
    texts = {}
    for t in late:
        sections = get(f"list=contenttranslationcorpora&translationid={t['translationId']}&striphtml=true"
                       "&types=user")["contenttranslationcorpora"]
        sections = sections.get("sections", {}) if isinstance(sections, dict) else {}
        values = sections.values() if isinstance(sections, dict) else sections
        texts[t["translationId"]] = [((s or {}).get("user") or {}).get("content") or "" for s in values]
        time.sleep(0.5)
    with open("gold/cx_mint_era.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["translation_id", "title", "published", "mt_share"])
        for t in late:
            w.writerow([t["translationId"], t["targetTitle"], t["publishedDate"], t["stats"].get("mt") or 0])
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False)
    print(f"translations={len(published)} mint_era={len(late)}", file=sys.stderr)


if __name__ == "__main__":
    main()
