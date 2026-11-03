"""Gemma 4 on a Kaggle GPU: AI explanations with a number check (Fiskalna karta JLS).

Generated from kaggle/gemma_runner.py by `python -m pipeline.explain --kaggle-test N`.
Do not edit kaggle/gemma_test.py by hand.

- Models: every attached Gemma 4 QAT Q4_0 GGUF (Kaggle model data sources, Apache-2.0), smallest
  first. A model larger than one T4 is split by layers across both T4s.
- Runtime: llama.cpp (MIT), built from source for the T4 (CUDA arch 75), served by llama-server.
- Every text is checked: each number must appear in the unit's fact pack. A failed text is
  generated again with feedback, at most 2 times, and then the template is used.
Output: /kaggle/working/gemma_test_output.json
"""
import glob
import json
import os
import subprocess
import sys
import time
import urllib.request

# ---- number check: pipeline/verify.py, embedded verbatim ----
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


# Content claims the prompt asks for with fixed phrases, so they can be checked (Gemma test v4):
# the weakest component, the strengths, and a capped grade, which only rule 2 can cause.
WEAKEST = re.compile(r"spušta sastavnica\s+[„\"“]([^”\"“]+)[”\"“]", re.IGNORECASE)
STRENGTHS = re.compile(r"jake strane jedinice su:\s*([^.;]+)", re.IGNORECASE)
CAPPED = re.compile(r"\bograničen\w*", re.IGNORECASE)


def content_issues(text, pack):
    facts = {f["label"]: f["value"] for f in pack["facts"]}
    issues = []
    for name in WEAKEST.findall(text):
        if name.strip().lower() != facts.get("Najslabija sastavnica", "").lower():
            issues.append(f"najslabija sastavnica „{name.strip()}”")
    strong = facts.get("Jake strane", "").lower()
    for listed in STRENGTHS.findall(text):
        for part in re.split(r",| i | te ", listed):
            part = part.strip().lower()
            if part and part not in strong:
                issues.append(f"jaka strana „{part}”")
    if CAPPED.search(text) and "Pravilo" not in facts:
        issues.append("ograničenje ocjene bez pravila")
    return issues


def verify(text, pack):
    """{"ok", "n_brojki", "nepoznate", "sadrzaj"}. ok only if there is at least one number, every
    number is in the pack and written the Croatian way, every grade mentioned is the unit's grade
    (this year or last year), and the weakest component, the strengths and any capped grade
    agree with the pack."""
    ok_vals = allowed(pack)
    found = numbers(text)
    unknown = [tok for v, tok in found if v is None or v not in ok_vals]
    grades = {str(g) for g in pack.get("ocjene", [])}
    if grades:
        unknown += [f"ocjena {g}" for g in claimed_grades(text) if g not in grades]
    issues = content_issues(text, pack)
    return {"ok": bool(found) and not unknown and not issues, "n_brojki": len(found), "nepoznate": unknown,
            "sadrzaj": issues}

# ---- end of pipeline/verify.py ----

# ---- prompt: pipeline/explain.py SYSTEM, RULES, messages(), feedback(), embedded verbatim ----
SYSTEM = 'Ti si urednik javnog portala o financijama općina, gradova i županija. Pišeš kratka, točna i neutralna objašnjenja za građane na hrvatskom standardnom jeziku.'
RULES = 'Pravila:\n1. Napiši 3 do 5 rečenica, najviše 100 riječi, u jednom odlomku. Bez naslova, natuknica i oznaka (markdown).\n2. Koristi samo činjenice s popisa. Svaku brojku prepiši točno kako je napisana, zajedno s riječju ili znakom uz nju (boda, %, €). Ne zaokružuj i ne računaj nove brojke ni razlike.\n3. Redoslijed: ocjena i bodovi; najslabija sastavnica s usporedbom s medijanom skupine; jake strane; upozorenja; pravilo i napomena o podacima. Dio za koji na popisu nema stavke izostavi.\n4. Najslabiju sastavnicu uvedi točno ovim riječima: \'Ocjenu najviše spušta sastavnica „…”.\' Jake strane uvedi riječima: \'Jake strane jedinice su: …\' Ne proglašavaj ništa drugo jakom ili slabom stranom.\n5. Upozorenja ne mijenjaju ocjenu: nikad ne piši da je ocjena zbog njih ograničena. O ograničenju ocjene piši samo ako na popisu postoji stavka "Pravilo".\n6. Ne dodaj rečenice o izvoru, obradi ili razdoblju podataka. Ton je neutralan i opisan; bez riječi "loše", "dobro", "uspjeh" i "neuspjeh", bez savjeta, nagađanja o uzrocima, političara i stranaka.\n7. Naziv jedinice piši samo u nominativu, kao subjekt rečenice ("{nom} ima ocjenu …"). Ne sklanjaj ga. U ostalim rečenicama piši "jedinica" ili naziv izostavi.'
EXAMPLE = 'PRIMJER za izmišljenu jedinicu (samo za stil; njegove brojke ne koristi):\nOpćina Primjerovo za 2025. godinu ima ocjenu 2 (pod pritiskom) i 31,4 boda od 100, dok je medijan usporedne skupine 78,8 boda. Ocjenu najviše spušta sastavnica „dospjele neplaćene obveze”: na kraju godine iznose 512.300 €, odnosno 41,2 % rashoda poslovanja, uz medijan skupine od 2,0 %. Jake strane jedinice su: servis duga. Upozorenje: novca na računu ima manje nego za mjesec dana rashoda poslovanja. Ocjena je ograničena na najviše 2 jer dospjele obveze dosežu 30 % rashoda poslovanja.'


