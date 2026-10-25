"""Write pt2mirandese/data/names.txt: given names, which take no article in Mirandese (falei cun Virgílio).

A native speaker reports that a personal name takes no article in Mirandese, where European Portuguese writes one:
falei com o Virgílio > falei cun Virgílio. The names are the labels of the Wikidata items that are male, female or
unisex given names, one Latin-script word each. A place keeps its article (cul México, cula China). Encyclopaedic
Portuguese writes an article before a place (da Europa, na Índia) but not before a person (de Pedro Álvares Cabral),
so a word that the Portuguese side of the gold files writes after an article at least twice, and more often than
after a bare preposition, is left out, even when it is also a given name. So is a word written after a bare em
at least twice (em Atenas), because Portuguese writes em before a place and not before a person, unless a
capitalised surname follows the word five times as often (João Silva).

    python scripts/build_names.py names.csv     # a SPARQL CSV export with one column, name
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent
NAME = re.compile(r"[A-ZÀ-Ý][a-zà-ÿ]+(?:-[A-ZÀ-Ý][a-zà-ÿ]+)?")
ARTICLE = re.compile(r"(?<![\w-])(?:o|os|as|do|da|dos|das|no|na|nos|nas|ao|aos|à|às|pelo|pela)\s+([A-ZÀ-Ý][a-zà-ÿ]+)")
LOCATED = re.compile(r"(?<![\w-])em\s+([A-ZÀ-Ý][a-zà-ÿ]+)")
SURNAME = re.compile(r"(?<![\w-])([A-ZÀ-Ý][a-zà-ÿ]+)\s+[A-ZÀ-Ý]")
BARE = re.compile(r"(?<![\w-])(?:de|em|com|por|para)\s+([A-ZÀ-Ý][a-zà-ÿ]+)")


def main():
    names = {r["name"].strip() for r in csv.DictReader(Path(sys.argv[1]).read_text(encoding="utf-8").splitlines())}
    rows = 0
    articled, bare, located, surname = Counter(), Counter(), Counter(), Counter()
    for path in sorted((ROOT / "gold").glob("*.tsv")):
        if path.name == "cx_mint_era.tsv":
            continue
        for r in csv.DictReader(path.read_text(encoding="utf-8").splitlines(), delimiter="\t"):
            rows += 1
            articled.update(ARTICLE.findall(r["pt"]))
            bare.update(BARE.findall(r["pt"]))
            located.update(LOCATED.findall(r["pt"]))
            surname.update(SURNAME.findall(r["pt"]))
    place = {n for n in names if (articled[n] >= 2 and articled[n] > bare[n]) or (located[n] >= 2 and 5 * located[n] > surname[n])}
    kept = sorted(n for n in names if NAME.fullmatch(n) and n not in place)
    (ROOT / "pt2mirandese" / "data" / "names.txt").write_text("".join(n + "\n" for n in kept), encoding="utf-8")
    print(f"names in={len(names)} gold rows={rows} places={len(place)} "
          f"out={len(kept)}", file=sys.stderr)


if __name__ == "__main__":
    main()
