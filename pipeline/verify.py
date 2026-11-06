"""Number check for AI texts (PLAN §5): every number in the text must appear in the fact pack.

The check is deliberately strict. A rounded number ("28 %" where the facts say "27,6 %"), a
computed one (a difference of two facts) or one written the English way ("41.7") fails, and
the text is generated again or replaced by the template. Numbers written as words are not
checked. The context (population, income) has its own rules: context_issues.

This file has no imports outside the standard library, because the Kaggle notebook embeds
it verbatim.
"""
import re
from decimal import Decimal, InvalidOperation

# Any run of digits joined by "." or "," (or a non-breaking space inside thousands) is one token,
# so "41.7" or "31.12.2025" cannot hide behind their first part. A plain space is not a
# thousands separator: "za 4 125 €" stays two numbers. A trailing ordinal dot ("2025.") is not
# part of the token.
NUMBER = re.compile(r"(?<![\d,.])-?\d+(?:[.,  ]\d+)*")
# The only accepted spellings: Croatian thousands groups and a decimal comma.
CROATIAN = re.compile(r"-?(?:\d{1,3}(?:[.  ]\d{3})+|\d+)(?:,\d+)?")


def normalise(token):
    """Decimal value of a Croatian-format number, or None for any other spelling."""
    if not CROATIAN.fullmatch(token):
        return None
    t = re.sub(r"[.  ]", "", token).replace(",", ".")
    try:
        return Decimal(t).normalize()
    except InvalidOperation:
        return None


def numbers(text):
    """All numbers in a text: (normalised Decimal or None if malformed, token)."""
    out = []
    for m in NUMBER.finditer(text):
        token = m.group(0).strip()
        v = normalise(token)
        out.append((abs(v) if v is not None else None, token))   # the sign is carried by words ("manjak")
    return out


def allowed(pack):
    vals = set()
    for f in pack["facts"]:
        for part in (f["label"], f["value"]):
            vals |= {v for v, _ in numbers(part) if v is not None}
    return vals


# Grades: after every "ocjen*" word, the first standalone digit 1-5 in the same sentence is
# a claimed grade and must be this year's or last year's. The scale wording "od 1 ... do 5"
# is removed first, and ordinals ("1. mjesto"), decimals and amounts ("1.767.926 €") are not grades.
# The search runs to the end of the sentence with no fixed length: a window of 120 characters
# once cut "3,8" after its "3", which was then read as a grade (11 correct texts rejected, 4.11.).
SCALE = re.compile(r"\bod\s+1\b[^.;]{0,40}?\bdo\s+5\b", re.IGNORECASE)
GRADE_WORD = re.compile(r"\bocjen\w*", re.IGNORECASE)
GRADE_DIGIT = re.compile(r"(?<![\d,.])([1-5])(?!\d)(?![,.]\d)(?!\.\s*[a-zčćđšž])")
SENTENCE_END = re.compile(r"[.!?;]\s+(?=[A-ZČĆĐŠŽ])")


def claimed_grades(text):
    t = SCALE.sub(" ", text)
    out = []
    for m in GRADE_WORD.finditer(t):
        rest = t[m.end():]
        end = SENTENCE_END.search(rest)
        d = GRADE_DIGIT.search(rest[:end.start() + 1] if end else rest)
        if d:
            out.append(d.group(1))
    return out


