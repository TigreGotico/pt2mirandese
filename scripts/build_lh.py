"""Write pt2mirandese/data/lh.tsv: the Mirandese words that sources write with initial lh-.

The Convenção (p. 15) writes lh- for initial l before a vowel in the traditional vocabulary, and l- only in
neologisms, loanwords and proper names. Writers on Wikipedia mix the two in both kinds of word, so their counts
cannot tell a traditional word from a neologism. This list takes the words that a curated source writes with lh-:
the examples of the Convenção, the Mirandese entries of the Portuguese Wiktionary, and the Lhenguabase.

    python scripts/build_lh.py convencao1999_text.txt wiktionary_pt_mwl.tsv lhenguabase.tsv
"""
import csv
import re
import sys
from pathlib import Path

LH = re.compile(r"(?<!\w)lh[aeiouáéíóúâêô]\w*")


def main():
    convencao, wiktionary, lhenguabase = map(Path, sys.argv[1:4])
    words = {}
    page = 0
    for line in convencao.read_text(encoding="utf-8").splitlines():
        if m := re.match(r"=== PDF page (\d+) ===", line):
            page = int(m.group(1))
        for w in LH.findall(line.lower()):
            words.setdefault(w, f"Convenção p. {page}")
    for r in csv.DictReader(wiktionary.read_text(encoding="utf-8").splitlines(), delimiter="\t"):
        if LH.fullmatch(r["mwl"].strip().lower()):
            words.setdefault(r["mwl"].strip().lower(), r["source_url"])
    for r in csv.DictReader(lhenguabase.read_text(encoding="utf-8").splitlines(), delimiter="\t"):
        for w in (r["lemma"], r["form"]):
            if LH.fullmatch(w.lower()):
                words.setdefault(w.lower(), r["url"])
    path = Path(__file__).parent.parent / "pt2mirandese" / "data" / "lh.tsv"
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["mwl", "source"])
        w.writerows(sorted(words.items()))
    print(f"words={len(words)}", file=sys.stderr)


if __name__ == "__main__":
    main()
