"""Rule-based European Portuguese to Mirandese.

The rules follow the Convenção Ortográfica da Língua Mirandesa (1999) in the spelling of its 2000 Adenda, which
writes ie, uo and ye without the circumflex. A comment that names "Convenção p. 24" points to that PDF page. A
comment that names "corpus" marks a form taken from the Mirandese side of the train split of the OPUS wikimedia
pairs, the Wikipedia articles that editors translated from Portuguese, with its count there.

Words the rules cannot derive from the Portuguese spelling, such as the ie and uo diphthongs (terra > tierra) or
the kept Latin -n- (lua > luna), come from data/lexicon.tsv. scripts/learn_lexicon.py writes that file from the
train split, and only for words where the rules give a different form.

    echo "O livro do meu pai está na mesa." | pt2mirandese
"""
import csv
import re
import sys
import unicodedata
from importlib import resources

# Closed classes from the Convenção tables. Articles, Convenção p. 23; un, ũa, p. 19 and 24, written ua as the
# Convenção allows (p. 19) and as the corpus writes it (ua 993, ũa 2).
CLOSED = {
    "o": "l", "a": "la", "os": "ls", "as": "las", "um": "un", "uma": "ua", "uns": "uns", "umas": "uas",
    # Contractions, Convenção p. 24-25.
    "ao": "al", "aos": "als", "à": "a la", "às": "a las", "do": "de l", "da": "de la", "dos": "de ls",
    "das": "de las", "no": "ne l", "na": "na", "nos": "ne ls", "nas": "nas", "pelo": "pul", "pela": "pula",
    "pelos": "puls", "pelas": "pulas", "num": "nun", "numa": "nua", "nuns": "nuns", "numas": "nuas", "dum": "dun",
    "duma": "dua", "duns": "duns", "dumas": "duas",
    # Personal pronouns, Convenção p. 25-26.
    "eu": "you", "ele": "el", "ela": "eilha", "eles": "eilhes", "elas": "eilhas", "vós": "bós", "lhe": "le",
    "lhes": "les", "mim": "mi", "comigo": "cumigo", "contigo": "cuntigo",
    # consigo > cunsigo, corpus (2); the Convenção p. 26 table gives cun el for the 3rd person.
    "consigo": "cunsigo",
    "dele": "del", "dela": "deilha", "deles": "deilhes", "delas": "deilhas",
    # Possessives, Convenção p. 27.
    "meu": "miu", "minha": "mie", "meus": "mius", "minhas": "mies", "teu": "tou", "tua": "tue", "teus": "tous",
    "tuas": "tues", "seu": "sou", "sua": "sue", "seus": "sous", "suas": "sues", "nosso": "nuosso",
    "nossa": "nuossa", "nossos": "nuossos", "nossas": "nuossas", "vosso": "buosso", "vossa": "buossa",
    # Demonstratives, Convenção p. 27.
    "aquele": "aquel", "aquela": "aqueilha", "aqueles": "aqueilhes", "aquelas": "aqueilhas", "aquilo": "aquilho",
    "este": "este", "esta": "esta", "estes": "estes", "estas": "estas", "esse": "esse", "essa": "essa",
    "esses": "esses", "essas": "essas",
    # isto, isso > esto, esso, corpus (esto 31, esso 58; isto 0, isso 1).
    "isto": "esto", "isso": "esso",
    "daquele": "d'aquel", "daquela": "d'aqueilha", "naquele": "naquel", "naquela": "naqueilha",
    # Indefinites and interrogatives, Convenção p. 28.
    "algum": "algun", "alguma": "algua", "nenhum": "ningun", "nenhuma": "ningua", "alguém": "alguien",
    "ninguém": "naide", "quem": "quien", "quais": "quales", "tudo": "todo", "certo": "cierto",
    "certa": "cierta",
    # mais, Convenção p. 28 (más / mais); corpus: mais 548, más 5.
    "mais": "mais",
    # Conjunctions, Convenção p. 28; ou > ó, corpus (ó 358, ou 13).
    "e": "i", "nem": "nin", "pois": "puis", "ou": "ó",
    # Prepositions, Convenção p. 24; com > cun, corpus (cun 590, com 54). desde > zde, corpus (zde 84, dende 12,
    # desde 0); the Convenção p. 24 prints dende and desde.
    "em": "an", "com": "cun", "entre": "antre", "sobre": "subre", "sem": "sin", "desde": "zde",
    # Adverbs, Convenção p. 29-30; não > nun, p. 29.
    "não": "nun", "aqui": "eiqui", "ali": "alhi", "lá": "alhá", "onde": "adonde", "dentro": "drento",
    "fora": "fuora", "então": "anton", "hoje": "hoije", "ainda": "inda", "logo": "lhougo", "amanhã": "manhana",
    "ontem": "onte", "sempre": "siempre", "já": "yá", "também": "tamien", "assim": "assi", "bem": "bien",
    "depois": "depuis", "muito": "mui", "como": "cumo",
    # após > passado, além > para alhá, apenas > solo, corpus (passado 136, para alhá 88, solo 167). The
    # Convenção p. 24 prints the preposition apuis, which the corpus does not use.
    "após": "passado", "além": "para alhá", "apenas": "solo",
    # é > ye, Convenção p. 18, in the Adenda spelling.
    "é": "ye",
    # The tables of ser, star, tener and ir, Convenção p. 34-35 and 46.
    "sou": "sou", "és": "sós", "são": "son", "somos": "somos", "foi": "fui", "foram": "fúrun", "eram": "éran",
    "estou": "stou", "estás": "stás", "está": "stá", "estamos": "stamos", "estão": "stan", "estar": "star",
    "estava": "staba", "estavam": "stában", "esteve": "stubo",
    "ter": "tener", "tenho": "tengo", "tens": "tenes", "tem": "ten", "temos": "tenemos", "têm": "ténen",
    "tinha": "tenie", "tinham": "tenien", "teria": "tenerie", "teriam": "tenerien", "teve": "tubo",
    "tendo": "tenendo", "tido": "tenido",
    "vou": "bou", "vais": "bás", "vai": "bai", "vamos": "bamos", "vão": "ban", "há": "hai",
    # poder has no table in the Convenção; pode > puode, corpus (77).
    "pode": "puode", "podem": "puoden",
    # Present tense of the irregular verbs fazer, dezir, ber, benir, querer and saber, Convenção p. 37-50.
    "faço": "fago", "faz": "faç", "fazem": "fázen", "digo": "digo", "diz": "diç", "dizem": "dízen",
    "vejo": "beio", "vês": "bés", "vê": "bei", "veem": "béien", "vêem": "béien", "venho": "bengo", "vens": "benes",
    "vem": "ben", "vêm": "bénen", "vir": "benir", "quero": "quiero", "queres": "quieres", "quer": "quier",
    "querem": "quieren", "sabem": "sáben",
    # Weekdays, Convenção p. 55, which prints Deimingo / Demingo.
    "domingo": "demingo",
    # Numerals, Convenção p. 55.
    "dois": "dous", "duas": "dues", "três": "trés", "sete": "siete", "oito": "uito", "nove": "nuobe",
    "dez": "dieç", "cem": "cien",
}
# A Portuguese word that a contraction or a preposition turns into two words, and the article it ends in.
# de um > dun and em um > nun, Convenção p. 25.
ARTICLE_AFTER = {"com": {"o": "cul", "a": "cula", "os": "culs", "as": "culas"},
                 "para": {"o": "pa l", "a": "pa la", "os": "pa ls", "as": "pa las"},
                 "de": {"um": "dun", "uma": "dua", "uns": "duns", "umas": "duas"},
                 "em": {"um": "nun", "uma": "nua", "uns": "nuns", "umas": "nuas"}}
