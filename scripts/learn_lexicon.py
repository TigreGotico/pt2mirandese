"""Write data/lexicon.tsv: the words whose Mirandese form the rules do not give.

The script aligns the words of the train pairs (scripts/align.py) with the word list switched off, so each
Portuguese word is compared with the rules' output. A word goes into the list when it occurs at least MIN_COUNT
times, its most frequent Mirandese form covers at least MIN_SHARE of its aligned occurrences, and that form differs
from the rules' output. Only one-word Mirandese forms count. The test split is never read.

    python scripts/learn_lexicon.py gold/wikimedia_train.tsv
"""
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

from align import TOKEN, align

import pt2mirandese

MIN_COUNT, MIN_SHARE = 2, 0.6


def main():
    pt2mirandese.LEXICON.clear()
    counts = defaultdict(Counter)
    rows = 0
    for path in sys.argv[1:]:
        for r in csv.DictReader(Path(path).read_text(encoding="utf-8").splitlines(), delimiter="\t"):
            rows += 1
            for p, m in align(TOKEN.findall(r["pt"].lower()), TOKEN.findall(r["mwl"].lower())):
                counts[p][m] += 1
    out = []
    for p, c in counts.items():
        total = sum(c.values())
        if p in pt2mirandese.CLOSED or total < MIN_COUNT:
            continue
        form, n = c.most_common(1)[0]
        if " " in form or not form or n / total < MIN_SHARE or form == pt2mirandese.word(p):
            continue
        out.append((p, form, n, total))
    out.sort()
    path = Path(pt2mirandese.__file__).parent / "data" / "lexicon.tsv"
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["pt", "mwl", "count", "total"])
        w.writerows(out)
    print(f"pairs={rows} pt_words={len(counts)} lexicon={len(out)}", file=sys.stderr)


if __name__ == "__main__":
    main()
