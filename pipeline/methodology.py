"""Methodology v2 (docs/PLAN.md §3): auxiliary quantities, indicators, 0-100 scores,
grades, sensitivity scenarios, red flags and context measures.

Inputs are plain dicts, one per unit and year, with PR-RAS values as p_<code> and
Bilanca values as b_<code> / b_<code>_D. Everything here is pure, so it is tested
directly in tests/test_methodology.py.
"""
import math

from . import config

WINDOW_WEIGHTS = [4, 3, 2, 1]  # year t, t-1, t-2, t-3 (INEKO)

ANCHORS = {
    "I1": [(-0.10, 0), (0.05, 50), (0.20, 100)],
    "I2": [(-0.05, 0), (0.0, 24), (0.05, 44), (0.10, 64), (0.15, 84), (0.20, 100)],
    "I3": [(0, 100), (3, 84), (7, 64), (12, 44), (25, 24), (35, 0)],
    "I4": [(0, 100), (0.05, 84), (0.10, 64), (0.15, 44), (0.20, 24), (0.30, 0)],
    "I5": [(0.005, 100), (0.15, 50), (0.30, 0)],
}

SCENARIOS = {
    "osnovni": {"I1": 20, "I2": 20, "I3": 15, "I4": 15, "I5": 30},
    "jednaki": {"I1": 20, "I2": 20, "I3": 20, "I4": 20, "I5": 20},
    "kdz": {"I1": 25, "I2": 25, "I3": 12.5, "I4": 12.5, "I5": 25},
    "ineko": {"I1": 30, "I2": 0, "I3": 30, "I4": 10, "I5": 30},
}

GRADES = [(80, 5, "vrlo stabilno"), (60, 4, "stabilno"), (40, 3, "umjereno stabilno"),
          (20, 2, "nestabilno"), (-1, 1, "vrlo nestabilno")]

# A principal repayment above this share of current revenue, financed by new
# borrowing in the same year, is treated as refinancing.
REFINANCING_SHARE = 0.10

# Rule 1 (docs/research/05): a loan reported as entirely overdue while its principal
# is being repaid on schedule is a reporting error (Sveta Marija 2025), so it does
# not count as overdue. A loan that is not being repaid stays overdue (Povljana).
LOAN_ALL_DUE_MIN = 10_000      # € of loan balance; smaller loans are left as reported
LOAN_ALL_DUE_SHARE = 0.90      # overdue part of the loan, as a share of the balance
LOAN_REPAID_SHARE = 0.03       # principal repaid in the year, as a share of the opening balance

# Rule 2: overdue liabilities of at least 30% of operating spending (where S5 reaches 0)
# cap the grade at 2. Points are capped too, so grade, rank and percentile agree.
DO_CAP_SHARE = 0.30
DO_CAP_POINTS = 39.9

# A merged unit (pipeline/merge.py) carries the overdue loan amount that rule 1 removed
# from each member under this key. Rule 1 is then not tested again on the sums, because
# a sum can pass or fail where no member does (PLAN §11, decision 16).
RULE1_EXCLUDED = "pravilo1_iskljuceno"

# Z5, the 10 % criterion (Government conclusion of 16.4.2026, docs/research/08 §5): a unit gets
# state-budget aid awarded through calls only when its deficit of revenue over expenditure,
# without EU sources, is at most 10 % of total revenue without EU sources, in the last annual
# report. PR-RAS does not split expenditure by source, so EU-funded expenditure is taken to equal
# EU revenue of the same year: the deficit is then (3 + 4) - (6 + 7) and only the base drops the
# EU revenue (accounts 638 and 6324; 6323, current aid from EU bodies, is not in our extract).
# Shown as context, outside the score and outside the red flags, so the AI fact packs stay as they are.
Z5_SHARE = 0.10
EU_REVENUE = ["638", "6324"]

# Fiscal equalization in ZO (pipeline/izravnanje_isplate.py, decided 4.11.): ZO adds back p_FI, the
# amount of the MF decision (share x budget amount, p_FI_odluka) capped at the current-grant accounts
# that can hold it, FI_ROOM = 6331 (633 - 6332) + 6352 + 6353. Without p_FI (no decision for the
# year) it is 6353 as booked. Quality notes when the decision amount and the books disagree by more
# than FI_NOTE_SHARE of the decision amount and more than FI_NOTE_MIN euros:
# - izravnanje_nije_medu_pomocima: the decision amount exceeds FI_ROOM (booked under taxes, 611);
#   ZO adds back only FI_ROOM;
# - from FI_6353_FROM (the first year 6353 is in general use; in 2021-2024 nobody books it, so a
#   note would mark every unit): izravnanje_na_drugom_kontu (6353 below the decision amount: booked
#   on 6331 or 6352) and konto_6353_vise_od_odluke (6353 above it: other grants on 6353 as well).
FI_ROOM = {"p_633": 1, "p_6332": -1, "p_6352": 1, "p_6353": 1}
FI_NOTE_SHARE = 0.10
FI_NOTE_MIN = 1_000.0
FI_6353_FROM = 2025

