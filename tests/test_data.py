"""The word lists come from the train split and Wiktionary only, never from the dev or test split."""
import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "pt2mirandese" / "data"


def load(path):
    return list(csv.DictReader(path.read_text(encoding="utf-8").splitlines(), delimiter="\t"))


def test_the_corpus_list_is_what_the_train_split_gives():
    # Regenerating from train must give the shipped file. A list learned from dev or test, or one left stale after
    # a rule change, differs.
    shipped = (DATA / "lexicon.tsv").read_text(encoding="utf-8")
    try:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "learn_lexicon.py"),
                        str(ROOT / "gold" / "wikimedia_train.tsv")], check=True, capture_output=True)
        assert (DATA / "lexicon.tsv").read_text(encoding="utf-8") == shipped
    finally:
        (DATA / "lexicon.tsv").write_text(shipped, encoding="utf-8")


def test_wiktionary_entries_name_their_page():
    entries = load(DATA / "wiktionary.tsv")
    assert entries
    assert all(e["source_url"].startswith("https://pt.wiktionary.org/wiki/") for e in entries)


def test_entries_are_single_lowercase_words():
    for name in ("lexicon.tsv", "wiktionary.tsv"):
        for e in load(DATA / name):
            assert e["pt"] == e["pt"].lower() and " " not in e["pt"] and " " not in e["mwl"] and e["mwl"], e