def messages(pack):
    n = pack["naziv"]
    lines = "\n".join(f"- {f['label']}: {f['value']}" for f in pack["facts"])
    user = (f"Jedinica: {n['nom']}. Napiši objašnjenje njezine ocjene financijske stabilnosti za {pack['year']}. godinu.\n\n"
            + RULES.format(**n) + f"\n\n{EXAMPLE}\n\nČINJENICE:\n{lines}")
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def feedback(unknown, issues=()):
    parts = []
    if unknown:
        parts.append("Tekst sadrži brojke kojih nema u činjenicama: " + ", ".join(unknown)
                     + ". Koristi samo brojke s popisa, prepisane točno.")
    if issues:
        parts.append("Tekst se ne slaže s činjenicama: " + "; ".join(issues)
                     + ". Najslabiju sastavnicu, jake strane i ograničenje ocjene navedi samo kako piše na popisu.")
    return " ".join(parts) + " Napiši tekst ponovno."

# ---- end of prompt ----

PACKS = json.loads("[{\"oib\":\"75901612733\",\"naziv\":{\"nom\":\"Općina Selca\",\"gen\":\"Općine Selca\",\"lok\":\"Općini Selca\"},\"year\":2025,\"ocjena\":1,\"ocjene\":[1,3],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Općina Selca (Splitsko-dalmatinska županija), 1.613 stanovnika (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"1 (ozbiljan pritisak) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"općine do 2.000 (202 jedinice)\"},{\"label\":\"Bodovi\",\"value\":\"14,2 boda od 100; medijan skupine 78,8 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"198. od 202\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"3 (umjereno)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni manjak iznosi 17,8 % tekućih prihoda; medijan skupine: višak 13,3 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita nedostaje 17,9 % tekućih prihoda; medijan skupine: ostaje 10,8 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"jedinica ima neto dug, a nema operativnog viška iz kojeg bi ga otplaćivala; većina jedinica u skupini nema neto duga\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 1,6 % zakonske osnovice; medijan skupine 3,1 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 851.125 €, što je 33,3 % rashoda poslovanja; medijan skupine 2,0 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"operativni saldo\"},{\"label\":\"Jake strane\",\"value\":\"servis duga\"},{\"label\":\"Upozorenja\",\"value\":\"preneseni manjak iz prethodnih godina veći od 5 % tekućih prihoda; otplata duga i dospjele obveze blizu zakonskog limita (više od 20 % zakonske osnovice); rashodi poslovanja veći od tekućih prihoda dvije godine zaredom; novca na računu manje nego za mjesec dana rashoda poslovanja\"}]},{\"oib\":\"96601278857\",\"naziv\":{\"nom\":\"Općina Prgomet\",\"gen\":\"Općine Prgomet\",\"lok\":\"Općini Prgomet\"},\"year\":2025,\"ocjena\":2,\"ocjene\":[2,3],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Općina Prgomet (Splitsko-dalmatinska županija), 498 stanovnika (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"2 (pod pritiskom) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"općine do 2.000 (202 jedinice)\"},{\"label\":\"Bodovi\",\"value\":\"36,3 boda od 100; medijan skupine 78,8 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"191. od 202\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"3 (umjereno)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni manjak iznosi 12,4 % tekućih prihoda; medijan skupine: višak 13,3 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita nedostaje 12,4 % tekućih prihoda; medijan skupine: ostaje 10,8 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"jedinica nema neto duga (novac na računu pokriva kredite); većina jedinica u skupini nema neto duga\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 0,0 % zakonske osnovice; medijan skupine 3,1 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 168.603 €, što je 23,7 % rashoda poslovanja; medijan skupine 2,0 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"operativni saldo\"},{\"label\":\"Jake strane\",\"value\":\"godine otplate neto duga, servis duga\"},{\"label\":\"Upozorenja\",\"value\":\"preneseni manjak iz prethodnih godina veći od 5 % tekućih prihoda; otplata duga i dospjele obveze blizu zakonskog limita (više od 20 % zakonske osnovice)\"}]},{\"oib\":\"95603491861\",\"naziv\":{\"nom\":\"Grad Biograd na Moru\",\"gen\":\"Grada Biograd na Moru\",\"lok\":\"Gradu Biograd na Moru\"},\"year\":2025,\"ocjena\":3,\"ocjene\":[3,4],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Grad Biograd na Moru (Zadarska županija), 5.601 stanovnik (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"3 (umjereno) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"gradovi 5.000-10.000 (45 jedinica)\"},{\"label\":\"Bodovi\",\"value\":\"55,5 boda od 100; medijan skupine 70,1 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"36. od 45\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"4 (stabilno)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni višak iznosi 7,4 % tekućih prihoda; medijan skupine: višak 8,1 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita ostaje 2,2 % tekućih prihoda; medijan skupine: ostaje 4,5 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"neto dug mogao bi se otplatiti iz operativnog viška za 12,3 godine; medijan skupine 0,8 godine\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 6,2 % zakonske osnovice; medijan skupine 5,3 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 1.236.050 €, što je 11,1 % rashoda poslovanja; medijan skupine 2,5 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"slobodni saldo nakon otplate glavnice\"},{\"label\":\"Upozorenja\",\"value\":\"preneseni manjak iz prethodnih godina veći od 5 % tekućih prihoda; novca na računu manje nego za mjesec dana rashoda poslovanja\"}]},{\"oib\":\"24482197680\",\"naziv\":{\"nom\":\"Općina Konavle\",\"gen\":\"Općine Konavle\",\"lok\":\"Općini Konavle\"},\"year\":2025,\"ocjena\":4,\"ocjene\":[4,5],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Općina Konavle (Dubrovačko-neretvanska županija), 8.607 stanovnika (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"4 (stabilno) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"općine 5.000-10.000 (28 jedinica)\"},{\"label\":\"Bodovi\",\"value\":\"78,8 boda od 100; medijan skupine 82,5 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"17. od 28\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"5 (vrlo stabilno)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni višak iznosi 11,2 % tekućih prihoda; medijan skupine: višak 15,4 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita ostaje 5,3 % tekućih prihoda; medijan skupine: ostaje 10,0 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"neto dug mogao bi se otplatiti iz operativnog viška za 0,9 godine; medijan skupine 0,1 godine\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 7,2 % zakonske osnovice; medijan skupine 3,8 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 30.374 €, što je 0,2 % rashoda poslovanja; medijan skupine 0,8 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"slobodni saldo nakon otplate glavnice\"},{\"label\":\"Jake strane\",\"value\":\"dospjele neplaćene obveze\"},{\"label\":\"Upozorenja\",\"value\":\"nema upozorenja\"}]},{\"oib\":\"88617357699\",\"naziv\":{\"nom\":\"Grad Cres\",\"gen\":\"Grada Cres\",\"lok\":\"Gradu Cres\"},\"year\":2025,\"ocjena\":5,\"ocjene\":[5,5],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Grad Cres (Primorsko-goranska županija), 2.716 stanovnika (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"5 (vrlo stabilno) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"gradovi 2.000-5.000 (21 jedinica)\"},{\"label\":\"Bodovi\",\"value\":\"93,9 boda od 100; medijan skupine 80,6 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"6. od 21\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"5 (vrlo stabilno)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni višak iznosi 22,9 % tekućih prihoda; medijan skupine: višak 14,1 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita ostaje 17,5 % tekućih prihoda; medijan skupine: ostaje 11,2 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"neto dug mogao bi se otplatiti iz operativnog viška za 0,4 godine; medijan skupine 0,4 godine\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 6,3 % zakonske osnovice; medijan skupine 3,0 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 66.631 €, što je 1,5 % rashoda poslovanja; medijan skupine 1,3 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"servis duga\"},{\"label\":\"Jake strane\",\"value\":\"operativni saldo, slobodni saldo nakon otplate glavnice, godine otplate neto duga\"},{\"label\":\"Upozorenja\",\"value\":\"novca na računu manje nego za mjesec dana rashoda poslovanja\"}]},{\"oib\":\"00981494061\",\"naziv\":{\"nom\":\"Grad Knin\",\"gen\":\"Grada Knin\",\"lok\":\"Gradu Knin\"},\"year\":2025,\"ocjena\":1,\"ocjene\":[1,1],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Grad Knin (Šibensko-kninska županija), 11.633 stanovnika (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"1 (ozbiljan pritisak) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"gradovi 10.000-35.000 (42 jedinice)\"},{\"label\":\"Bodovi\",\"value\":\"19,4 boda od 100; medijan skupine 82,6 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"42. od 42\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"1 (ozbiljan pritisak)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni manjak iznosi 6,3 % tekućih prihoda; medijan skupine: višak 12,6 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita nedostaje 18,4 % tekućih prihoda; medijan skupine: ostaje 9,2 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"jedinica ima neto dug, a nema operativnog viška iz kojeg bi ga otplaćivala; medijan skupine 0,8 godine\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 19,1 % zakonske osnovice; medijan skupine 2,1 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 1.701.266 €, što je 17,2 % rashoda poslovanja; medijan skupine 0,6 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"slobodni saldo nakon otplate glavnice\"},{\"label\":\"Upozorenja\",\"value\":\"preneseni manjak iz prethodnih godina veći od 5 % tekućih prihoda; otplata duga i dospjele obveze blizu zakonskog limita (više od 20 % zakonske osnovice); rashodi poslovanja veći od tekućih prihoda dvije godine zaredom; novca na računu manje nego za mjesec dana rashoda poslovanja\"}]},{\"oib\":\"23492092438\",\"naziv\":{\"nom\":\"Općina Smokvica\",\"gen\":\"Općine Smokvica\",\"lok\":\"Općini Smokvica\"},\"year\":2025,\"ocjena\":2,\"ocjene\":[2,2],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Općina Smokvica (Dubrovačko-neretvanska županija), 868 stanovnika (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"2 (pod pritiskom) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"općine do 2.000 (202 jedinice)\"},{\"label\":\"Bodovi\",\"value\":\"27,1 boda od 100; medijan skupine 78,8 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"194. od 202\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"2 (pod pritiskom)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni višak iznosi 6,7 % tekućih prihoda; medijan skupine: višak 13,3 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita ostaje 2,7 % tekućih prihoda; medijan skupine: ostaje 10,8 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"neto dug mogao bi se otplatiti iz operativnog viška za 15,1 godine; većina jedinica u skupini nema neto duga\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 21,6 % zakonske osnovice; medijan skupine 3,1 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 365.095 €, što je 68,2 % rashoda poslovanja; medijan skupine 2,0 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"dospjele neplaćene obveze\"},{\"label\":\"Upozorenja\",\"value\":\"preneseni manjak iz prethodnih godina veći od 5 % tekućih prihoda; otplata duga i dospjele obveze blizu zakonskog limita (više od 20 % zakonske osnovice)\"}]},{\"oib\":\"99793768997\",\"naziv\":{\"nom\":\"Općina Kijevo\",\"gen\":\"Općine Kijevo\",\"lok\":\"Općini Kijevo\"},\"year\":2025,\"ocjena\":3,\"ocjene\":[3,4],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Općina Kijevo (Šibensko-kninska županija), 272 stanovnika (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"3 (umjereno) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"općine do 2.000 (202 jedinice)\"},{\"label\":\"Bodovi\",\"value\":\"46,6 boda od 100; medijan skupine 78,8 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"167. od 202\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"4 (stabilno)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni manjak iznosi 7,3 % tekućih prihoda; medijan skupine: višak 13,3 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita nedostaje 12,0 % tekućih prihoda; medijan skupine: ostaje 10,8 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"jedinica nema neto duga (novac na računu pokriva kredite); većina jedinica u skupini nema neto duga\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 10,2 % zakonske osnovice; medijan skupine 3,1 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 45.980 €, što je 9,8 % rashoda poslovanja; medijan skupine 2,0 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"slobodni saldo nakon otplate glavnice\"},{\"label\":\"Jake strane\",\"value\":\"godine otplate neto duga\"},{\"label\":\"Upozorenja\",\"value\":\"preneseni manjak iz prethodnih godina veći od 5 % tekućih prihoda; otplata duga i dospjele obveze blizu zakonskog limita (više od 20 % zakonske osnovice)\"}]},{\"oib\":\"08666646178\",\"naziv\":{\"nom\":\"Općina Severin\",\"gen\":\"Općine Severin\",\"lok\":\"Općini Severin\"},\"year\":2025,\"ocjena\":4,\"ocjene\":[4,5],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Općina Severin (Bjelovarsko-bilogorska županija), 702 stanovnika (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"4 (stabilno) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"općine do 2.000 (202 jedinice)\"},{\"label\":\"Bodovi\",\"value\":\"76,4 boda od 100; medijan skupine 78,8 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"106. od 202\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"5 (vrlo stabilno)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni višak iznosi 5,3 % tekućih prihoda; medijan skupine: višak 13,3 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita ostaje 3,5 % tekućih prihoda; medijan skupine: ostaje 10,8 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"jedinica nema neto duga (novac na računu pokriva kredite); većina jedinica u skupini nema neto duga\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 3,0 % zakonske osnovice; medijan skupine 3,1 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 678 €, što je 0,1 % rashoda poslovanja; medijan skupine 2,0 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"slobodni saldo nakon otplate glavnice\"},{\"label\":\"Jake strane\",\"value\":\"godine otplate neto duga, servis duga, dospjele neplaćene obveze\"},{\"label\":\"Upozorenja\",\"value\":\"nema upozorenja\"}]},{\"oib\":\"20647441417\",\"naziv\":{\"nom\":\"Općina Barilović\",\"gen\":\"Općine Barilović\",\"lok\":\"Općini Barilović\"},\"year\":2025,\"ocjena\":5,\"ocjene\":[5,5],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Općina Barilović (Karlovačka županija), 2.673 stanovnika (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"5 (vrlo stabilno) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"općine 2.000-5.000 (193 jedinice)\"},{\"label\":\"Bodovi\",\"value\":\"95,1 boda od 100; medijan skupine 87,8 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"58. od 193\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"5 (vrlo stabilno)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni višak iznosi 21,5 % tekućih prihoda; medijan skupine: višak 20,0 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita ostaje 17,4 % tekućih prihoda; medijan skupine: ostaje 16,9 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"jedinica nema neto duga (novac na računu pokriva kredite); većina jedinica u skupini nema neto duga\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 6,3 % zakonske osnovice; medijan skupine 3,8 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 6.807 €, što je 0,4 % rashoda poslovanja; medijan skupine 1,5 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"servis duga\"},{\"label\":\"Jake strane\",\"value\":\"operativni saldo, slobodni saldo nakon otplate glavnice, godine otplate neto duga, dospjele neplaćene obveze\"},{\"label\":\"Upozorenja\",\"value\":\"nema upozorenja\"}]},{\"oib\":\"67632922243\",\"naziv\":{\"nom\":\"Općina Oriovac\",\"gen\":\"Općine Oriovac\",\"lok\":\"Općini Oriovac\"},\"year\":2025,\"ocjena\":2,\"ocjene\":[2,2],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Općina Oriovac (Brodsko-posavska županija), 4.770 stanovnika (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"2 (pod pritiskom) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"općine 2.000-5.000 (193 jedinice)\"},{\"label\":\"Bodovi\",\"value\":\"21,2 boda od 100; medijan skupine 87,8 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"192. od 193\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"2 (pod pritiskom)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni manjak iznosi 4,3 % tekućih prihoda; medijan skupine: višak 20,0 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita nedostaje 10,6 % tekućih prihoda; medijan skupine: ostaje 16,9 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"jedinica ima neto dug, a nema operativnog viška iz kojeg bi ga otplaćivala; većina jedinica u skupini nema neto duga\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 16,6 % zakonske osnovice; medijan skupine 3,8 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 823.979 €, što je 18,2 % rashoda poslovanja; medijan skupine 1,5 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"slobodni saldo nakon otplate glavnice\"},{\"label\":\"Upozorenja\",\"value\":\"preneseni manjak iz prethodnih godina veći od 5 % tekućih prihoda; otplata duga i dospjele obveze blizu zakonskog limita (više od 20 % zakonske osnovice); novca na računu manje nego za mjesec dana rashoda poslovanja\"}]},{\"oib\":\"43345188266\",\"naziv\":{\"nom\":\"Općina Berek\",\"gen\":\"Općine Berek\",\"lok\":\"Općini Berek\"},\"year\":2025,\"ocjena\":3,\"ocjene\":[3,3],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Općina Berek (Bjelovarsko-bilogorska županija), 1.106 stanovnika (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"3 (umjereno) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"općine do 2.000 (202 jedinice)\"},{\"label\":\"Bodovi\",\"value\":\"48,5 boda od 100; medijan skupine 78,8 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"165. od 202\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"3 (umjereno)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni višak iznosi 5,4 % tekućih prihoda; medijan skupine: višak 13,3 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita nedostaje 7,3 % tekućih prihoda; medijan skupine: ostaje 10,8 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"neto dug mogao bi se otplatiti iz operativnog viška za 0,5 godine; većina jedinica u skupini nema neto duga\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 29,3 % zakonske osnovice; medijan skupine 3,1 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 54.473 €, što je 6,9 % rashoda poslovanja; medijan skupine 2,0 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"slobodni saldo nakon otplate glavnice\"},{\"label\":\"Upozorenja\",\"value\":\"preneseni manjak iz prethodnih godina veći od 5 % tekućih prihoda\"}]},{\"oib\":\"73261610446\",\"naziv\":{\"nom\":\"Općina Vidovec\",\"gen\":\"Općine Vidovec\",\"lok\":\"Općini Vidovec\"},\"year\":2025,\"ocjena\":4,\"ocjene\":[4,4],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Općina Vidovec (Varaždinska županija), 4.915 stanovnika (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"4 (stabilno) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"općine 2.000-5.000 (193 jedinice)\"},{\"label\":\"Bodovi\",\"value\":\"67,7 boda od 100; medijan skupine 87,8 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"159. od 193\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"4 (stabilno)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni višak iznosi 15,9 % tekućih prihoda; medijan skupine: višak 20,0 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita ostaje 8,2 % tekućih prihoda; medijan skupine: ostaje 16,9 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"neto dug mogao bi se otplatiti iz operativnog viška za 2,5 godine; većina jedinica u skupini nema neto duga\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 14,1 % zakonske osnovice; medijan skupine 3,8 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 331.522 €, što je 11,1 % rashoda poslovanja; medijan skupine 1,5 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"servis duga\"},{\"label\":\"Upozorenja\",\"value\":\"preneseni manjak iz prethodnih godina veći od 5 % tekućih prihoda; otplata duga i dospjele obveze blizu zakonskog limita (više od 20 % zakonske osnovice); novca na računu manje nego za mjesec dana rashoda poslovanja\"}]},{\"oib\":\"15857239976\",\"naziv\":{\"nom\":\"Grad Duga Resa\",\"gen\":\"Grada Duga Resa\",\"lok\":\"Gradu Duga Resa\"},\"year\":2025,\"ocjena\":5,\"ocjene\":[5,5],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Grad Duga Resa (Karlovačka županija), 10.212 stanovnika (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"5 (vrlo stabilno) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"gradovi 10.000-35.000 (42 jedinice)\"},{\"label\":\"Bodovi\",\"value\":\"98,1 boda od 100; medijan skupine 82,6 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"6. od 42\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"5 (vrlo stabilno)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni višak iznosi 19,6 % tekućih prihoda; medijan skupine: višak 12,6 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita ostaje 18,7 % tekućih prihoda; medijan skupine: ostaje 9,2 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"jedinica nema neto duga (novac na računu pokriva kredite); medijan skupine 0,8 godine\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 1,2 % zakonske osnovice; medijan skupine 2,1 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 55.233 €, što je 0,8 % rashoda poslovanja; medijan skupine 0,6 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"slobodni saldo nakon otplate glavnice\"},{\"label\":\"Jake strane\",\"value\":\"operativni saldo, slobodni saldo nakon otplate glavnice, godine otplate neto duga, servis duga\"},{\"label\":\"Upozorenja\",\"value\":\"nema upozorenja\"}]},{\"oib\":\"57113796391\",\"naziv\":{\"nom\":\"Općina Sveti Filip i Jakov\",\"gen\":\"Općine Sveti Filip i Jakov\",\"lok\":\"Općini Sveti Filip i Jakov\"},\"year\":2025,\"ocjena\":2,\"ocjene\":[2,4],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Općina Sveti Filip i Jakov (Zadarska županija), 4.461 stanovnik (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"2 (pod pritiskom) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"općine 2.000-5.000 (193 jedinice)\"},{\"label\":\"Bodovi\",\"value\":\"36,5 boda od 100; medijan skupine 87,8 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"185. od 193\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"4 (stabilno)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni višak iznosi 0,4 % tekućih prihoda; medijan skupine: višak 20,0 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita nedostaje 4,6 % tekućih prihoda; medijan skupine: ostaje 16,9 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"neto dug mogao bi se otplatiti iz operativnog viška za 211,9 godine; većina jedinica u skupini nema neto duga\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 5,8 % zakonske osnovice; medijan skupine 3,8 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 1.103.556 €, što je 12,9 % rashoda poslovanja; medijan skupine 1,5 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"godine otplate neto duga\"},{\"label\":\"Upozorenja\",\"value\":\"preneseni manjak iz prethodnih godina veći od 5 % tekućih prihoda; novca na računu manje nego za mjesec dana rashoda poslovanja\"}]},{\"oib\":\"81025770849\",\"naziv\":{\"nom\":\"Općina Brtonigla - Verteneglio\",\"gen\":\"Općine Brtonigla - Verteneglio\",\"lok\":\"Općini Brtonigla - Verteneglio\"},\"year\":2025,\"ocjena\":3,\"ocjene\":[3,4],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Općina Brtonigla - Verteneglio (Istarska županija), 1.523 stanovnika (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"3 (umjereno) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"općine do 2.000 (202 jedinice)\"},{\"label\":\"Bodovi\",\"value\":\"58,7 boda od 100; medijan skupine 78,8 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"153. od 202\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"4 (stabilno)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni višak iznosi 11,6 % tekućih prihoda; medijan skupine: višak 13,3 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita ostaje 7,3 % tekućih prihoda; medijan skupine: ostaje 10,8 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"jedinica nema neto duga (novac na računu pokriva kredite); većina jedinica u skupini nema neto duga\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 4,5 % zakonske osnovice; medijan skupine 3,1 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 741.235 €, što je 24,2 % rashoda poslovanja; medijan skupine 2,0 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"dospjele neplaćene obveze\"},{\"label\":\"Jake strane\",\"value\":\"godine otplate neto duga\"},{\"label\":\"Upozorenja\",\"value\":\"otplata duga i dospjele obveze blizu zakonskog limita (više od 20 % zakonske osnovice)\"}]},{\"oib\":\"06550373801\",\"naziv\":{\"nom\":\"Općina Budinščina\",\"gen\":\"Općine Budinščina\",\"lok\":\"Općini Budinščina\"},\"year\":2025,\"ocjena\":4,\"ocjene\":[4,3],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Općina Budinščina (Krapinsko-zagorska županija), 2.182 stanovnika (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"4 (stabilno) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"općine 2.000-5.000 (193 jedinice)\"},{\"label\":\"Bodovi\",\"value\":\"64,3 boda od 100; medijan skupine 87,8 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"165. od 193\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"3 (umjereno)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni višak iznosi 9,3 % tekućih prihoda; medijan skupine: višak 20,0 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita ostaje 1,9 % tekućih prihoda; medijan skupine: ostaje 16,9 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"neto dug mogao bi se otplatiti iz operativnog viška za 6,4 godine; većina jedinica u skupini nema neto duga\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 13,8 % zakonske osnovice; medijan skupine 3,8 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 34.012 €, što je 2,7 % rashoda poslovanja; medijan skupine 1,5 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"slobodni saldo nakon otplate glavnice\"},{\"label\":\"Upozorenja\",\"value\":\"nema upozorenja\"}]},{\"oib\":\"45800936748\",\"naziv\":{\"nom\":\"Općina Babina Greda\",\"gen\":\"Općine Babina Greda\",\"lok\":\"Općini Babina Greda\"},\"year\":2025,\"ocjena\":5,\"ocjene\":[5,4],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Općina Babina Greda (Vukovarsko-srijemska županija), 2.762 stanovnika (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"5 (vrlo stabilno) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"općine 2.000-5.000 (193 jedinice)\"},{\"label\":\"Bodovi\",\"value\":\"87,1 boda od 100; medijan skupine 87,8 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"99. od 193\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"4 (stabilno)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni višak iznosi 23,4 % tekućih prihoda; medijan skupine: višak 20,0 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita ostaje 23,4 % tekućih prihoda; medijan skupine: ostaje 16,9 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"neto dug mogao bi se otplatiti iz operativnog viška za 4,3 godine; većina jedinica u skupini nema neto duga\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 1,1 % zakonske osnovice; medijan skupine 3,8 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 169.889 €, što je 9,2 % rashoda poslovanja; medijan skupine 1,5 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"dospjele neplaćene obveze\"},{\"label\":\"Jake strane\",\"value\":\"operativni saldo, slobodni saldo nakon otplate glavnice, servis duga\"},{\"label\":\"Upozorenja\",\"value\":\"preneseni manjak iz prethodnih godina veći od 5 % tekućih prihoda; novca na računu manje nego za mjesec dana rashoda poslovanja\"}]},{\"oib\":\"65496793357\",\"naziv\":{\"nom\":\"Grad Obrovac\",\"gen\":\"Grada Obrovac\",\"lok\":\"Gradu Obrovac\"},\"year\":2025,\"ocjena\":2,\"ocjene\":[2,2],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Grad Obrovac (Zadarska županija), 3.453 stanovnika (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"2 (pod pritiskom) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"gradovi 2.000-5.000 (21 jedinica)\"},{\"label\":\"Bodovi\",\"value\":\"34 boda od 100; medijan skupine 80,6 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"21. od 21\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"2 (pod pritiskom)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni manjak iznosi 11,2 % tekućih prihoda; medijan skupine: višak 14,1 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita nedostaje 15,8 % tekućih prihoda; medijan skupine: ostaje 11,2 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"jedinica ima neto dug, a nema operativnog viška iz kojeg bi ga otplaćivala; medijan skupine 0,4 godine\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 8,1 % zakonske osnovice; medijan skupine 3,0 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 333.457 €, što je 7,0 % rashoda poslovanja; medijan skupine 1,3 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"operativni saldo\"},{\"label\":\"Upozorenja\",\"value\":\"rashodi poslovanja veći od tekućih prihoda dvije godine zaredom\"}]},{\"oib\":\"14013350842\",\"naziv\":{\"nom\":\"Općina Cerna\",\"gen\":\"Općine Cerna\",\"lok\":\"Općini Cerna\"},\"year\":2025,\"ocjena\":3,\"ocjene\":[3,5],\"facts\":[{\"label\":\"Jedinica\",\"value\":\"Općina Cerna (Vukovarsko-srijemska županija), 3.712 stanovnika (Popis 2021.)\"},{\"label\":\"Ocjena financijske stabilnosti za 2025.\",\"value\":\"3 (umjereno) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)\"},{\"label\":\"Usporedna skupina\",\"value\":\"općine 2.000-5.000 (193 jedinice)\"},{\"label\":\"Bodovi\",\"value\":\"44,5 boda od 100; medijan skupine 87,8 boda\"},{\"label\":\"Mjesto u skupini\",\"value\":\"177. od 193\"},{\"label\":\"Ocjena za 2024.\",\"value\":\"5 (vrlo stabilno)\"},{\"label\":\"Sastavnica: operativni saldo\",\"value\":\"operativni višak iznosi 11,8 % tekućih prihoda; medijan skupine: višak 20,0 % tekućih prihoda\"},{\"label\":\"Sastavnica: slobodni saldo nakon otplate glavnice\",\"value\":\"nakon otplate glavnice kredita nedostaje 0,0 % tekućih prihoda; medijan skupine: ostaje 16,9 % tekućih prihoda\"},{\"label\":\"Sastavnica: godine otplate neto duga\",\"value\":\"neto dug mogao bi se otplatiti iz operativnog viška za 2,3 godine; većina jedinica u skupini nema neto duga\"},{\"label\":\"Sastavnica: servis duga\",\"value\":\"otplata kredita i kamata iznosi 23,7 % zakonske osnovice; medijan skupine 3,8 % zakonske osnovice\"},{\"label\":\"Sastavnica: dospjele neplaćene obveze\",\"value\":\"dospjele neplaćene obveze na kraju godine iznose 592.661 €, što je 20,2 % rashoda poslovanja; medijan skupine 1,5 % rashoda poslovanja\"},{\"label\":\"Najslabija sastavnica\",\"value\":\"servis duga\"},{\"label\":\"Upozorenja\",\"value\":\"preneseni manjak iz prethodnih godina veći od 5 % tekućih prihoda; otplata duga i dospjele obveze blizu zakonskog limita (više od 20 % zakonske osnovice); novca na računu manje nego za mjesec dana rashoda poslovanja\"}]}]")
MAX_RETRIES = 2
HF_MODELS = [["unsloth/gemma-4-31B-it-qat-GGUF", "gemma-4-31B-it-qat-UD-Q4_K_XL.gguf"]]                 # [[repo, file], ...] downloaded from Hugging Face in the session
HF_DIR = "/tmp/hf-models"                 # not /kaggle/working: the 20 GB output would keep the file
SRC = "/tmp/llama.cpp"
SERVER = f"{SRC}/build/bin/llama-server"
OUT = "/kaggle/working/gemma_test_output.json"
LOG = "/kaggle/working/llama_server.log"
PORT = 8080