# Portuguese a is the article la, but stays the preposition a before an infinitive, a numeral or a pronoun:
# ampeçou a screbir, a 3 de Maio, a el. Corpus counts of the preposition a: before an infinitive 411, before a
# number 40, before a pronoun or determiner 140. A feminine possessive takes the article: la sue (195), a sue (0).
PREP_A_BEFORE = {"um", "uma", "uns", "umas", "ele", "ela", "eles", "elas", "este", "esta", "estes", "estas", "esse",
                 "essa", "esses", "essas", "isso", "isto", "todos", "todas", "outros", "outras", "cada", "partir",
                 "respeito", "mim", "ti", "si", "nós", "vós", "você", "vocês", "quem", "qual", "quais", "seu", "seus",
                 "meu", "nosso", "pé", "cavalo", "fim", "menos", "pouco"}
NOUN_IN_R = {"mulher", "colher"}
# Words after which Portuguese puts an object pronoun before the verb. nos after them is the pronoun only when the
# next word is a lowercase word that does not end in -os or -as, as a verb form does: já nos anos is a contraction.
BEFORE_CLITIC = {"não", "que", "se", "também", "já", "nunca", "quem", "onde", "quando", "porque", "ainda",
                 "sempre", "nem", "lhe", "eles", "elas", "nós"}
