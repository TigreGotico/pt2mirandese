"""Every gold row listed in gold/passing.txt must keep translating to its reference or an alternative. A rule
change that breaks one fails here; a change that fixes more rows adds them with scripts/pin_passing.py."""
import csv
from pathlib import Path

from pt2mirandese import translate

GOLD = Path(__file__).parent.parent / "gold"
DEV_FILES = ("convencao.tsv", "wikimedia_dev.tsv", "tatoeba.tsv")


def norm(s):
    return " ".join(s.lower().replace("’", "'").replace("´", "'").split())


def load(name):
    return list(csv.DictReader((GOLD / name).read_text(encoding="utf-8").splitlines(), delimiter="\t"))


def test_passing_rows_still_pass():
    rows = {r["id"]: r for name in DEV_FILES for r in load(name)}
    expected = set((GOLD / "passing.txt").read_text().split())
    assert expected <= set(rows)
    broken = [i for i in sorted(expected) if norm(translate(rows[i]["pt"]))
              not in {norm(rows[i]["mwl"])} | {norm(a) for a in rows[i]["alt"].split("|") if a.strip()}]
    assert not broken, f"rows that passed and now fail: {broken}"


def test_the_splits_share_no_sentence():
    seen = {}
    for name in ("wikimedia_train.tsv", "wikimedia_dev.tsv", "wikimedia_test.tsv"):
        for r in load(name):
            assert seen.setdefault(r["pt"], name) == name, f"{r['id']} is in {seen[r['pt']]} and {name}"
