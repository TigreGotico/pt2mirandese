# Rule sources

`citations.tsv` lists 78 rules of the *Convenção Ortográfica da Língua Mirandesa* (1999). Each row gives the section, the PDF page, a short quote from that page and an example pair. The `class` column says whether the Portuguese spelling predicts the rule (`regular`), a word list must carry it (`lexical`), or it is a fixed table (`closed`). The `pt_basis` column says whether the book prints the Portuguese form or the Portuguese is a gloss of the printed Mirandese.

The Convenção PDF prints no page numbers, so every page is a PDF page.

`scripts/verify_citations.py` checks that each form the code quotes after "Convenção p. N:" occurs on that page. It needs the text of the Convenção with page markers, which this repository does not hold, because the Convenção states no licence:

```bash
python scripts/verify_citations.py convencao1999_text.txt
```

The PDF is at https://mirandadodouro.jfreguesia.com/images/stories/PDF/convencaomirandes.pdf.