INFINITIVE = re.compile(r"(ar|er|ir|ôr)(-\w+)?$")
# Object pronouns after a hyphen, Convenção p. 22 and 25; an indirect and a direct pronoun stay apart, Convenção
# p. 26: dá-me-lo, mos-lo, bos-lo.
ENCLITIC = {"mo": "me-lo", "ma": "me-la", "mos": "me-los", "mas": "me-las", "to": "te-lo", "ta": "te-la",
            "lho": "le-lo", "lha": "le-la", "lhos": "le-los", "lhas": "le-las", "no": "mos", "vo": "bos",
            "o": "lo", "a": "la", "os": "los", "as": "las", "lhe": "le", "lhes": "les", "nos": "mos", "vos": "bos",
            "me": "me", "te": "te", "se": "se", "lo": "lo", "la": "la", "los": "los", "las": "las"}
# A verb before -lo, -la, -los, -las is an infinitive that lost its r (vê-la, dá-lo), Convenção p. 20: perdé-lo.
INFINITIVE_CLITIC = {"lo", "la", "los", "las"}
# Endings, longest first. Each is (Portuguese, Mirandese).
ENDINGS = [
    ("arão", "aran"), ("erão", "eran"), ("irão", "iran"),                     # Convenção p. 31: cantaran
    ("ções", "çones"), ("ção", "çon"), ("ões", "ones"), ("ão", "on"),          # Convenção p. 19: coraçon
    ("agens", "aiges"), ("agem", "aige"),                                     # Wiktionary: aragem > araige
    ("áveis", "ables"), ("íveis", "ibles"), ("ável", "able"), ("ível", "ible"),  # corpus: ampossible
    ("ais", "ales"), ("éis", "eles"), ("óis", "oles"),                        # corpus: profissionales
    ("ês", "és"),                                                             # corpus: anglés, mirandés
    ("aram", "órun"), ("eram", "írun"), ("iram", "írun"),                     # Convenção p. 31-33
    ("ias", "ies"), ("iam", "ien"), ("ia", "ie"),                             # Convenção p. 20 and 32: die, comie
]
# Preterite 3sg -eu > -iu, Convenção p. 32: comiu. The corpus writes nouns the same way: dius, judius, caldiu.
VERB_EU = re.compile(r"[^aeiou]eu$")
NUCLEUS = re.compile(r"[aeiouáéíóúâêôãõàü]+")
ACCENT = re.compile(r"[áéíóúâêôãõ]")


def _stress(w: str) -> int:
    """The index of the stressed vowel group of a Portuguese word, by the written accent or the default rule."""
    groups = [m.group() for m in NUCLEUS.finditer(w)]
    for i, g in enumerate(groups):
        if re.search("[áéíóúâêô]", g):
            return i
    for i, g in enumerate(groups):
        if re.search("[ãõ]", g):
            return i
    if len(groups) > 1 and re.search(r"([aeo]s?|[ae]m|ens)$", w):
        return len(groups) - 2
    return len(groups) - 1


def _load(name):
    path = resources.files(__package__) / "data" / name
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        return {r["pt"]: r["mwl"] for r in csv.DictReader(f, delimiter="\t")}


# The corpus list wins over Wiktionary: it records the form the translators of running text chose.
LEXICON = _load("wiktionary.tsv") | _load("lexicon.tsv")


