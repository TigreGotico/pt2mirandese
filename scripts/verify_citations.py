"""Check that every form the code quotes after "Convenção p. N:" is printed on that page of the Convenção.

The input is the text of the Convenção with "=== PDF page N ===" markers. The Convenção states no licence, so
its text is not part of this repository. The check reads the 1999 spelling: iê and uô match ie and uo.

    python scripts/verify_citations.py convencao1999_text.txt
"""
import re
import sys
import unicodedata
from pathlib import Path

import pt2mirandese

CITATION = re.compile(r"Convenção p\. ([\d\-]+(?:(?:, | and )\d+)*)(?: note \d+)?: ([^;\n]+)")


def fold(s):
    s = s.lower().replace("iê", "ie").replace("uô", "uo").replace("yê", "ye")
    return unicodedata.normalize("NFC", s)


def pages(spec):
    out = set()
    for part in re.split(r", | and ", spec):
        a, _, b = part.partition("-")
        out.update(range(int(a), int(b or a) + 1))
    return out


def main():
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    page_text = {int(n): fold(t) for n, t in re.findall(r"=== PDF page (\d+) ===\n(.*?)(?==== PDF page|\Z)", text, re.DOTALL)}
    source = Path(pt2mirandese.__file__).read_text(encoding="utf-8")
    checked, missing = 0, []
    for spec, forms in CITATION.findall(source):
        for form in re.split(r", | / ", forms.split(".")[0]):
            form = form.strip().strip("()")
            if not form or " " in form and not form.startswith(("nun ", "dá-")):
                continue
            checked += 1
            if not any(fold(form) in page_text.get(p, "") for p in pages(spec)):
                missing.append(f"p. {spec}: {form}")
    print(f"forms checked={checked} missing={len(missing)}")
    for m in missing:
        print("  ", m)
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
