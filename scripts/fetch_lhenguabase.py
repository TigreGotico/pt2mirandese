"""Download every lexeme of the Lhenguabase, the Mirandese dictionary on Wikibase Cloud, and flatten it to a TSV.

The Lhenguabase (https://lhenguabase.wikibase.cloud) was seeded from the Mirandese entries of the Portuguese
Wiktionary in January 2025; a native speaker and a lexicographer review later edits. Its data is CC-BY-SA 4.0, as
each statement's reference says. The script lists the Lexeme namespace, fetches the entities 50 at a time through
the MediaWiki API, and records for each lexeme the users who edited it, so entries changed by a person after the
import can be told apart. It writes the raw entities as JSON lines and one TSV row per form and sense.

    python scripts/fetch_lhenguabase.py OUT_DIR
"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://lhenguabase.wikibase.cloud/w/api.php"
AGENT = "pt2mirandese/0.1 (https://github.com/TigreGotico/pt2mirandese; jarbasai@mailfence.com)"
LEXEME_NS = 146


def get(**params):
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json", "formatversion": 2})
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": AGENT}), timeout=60) as r:
        data = json.load(r)
    time.sleep(1)
    return data


def lexeme_titles():
    titles, cont = [], {}
    while True:
        data = get(action="query", list="allpages", apnamespace=LEXEME_NS, aplimit=500, **cont)
        titles += [p["title"] for p in data["query"]["allpages"]]
        if "continue" not in data:
            return titles
        cont = {"apcontinue": data["continue"]["apcontinue"]}


def editors():
    """The users who edited each lexeme page, oldest first."""
    out, cont = {}, {}
    while True:
        data = get(action="query", list="allrevisions", arvnamespace=LEXEME_NS, arvprop="user|timestamp",
                   arvlimit=500, arvdir="newer", **cont)
        for page in data["query"]["allrevisions"]:
            out.setdefault(page["title"], []).extend((r["user"], r["timestamp"]) for r in page["revisions"])
        if "continue" not in data:
            return out
        cont = {"arvcontinue": data["continue"]["arvcontinue"]}


def labels(ids):
    out = {}
    for k in range(0, len(ids), 50):
        data = get(action="wbgetentities", ids="|".join(ids[k:k + 50]), props="labels", languages="en|pt")
        for i, e in data["entities"].items():
            lab = e.get("labels", {})
            out[i] = (lab.get("en") or lab.get("pt") or {}).get("value", i)
    return out


def text(claims, prop):
    # formatversion=2 writes an empty claim set as [].
    if not claims:
        return []
    return [c["mainsnak"]["datavalue"]["value"] for c in claims.get(prop, []) if c["mainsnak"]["snaktype"] == "value"]


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    titles = lexeme_titles()
    ids = [t.split(":", 1)[1] for t in titles]
    entities = {}
    for k in range(0, len(ids), 50):
        data = get(action="wbgetentities", ids="|".join(ids[k:k + 50]))
        for e in data["entities"].values():
            if "missing" not in e:
                entities[e["id"]] = e
    history = editors()
    items = sorted({e["lexicalCategory"] for e in entities.values()}
                   | {f for e in entities.values() for form in e.get("forms", []) for f in form["grammaticalFeatures"]}
                   | {c["mainsnak"]["datavalue"]["value"]["id"] for e in entities.values()
                      for c in (e.get("claims") or {}).get("P12", []) if c["mainsnak"]["snaktype"] == "value"})
    names = labels(items)
    with open(out / "lhenguabase.jsonl", "w", encoding="utf-8") as f:
        for i in sorted(entities, key=lambda x: int(x[1:])):
            e = entities[i]
            e["_history"] = history.get(f"Lexeme:{i}", [])
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    rows = 0
    with open(out / "lhenguabase.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["lexeme", "lemma", "pos", "gender", "form", "features", "sense", "gloss_pt", "gloss_mwl",
                    "ipa", "source", "editors", "url"])
        for i in sorted(entities, key=lambda x: int(x[1:])):
            e = entities[i]
            lemma = e["lemmas"].get("mwl", {}).get("value", "")
            claims = e.get("claims") or {}
            gender = ",".join(names.get(v["id"], v["id"]) for v in text(claims, "P12"))
            sources = sorted({s["datavalue"]["value"] for c in claims.get("P6", []) for ref in c.get("references", [])
                              for s in ref["snaks"].get("P8", [])})
            people = sorted({u for u, _ in e["_history"]})
            forms = e.get("forms") or [{"representations": {"mwl": {"value": lemma}}, "grammaticalFeatures": [],
                                        "claims": {}}]
            senses = e.get("senses") or [{"id": "", "glosses": {}}]
            for form in forms:
                rep = form["representations"].get("mwl", {}).get("value", "")
                feats = ",".join(names.get(x, x) for x in form["grammaticalFeatures"])
                ipa = ",".join(text(form.get("claims", {}), "P18"))
                for sense in senses:
                    g = sense.get("glosses", {})
                    w.writerow([i, lemma, names.get(e["lexicalCategory"], e["lexicalCategory"]), gender, rep, feats,
                                sense.get("id", ""), g.get("pt", {}).get("value", ""), g.get("mwl", {}).get("value", ""),
                                ipa, " ".join(sources), " ".join(people),
                                f"https://lhenguabase.wikibase.cloud/wiki/Lexeme:{i}"])
                    rows += 1
    print(f"titles={len(titles)} entities={len(entities)} rows={rows}", file=sys.stderr)


if __name__ == "__main__":
    main()
