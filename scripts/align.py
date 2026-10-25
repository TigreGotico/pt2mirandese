"""Align the words of parallel sentences and count which Mirandese form each Portuguese word takes.

The alignment is monotonic: a dynamic program over the two word sequences, where a substitution costs the
normalised edit distance between the translator's output for the Portuguese word and the Mirandese word, and an
insertion or a deletion costs 0.6. Mirandese splits some Portuguese contractions (do > de l), so a Portuguese word
may also align with two Mirandese words.

    python scripts/align.py gold/wikimedia_dev.tsv > counts.tsv
"""
import csv
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from pt2mirandese import word

# An elided article or preposition (l'obra, d'outros, qu'el) is a word of its own.
TOKEN = re.compile(r"[^\W\d_]+['’]|[^\W\d_]+(?:-[^\W\d_]+)*", re.UNICODE)
GAP = 0.6


def dist(a, b):
    return 1 - SequenceMatcher(None, a, b).ratio()


def align(pt, mwl):
    hyp = [word(w) for w in pt]
    n, m = len(pt), len(mwl)
    cost = [[0.0] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        for j in range(m + 1):
            if i == j == 0:
                continue
            options = []
            if i and j:
                options.append((cost[i - 1][j - 1] + dist(hyp[i - 1], mwl[j - 1]), (1, 1)))
            if i and j > 1:
                options.append((cost[i - 1][j - 2] + dist(hyp[i - 1], mwl[j - 2] + " " + mwl[j - 1]), (1, 2)))
            if i:
                options.append((cost[i - 1][j] + GAP, (1, 0)))
            if j:
                options.append((cost[i][j - 1] + GAP, (0, 1)))
            cost[i][j], back[i][j] = min(options)
    pairs, i, j = [], n, m
    while i or j:
        di, dj = back[i][j]
        if di and dj:
            pairs.append((pt[i - 1], " ".join(mwl[j - dj:j])))
        elif di:
            pairs.append((pt[i - 1], ""))
        i, j = i - di, j - dj
    return pairs[::-1]


def main():
    counts = defaultdict(Counter)
    for path in sys.argv[1:]:
        for r in csv.DictReader(Path(path).read_text(encoding="utf-8").splitlines(), delimiter="\t"):
            pt = TOKEN.findall(r["pt"].lower())
            mwl = TOKEN.findall(r["mwl"].lower())
            for p, m in align(pt, mwl):
                counts[p][m] += 1
    for p, c in sorted(counts.items(), key=lambda kv: -sum(kv[1].values())):
        total = sum(c.values())
        best = c.most_common(4)
        print(p, total, word(p), *(f"{m}:{k}" for m, k in best), sep="\t")


if __name__ == "__main__":
    main()
