"""Fact pack for the AI explanation of a unit's grade (PLAN §5).

Python computes every number and also decides what the story is: the weakest and the
strongest component, the change against last year and the comparison with similar units.
The language model only writes sentences around these facts. pipeline/verify.py then checks
that every number in the text appears here.

Numbers are written the Croatian way (1.625,85; 27,6 %), so the model can copy them.
"""
import math

import pandas as pd

GRADE_WORDS = {5: "vrlo stabilno", 4: "stabilno", 3: "umjereno", 2: "pod pritiskom", 1: "ozbiljan pritisak"}

COMPONENTS = {
    "I1": "operativni saldo",
    "I2": "slobodni saldo nakon otplate glavnice",
    "I3": "godine otplate neto duga",
    "I4": "servis duga",
    "I5": "dospjele neplaćene obveze",
}

FLAGS = {
    "Z1": "preneseni manjak iz prethodnih godina veći od 5 % tekućih prihoda",
    "Z2": "otplata duga i dospjele obveze blizu zakonskog limita (više od 20 % zakonske osnovice)",
    "Z3": "rashodi poslovanja veći od tekućih prihoda dvije godine zaredom",
    "Z4": "novca na računu manje nego za mjesec dana rashoda poslovanja",
}


def num(x, dec=0):
    """Croatian number format: 1.625,85"""
    s = f"{abs(x):,.{dec}f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return ("-" if x < 0 and float(s.replace(".", "").replace(",", ".")) != 0 else "") + s


def pct(share, dec=1):
    return f"{num(share * 100, dec)} %"


def eur(x):
    return f"{num(x)} €"


def plural(n, one, few, many):
    """Croatian noun after a whole number: 1 jedinica, 2 jedinice, 5 jedinica, 21 jedinica... """
    n = int(n)
    if n % 10 == 1 and n % 100 != 11:
        return one
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return few
    return many


def years(x):
    """Years as a decimal take the genitive singular: 1,2 godine."""
    return f"{num(x, 1)} godine"


def cases(naziv, vrsta):
    """Name in the nominative, genitive and locative. Only the leading noun is declined
    ("Općine Sveta Marija", "Gradu Dugo Selo"), which is the usual administrative style."""
    if naziv == "Grad Zagreb":
        return {"nom": naziv, "gen": "Grada Zagreba", "lok": "Gradu Zagrebu"}
    if vrsta == "opcina":
        rest = naziv.removeprefix("Općina ")
        return {"nom": naziv, "gen": f"Općine {rest}", "lok": f"Općini {rest}"}
    if vrsta == "grad":
        rest = naziv.removeprefix("Grad ")
        return {"nom": naziv, "gen": f"Grada {rest}", "lok": f"Gradu {rest}"}
    adj = naziv.removesuffix(" županija")            # "Međimurska" -> "Međimurske županije"
    return {"nom": naziv, "gen": f"{adj[:-1]}e županije", "lok": f"{adj[:-1]}oj županiji"}


def describe(code, value, row):
    """One line per component, in words a citizen understands."""
    if code == "I1":
        word = "operativni višak" if value >= 0 else "operativni manjak"
        return f"{word} iznosi {pct(abs(value))} tekućih prihoda"
    if code == "I2":
        if value >= 0:
            return f"nakon otplate glavnice kredita ostaje {pct(value)} tekućih prihoda"
        return f"nakon otplate glavnice kredita nedostaje {pct(-value)} tekućih prihoda"
    if code == "I3":
        if row["ND"] <= 0:
            return "jedinica nema neto duga (novac na računu pokriva kredite)"
        if math.isinf(value):
            return "jedinica ima neto dug, a nema operativnog viška iz kojeg bi ga otplaćivala"
        if value < 0.05:
            return "neto dug je zanemariv (otplatio bi se iz operativnog viška za manje od mjesec dana)"
        return f"neto dug mogao bi se otplatiti iz operativnog viška za {years(value)}"
    if code == "I4":
        return f"otplata kredita i kamata iznosi {pct(value)} zakonske osnovice"
    if code == "I5":
        if row["DO"] <= 0:
            return "na kraju godine nema dospjelih neplaćenih obveza"
        return f"dospjele neplaćene obveze na kraju godine iznose {eur(row['DO'])}, što je {pct(value)} rashoda poslovanja"
    raise KeyError(code)


def median_phrase(code, mv):
    """The peer median in the same words as the unit's value, so a deficit is never set
    against a surplus without saying so."""
    if pd.isna(mv):
        return "medijan skupine nije dostupan"
    if code == "I1":
        return f"medijan skupine: {'višak' if mv >= 0 else 'manjak'} {pct(abs(mv))} tekućih prihoda"
    if code == "I2":
        return f"medijan skupine: {'ostaje' if mv >= 0 else 'nedostaje'} {pct(abs(mv))} tekućih prihoda"
    if code == "I3":
        if math.isinf(mv):
            return "većina jedinica u skupini ima neto dug bez operativnog viška"
        return "većina jedinica u skupini nema neto duga" if mv < 0.05 else f"medijan skupine {years(mv)}"
    if code == "I4":
        return f"medijan skupine {pct(mv)} zakonske osnovice"
    return f"medijan skupine {pct(mv)} rashoda poslovanja"