def sh(cmd, check=True):
    print("$", cmd, flush=True)
    t = time.time()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    tail = (r.stdout + r.stderr)[-3000:]
    print(tail, flush=True)
    print(f"  ({time.time() - t:.0f} s, exit {r.returncode})", flush=True)
    if r.returncode and check:
        raise SystemExit(f"failed: {cmd}")
    return r.stdout if not r.returncode else None


BIN_OUT = "/kaggle/working/llama-bin"     # saved with the notebook output, reused by later runs


def cached_build():
    """A llama-server built by an earlier run, attached as a kernel source."""
    hits = glob.glob("/kaggle/input/**/llama-bin/llama-server", recursive=True)
    if not hits:
        return None
    src = os.path.dirname(hits[0])
    sh(f"mkdir -p {SRC}/build && cp -r {src} {SRC}/build/bin && chmod +x {SERVER}")
    commit = open(os.path.join(src, "COMMIT")).read().strip() if os.path.exists(os.path.join(src, "COMMIT")) else "?"
    print("using cached llama-server from", src, commit, flush=True)
    return commit


def save_build(commit):
    sh(f"mkdir -p {BIN_OUT} && cp {SRC}/build/bin/llama-server {BIN_OUT}/ && "
       f"cp {SRC}/build/bin/*.so* {BIN_OUT}/ 2>/dev/null; echo {commit} > {BIN_OUT}/COMMIT; ls -la {BIN_OUT}")


