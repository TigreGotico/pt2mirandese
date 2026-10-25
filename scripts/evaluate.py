"""Score the translator on a gold file against copying the Portuguese.

A hypothesis counts as exact when it equals the reference or any alternative after lowercasing and apostrophe
normalisation. chrF2 is corpus chrF from sacrebleu against the main reference.

    python scripts/evaluate.py gold/wikimedia_dev.tsv [--errors N]
    python scripts/evaluate.py gold/wikimedia_dev.tsv --hyps bench/madlad    # another system's output
"""
import argparse
import csv
from pathlib import Path

from sacrebleu.metrics import CHRF

from pt2mirandese import CONVENCAO, LEXICON, translate


def norm(s):
    return " ".join(s.lower().replace("’", "'").replace("´", "'").split())


def refs(r):
    return {norm(r["mwl"])} | {norm(a) for a in r["alt"].split("|") if a.strip()}


def score(rows, hyps):
    exact = sum(norm(h) in refs(r) for h, r in zip(hyps, rows))
    chrf = CHRF().corpus_score([norm(h) for h in hyps], [[norm(r["mwl"]) for r in rows]]).score
    return exact / len(rows), chrf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gold", nargs="+")
    ap.add_argument("--errors", type=int, default=0)
    ap.add_argument("--no-lexicon", action="store_true", help="score the rules alone, without the word lists in data/")
    ap.add_argument("--hyps", help="score the hypotheses in DIR/<gold file> (id, hyp) instead of the translator")
    args = ap.parse_args()
    name = Path(args.hyps).name if args.hyps else "pt2mirandese"
    if args.no_lexicon:
        LEXICON.clear()
        CONVENCAO.clear()
    print(f"| Set | Rows | Copy exact | Copy chrF2 | {name} exact | {name} chrF2 |\n| --- | ---: | ---: | ---: | ---: | ---: |")
    for path in args.gold:
        rows = list(csv.DictReader(Path(path).read_text(encoding="utf-8").splitlines(), delimiter="\t"))
        if args.hyps:
            saved = {h["id"]: h["hyp"] for h in csv.DictReader(
                (Path(args.hyps) / Path(path).name).read_text(encoding="utf-8").splitlines(), delimiter="\t")}
            hyps = [saved[r["id"]] for r in rows]
        else:
            hyps = [translate(r["pt"]) for r in rows]
        (ce, cc), (re_, rc) = score(rows, [r["pt"] for r in rows]), score(rows, hyps)
        print(f"| {Path(path).name} | {len(rows)} | {ce:.3f} | {cc:.1f} | {re_:.3f} | {rc:.1f} |")
        shown = 0
        for h, r in zip(hyps, rows):
            if shown < args.errors and norm(h) not in refs(r):
                print(f"{r['id']}\n  pt  {r['pt']}\n  ref {r['mwl']}\n  hyp {h}")
                shown += 1


if __name__ == "__main__":
    main()