def rules(w: str) -> str:
    """Spell one lowercase Portuguese word by the regular rules alone, with no word list."""
    first_unstressed = _stress(w) > 0
    if len(w) > 2:
        for pt, mwl in ENDINGS:
            # A final -ia is stressed only when the word has no written accent: die, but stória. It applies after a
            # one-letter stem too (dia), the other endings after two letters or more (mais, pais stay).
            stem = 1 if pt in ("ia", "ias") else 2
            if w.endswith(pt) and len(w) >= len(pt) + stem and not (pt.startswith("ia") and ACCENT.search(w)):
                w = w[: -len(pt)] + mwl
                break
        else:
            if VERB_EU.search(w):
                w = w[:-2] + "iu"
    # -mento > -miento, the ie diphthong of a stressed open e that the Convenção p. 18 states; corpus: sentimientos.
    w = re.sub(r"mento(s?)$", r"miento\1", w)
    # The c of ct and cç is not written: dialeto, açon. Corpus: 149 rows.
    w = re.sub(r"c(?=[tç])", "", w)
    # x before a consonant > s: testo, spressar. Initial ex before a vowel > eis: eisiste. Corpus: 411 rows.
    w = re.sub(r"^ex(?=[^aeiouáéíóúâêô])", "s", w)
    w = re.sub(r"^ex(?=[aeiouáéíóúâêô])", "eis", w)
    w = re.sub(r"x(?=[^aeiouáéíóúâêôh])", "s", w)
    # Initial es + consonant > s, Convenção p. 16-17 and 34: scalada, star; his + consonant too: stória (323 rows).
    w = re.sub(r"^(?:h?e|hi)s(?=[bcdfgjlmnpqrtvz])", "s", w)
    # Initial des-, dis- before a voiceless consonant > ç, Convenção p. 13: çcalçar, çtapar; corpus: çcubriu.
    w = re.sub(r"^d[ei]s(?=[cpqt])", "ç", w)
    # Initial en-, em-, in-, im- before a consonant > an-, am-, Convenção p. 36 note 38: anchir.
    w = re.sub(r"^[ei]([nm])(?=[bcdfgjlmnpqrstvz])", r"a\1", w)
    # Pretonic con-, com- > cun-, cum-, Convenção p. 19: cumbidado; cons + consonant > cus: custituen.
    if first_unstressed:
        w = re.sub(r"^cons(?=[^aeiouáéíóúâêô])", "cus", w)
        w = re.sub(r"^co([nm])(?=[^aeiouáéíóúâêôh])", r"cu\1", w)
        # A pretonic initial e, i, o or u before one consonant takes the glide: eidade, eiditor, ourige, outelizado.
        # Corpus: 1,980 rows.
        w = re.sub(r"^[ei](?=[bcdfgjlprtv][aeiouáéíóúâêô])", "ei", w)
        w = re.sub(r"^[ou](?=[bcdfgjlmnprtv][aeiouáéíóúâêô]|[bcp][lrst])", "ou", w)
    # Initial au- > ou-: outor, outoridade. Corpus: 325 rows.
    w = re.sub(r"^au", "ou", w)
    w = re.sub(r"^trans", "tras", w)
    # -ário > -airo: comentairos, secretairo. Corpus: 298 rows.
    w = re.sub(r"ário(s?)$", r"airo\1", w)
    # Mirandese writes the acute accent only: ciéncia, cuntemporáneo, trés. Corpus: â, ê, ô 105 times against
    # 2,242 in the Portuguese side.
    w = w.translate(str.maketrans("âêô", "áéó"))
    # Final -z > -ç, Convenção p. 13 and 17: paç.
    w = re.sub(r"z$", "ç", w)
    # A final nasal is written n, Convenção p. 19.
    w = re.sub(r"(?<=[aeiou])m$", "n", w)
    # Mirandese has no v, Convenção p. 17; m before b and p, Convenção p. 19: cumbite, cumpanheiro.
    # The Convenção p. 17 lets proper names keep an official V (Virgílio); the corpus writes Birgílio, and place
    # names take b (Bimioso), so names follow the rule too.
    return re.sub(r"n(?=[bp])", "m", w.replace("v", "b"))


def word(w: str) -> str:
    """Translate one lowercase word with no context."""
    if w in CLOSED:
        return CLOSED[w]
    if w in LEXICON:
        return LEXICON[w]
    if "-" in w:
        head, *rest = w.split("-")
        head = rules(head) if rest[0] in INFINITIVE_CLITIC and head not in LEXICON else word(head)
        return "-".join([head] + [ENCLITIC.get(p, word(p)) for p in rest])
    return rules(w)