def build_llama_cpp():
    os.environ["PATH"] = "/usr/local/cuda/bin:" + os.environ["PATH"]
    sh("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv")
    cached = cached_build()
    if cached:
        return cached
    sh("nvcc --version | tail -2; cmake --version | head -1")
    sh(f"git clone --depth 1 https://github.com/ggml-org/llama.cpp {SRC}")
    commit = sh(f"git -C {SRC} rev-parse HEAD").strip()
    # CUDA 13 on Kaggle: CMake may not find the libcuda stub, so point it at every stub
    # directory; if CUDA::cuda_driver is still missing, build without VMM (no libcuda link).
    stubs = sorted({os.path.dirname(p) for p in glob.glob("/usr/local/cuda*/**/stubs/libcuda.so", recursive=True)})
    print("libcuda stubs:", stubs, flush=True)
    base = (f"cmake -S {SRC} -B {SRC}/build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=75 "
            f"-DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release")
    if stubs:
        base += f" -DCMAKE_LIBRARY_PATH={';'.join(stubs)}"
    if sh(base, check=False) is None:
        sh(f"rm -rf {SRC}/build")
        sh(base + " -DGGML_CUDA_NO_VMM=ON")
    sh(f"cmake --build {SRC}/build --config Release -j {os.cpu_count()} --target llama-server")
    save_build(commit)
    return commit


