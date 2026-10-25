"""Write gold/passing.txt: the ids of the rows of the development gold files that the translator gets exactly right.

tests/test_gold.py fails when a listed row stops passing. Run this script after a change that fixes more rows.

    python scripts/pin_passing.py gold/convencao.tsv gold/wikimedia_dev.tsv gold/tatoeba.tsv
"""
import csv
import sys
from pathlib import Path

from evaluate import norm, refs

from pt2mirandese import translate


def main():
    ids = []
    for path in sys.argv[1:]:
        rows = list(csv.DictReader(Path(path).read_text(encoding="utf-8").splitlines(), delimiter="\t"))
        passing = [r["id"] for r in rows if norm(translate(r["pt"])) in refs(r)]
        print(f"{path}: {len(passing)} of {len(rows)} pass", file=sys.stderr)
        ids += passing
    Path("gold/passing.txt").write_text("\n".join(ids) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