def _case(src: str, out: str) -> str:
    if src.isupper() and len(src) > 1:
        return out.upper()
    if src[:1].isupper():
        return out[:1].upper() + out[1:]
    return out


# A slot, a URL or e-mail address, a word, a space or one other character. Slots and addresses stay as they are.
TOKEN = re.compile(r"\{[^}]*\}|https?://\S+|[\w.+-]+@[\w-]+(?:\.[\w-]+)+|[\w-]{2,}(?:\.[\w-]+)*\.[a-z]{2,}/\S*"
                   r"|www\.\S+|[^\W\d_]+(?:-[^\W\d_]+)*|\s+|.", re.UNICODE)
WORD = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*", re.UNICODE)
ROMAN = re.compile(r"[IVXLCDM]+")


def translate(text: str) -> str:
    """Translate one sentence or line of European Portuguese."""
    text = unicodedata.normalize("NFC", text)
    if "\n" in text:
        return "\n".join(translate(line) for line in text.split("\n"))
    tokens = TOKEN.findall(text)
    words = [i for i, t in enumerate(tokens) if WORD.fullmatch(t)]
    out = list(tokens)
    skip = set()
    for n, i in enumerate(words):
        if i in skip:
            continue
        low = tokens[i].lower()
        # A one-letter word between full stops and letters is an abbreviation (a.C., d.C.), and a Roman numeral is
        # a number.
        abbreviation = len(low) == 1 and tokens[i + 1:i + 2] == ["."] and WORD.match(tokens[i + 2] if i + 2 < len(tokens) else "")
        if abbreviation or ROMAN.fullmatch(tokens[i]):
            continue
        nxt = words[n + 1] if n + 1 < len(words) else None
        if low in ARTICLE_AFTER and nxt is not None and nxt == i + 2 and tokens[nxt].lower() in ARTICLE_AFTER[low]:
            out[i] = _case(tokens[i], ARTICLE_AFTER[low][tokens[nxt].lower()])
            out[i + 1] = out[nxt] = ""
            skip.add(nxt)
            continue
        if low == "a" and _preposition(tokens, i, nxt):
            continue
        # nos before the verb is the object pronoun mos, Convenção p. 25: fai-mos. The corpus writes ne ls here.
        if low == "nos" and n and tokens[words[n - 1]].lower() in BEFORE_CLITIC and nxt is not None \
                and tokens[nxt].islower() and not tokens[nxt].endswith(("os", "as")):
            out[i] = _case(tokens[i], "mos")
            continue
        # An acronym in mixed-case text stays as it is: TV, IVA, EUA.
        if tokens[i].isupper() and len(low) > 1 and not text.isupper():
            continue
        out[i] = _case(tokens[i], word(low))
    return _elide("".join(out))


def _preposition(tokens, i, nxt):
    after = tokens[i + 2] if i + 2 < len(tokens) else ""
    if after[:1].isdigit():
        return True
    if nxt != i + 2:
        return False
    w = tokens[nxt].lower()
    return w in PREP_A_BEFORE or (bool(INFINITIVE.search(w)) and w not in NOUN_IN_R)


# la before a vowel > l', Convenção p. 21: l'alma. The corpus elides the masculine l, de > d' and que > qu' the
# same way, and all four before h: l'home, d'hoije. Counts in the train split: d' 629 against de 64, qu' 415
# against que 14. The corpus keeps the word whole before a capital (l Eigito, de Abril: 599 against 6) and mostly
# before an accented vowel: la época, la única. An enclitic after a hyphen does not elide: cumprá-la i.
ELIDE = re.compile(r"(?<![\w-])([Ll]a|[Ll]|[Dd]e|[Qq]ue) (?=h?[aeiou])")


def _elide(text: str) -> str:
    return ELIDE.sub(lambda m: m.group(1)[:-1] + "'" if m.group(1).lower() == "que" else m.group(1)[0] + "'", text)


def main():
    for line in sys.stdin:
        print(translate(line.rstrip("\n")))


if __name__ == "__main__":
    main()
