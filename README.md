# pt2mirandese

`pt2mirandese` translates European Portuguese text into Mirandese with hand-written rules and two word lists. It is a baseline for a language with few resources: it needs no model and no network.

[Mirandese](https://en.wikipedia.org/wiki/Mirandese_language) (*lhéngua mirandesa*, ISO 639-3 `mwl`) is an Astur-Leonese language of the Terra de Miranda in north-east Portugal. It has fewer than 4,000 speakers and is co-official with Portuguese in its region. Its spelling follows the *Convenção Ortográfica da Língua Mirandesa* (1999).

## Install and use

```bash
uv pip install -e .
echo "O livro do meu pai está na mesa." | pt2mirandese
# L libro de l miu pai stá na mesa.
```

```python
from pt2mirandese import translate, word

translate("Ela foi com o irmão para a escola e começou a escrever um poema.")
# 'Eilha fui cul armano pa la scuola i ampeçou a screbir un poema.'
word("história")   # 'stória'
```

`translate` takes one sentence or line and keeps template slots such as `{name}`. `word` converts one lowercase word with no context.

## How it works

The translator works in three layers. A word goes to the first layer that has it.

1. **Closed classes** come from the tables of the Convenção: articles (*l*, *la*, *ls*, *las*), contractions (*de l*, *al*, *cul*, *pa l*), pronouns, possessives, demonstratives, prepositions, adverbs and the present tense of the irregular verbs. Each group names its PDF page in the code.
2. **Word lists.** `data/lexicon.tsv` holds 1,768 words whose Mirandese form the rules do not give, such as *tierra*, *muorte* and *anho*. `scripts/learn_lexicon.py` learns them from the train split of the parallel corpus. `data/wiktionary.tsv` adds 562 words from the Portuguese Wiktionary that the corpus does not check.
3. **Spelling rules** convert the rest. Among them: *v* > *b*, *-ção* > *-çon*, final *-z* > *-ç*, initial *es-* > *s-*, *en-*/*in-* > *an-*, pretonic *con-* > *cun-*, stressed final *-ia* > *-ie*, *-mento* > *-miento*, and the verb endings of the Convenção tables (*cantórun*, *comie*, *cantarie*).

Some rules need the words around a word. *a* is the article *la* except before an infinitive, a numeral or a pronoun. *la*, *l*, *de* and *que* elide before a vowel (*l'alma*, *d'outro*, *qu'el*). *nos* before the verb is the pronoun *mos*. Roman numerals, acronyms (*TV*), one-letter abbreviations (*a.C.*), web and e-mail addresses and template slots stay as they are.

The spelling follows the 2000 Adenda to the Convenção, which writes *ie*, *uo* and *ye* without the circumflex.

## Evaluation

| Set | Rows | Copy the Portuguese: chrF2 | Rules alone: chrF2 | pt2mirandese: exact | pt2mirandese: chrF2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `wikimedia_test.tsv` | 1,489 | 62.4 | 87.9 | 0.410 | 94.9 |
| `wikimedia_dev.tsv` | 493 | 62.0 | 87.5 | 0.416 | 94.5 |
| `tatoeba.tsv` | 41 | 32.4 | 47.2 | 0.244 | 54.8 |
| `convencao.tsv` | 76 | 36.5 | 73.6 | 0.908 | 89.2 |

"Exact" accepts the reference or an alternative after lowercasing. chrF2 is corpus chrF from sacrebleu. "Rules alone" switches both word lists off.

```bash
uv run --with sacrebleu --with-editable . python scripts/evaluate.py gold/wikimedia_test.tsv --errors 20
```

**The wikimedia sets are the main test.** They are Wikipedia articles that editors translated from Portuguese into Mirandese with the Content Translation tool (OPUS release v20260327). The rules were tuned on the dev split, and the test split was read only after each round of tuning was complete. The word list comes from the train split only, and a test checks that every entry occurs at least twice there.

**Machine drafts are left out.** Content Translation offers MinT drafts for Portuguese to Mirandese since 2023. Of the 440 published translations, 414 date from 2017, before MinT. `scripts/fetch_cx.py` lists the 17 translations published since 2023 (`gold/cx_mint_era.tsv`), which Content Translation records as 34% to 59% machine text, and `scripts/make_gold.py` drops the 481 pairs that come from them. The older text still shows a mechanical habit of some translators: Roman *VI* written *BI* and *TV* written *TB* in 23 rows.

**The test set shares its domain with the word list.** Encyclopaedic text by a few translators is the whole corpus. Tatoeba holds everyday sentences by other writers, and there the translator scores 54.8: it misses everyday words (*teç* for *pele*, *Adius* for *Tchau*) and idioms. Tatoeba and the Convenção examples are development sets: their passing rows are pinned in `gold/passing.txt`, and they guided the rules.

**The corpus does not always follow the Convenção.** Where the two differ, a native speaker should decide which form the translator writes by default:

- The corpus writes *libro* and *léngua* in most rows, where the Convenção asks for *lh-* in traditional words (*lhibro*, *lhéngua*). The word list follows the corpus.
- The corpus writes the object pronoun *nos* as *ne ls*. The translator writes *mos*, as the Convenção (p. 25) does, and so loses those rows.
- The Convenção (p. 17) lets proper names keep an official *V* (*Virgílio*). The corpus writes *Birgílio*, and place names take *b* (*Bimioso*), so the translator writes *b* in names too.

## Sources

- *Convenção Ortográfica da Língua Mirandesa* (1999). Câmara Municipal de Miranda do Douro and Centro de Linguística da Universidade de Lisboa.
- Ferreira, M. B. (2003). "Resposta a uma recensão crítica da Convenção Ortográfica da Língua Mirandesa". *Revista de Filoloxía Asturiana* 3-4, 327-343. It states what the 2000 Adenda changed.
- OPUS wikimedia mwl-pt, release v20260327 (CC-BY-SA 4.0). J. Tiedemann (2012), "Parallel Data, Tools and Interfaces in OPUS", LREC.
- Wiktionary, Portuguese edition, Mirandese entries (CC-BY-SA 4.0).
- Tatoeba (CC-BY 2.0 FR).

## Licence

The code is Apache-2.0. The word lists in `pt2mirandese/data/` and the wikimedia gold files are derived from CC-BY-SA 4.0 sources and are CC-BY-SA 4.0. `gold/tatoeba.tsv` is CC-BY 2.0 FR.
