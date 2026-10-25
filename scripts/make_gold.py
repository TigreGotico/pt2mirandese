"""Build the gold files from public parallel text.

wikimedia.tsv comes from the OPUS wikimedia mwl-pt release: Wikipedia articles that editors translated from
Portuguese into Mirandese with the Content Translation tool. tatoeba.tsv comes from the Tatoeba export.

    python scripts/make_gold.py <dir with wikimedia.mwl-pt.pt and .mwl> <tatoeba_mwl_por.tsv> <mint_text.json>

The third file comes from scripts/fetch_cx.py. A pair whose Mirandese side occurs in a translation published since
MinT arrived (2023) is dropped, because those translations started from machine drafts.

A pair is dropped when the Mirandese side equals the Portuguese side, when one side is under three words, or when
the length ratio is outside 0.67 to 1.5, which marks a sentence cut on one side only. The first copy of a
Portuguese sentence is kept. The first hex digit of the sha256 of the
Portuguese side picks the split, so the split does not depend on the order of the release: 0, 1 or 2 is test, 3 is
dev, and the rest is train. Only the train split feeds data/lexicon.tsv; the dev split chooses between rules.
"""
import csv
import hashlib
import json
import sys
import unicodedata
from pathlib import Path

FIELDS = ["id", "pt", "mwl", "alt", "source", "kind", "class", "note"]


def clean(s):
    return " ".join(unicodedata.normalize("NFC", s).split())


def folded(s):
    return clean(s).lower()


def write(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, FIELDS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main():
    opus, tatoeba = Path(sys.argv[1]), Path(sys.argv[2])
    mint_era = " ".join(folded(t) for texts in json.loads(Path(sys.argv[3]).read_text(encoding="utf-8")).values()
                        for t in texts)
    pt = (opus / "wikimedia.mwl-pt.pt").read_text(encoding="utf-8").splitlines()
    mwl = (opus / "wikimedia.mwl-pt.mwl").read_text(encoding="utf-8").splitlines()
    assert len(pt) == len(mwl)
    seen, splits, dropped = set(), {"train": [], "dev": [], "test": []}, {}
    for i, (p, m) in enumerate(zip(pt, mwl), 1):
        p, m = clean(p), clean(m)
        reason = ("same" if p.lower() == m.lower() else "short" if min(len(p.split()), len(m.split())) < 3
                  else "ratio" if not 0.67 <= len(m) / len(p) <= 1.5 else "duplicate" if p in seen
                  else "mint-era" if folded(m) in mint_era else None)
        if reason:
            dropped[reason] = dropped.get(reason, 0) + 1
            continue
        seen.add(p)
        digit = hashlib.sha256(p.encode()).hexdigest()[0]
        split = "test" if digit in "012" else "dev" if digit == "3" else "train"
        splits[split].append({"id": f"w{i:05d}", "pt": p, "mwl": m, "alt": "", "source": "opus-wikimedia",
                              "kind": "sentence", "class": "", "note": ""})
    for split, rows in splits.items():
        write(f"gold/wikimedia_{split}.tsv", rows)
    print(f"wikimedia in={len(pt)}", *(f"{k}={len(v)}" for k, v in splits.items()), f"dropped={dropped}")

    rows = list(csv.DictReader(tatoeba.read_text(encoding="utf-8").splitlines(), delimiter="\t"))
    out, seen = [], set()
    for r in rows:
        if r["mwl"] in seen:
            continue
        seen.add(r["mwl"])
        out.append({"id": f"t{r['mwl_id']}", "pt": clean(r["por"]), "mwl": clean(r["mwl"]), "alt": "",
                    "source": r["source_url"], "kind": "sentence", "class": "", "note": ""})
    write("gold/tatoeba.tsv", out)
    print(f"tatoeba in={len(rows)} out={len(out)}")


if __name__ == "__main__":
    main()