# Content claims the prompt asks for with fixed phrases, so they can be checked (Gemma test v4):
# the weakest component, the strengths, and a capped grade, which only rule 2 can cause.
# "sastavnica" is the word of the texts written before 5.11.; the prompt now says "pokazatelj"
WEAKEST = re.compile(r"spušta (?:pokazatelj|sastavnica)\s+[„\"“]([^”\"“]+)[”\"“]", re.IGNORECASE)
STRENGTHS = re.compile(r"jake strane jedinice su:\s*([^.;]+)", re.IGNORECASE)
CAPPED = re.compile(r"\bograničen\w*", re.IGNORECASE)
# The peer median glued to the fact's own words with "od": "uz medijan skupine od nedostaje 1,7 %
# tekućih prihoda" (14 of the 20 counties, 6.11.), "... od viška 13,3 % ..." (28 texts). The numbers
# are right and the sentence is not Croatian, so it is written again. The same for the verb put
# after the nominative: "dok je medijan skupine nedostaje 1,7 %" (the pilot of 6.11.), "dok medijan
# skupine iznosi nedostaje 1,7 %"; "kod medijana skupine nedostaje 1,7 %" is fine and does not match.
MEDIAN_OF = re.compile(r"\bmedijan\w*\s+(?:usporedne\s+)?skupine\s+(od\s+(?:nedostaje|ostaje|viš[a-zčćđšž]+|manj[a-zčćđšž]+))",
                       re.IGNORECASE)
MEDIAN_VERB = re.compile(r"\bmedijan\s+(?:usporedne\s+)?skupine\s+((?:(?:je|iznosi)\s+)?(?:nedostaje|ostaje))\b",
                         re.IGNORECASE)
# The sign of the peer median is a word in the facts: "nedostaje 18,4 % tekućih prihoda; medijan
# skupine: ostaje 9,2 % tekućih prihoda". A text that keeps only the number ("nedostaje 18,4 %, uz
# medijan skupine od 9,2 %") reads as if the median lacked 9,2 % as well (67 accepted texts, 6.11.).
MEDIAN_SEP = "; medijan skupine: "
SIGN_WORDS = {"ostaje": 1, "nedostaje": -1, "višak": 1, "manjak": -1}
SIGN_FORMS = {"ostaje": r"\bostaje\b", "nedostaje": r"\bnedostaje\b", "višak": r"\bviš(?:ak|ka|kom|ku)\b",
              "manjak": r"\bmanj(?:ak|ka|kom|ku)\b"}
# No bracket in between: the context sentence writes its own median as "ispod medijana skupine (−3,9 %)".
MEDIAN_PERCENT = re.compile(r"\bmedijan\w*\s+(?:usporedne\s+)?skupine\b([^.;%\d(]{0,60}?)(\d+(?:[.,]\d+)*)\s*%",
                            re.IGNORECASE)


def median_sign_issue(text, fact):
    """The word that has to stand with the peer median's number, when the text gives that number
    without it and the unit's own value has the other sign; otherwise None. Same signs need no word:
    "nedostaje 0,4 %, uz medijan skupine od 1,7 %" is read the right way."""
    own, sep, median = fact.partition(MEDIAN_SEP)
    word = median.split(" ", 1)[0]
    own_sign = next((s for w, s in SIGN_WORDS.items() if re.search(SIGN_FORMS[w], own)), None)
    if not sep or word not in SIGN_WORDS or own_sign in (None, SIGN_WORDS[word]):
        return None
    value = next((v for v, _ in numbers(median) if v is not None), None)
    for between, token in MEDIAN_PERCENT.findall(text):
        if normalise(token) == value and not re.search(SIGN_FORMS[word], between, re.IGNORECASE):
            return word
    return None


def states_value(text, fact):
    """True when the text carries a number of the unit's own part of an indicator fact, the part
    before the peer median ("… ostaje 10,7 % tekućih prihoda; medijan skupine: …"). A fact with no
    number of its own ("jedinica nema neto duga") asks for nothing."""
    need = {v for v, _ in numbers(fact.split(";", 1)[0]) if v is not None}
    return not need or bool(need & {v for v, _ in numbers(text) if v is not None})


