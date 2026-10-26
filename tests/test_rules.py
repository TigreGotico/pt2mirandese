"""The spelling rules, checked on the examples of the Convenção Ortográfica (PDF pages) and of the corpus, with the
word lists switched off so that the rules alone produce each form."""
import pytest

from pt2mirandese import rules


@pytest.mark.parametrize("pt, mwl", [
    ("vida", "bida"),            # v > b, p. 17
    ("paz", "paç"),              # final -z > -ç, p. 13
    ("coração", "coraçon"),      # final nasal written n, p. 19
    ("convidado", "cumbidado"),  # pretonic con- > cun-, n > m before b, p. 19
    ("vinte", "binte"),          # p. 19
    ("noventa", "nobenta"),      # final -o stays, p. 16
    ("dia", "die"),              # stressed final -ia > -ie, p. 20
    ("comia", "comie"),          # imperfect, p. 32
    ("cantaria", "cantarie"),    # conditional, p. 31
    ("cantaram", "cantórun"),    # preterite 3pl, p. 31
    ("partiram", "partírun"),    # p. 33
    ("cantarão", "cantaran"),    # future 3pl, p. 31
    ("cantava", "cantaba"),      # p. 31
    ("encher", "ancher"),          # en- > an-, p. 36 note 38: anchir; the verb stem is lexical
    ("estado", "stado"),         # initial es + consonant > s, p. 16-17
])
def test_convencao_examples(pt, mwl):
    assert rules(pt) == mwl


@pytest.mark.parametrize("pt, mwl", [
    ("história", "stória"),          # an accented -ia keeps -ia; his + consonant > s
    ("ciência", "ciéncia"),          # the circumflex becomes acute
    ("sentimentos", "sentimientos"),  # -mento > -miento
    ("dialecto", "dialeto"),         # ct > t
    ("texto", "testo"),              # x before a consonant > s
    ("existe", "eisiste"),           # initial ex + vowel > eis
    ("descrito", "çcrito"),          # des + voiceless consonant > ç
    ("edição", "eidiçon"),           # pretonic initial e + consonant > ei
    ("utilizado", "outilizado"),     # pretonic initial u > ou; outelizado has a lexical i > e
    ("autor", "outor"),              # au- > ou-
    ("comentários", "comentairos"),  # -ário > -airo
    ("nasceu", "nasciu"),            # preterite 3sg -eu > -iu; naciu is lexical
    ("principais", "principales"),  # -ais > -ales
    ("impossível", "ampossible"),    # im- > am-, -ível > -ible
])
def test_corpus_patterns(pt, mwl):
    assert rules(pt) == mwl


def test_a_stressed_first_syllable_keeps_its_vowel():
    # obra and ordem stress the first syllable, so the pretonic o > ou rule does not apply.
    assert rules("obra") == "obra"
    assert rules("ordem") == "orden"


def test_the_imperfect_3rd_plural_takes_the_accent():
    # Convenção p. 31 prints cantában; the corpus writes -ában 3,014 times against 53 for -aban.
    assert [rules(w) for w in ("falavam", "andavam", "gaiavam")] == ["falában", "andában", "gaiában"]


def test_a_present_tense_in_avam_takes_no_accent():
    # gravar, travar: the present 3rd plural of a one-syllable stem in -av- (grában would be the imperfect of grar).
    assert [rules(w) for w in ("gravam", "travam", "cravam")] == ["graban", "traban", "craban"]


@pytest.mark.parametrize("pt, mwl", [
    # Convenção p. 31-33 model verbs. The corpus agrees (-áren 361 against -aren 21, -isse 376 against 1) or has no
    # form at all.
    ("cantaste", "canteste"),
    ("cantarem", "cantáren"),
    ("cantáreis", "cantárades"),
    ("cantásseis", "cantássedes"),
    ("comerem", "comíren"),
    ("comesse", "comisse"),
    ("comesses", "comisses"),
    ("comêssemos", "comíssemos"),
    ("comêsseis", "comíssedes"),
    ("comessem", "comíssen"),
    ("comêramos", "comíramos"),
    ("comêreis", "comírades"),
    ("partirem", "partíren"),
    ("partissem", "partíssen"),
    ("partísseis", "partíssedes"),
    ("partíreis", "partírades"),
])
def test_a_regular_verb_ending_follows_the_model_verbs(pt, mwl):
    assert rules(pt) == mwl
