"""evaluate.py --hyps scores saved output with the same metrics as the translator."""
import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
GOLD = ROOT / "gold" / "convencao.tsv"


def run(tmp_path, column):
    rows = list(csv.DictReader(GOLD.read_text(encoding="utf-8").splitlines(), delimiter="\t"))
    with open(tmp_path / GOLD.name, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["id", "hyp"])
        w.writerows((r["id"], r[column]) for r in rows)
    out = subprocess.run([sys.executable, ROOT / "scripts" / "evaluate.py", GOLD, "--hyps", tmp_path],
                         capture_output=True, text=True, check=True).stdout
    return out.splitlines()[-1].strip("| ").split(" | ")


def test_the_references_score_full_marks(tmp_path):
    assert run(tmp_path, "mwl")[4:] == ["1.000", "100.0"]


def test_a_copy_of_the_portuguese_scores_as_the_copy_columns(tmp_path):
    cells = run(tmp_path, "pt")
    assert cells[4:] == cells[2:4]