# Peer groups (PLAN §3.5): type and size class; each group has at least 15 units.
SIZE_CLASSES = [(0, 2000, "do 2.000"), (2000, 5000, "2.000-5.000"), (5000, 10000, "5.000-10.000"),
                (10000, 35000, "10.000-35.000"), (35000, 10**9, "35.000+")]


def size_class(pop):
    for lo, hi, label in SIZE_CLASSES:
        if lo <= pop < hi:
            return label
    return None


def peer_group(u):
    """u has vrsta, zagreb and stanovnici_2021 (a units.csv row as a namedtuple)."""
    if u.vrsta == "zupanija":
        return "županije"
    if u.zagreb:
        return "Grad Zagreb"
    if u.vrsta == "grad" and u.stanovnici_2021 >= 35000:
        return "veliki gradovi"
    return f"{'općine' if u.vrsta == 'opcina' else 'gradovi'} {size_class(u.stanovnici_2021)}"


def _num(r, k):
    """Value from a unit-year dict; missing, None and NaN count as 0."""
    v = (r or {}).get(k)
    return 0.0 if v is None or (isinstance(v, float) and math.isnan(v)) else float(v)


def loan_reported_all_due_but_repaid(r, prev):
    """Rule 1. r: unit-year dict for year t, prev: the same unit's dict for t-1 or None.

    The loan counts as regular (not overdue) when it is repaid on schedule, or, since
    decision 17 (PLAN §11, 4.11.), when it is still being drawn: the balance at the end
    of t is above the balance at the end of t-1 (Sveta Marija 2023, grace period, no
    principal yet). The first year of the series has no t-1 and is never a drawdown."""
    loan, due = _num(r, "b_26"), _num(r, "b_26_D")
    if loan <= LOAN_ALL_DUE_MIN or due < LOAN_ALL_DUE_SHARE * loan:
        return False
    opening = (prev or {}).get("b_26")
    if opening is None or (isinstance(opening, float) and math.isnan(opening)):
        opening = loan                      # first year of the series: use the closing balance
    elif loan > opening:
        return True                         # decision 17: loan still being drawn
    return _num(r, "p_54") >= LOAN_REPAID_SHARE * opening   # opening 0 = new loan, passes


def rule1_excluded(r, prev):
    """Overdue loan amount that rule 1 takes out of DO: the whole b_26_D when the rule holds,
    else 0. A merged unit brings the sum over its members instead (RULE1_EXCLUDED)."""
    if RULE1_EXCLUDED in r:
        return _num(r, RULE1_EXCLUDED)
    return _num(r, "b_26_D") if loan_reported_all_due_but_repaid(r, prev) else 0.0


