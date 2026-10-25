"""Rules that need the words around a word: articles and contractions, the preposition a, elision, enclitics and
the object pronoun nos. Each expected form is printed in the Convenção (PDF page) or counted in the corpus."""
import pytest

from pt2mirandese import translate


@pytest.mark.parametrize("pt, mwl", [
    ("o livro", "l libro"),                    # article l, p. 23
    ("a alma", "l'alma"),                      # la > l' before a vowel, p. 21
    ("ao rei", "al rei"),                      # a + o > al, p. 24
    ("à porta", "a la puorta"),                # a + a stays apart, p. 24
    ("do rei", "de l rei"),                    # p. 24
    ("com os filhos", "culs filhos"),          # p. 25
    ("para o céu", "pa l cielo"),              # p. 25
    ("numa casa", "nua casa"),                 # p. 25, nũa written without the tilde
    ("de uma casa", "dua casa"),               # de um > dun, p. 25
])
def test_articles_and_contractions(pt, mwl):
    assert translate(pt) == mwl


def test_a_is_a_preposition_before_an_infinitive_and_an_article_before_a_noun():
    # Corpus: the preposition a before an infinitive 411 times; la before a noun.
    assert translate("começou a escrever a obra") == "ampeçou a screbir l'obra"


def test_a_before_a_numeral_is_a_preposition():
    assert translate("a 3 de maio") == "a 3 de maio"


def test_one_letter_abbreviations_stay():
    assert translate("no século V a.C.") == "ne l seclo V a.C."


def test_de_and_que_elide_before_a_lowercase_vowel_only():
    # Corpus: d' 629 against de 64 before a lowercase vowel; de 599 against d' 6 before a capital.
    assert translate("o nome de outro") == "l nome d'outro"
    assert translate("o rei de Espanha") == "l rei de Spanha"


def test_enclitic_pronouns_stay_after_the_hyphen():
    # p. 22: dá-me-lo; the indirect and the direct pronoun stay apart.
    assert translate("dá-mo") == "dá-me-lo"


def test_nos_before_the_verb_is_the_object_pronoun():
    # p. 25: mos in the pronoun table, fai-mos; Tatoeba 8406327: nun mos déixedes.
    assert translate("não nos deixes") == "nun mos deixes"


def test_nos_before_a_plural_noun_is_the_contraction():
    assert translate("já nos anos 80") == "yá ne ls anhos 80"


def test_a_before_a_feminine_possessive_is_the_article():
    # Corpus: la sue 195, a sue 0.
    assert translate("A sua obra") == "La sue obra"


def test_an_enclitic_does_not_elide_before_a_vowel():
    assert translate("comprá-la e") == "cumprá-la i"


def test_a_verb_before_lo_or_la_is_an_infinitive():
    # p. 20: perdé-lo; corpus: vê > bé 7 times.
    assert translate("quero vê-la") == "quiero bé-la"


def test_no_lo_is_mos_lo():
    # p. 26: mos-lo.
    assert translate("dá-no-lo") == "dá-mos-lo"


def test_sentence_final_e_is_a_verb():
    assert translate("assim é.") == "assi ye."


def test_addresses_and_acronyms_stay():
    assert translate("a TV e exemplo.pt/vida") == "la TV i exemplo.pt/vida"
    assert translate("escreva para eu@vida.pt") == "screba para eu@vida.pt"


def test_all_caps_text_stays_in_capitals():
    assert translate("O LIVRO DO REI") == "L LIBRO DE L REI"


def test_case_and_template_slots_are_kept():
    assert translate("O {name} vive em Lisboa.") == "L {name} bibe an Lisboua."


def test_each_line_is_translated_on_its_own():
    assert translate("o livro\na casa") == "l libro\nla casa"