def content_issues(text, pack):
    facts = {f["label"]: f["value"] for f in pack["facts"]}
    issues = []
    for name in WEAKEST.findall(text):
        weakest = facts.get("Najslabiji pokazatelj", facts.get("Najslabija sastavnica", ""))
        if name.strip().lower() != weakest.lower():
            issues.append(f"najslabiji pokazatelj „{name.strip()}”")
        # the weakest indicator named without its value says nothing (Grad Zagreb and Općina Blato, 6.11.)
        elif not states_value(text, facts.get(f"Pokazatelj: {weakest}", "")):
            issues.append(f"najslabiji pokazatelj „{weakest}” bez vrijednosti")
    strong = facts.get("Jake strane", "").lower()
    for listed in STRENGTHS.findall(text):
        for part in re.split(r",| i | te ", listed):
            part = part.strip().lower()
            if part and part not in strong:
                issues.append(f"jaka strana „{part}”")
    if CAPPED.search(text) and "Pravilo" not in facts:
        issues.append("ograničenje ocjene bez pravila")
    for words in MEDIAN_OF.findall(text) + MEDIAN_VERB.findall(text):
        issues.append(f"medijan skupine uveden riječima „{' '.join(words.lower().split())}”")
    weakest = facts.get("Najslabiji pokazatelj", "")
    word = median_sign_issue(text, facts.get(f"Pokazatelj: {weakest}", ""))
    if word:
        issues.append(f"medijan skupine bez riječi „{word}”")
    return issues + context_issues(text, pack)


# Context (facts.context_facts: population change, net income per inhabitant; items marked
# "kontekst": true) never enters the score. A sentence about it needs its item in the pack, uses only
# the context numbers, with their sign and their side of the median, and does not tie them to the
# grade. The texts written before context existed mention none of these words (576 of 576, 4.11.).
POPULATION = re.compile(r"\b(?:stanovništv\w*|broj\w*\s+stanovnika|iseljav\w*|doseljav\w*|migracij\w*|"
                        r"demograf\w*|depopulacij\w*)", re.IGNORECASE)
INCOME = re.compile(r"\b(?:dohod\w*|dohot\w*)", re.IGNORECASE)
CONTEXT_WORD = re.compile(r"\bkontekst\w*", re.IGNORECASE)
UP = r"poveća\w*|porast\w*|porasl\w*|narast\w*|narasl\w*|rast\w*"
DOWN = r"smanj\w*|pad\w*|pao|pala|palo|opao|opala|opalo|opada\w*"
TREND = re.compile(rf"\b(?:{UP}|{DOWN})\b", re.IGNORECASE)
# a direction word bound to the number after the next "za": "smanjio se za 8,3 %",
# "porastao je od 2021. do 2025. za 6,2 %"
DIRECTION = re.compile(rf"\b(?:({UP})|({DOWN}))(?:\s+\S+){{0,6}}?\s+za\s+[+−-]?(\d+(?:[.,]\d+)*)", re.IGNORECASE)
SIDE = re.compile(r"\b(iznad|ispod)\s+medijan", re.IGNORECASE)
# a link between the context and the grade or its components; negated phrases ("ne ulazi u ocjenu",
# "ne objašnjava je", "nisu dio ocjene", "ne utječe na ocjenu") are taken out first
NEGATED = re.compile(r"\b(?:ne|nisu|nije|niti)\s+(?:\w+\s+){0,3}?(?:ocjen\w*|(?:utje|utječ|objašnjav|uzrok|doprinos|"
                     r"pridonos|odraž|povezan)\w*(?:\s+(?:na|u|s|sa|za)\s+(?:\w+\s+)?ocjen\w*)?)", re.IGNORECASE)
CAUSAL = re.compile(r"\b(?:ocjen\w*|sastavnic\w*|pokazatelj\w*|zbog|uslijed|uzrok\w*|posljedic\w*|utje\w*|utječ\w*|doprinos\w*|"
                    r"pridonos\w*|objašnjav\w*|stoga|zato|rezultir\w*|odraž\w*|povezan\w*)", re.IGNORECASE)


def sentences(text):
    out, start = [], 0
    for m in SENTENCE_END.finditer(text):
        out.append(text[start:m.end()])
        start = m.end()
    return out + [text[start:]]


