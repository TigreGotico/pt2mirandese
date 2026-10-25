"""Write data/lexicon.tsv: the words whose Mirandese form the rules do not give.

The script aligns the words of every parallel pair in gold/ (scripts/align.py) with the word list switched off, so
each Portuguese word is compared with the rules' output. A pair that occurs in more than one file counts once. A word
goes into the list when its most frequent one-word Mirandese form occurs at least MIN_COUNT times, covers at least
MIN_SHARE of the word's one-word alignments, occurs more often than the rules' output and differs from it. The
translators split on some words (lhéngua and léngua), so the most frequent form wins without a majority. A perfect
in -aram, -eram or -iram keeps the Convenção ending (-órun, -írun): the corpus writes some of them -an, which is
the future. A word the Convenção prints (data/convencao.tsv) is not learned: its form wins. Mirandese text is scarce, so the list learns from all of it; the rules alone are the score on unseen text.

    python scripts/learn_lexicon.py              # every file in gold/
    python scripts/learn_lexicon.py FILE ...     # these files only
"""
import csv
import hashlib
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

from align import TOKEN, align

import pt2mirandese

MIN_COUNT, MIN_SHARE = 2, 0.4
ROOT = Path(__file__).parent.parent
GOLD = ROOT / "gold"
NOT_PAIRS = {"cx_mint_era.tsv"}
CODE = ["pt2mirandese/__init__.py", "pt2mirandese/data/convencao.tsv", "scripts/align.py", "scripts/learn_lexicon.py"]


def inputs(paths):
    """The sha256 of every file the list depends on, written to data/lexicon.sources."""
    files = CODE + sorted(str(Path(p).resolve().relative_to(ROOT)) for p in paths)
    return "".join(f"{hashlib.sha256((ROOT / f).read_bytes()).hexdigest()}  {f}\n" for f in files)


def forget():
    # Each worker process imports pt2mirandese afresh, with the lists on disk loaded. The verb list comes from the
    # word list, so it goes too, or a verb it covers is never learned and drops out of the next build.
    pt2mirandese.LEXICON.clear()
    pt2mirandese.LEXICON_VERB.clear()


def pair_words(pair):
    return align(TOKEN.findall(pair[0]), TOKEN.findall(pair[1]))


def main():
    forget()
    paths = sys.argv[1:] or sorted(str(p) for p in GOLD.glob("*.tsv") if p.name not in NOT_PAIRS)
    rows, pairs = 0, set()
    for path in paths:
        for r in csv.DictReader(Path(path).read_text(encoding="utf-8").splitlines(), delimiter="\t"):
            rows += 1
            pairs.add((r["pt"].lower(), r["mwl"].lower()))
    counts = defaultdict(Counter)
    with Pool(initializer=forget) as pool:
        for aligned in pool.imap_unordered(pair_words, sorted(pairs), chunksize=64):
            for p, m in aligned:
                counts[p][m] += 1
    out = []
    for p, c in counts.items():
        rules = pt2mirandese.word(p)
        words = Counter({m: k for m, k in c.items() if m and " " not in m})
        if p in pt2mirandese.CLOSED or p in pt2mirandese.CONVENCAO or not words or rules.endswith("run"):
            continue
        form, n = min(words.items(), key=lambda fn: (-fn[1], fn[0]))
        total = sum(words.values())
        if n < MIN_COUNT or n / total < MIN_SHARE or n <= words[rules] or pt2mirandese._lh(form) == rules:
            continue
        out.append((p, form, n, total))
    out.sort()
    path = Path(pt2mirandese.__file__).parent / "data" / "lexicon.tsv"
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["pt", "mwl", "count", "total"])
        w.writerows(out)
    (path.parent / "lexicon.sources").write_text(inputs(paths), encoding="utf-8")
    print(f"files={len(paths)} rows={rows} unique_pairs={len(pairs)} pt_words={len(counts)} lexicon={len(out)}", file=sys.stderr)


if __name__ == "__main__":
    main()