def download_hf_models():
    """GGUF files that are not on Kaggle Models (e.g. Unsloth quants), fetched over HTTPS."""
    os.makedirs(HF_DIR, exist_ok=True)
    for repo, name in HF_MODELS:
        dest = os.path.join(HF_DIR, name)
        if not os.path.exists(dest):
            sh(f"curl -L --fail --retry 3 -sS -o {dest} https://huggingface.co/{repo}/resolve/main/{name} && ls -la {dest}")


def find_models():
    """Every attached or downloaded GGUF model except the vision projector and MTP drafter,
    smallest first."""
    files = glob.glob("/kaggle/input/**/*.gguf", recursive=True) + glob.glob(f"{HF_DIR}/*.gguf")
    files = [f for f in files if "mmproj" not in f and "mtp-" not in os.path.basename(f)]
    files.sort(key=os.path.getsize)
    print("GGUF files:", files, flush=True)
    if not files:
        raise SystemExit("no GGUF model attached")
    return files


def start_server(model):
    log = open(LOG, "w")
    proc = subprocess.Popen([SERVER, "-m", model, "-ngl", "99", "-c", "8192", "--jinja",
                             "--split-mode", "layer", "--port", str(PORT), "-np", "1"],
                            stdout=log, stderr=subprocess.STDOUT)
    for _ in range(600):                      # up to 20 min: the 31B file is 17.7 GB
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=5) as r:
                if r.status == 200:
                    return proc
        except Exception:
            pass
        if proc.poll() is not None:
            break
        time.sleep(2)
    print(open(LOG).read()[-5000:])
    raise SystemExit("llama-server did not start")