def interp(x, anchors):
    """Piecewise-linear score between anchors, clamped at both ends. inf -> worst end."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    if math.isinf(x):
        return anchors[-1][1] if x > 0 else anchors[0][1]
    if x <= anchors[0][0]:
        return float(anchors[0][1])
    for (x0, s0), (x1, s1) in zip(anchors, anchors[1:]):
        if x <= x1:
            return s0 + (s1 - s0) * (x - x0) / (x1 - x0)
    return float(anchors[-1][1])


def grade(total):
    if total is None:
        return None, None
    for cut, g, word in GRADES:
        if total >= cut:
            return g, word
    return 1, "vrlo nestabilno"


def equalization(r):
    """Fiscal equalization that ZO adds back (FI_ROOM above): p_FI when the build gives it, else
    account 6353 as booked."""
    v = r.get("p_FI")
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return _num(r, "p_6353")
    return float(v)


def equalization_paid(r):
    """Equalization the unit received (context measure udio_fiskalnog_izravnanja): the decision
    amount p_FI_odluka, uncapped, else account 6353 as booked."""
    v = r.get("p_FI_odluka")
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return _num(r, "p_6353")
    return float(v)


def equalization_notes(r, year=None):
    """Quality notes on the equalization booking of one unit-year (FI_ROOM above)."""
    decided = r.get("p_FI_odluka")
    if decided is None or (isinstance(decided, float) and math.isnan(decided)):
        return []
    decided = float(decided)
    tol = max(FI_NOTE_MIN, FI_NOTE_SHARE * decided)
    room = max(0.0, sum(sign * _num(r, k) for k, sign in FI_ROOM.items()))
    booked = _num(r, "p_6353")
    if decided - room > tol:
        return ["izravnanje_nije_medu_pomocima"]
    if year is not None and year >= FI_6353_FROM:
        if decided - booked > tol:
            return ["izravnanje_na_drugom_kontu"]
        if booked - decided > tol:
            return ["konto_6353_vise_od_odluke"]
    return []


def aux(r, prev=None):
    """Per-year auxiliary quantities (PLAN §3.1) from one unit-year dict (prev: year t-1)."""
    g = lambda k: r.get(k) or 0.0
    kp = sum(g(f"p_{c}") for c in config.CAPITAL_GRANTS)
    po = g("p_6") - kp
    os_ = po - g("p_3")
    principal = g("p_54")
    refinancing = principal > REFINANCING_SHARE * po and g("p_84") > 0 and po > 0
    principal_adj = max(0.0, principal - g("p_84")) if refinancing else principal
    zo = g("p_6") + g("p_7") - g("p_63") + equalization(r) - g("p_663") - g("p_dio611")
    do_reported = _num(r, "b_23_D") + _num(r, "b_24_D") + _num(r, "b_26_D")
    excluded = rule1_excluded(r, prev)
    return {
        "KP": kp,
        "PO": po,
        "OS": os_,
        "ND": max(0.0, g("b_26") + g("b_25") - g("b_11")),
        "SD": g("p_341") + g("p_342") + principal_adj,
        "glavnica_adj": principal_adj,
        "refinanciranje": refinancing,
        "ZO": zo,
        "DO": do_reported - excluded,
        "DO_iskazano": do_reported,
        "kredit_iskazan_dospio": excluded > 0,
    }


def _wsum(series, key, years, shift=0):
    """Weighted sum over the window. series: {year: aux}. Returns (sum, weight used)."""
    total, wsum = 0.0, 0
    for w, y in zip(WINDOW_WEIGHTS, years):
        a = series.get(y - shift)
        if a is None:
            continue
        total += w * a[key]
        wsum += w
    return total, wsum


def indicators(series, t, opex_t):
    """Windowed indicators I1-I5 for year t. series: {year: aux dict}."""
    years = [t - k for k in range(len(WINDOW_WEIGHTS))]
    years = [y for y in years if y in series]
    po, w = _wsum(series, "PO", years)
    os_, _ = _wsum(series, "OS", years)
    princ, _ = _wsum(series, "glavnica_adj", years)
    a = series[t]
    out = {"prozor_godina": len(years)}
    out["I1"] = os_ / po if po > 0 else None
    out["I2"] = (os_ - princ) / po if po > 0 else None
    if a["ND"] <= 0:
        out["I3"] = 0.0
    else:
        os_avg = os_ / w if w else 0.0
        out["I3"] = a["ND"] / os_avg if os_avg > 0 else math.inf
    sd, zo = 0.0, 0.0
    for wt, y in zip(WINDOW_WEIGHTS, [t - k for k in range(len(WINDOW_WEIGHTS))]):
        if y in series and (y - 1) in series:
            sd += wt * series[y]["SD"]
            zo += wt * series[y - 1]["ZO"]
    out["I4"] = sd / zo if zo > 0 else None
    out["I5"] = a["DO"] / opex_t if opex_t > 0 else None
    return out


def scores(ind):
    return {f"S{k[1]}": (None if interp(ind[k], ANCHORS[k]) is None else round(interp(ind[k], ANCHORS[k]), 1))
            for k in ANCHORS}


def total(sc, weights):
    num, den = 0.0, 0.0
    for k, w in weights.items():
        s = sc.get(f"S{k[1]}")
        if s is None or w == 0:
            continue
        num += w * s
        den += w
    return round(num / den, 1) if den else None


def capped_total(sc, weights, i5):
    """Weighted total with rule 2 applied. Returns (points, points before the cap, capped?)."""
    tot = total(sc, weights)
    if tot is not None and i5 is not None and i5 >= DO_CAP_SHARE and tot > DO_CAP_POINTS:
        return DO_CAP_POINTS, tot, True
    return tot, tot, False


def flags(series, t, r):
    """Red flags (PLAN §3.3), outside the score."""
    a = series[t]
    g = lambda k: r.get(k) or 0.0
    prev = series.get(t - 1)
    out = {
        "Z1": a["PO"] > 0 and (g("b_9222") - g("b_9221")) > 0.05 * a["PO"],
        "Z2": prev is not None and prev["ZO"] > 0 and (a["SD"] + a["DO"]) / prev["ZO"] > 0.20,
        "Z3": a["OS"] < 0 and prev is not None and prev["OS"] < 0,
        "Z4": g("p_3") > 0 and g("b_11") < g("p_3") / 12,
    }
    return [k for k, v in out.items() if v]


def criterion_10(r):
    """Z5 (Z5_SHARE above) for one unit-year dict: the deficit without EU sources as a share of
    revenue without EU sources (0 when there is a surplus), and whether it is within 10 %.
    Both are None when revenue without EU sources is not positive."""
    g = lambda k: r.get(k) or 0.0
    base = g("p_6") + g("p_7") - sum(g(f"p_{c}") for c in EU_REVENUE)
    if base <= 0:
        return {"z5_manjak_udio": None, "z5_zadovoljava": None}
    share = max(0.0, (g("p_3") + g("p_4")) - (g("p_6") + g("p_7"))) / base
    return {"z5_manjak_udio": share, "z5_zadovoljava": share <= Z5_SHARE}


def context(r, a, pop):
    """Context measures (PLAN §3.4), shown but not scored."""
    g = lambda k: r.get(k) or 0.0
    kp63 = sum(g(f"p_{c}") for c in config.CAPITAL_GRANTS if c != "6632")
    div = lambda x, y: (x / y) if y else None
    return {
        **criterion_10(r),
        "udio_tekucih_pomoci": div(g("p_63") - kp63, a["PO"]),
        "udio_fiskalnog_izravnanja": div(equalization_paid(r), a["PO"]),
        "udio_pomoci": div(g("p_63"), g("p_6")),
        "udio_eu": div(g("p_638"), g("p_6")),
        "investicijska_stopa": div(g("p_4"), g("p_3") + g("p_4")),
        "tekuci_prihodi_pc": div(a["PO"], pop),
        "vlastiti_prihodi_pc": div(g("p_61") + g("p_64") + g("p_65"), pop),
        "uprava_pc": div(g("p_01") - g("p_017") - g("p_018"), pop),
        "djelatnici_na_1000": div(g("p_Z006") * 1000, pop),
        "neto_dug_pc": div(a["ND"], pop),
        "akumulirani_rezultat": g("b_9221") - g("b_9222"),
    }


def quality(r):
    """Data-quality notes for one unit-year."""
    g = lambda k: r.get(k) or 0.0
    notes = []
    # RAS-funkcijski leaves out 367 (transfers to the unit's own budget users)
    spend = g("p_3") + g("p_4") - g("p_367")
    if spend > 0 and abs(g("p_R1") - spend) > 0.01 * spend:
        notes.append("funkcije_ne_odgovaraju_rashodima")
    if g("p_6") <= 0:
        notes.append("nema_prihoda")
    return notes


def evaluate_unit(rows, pop):
    """rows: {year: unit-year dict}. Returns {year: result dict} for every year."""
    series = {y: aux(r, rows.get(y - 1)) for y, r in rows.items()}
    out = {}
    for t in sorted(rows):
        r = rows[t]
        ind = indicators(series, t, r.get("p_3") or 0.0)
        sc = scores(ind)
        tot, uncapped, capped = capped_total(sc, SCENARIOS["osnovni"], ind["I5"])
        gr, word = grade(tot)
        scen = {name: grade(capped_total(sc, w, ind["I5"])[0])[0] for name, w in SCENARIOS.items()}
        grades = [v for v in scen.values() if v is not None]
        a = series[t]
        out[t] = {
            **{k: v for k, v in a.items()},
            **ind, **sc,
            "bodovi": tot, "bodovi_bez_ogranicenja": uncapped, "ogranicenje_do": capped,
            "ocjena": gr, "ocjena_rijec": word,
            "ocjene_scenarija": scen,
            "stabilnost": None if not grades else ("stabilna" if min(grades) == max(grades) else "osjetljiva"),
            "raspon_ocjena": None if not grades else [min(grades), max(grades)],
            "zastavice": flags(series, t, r),
            "oznake": (["eu_projekt"] if (r.get("p_638") or 0) > 0.10 * (r.get("p_6") or 0) else [])
                      + (["refinanciranje"] if a["refinanciranje"] else []),
            "kvaliteta": quality(r) + (["kredit_iskazan_kao_dospio"] if a["kredit_iskazan_dospio"] else [])
                         + equalization_notes(r, t),
            **context(r, a, pop),
        }
    return out
