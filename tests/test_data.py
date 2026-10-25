"""The word lists are up to date with the rules and the parallel data they come from."""
import csv
import hashlib
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "pt2mirandese" / "data"


def load(path):
    return list(csv.DictReader(path.read_text(encoding="utf-8").splitlines(), delimiter="\t"))


def test_the_corpus_list_was_learned_from_the_current_rules_and_data():
    # scripts/learn_lexicon.py writes the sha256 of the rules, the aligner, itself and every gold file it read. A
    # rule change, a new gold file or a hand edit of a gold file without a relearn leaves a stale hash.
    listed = dict(reversed(line.split("  ", 1)) for line in (DATA / "lexicon.sources").read_text().splitlines())
    gold = {f"gold/{p.name}" for p in (ROOT / "gold").glob("*.tsv") if p.name != "cx_mint_era.tsv"}
    assert {f for f in listed if f.startswith("gold/")} == gold
    stale = [f for f, digest in listed.items() if hashlib.sha256((ROOT / f).read_bytes()).hexdigest() != digest]
    assert not stale, f"relearn with scripts/learn_lexicon.py: {stale}"


def test_the_learner_ignores_the_list_on_disk():
    # The learner compares the corpus with the rules alone. Its worker processes must not align with the list that
    # an earlier run left in data/, or each run learns from the one before.
    files = [DATA / "lexicon.tsv", DATA / "lexicon.sources"]
    kept = [f.read_bytes() for f in files]
    learn = [sys.executable, str(ROOT / "scripts" / "learn_lexicon.py"), str(ROOT / "gold" / "tatoeba.tsv"),
             str(ROOT / "gold" / "convencao.tsv")]
    try:
        subprocess.run(learn, check=True, capture_output=True)
        first = (DATA / "lexicon.tsv").read_text(encoding="utf-8")
        (DATA / "lexicon.tsv").write_text("pt\tmwl\tcount\ttotal\n" + "".join(
            f"{w}\tzzz\t9\t9\n" for w in ("o", "a", "de", "que", "não", "eu", "é", "lua", "nos")), encoding="utf-8")
        subprocess.run(learn, check=True, capture_output=True)
        assert (DATA / "lexicon.tsv").read_text(encoding="utf-8") == first
    finally:
        for f, content in zip(files, kept):
            f.write_bytes(content)


def test_the_learner_forgets_the_verb_list_too():
    # The verb list derives from the word list. A learner that keeps it never learns the verbs it covers, and the
    # next build of the verb list loses them.
    import pt2mirandese
    sys.path.insert(0, str(ROOT / "scripts"))
    import learn_lexicon
    learn_lexicon.forget()
    assert not pt2mirandese.LEXICON and not pt2mirandese.LEXICON_VERB
    importlib.reload(pt2mirandese)


def test_wiktionary_entries_name_their_page():
    entries = load(DATA / "wiktionary.tsv")
    assert entries
    assert all(e["source_url"].startswith("https://pt.wiktionary.org/wiki/") for e in entries)


def test_entries_are_single_lowercase_words():
    for name in ("lexicon.tsv", "wiktionary.tsv"):
        for e in load(DATA / name):
            assert e["pt"] == e["pt"].lower() and " " not in e["pt"] and " " not in e["mwl"] and e["mwl"], e


def test_the_verb_list_is_current():
    # scripts/build_verbs.py reads the word lists and the gold files; a relearn without a rebuild leaves it stale.
    path = DATA / "verbs.tsv"
    kept = path.read_bytes()
    try:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_verbs.py")], check=True, capture_output=True)
        assert path.read_bytes() == kept, "rebuild with scripts/build_verbs.py"
    finally:
        path.write_bytes(kept)