def signed_values(text):
    """{(abs value, +1 | -1, token)} a text claims: an explicit sign (+6,2 %, −8,3 %, -8,3 %) or a
    direction word bound to the number (smanjio se za 8,3 %)."""
    out = set()
    for m in NUMBER.finditer(text):
        token = m.group(0).strip()
        before = text[m.start() - 1] if m.start() else ""
        sign = -1 if token.startswith("-") else {"+": 1, "−": -1}.get(before)
        v = normalise(token)
        if sign and v is not None:
            out.add((abs(v), sign, token if token.startswith("-") else before + token))
    for m in DIRECTION.finditer(text):
        v = normalise(m.group(3))
        if v is not None:
            out.add((abs(v), 1 if m.group(1) else -1, m.group(0)))
    return out


def context_issues(text, pack):
    ctx = [f for f in pack["facts"] if f.get("kontekst")]
    labels = " ".join(f["label"].lower() for f in ctx)
    ctx_text = " ".join(f["value"] for f in ctx)
    issues = []
    about = []
    for s in sentences(text):
        pop = POPULATION.search(s) and (TREND.search(s) or "%" in s)
        inc = INCOME.search(s)
        if not (pop or inc or CONTEXT_WORD.search(s)):
            continue
        about.append(s)
        if pop and "stanovnik" not in labels:
            issues.append("kretanje stanovništva bez stavke u činjenicama")
        if inc and "dohod" not in labels:
            issues.append("dohodak bez stavke u činjenicama")
        if not ctx and not (pop or inc):
            issues.append("kontekst bez stavke u činjenicama")
    if not about or not ctx:
        return issues
    # numbers: only from the context items (and the unit line, e.g. its population); a number that
    # is nowhere in the pack is already in "nepoznate"
    in_pack = allowed(pack)
    ok_vals = allowed({"facts": ctx + [f for f in pack["facts"] if f["label"] == "Jedinica"]})
    pack_signs = {(v, s) for v, s, _ in signed_values(ctx_text)}
    signed = {v for v, _ in pack_signs}
    for s in about:
        for v, tok in numbers(s):
            if v in in_pack and v not in ok_vals:
                issues.append(f"brojka „{tok}” u rečenici o kontekstu nije iz stavki konteksta")
        for v, sign, tok in sorted(signed_values(s), key=lambda x: (x[0], x[1])):
            if v in signed and (v, sign) not in pack_signs:
                issues.append(f"smjer promjene „{tok}” ne slaže se s činjenicama")
        for side in SIDE.findall(s):
            if f"{side.lower()} medijana" not in ctx_text:
                issues.append(f"„{side} medijana” ne slaže se s činjenicama")
        if CAUSAL.search(NEGATED.sub(" ", s)):
            issues.append("kontekst povezan s ocjenom ili pokazateljima")
    return issues


def verify(text, pack):
    """{"ok", "n_brojki", "nepoznate", "sadrzaj"}. ok only if there is at least one number, every
    number is in the pack and written the Croatian way, every grade mentioned is the unit's grade
    (this year or last year), the weakest component, the strengths and any capped grade agree
    with the pack (no weakest component is named when the pack has none), the weakest component
    comes with its value (states_value), the peer median is not glued on with "od" or a verb
    (MEDIAN_OF, MEDIAN_VERB) and keeps its word when its sign differs from the unit's
    (median_sign_issue), and any sentence on the context keeps to the context items (context_issues)."""
    ok_vals = allowed(pack)
    found = numbers(text)
    unknown = [tok for v, tok in found if v is None or v not in ok_vals]
    grades = {str(g) for g in pack.get("ocjene", [])}
    if grades:
        unknown += [f"ocjena {g}" for g in claimed_grades(text) if g not in grades]
    issues = content_issues(text, pack)
    return {"ok": bool(found) and not unknown and not issues, "n_brojki": len(found), "nepoznate": unknown,
            "sadrzaj": issues}
