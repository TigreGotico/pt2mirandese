"""Write pt2mirandese/data/verbs.tsv: verbs whose Mirandese stem carries to every form (ficaram > quedórun).

A candidate is a verb whose infinitive the word lists give with another stem than the rules do, in the same
conjugation in both languages: ficar > quedar. A difference in lh- alone does not count, because data/lh.tsv decides
it. For every form of the verb on the Portuguese side of the gold files that no word list holds, the script compares
two spellings: the Mirandese stem with the Portuguese ending (quedórun), and the rules (ficórun). The verb is kept
when the Mirandese side of the gold files writes the stem spellings at least three times and twice as often as the
rule spellings. Vowels that
change only under stress (buoltar, but boltou) fail this test.

    python scripts/build_verbs.py
"""
import bisect
import csv
import re
import sys
from collections import Counter
from pathlib import Path

import pt2mirandese as m

ROOT = Path(__file__).parent.parent
WORD = re.compile(r"[\wáéíóúãõçâêôà]+")


def main():
    pt_words, mwl_words = Counter(), Counter()
    for path in sorted((ROOT / "gold").glob("*.tsv")):
        if path.name == "cx_mint_era.tsv":
            continue
        for r in csv.DictReader(path.read_text(encoding="utf-8").splitlines(), delimiter="\t"):
            pt_words.update(WORD.findall(r["pt"].lower()))
            mwl_words.update(WORD.findall(r["mwl"].lower()))
    known = m.LEXICON.keys() | m.CONVENCAO.keys() | m.CLOSED.keys() | m.NATIVE.keys()
    candidates = [(pt, mwl) for pt, mwl in (m.LEXICON | m.CONVENCAO).items()
                  if len(pt) > 4 and pt[-2:] in m.CONJUGATIONS and mwl[-2:] == pt[-2:] and m.rules(pt) != mwl
                  and re.sub("^lh", "l", mwl) != re.sub("^lh", "l", m.rules(pt))]
    unknown = sorted(w for w in pt_words if w not in known)
    kept = []
    for pt, mwl in sorted(candidates):
        table = m._verb_table([(pt, mwl)])
        forms = {w for key in table for w in unknown[bisect.bisect_left(unknown, key):bisect.bisect_left(unknown, key + "\uffff")]}
        stem = rule = 0
        for w in forms:
            conj = m._conjugate(w, table)
            base = m._lh(m.rules(w))
            if conj and conj != base:
                stem += mwl_words[conj]
                rule += mwl_words[base]
        if stem >= 3 and stem >= 2 * rule:
            kept.append((pt, mwl, stem, rule))
    with open(ROOT / "pt2mirandese" / "data" / "verbs.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["pt", "mwl", "stem_forms", "rule_forms"])
        w.writerows(kept)
    print(f"candidates in={len(candidates)} kept={len(kept)} dropped={len(candidates) - len(kept)}", file=sys.stderr)


if __name__ == "__main__":
    main()
