"""Write pt2mirandese/data/wiktionary.tsv from the Mirandese entries of the Portuguese Wiktionary.

The input is the pt-mwl word list built from the kaikki.org extract of pt.wiktionary (columns pt, mwl, POS,
source_url). Only one-word pairs of open classes are kept; the closed classes come from the Convenção. When an
entry gives several Mirandese words for one Portuguese word, the one closest to the rules' output is kept, because
a cognate is the safer choice in running text. A pair is left out when the rules already give it, and when the
word occurs twice or more in the parallel data: there scripts/learn_lexicon.py has already checked the rules
against the translators' choice.

    python scripts/build_wiktionary.py wiktionary_pt_mwl.tsv gold/*.tsv
"""
import csv
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from align import TOKEN

import pt2mirandese

OPEN = {"noun", "adj", "verb", "adv", "num"}


def main():
    rows = list(csv.DictReader(Path(sys.argv[1]).read_text(encoding="utf-8").splitlines(), delimiter="\t"))
    seen = Counter(w for path in sys.argv[2:] if not path.endswith("cx_mint_era.tsv")
                   for r in csv.DictReader(Path(path).read_text(encoding="utf-8").splitlines(), delimiter="\t")
                   for w in TOKEN.findall(r["pt"].lower()))
    pt2mirandese.LEXICON.clear()
    candidates = defaultdict(list)
    for r in rows:
        pt, mwl = r["pt"].strip().lower(), r["mwl"].strip()
        if r["POS"] in OPEN and seen[pt] < 2 and " " not in pt and " " not in mwl and mwl and pt not in pt2mirandese.CLOSED:
            candidates[pt].append((mwl, r["source_url"]))
    out = []
    for pt, forms in sorted(candidates.items()):
        guess = pt2mirandese.rules(pt)
        mwl, url = max(forms, key=lambda f: SequenceMatcher(None, guess, f[0].lower()).ratio())
        if mwl.lower() != guess:
            out.append((pt, mwl.lower() if not mwl[:1].isupper() or pt[:1].isupper() else mwl, url))
    path = Path(pt2mirandese.__file__).parent / "data" / "wiktionary.tsv"
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["pt", "mwl", "source_url"])
        w.writerows(out)
    print(f"rows={len(rows)} words={len(candidates)} written={len(out)}", file=sys.stderr)


if __name__ == "__main__":
    main()
