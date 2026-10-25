# Gold data

Every file has the same columns.

| Column | Content |
| --- | --- |
| `id` | `w` + line number in the OPUS release, `t` + Tatoeba sentence id, or `R` + rule id |
| `pt` | the European Portuguese |
| `mwl` | the Mirandese reference |
| `alt` | other accepted forms, separated by `|` |
| `source` | where the pair comes from |
| `kind` | `word`, `phrase` or `sentence` |
| `class` | `closed`, `regular` or `lexical` for the Convenção rows |
| `note` | for the Convenção rows, whether the source prints the Portuguese or the Portuguese is a gloss |

## wikimedia_train.tsv, wikimedia_dev.tsv, wikimedia_test.tsv

These come from the OPUS wikimedia mwl-pt release v20260327: 9,709 sentence pairs from Wikipedia articles that editors translated from Portuguese into Mirandese with the Content Translation tool. `scripts/make_gold.py` builds them. It drops a pair when the two sides are the same (33), when a side has fewer than three words (1,105), when the length ratio shows a sentence cut on one side (334), when the Portuguese repeats an earlier pair (19), and when the Mirandese comes from a translation published since MinT machine drafts arrived in 2023 (481). That leaves 7,737 pairs. `cx_mint_era.tsv` lists those translations; `scripts/fetch_cx.py` writes it.

The first hex digit of the sha256 of the Portuguese side picks the split, so the split does not depend on the order of the release: 0 to 2 is test (1,489), 3 is dev (493) and the rest is train (5,755). The word list learns from train only. The rules were tuned on dev; the test split was read only after each round of tuning.

The Mirandese side is text that editors wrote, not checked against the Convenção. Its translators write *l-* where the Convenção asks for *lh-* in most words (*libro*, *léngua*), and some rows keep a Portuguese word.

The files are CC-BY-SA 4.0, as the OPUS release is. `OPUS_wikimedia_LICENSE` is the licence text from the release.

## tatoeba.tsv

41 everyday sentences from Tatoeba with a link between Mirandese and Portuguese. Some Portuguese sides are Brazilian (*Papai Noel*, *Me chame*). Tatoeba is CC-BY 2.0 FR.

## convencao.tsv

76 example pairs from the *Convenção Ortográfica da Língua Mirandesa* (1999), one per rule, each with its PDF page. The Mirandese is written in the spelling of the 2000 Adenda (*ie*, *uo*, *ye*). Most Portuguese sides are glosses of the printed Mirandese, as the `note` column says. Two rows follow other sources: 200 is *dous cientos* by a native-speaker ruling, with *duzientos* as an alternative, and the 3rd plural forms accept the form without an accent that the corpus writes.

The rules come from the same book, so this set measures coverage of the norm, not translation of unseen text.

## passing.txt

The ids of the dev rows that the translator gets exactly right. `tests/test_gold.py` fails when one of them stops passing. `scripts/pin_passing.py` rewrites the list.
