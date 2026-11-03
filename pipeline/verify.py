"""Number check for AI texts (PLAN §5): every number in the text must appear in the fact pack.

The check is deliberately strict. A rounded number ("28 %" where the facts say "27,6 %"), a
computed one (a difference of two facts) or one written the English way ("41.7") fails, and
the text is generated again or replaced by the template. Numbers written as words are not
checked.

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
SCALE = re.compile(r"\bod\s+1\b[^.;]{0,40}?\bdo\s+5\b", re.IGNORECASE)
GRADE_WORD = re.compile(r"\bocjen\w*", re.IGNORECASE)
GRADE_DIGIT = re.compile(r"(?<![\d,.])([1-5])(?!\d)(?![,.]\d)(?!\.\s*[a-zčćđšž])")
SENTENCE_END = re.compile(r"[.!?;]\s+(?=[A-ZČĆĐŠŽ])")


def claimed_grades(text):
    t = SCALE.sub(" ", text)
    out = []
    for m in GRADE_WORD.finditer(t):
        rest = t[m.end():m.end() + 120]
        end = SENTENCE_END.search(rest)
        d = GRADE_DIGIT.search(rest[:end.start() + 1] if end else rest)
        if d:
            out.append(d.group(1))
    return out


def verify(text, pack):
    """{"ok", "n_brojki", "nepoznate"}. ok only if there is at least one number, every number is
    in the pack and written the Croatian way, and every grade mentioned is the unit's grade
    (this year or last year)."""
    ok_vals = allowed(pack)
    found = numbers(text)
    unknown = [tok for v, tok in found if v is None or v not in ok_vals]
    grades = {str(g) for g in pack.get("ocjene", [])}
    if grades:
        unknown += [f"ocjena {g}" for g in claimed_grades(text) if g not in grades]
    return {"ok": bool(found) and not unknown, "n_brojki": len(found), "nepoznate": unknown}
