"""Write pt2mirandese/data/convencao.tsv: the Mirandese words that the Convenção prints, by Portuguese word.

A word the Convenção prints is the preferred form of that word, above the forms the corpus uses. The list takes
the word rows of gold/convencao.tsv first, then every Mirandese word cited on a page of the Convenção with a
Portuguese gloss, glossed page by page by Claude Opus 5.5 and checked against the page in a second pass
(convencao_checks.tsv). A gloss stays only when the check finds the word cited as Mirandese, the gloss right, and
the Portuguese word free of another common sense that Mirandese writes differently (verão is summer as well as
they will see). The Mirandese is the Convenção's own spelling, with ie, uo and ye written without the circumflex
as the 2000 Adenda asks. When the pages give one Portuguese word more than one Mirandese form, the form cited on
more pages wins, then the earlier page. Closed classes and multi-word glosses stay with the rules of the translator.

    python scripts/build_convencao.py convencao_checks.tsv
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import pt2mirandese

ROOT = Path(__file__).parent.parent


def adenda(w):
    return re.sub(r"([iuy])([êô])", lambda m: m[1] + {"ê": "e", "ô": "o"}[m[2]], w)


def main():
    rows = 0
    pinned = {}
    for r in csv.DictReader((ROOT / "gold" / "convencao.tsv").read_text(encoding="utf-8").splitlines(), delimiter="\t"):
        rows += 1
        if r["kind"] == "word":
            pinned.setdefault(r["pt"].lower(), (r["mwl"].lower(), r["source"]))
    cited = defaultdict(lambda: defaultdict(set))
    for r in csv.DictReader(Path(sys.argv[1]).read_text(encoding="utf-8").splitlines(), delimiter="\t"):
        rows += 1
        if (r["mirandese"] == r["gloss_ok"] == "True" and r["ambiguous"] == "False"
                and " " not in r["pt"] and " " not in r["mwl"]):
            cited[r["pt"]][adenda(r["mwl"])].add(int(r["page"]))
    for pt, forms in cited.items():
        mwl, pages = min(forms.items(), key=lambda fp: (-len(fp[1]), min(fp[1]), fp[0]))
        pinned.setdefault(pt, (mwl, "Convenção 1999 p. " + ";".join(map(str, sorted(pages)))))
    pinned = {pt: v for pt, v in pinned.items() if pt not in pt2mirandese.CLOSED and " " not in v[0]}
    with open(ROOT / "pt2mirandese" / "data" / "convencao.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["pt", "mwl", "source"])
        w.writerows((pt, *pinned[pt]) for pt in sorted(pinned))
    print(f"rows in={rows} words out={len(pinned)}", file=sys.stderr)


if __name__ == "__main__":
    main()
