"""Write pt2mirandese/data/common.txt: Portuguese words that the rules for proper names must not touch.

Proper names keep an official V, Convenção p. 17, and initial l-, p. 15. A capitalised word inside a sentence is
a proper name unless it is a common word in capitals, as in Universidade de Lisboa. This list holds the words with
a v or an initial l that the Portuguese side of the gold files writes in lowercase at least MIN_LOWER times. A name
such as Silva, Viena or Vasco is almost never lowercase. A surname that is also a common word (Oliveira) is on the
list and takes b.

    python scripts/build_common.py              # every file in gold/
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

GOLD = Path(__file__).parent.parent / "gold"
NOT_PAIRS = {"cx_mint_era.tsv"}
MIN_LOWER = 3
WORD = re.compile(r"[^\W\d_]+")


def main():
    paths = sys.argv[1:] or sorted(str(p) for p in GOLD.glob("*.tsv") if p.name not in NOT_PAIRS)
    lower, rows = Counter(), 0
    for path in paths:
        for r in csv.DictReader(Path(path).read_text(encoding="utf-8").splitlines(), delimiter="\t"):
            rows += 1
            lower.update(w for w in WORD.findall(r["pt"]) if w.islower())
    words = sorted(w for w, n in lower.items() if n >= MIN_LOWER and ("v" in w or re.match(r"l[aeiouáéíóú]", w)))
    (Path(__file__).parent.parent / "pt2mirandese" / "data" / "common.txt").write_text(
        "".join(w + "\n" for w in words), encoding="utf-8")
    print(f"files={len(paths)} rows={rows} words={len(words)}", file=sys.stderr)


if __name__ == "__main__":
    main()