def not_worse_than_median(code, value, mv):
    """I1 and I2: higher is better; I3, I4 and I5: lower is better."""
    if pd.isna(mv) or value is None or pd.isna(value):
        return True
    return value >= mv if code in ("I1", "I2") else value <= mv


def points(x):
    """Points with the right noun: 34,2 boda (decimals take the genitive singular), 100 bodova."""
    if float(x).is_integer():
        return f"{num(x)} {plural(x, 'bod', 'boda', 'bodova')}"
    return f"{num(x, 1)} boda"


def peer_medians(results):
    """Medians per peer group and year. I3 keeps its infinite values (net debt and no operating
    surplus): they are the worst cases, and dropping them would bias the median towards 'no debt'."""
    cols = ["I1", "I2", "I3", "I4", "I5", "uprava_pc", "udio_tekucih_pomoci", "bodovi"]
    return results.groupby(["skupina", "year"])[cols].median()


def fact_pack(unit, history, med, year):
    """unit: row of units.csv; history: {year: results row}; med: peer_medians()."""
    r = history[year]
    prev = history.get(year - 1)
    m = med.loc[(r["skupina"], year)]
    names = cases(unit["naziv"], unit["vrsta"])
    n_peer = int(r["n_skupine"])
    peers = n_peer > 1                      # Grad Zagreb is a group of one: no comparison (PLAN §3.6)
    pop = int(unit["stanovnici_2021"])
    facts = [
        ("Jedinica", f"{names['nom']} ({unit['zupanija']}), {num(pop)} "
                     f"{plural(pop, 'stanovnik', 'stanovnika', 'stanovnika')} (Popis 2021.)"),
        (f"Ocjena financijske stabilnosti za {year}.",
         f"{int(r['ocjena'])} ({r['ocjena_rijec']}) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)"),
    ]
    if peers:
        facts += [
            ("Usporedna skupina", f"{r['skupina']} ({n_peer} {plural(n_peer, 'jedinica', 'jedinice', 'jedinica')})"),
            ("Bodovi", f"{points(r['bodovi'])} od 100; medijan skupine {points(m['bodovi'])}"),
            ("Mjesto u skupini", f"{int(r['rang'])}. od {n_peer}"),
        ]
    else:
        facts += [
            ("Bodovi", f"{points(r['bodovi'])} od 100"),
            ("Usporedba", "jedinica nema usporedive skupine, pa se ocjenjuje samo prema pragovima"),
        ]
    if prev is not None and pd.notna(prev.get("ocjena")):
        facts.append((f"Ocjena za {year - 1}.", f"{int(prev['ocjena'])} ({prev['ocjena_rijec']})"))
    # the averaging window is shown on the profile page; in the text it only took up words (Gemma test v3)

    scores = {c: r[f"S{c[1]}"] for c in COMPONENTS}
    for c, label in COMPONENTS.items():
        line = describe(c, r[c], r)
        if peers:
            line += "; " + median_phrase(c, m[c])
        facts.append((f"Sastavnica: {label}", line))
    # the story: the weakest component (if it is weak at all) and the clear strengths.
    # A strength must score high and, where there is a peer group, not be worse than its median.
    valid = {c: s for c, s in scores.items() if s is not None and not pd.isna(s)}
    weakest = min(valid, key=valid.get)
    if valid[weakest] < 80:
        facts.append(("Najslabija sastavnica", COMPONENTS[weakest]))
    strong = [COMPONENTS[c] for c, s in valid.items()
              if s >= 90 and (not peers or not_worse_than_median(c, r[c], m[c]))]
    if strong:                      # no "nijedna ..." line: the model turned it into "Jake strane su: nijedna" (v4)
        facts.append(("Jake strane", ", ".join(strong)))

    flags = [f for f in str(r.get("zastavice") or "").split(",") if f]
    facts.append(("Upozorenja", "; ".join(FLAGS[f] for f in flags) if flags else "nema upozorenja"))
    if r.get("ogranicenje_do"):
        facts.append(("Pravilo", "ocjena je ograničena na najviše 2 jer dospjele obveze dosežu 30 % rashoda poslovanja"))
    if r.get("kredit_iskazan_dospio"):
        facts.append(("Napomena o podacima", "u Bilanci je cijeli kredit iskazan kao dospio, ali se redovno otplaćuje, "
                                              "pa se ne broji u dospjele obveze"))
    # Context (grants, administration cost) is on the profile page, not in the pack: in the Gemma
    # test it only produced filler and invented phrases ("kućne pomoći").
    grades = [int(r["ocjena"])] + ([int(prev["ocjena"])] if prev is not None and pd.notna(prev.get("ocjena")) else [])
    return {"oib": unit["oib"], "naziv": names, "year": year, "ocjena": int(r["ocjena"]), "ocjene": grades,
            "facts": [{"label": k, "value": v} for k, v in facts]}


def build_all(units, results, year):
    """Fact packs for every unit in one year."""
    med = peer_medians(results)
    by_oib = {oib: {int(x["year"]): x for x in g.to_dict("records")} for oib, g in results.groupby("oib")}
    return [fact_pack(u, by_oib[u["oib"]], med, year) for u in units.to_dict("records") if u["oib"] in by_oib]