def chat(msgs):
    body = {"messages": msgs, "temperature": 0.3, "top_p": 0.9, "max_tokens": 450,
            "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/v1/chat/completions",
                                 data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    t = time.time()
    with urllib.request.urlopen(req, timeout=300) as r:
        out = json.loads(r.read())
    text = out["choices"][0]["message"].get("content") or ""
    for tag in ("<think>", "<|channel>"):          # in case a thinking block slips through
        if tag in text:
            text = text.split("</think>")[-1].split("<channel|>")[-1]
    return text.strip(), round(time.time() - t, 1), out.get("usage", {})


def run_job(pack):
    """Same loop as pipeline/explain.generate, but keeps the last model text instead of the
    template, so the test shows what the model wrote."""
    msgs = messages(pack)
    attempts = []
    for _ in range(1 + MAX_RETRIES):
        text, secs, usage = chat(msgs)
        check = verify(text, pack)
        attempts.append({"text": text, "check": check, "seconds": secs, "usage": usage})
        if check["ok"]:
            break
        msgs = msgs + [{"role": "assistant", "content": text},
                       {"role": "user", "content": feedback(check["nepoznate"], check.get("sadrzaj", []))}]
    return {"oib": pack["oib"], "naziv": pack["naziv"]["nom"], "text": attempts[-1]["text"],
            "source": "ai" if attempts[-1]["check"]["ok"] else "neprovjereno",
            "check": attempts[-1]["check"], "attempts": attempts}


def main():
    t0 = time.time()
    commit = build_llama_cpp()
    gpu = sh("nvidia-smi --query-gpu=name --format=csv,noheader").strip()
    out = {"partial": True, "meta": {"llama_cpp_commit": commit, "gpu": gpu, "max_retries": MAX_RETRIES,
                                     "hf_models": HF_MODELS}, "models": {}}
    t_dl = time.time()
    download_hf_models()
    out["meta"]["hf_download_seconds"] = round(time.time() - t_dl)
    for model in find_models():
        name = os.path.basename(model)
        t1 = time.time()
        try:
            proc = start_server(model)
        except SystemExit as e:                # e.g. out of GPU memory: keep the other models
            out["models"][name] = {"error": str(e), "log": open(LOG).read()[-3000:], "results": []}
            json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
            continue
        out["models"][name] = {"load_seconds": round(time.time() - t1), "results": [],
                               "gpu_memory": sh("nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader")}
        results = []
        for i, pack in enumerate(PACKS, 1):
            r = run_job(pack)
            results.append(r)
            print(f"[{name} {i}/{len(PACKS)}] {r['naziv']}: {r['source']}, {len(r['attempts'])} pokušaja, "
                  f"{r['check']['n_brojki']} brojki, nepoznate {r['check']['nepoznate']}", flush=True)
            out["models"][name]["results"] = results
            json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
        proc.terminate()
        proc.wait(timeout=60)
        out["models"][name]["seconds"] = round(time.time() - t1)
        ok = sum(r["source"] == "ai" for r in results)
        print(f"{name}: {ok}/{len(results)} tekstova prošlo provjeru u {out['models'][name]['seconds']} s", flush=True)
    out["partial"] = False
    out["meta"]["seconds_total"] = round(time.time() - t0)
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("Gotovo:", out["meta"])


if __name__ == "__main__":
    main()
