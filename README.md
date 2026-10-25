# pt2mirandese

`pt2mirandese` translates European Portuguese text into Mirandese with hand-written rules and word lists. It is a baseline for a language with few resources: it needs no model and no network.

[Mirandese](https://en.wikipedia.org/wiki/Mirandese_language) (*lhéngua mirandesa*, ISO 639-3 `mwl`) is an Astur-Leonese language of the Terra de Miranda in north-east Portugal. It has fewer than 4,000 speakers and is co-official with Portuguese in its region. Its spelling follows the *Convenção Ortográfica da Língua Mirandesa* (1999).

## Install and use

```bash
uv pip install -e .
echo "O livro do meu pai está na mesa." | pt2mirandese
# L lhibro de l miu pai stá na mesa.
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
2. **Word lists.** `data/convencao.tsv` comes first: it holds 1,699 words that the Convenção prints, such as *scola*, *dixo* and *irie*, and its form wins over the corpus. Claude Opus 5.5 glossed each Mirandese word on each page into Portuguese, and a second pass checked each gloss against its page. A gloss stays only when the word is Mirandese, the gloss is right, and the Portuguese word has no other common sense that Mirandese writes differently: *verão* is summer as well as *beran*, they will see. `scripts/build_convencao.py` builds the list. `data/lexicon.tsv` holds 10,424 words whose Mirandese form the rules do not give, such as *tierra*, *muorte* and *anho*. `scripts/learn_lexicon.py` learns them from every parallel pair in `gold/`: 113,259 rows, of which 109,678 are different pairs. Where the writers disagree (*lhéngua* and *léngua*), the most frequent form wins. `data/lhenguabase.tsv` adds 296 words from the [Lhenguabase](https://lhenguabase.wikibase.cloud) that the parallel data does not check, such as *gabilanes* and *majaricones*. The Lhenguabase glosses a lemma, so Claude Opus 5.5 gave each Mirandese form the Portuguese word in the same gender and number. `data/wiktionary.tsv` adds 176 more from the Portuguese Wiktionary.
3. **Spelling rules** convert the rest. Among them: *v* > *b*, *-ção* > *-çon*, final *-z* > *-ç*, initial *es-* > *s-*, *en-*/*in-* > *an-*, pretonic *con-* > *cun-*, stressed final *-ia* > *-ie*, *-mento* > *-miento*, and the verb endings of the Convenção tables (*cantórun*, *comie*, *cantarie*).

Some rules need the words around a word. *a* is the article *la* except before an infinitive, a numeral or a pronoun. *la*, *l*, *de* and *que* elide before a vowel (*l'alma*, *d'outro*, *qu'el*). *nos* before the verb is the pronoun *mos*. Roman numerals, acronyms (*TV*), one-letter abbreviations (*a.C.*), web and e-mail addresses and template slots stay as they are.

The spelling follows the 2000 Adenda to the Convenção, which writes *ie*, *uo* and *ye* without the circumflex.

## Evaluation

| Set | Rows | Copy the Portuguese: chrF2 | Rules alone: exact | Rules alone: chrF2 | pt2mirandese: exact | pt2mirandese: chrF2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `wikimedia_test.tsv` | 1,489 | 62.4 | 0.075 | 87.3 | 0.375 | 94.9 |
| `wikimedia_dev.tsv` | 493 | 62.0 | 0.095 | 86.8 | 0.377 | 94.5 |
| `wikipedia_mined.tsv` | 54,360 | 58.0 | 0.036 | 82.7 | 0.252 | 91.3 |
| `tatoeba.tsv` | 35 | 35.1 | 0.229 | 50.2 | 0.457 | 63.5 |
| `convencao.tsv` | 76 | 36.5 | 0.711 | 74.3 | 0.987 | 96.3 |

"Exact" accepts the reference or an alternative after lowercasing. chrF2 is corpus chrF from sacrebleu. "Rules alone" switches all the word lists off.

```bash
uv run --with sacrebleu --with-editable . python scripts/evaluate.py gold/wikimedia_test.tsv --no-lexicon --errors 20
```

**Rules alone is the score on unseen text.** The word lists learn from every file in `gold/`, the test files included, so the full pt2mirandese columns show how well the lists fit the data they come from. They are not a held-out score. Mirandese text is scarce, and the translator is meant to make synthetic training data for a later translation model, so it uses all the parallel text there is. The rules were tuned on `wikimedia_dev.tsv`, and the test split was read only after each round of tuning, so the rules-alone score on `wikimedia_test.tsv` is held out.

**Machine drafts are left out.** Content Translation offers MinT drafts for Portuguese to Mirandese since 2023. Of the 440 published translations, 414 date from 2017, before MinT. `scripts/fetch_cx.py` lists the 17 translations published since 2023 (`gold/cx_mint_era.tsv`), which Content Translation records as 34% to 59% machine text, and `scripts/make_gold.py` drops the 481 pairs that come from them. The older text still shows a mechanical habit of some translators: Roman *VI* written *BI* and *TV* written *TB* in 23 rows.

**One Portuguese side is machine translation.** `gold/wikipedia_backtranslated.tsv` pairs 51,045 Mirandese Wikipedia sentences with Portuguese from Claude Haiku 5.5. Its Mirandese side gives the word list real forms, but its Portuguese side is not a reference, so the table does not score it.

**Encyclopaedic text is most of the data.** Tatoeba holds everyday sentences by other writers, and there the translator scores 63.5: it misses everyday words (*teç* for *pele*, *Adius* for *Tchau*) and idioms.

**The corpus does not always follow the Convenção.** Where the two differ, the translator follows the Convenção, and loses exact matches against references that follow the corpus. On `wikimedia_dev.tsv` the printed words, *lh-* and proper names cost 41 of 493 rows together: 227 rows pass with the corpus forms, 186 with the Convenção forms.

- A word the Convenção prints takes that form (`data/convencao.tsv`): *scola*, where the corpus writes *scuola* 593 times.
- The Convenção (p. 15) asks for *lh-* in traditional words (*lhibro*, *lhéngua*, *lhuna*) and *l-* in neologisms, loanwords and proper names. The corpus mixes the two in both kinds of word, so its counts cannot tell them apart. `data/lh.tsv` lists the words that a curated source writes with *lh-*: the examples of the Convenção, the Portuguese Wiktionary and the [Lhenguabase](https://lhenguabase.wikibase.cloud). The translator writes *lh-* for those words and their verb forms, and *l-* for the rest (*lógica*, *laboratório*). `scripts/build_lh.py` builds the list.
- The corpus writes the object pronoun *nos* as *ne ls*. The translator writes *mos*, as the Convenção (p. 25) does, and so loses those rows.
- The Convenção (p. 17) lets proper names keep an official *V* (*Virgílio*). The corpus writes *Birgílio*. The translator keeps *V* and initial *l-* in a capitalised word inside a sentence, unless the word list has a Mirandese form for it (*Lisboua*) or the word is a common word in capitals (*Universidade*, *Revolução*). `data/common.txt` lists the common words: the words with a *v* or an initial *l* that the Portuguese side of the gold files writes in lowercase three times or more. `scripts/build_common.py` builds the list.

## Sources

- *Convenção Ortográfica da Língua Mirandesa* (1999). Câmara Municipal de Miranda do Douro and Centro de Linguística da Universidade de Lisboa.
- Ferreira, M. B. (2003). "Resposta a uma recensão crítica da Convenção Ortográfica da Língua Mirandesa". *Revista de Filoloxía Asturiana* 3-4, 327-343. It states what the 2000 Adenda changed.
- OPUS wikimedia mwl-pt, release v20260327 (CC-BY-SA 4.0). J. Tiedemann (2012), "Parallel Data, Tools and Interfaces in OPUS", LREC.
- Portuguese and Mirandese Wikipedia (CC-BY-SA 4.0), for the mined and back-translated pairs.
- Wiktionary, Portuguese edition, Mirandese entries (CC-BY-SA 4.0).
- Lhenguabase, the Mirandese lexical database on Wikibase Cloud (CC-BY-SA 4.0). `scripts/fetch_lhenguabase.py` downloads it.
- Tatoeba (CC-BY 2.0 FR).

## Licence

The code is Apache-2.0. The word lists in `pt2mirandese/data/` and the Wikipedia gold files are derived from CC-BY-SA 4.0 sources and are CC-BY-SA 4.0. `gold/tatoeba.tsv` is CC-BY 2.0 FR.
