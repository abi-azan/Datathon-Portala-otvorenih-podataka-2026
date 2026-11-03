"""Number check for AI texts (PLAN §5): every number in the text must appear in the fact pack.

The check is deliberately strict. A rounded number ("28 %" where the facts say "27,6 %") or
a computed one (a difference of two facts) fails, and the text is generated again or
replaced by the template. Numbers written as words are not checked.

This file has no imports outside the standard library, because the Kaggle notebook embeds
it verbatim.
"""
import re
from decimal import Decimal, InvalidOperation

# 1.625,85 | 1 625,85 (non-breaking space) | 27,6 | 2025 ; thousands groups first, so "1.625" is
# one number. A plain space is not a thousands separator: "za 4 125 €" must stay two numbers.
NUMBER = re.compile(r"(?<![\d,])-?\d{1,3}(?:[.  ]\d{3})+(?:,\d+)?(?![\d])|(?<![\d,.])-?\d+(?:,\d+)?")


def normalise(token):
    t = re.sub(r"[.  ]", "", token).replace(",", ".")
    try:
        return Decimal(t).normalize()
    except InvalidOperation:
        return None


def numbers(text):
    """All numbers in a text, as normalised Decimals with the token they came from."""
    out = []
    for m in NUMBER.finditer(text):
        token = m.group(0).strip()
        v = normalise(token)
        if v is not None:
            out.append((abs(v), token))       # the sign is carried by words ("manjak"), not by "-"
    return out


def allowed(pack):
    vals = set()
    for f in pack["facts"]:
        for part in (f["label"], f["value"]):
            vals |= {v for v, _ in numbers(part)}
    return vals


# "ocjenu 4", "ocjena je 4", "ocjenom 3": the digit after the word must be a grade from the pack
GRADE = re.compile(r"\bocjen\w*(?:\s+(?:je|od|bila|iznosi|za\s+\d{4}\.?(?:\s+godinu)?))*\s+(\d)\b", re.IGNORECASE)


def verify(text, pack):
    """{"ok", "n_brojki", "nepoznate"}. ok only if there is at least one number, every number is
    in the pack, and every grade mentioned is the unit's grade (this year or last year)."""
    ok_vals = allowed(pack)
    found = numbers(text)
    unknown = [tok for v, tok in found if v not in ok_vals]
    grades = {str(g) for g in pack.get("ocjene", [])}
    if grades:
        unknown += [f"ocjena {g}" for g in GRADE.findall(text) if g not in grades]
    return {"ok": bool(found) and not unknown, "n_brojki": len(found), "nepoznate": unknown}
