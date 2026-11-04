"""Fiscal equalization (fiskalno izravnanje) by the statutory formula, checked against MF.

Law: Zakon o financiranju jedinica lokalne i područne (regionalne) samouprave,
NN 127/17, 138/20, 151/22, 114/23 (no later amendment as of 2026-11-04). Article 8 as
replaced by NN 114/23 čl. 3 (in force 1.1.2024), article 9 as amended by NN 138/20.

- čl. 8. st. 1.: a unit whose capacity is below the reference value is entitled to
  equalization. Hence the full amount is max(0, ...).
- čl. 8. st. 2.: capacity of a municipality or town = five-year average of the income tax
  that would be collected in its area at the highest rate it may set, including the maximum
  lump-sum tax on tourist rentals, per inhabitant.
- čl. 8. st. 3.: reference value for municipalities = the same per capita over all
  municipalities, increased by 50 %. St. 4.: for towns, over all towns, without the 50 %.
  St. 5.-6.: counties use the county share of income tax (čl. 5. st. 2. t. 2., 20 %).
  St. 7.: "highest rate" = upper limit of the lower income tax rate the unit may set.
  St. 8.: Grad Zagreb is left out of the reference values for towns and counties.
- čl. 9. st. 1.-3.: full amount = (reference value - capacity) x population.
- čl. 9. st. 4.-5.: the shares are full amount / sum of all full amounts.
- čl. 9. st. 7. (and čl. 16. st. 2.): the minister's decision sets each unit's amount as
  share x the amount in the state budget for that year. The payout is therefore NOT the full
  amount: in 2026 the budget gave 280,445,617 EUR against 444,596,598 EUR of full amounts.

MF publishes the whole calculation as one workbook per year ("Tablica udjela po JLP(R)S za
fiskalno izravnanje u <godina>", config.MF_FI_XLSX): the income tax per year as recomputed
at the highest rates, the five-year average P1, the capacity per capita P2, the reference
value P3, the full amount P4 ("optimalni iznos") and the share Z, plus the decision's shares
on the sheet "Udjeli". parse_mf() reads it; provjera() recomputes P2, P3, P4 and Z from the
yearly columns with the formula above and compares them unit by unit.

za_spajanje() estimates the full amount of a merged unit (merger simulator, PLAN §4 t. 4).
Everything here is the full amount under the formula, at the published reference values.
What a unit is paid is its share of a budget line, so a merger also shifts the shares of all
other units slightly; that is left out and stated in the output flags.

CLI:
  python -m pipeline.izravnanje --provjera [--xlsx PATH]
  python -m pipeline.izravnanje --spoji grad-pag opcina-povljana
"""
import argparse
import difflib
import re
import sys

import pandas as pd

from . import config
from .units import bare_name, match_key, slugify

XLSX = config.RAW / "izravnanje" / f"fi_{config.MF_FI_YEAR}.xlsx"

TITULA = {"OPĆINA": "opcina", "GRAD": "grad", "ZG": "zagreb", "ŽUPANIJA": "zupanija"}
LAST_PRIREZ_YEAR = 2023      # prirez (surtax) was abolished on 1.1.2024 (NN 114/23)
PRAG_OPCINA_GRAD = 0.05      # the check passes a unit when |ours - MF| <= 5 % of MF (or 1 EUR)
PRAG_JEDINICA = 0.90         # ... and the formula passes when at least 90 % of units do

# Payout of the last decision with an amount (Odluka ... s iznosom sredstava za 2026., point II,
# column 4 "3 x 280.445.617 EUR") and the sum of full amounts in the 2026 table (Ʃ P4).
# Used only to show the order of magnitude of payout vs full amount.
ISPLATA_2026 = 280_445_617.0
PUNI_UKUPNO_2026 = 444_596_597.99


# ---------------------------------------------------------------- parsing the MF workbook

def _s(v):
    return str(v).strip() if v is not None else ""


def _num(v):
    return float(v) if isinstance(v, (int, float)) else None


def _code_cols(code_row):
    """Column of P1 (towns) / X1 (counties); P2, P3, P4, A, Z follow it in this order."""
    for j, v in enumerate(code_row):
        if re.match(r"^(P1|X1)\s*\(", _s(v)):
            names = ["P1", "P2", "P3", "P4", "A", "Z"]
            cols = {n: j + k for k, n in enumerate(names)}
            if "IF<0" not in _s(code_row[cols["P4"]]).replace(" ", ""):
                raise ValueError(f"unexpected code row near P4: {code_row[cols['P4']]!r}")
            return cols
    raise ValueError("no P1/X1 column in the code row")


def _header_cols(header):
    cols = {}
    for j, v in enumerate(header):
        t = re.sub(r"\s+", " ", _s(v))
        if t == "ZAP ID":
            cols["zap_id"] = j
        elif t == "ID Županije":
            cols["zup_id"] = j
        elif t == "Titula":
            cols["titula"] = j
        elif t == "Naziv subjekta":
            cols["naziv"] = j
        elif t.startswith("Ukupan broj stanovnika"):
            cols["stanovnici"] = j
        elif t.startswith("MOGUĆA STOPA PRIREZA"):
            cols["prirez_max"] = j
        elif t.startswith("MAX NIŽA STOPA POREZA"):
            cols["stopa_max"] = j
    return cols


def _year_cols(header):
    """{year: column} of the per-year amounts that enter the five-year average."""
    out = {}
    for j, v in enumerate(header):
        t = re.sub(r"\s+", " ", _s(v))
        m = re.search(r"za izračun (kapaciteta|pomoći) za razdoblje 01\.01\.(\d{4})", t)
        if m:
            out[int(m.group(2))] = j
    return out


def parse_mf(path=XLSX):
    """Read the MF equalization workbook into one row per unit.

    Columns: zap_id, zup_id, vrsta (opcina/grad/zagreb/zupanija), naziv_mf, stanovnici,
    prirez_max (%), stopa_max (share), kap_<year> for the five years of the average,
    P1 (five-year average, EUR), P2 (capacity per capita), P3 (reference value), P4 (full
    amount), Z (share in the table), udio_odluka (share on the sheet "Udjeli") and red
    (Excel row). df.attrs carries godina, godine, referentne_mf (published reference values
    per type) and puni_ukupno_mf (Ʃ P4 as printed)."""
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = next(w for w in wb.worksheets if w.title.startswith("Izračun"))
    godina = int(re.search(r"(\d{4})", ws.title).group(1))
    rows = list(ws.iter_rows(values_only=True))

    headers = [i for i, r in enumerate(rows) if any(_s(v) == "Titula" for v in r)]
    if len(headers) != 2:
        raise ValueError(f"expected 2 header rows (towns, counties), found {len(headers)}")
    first_years = _year_cols(rows[headers[0]])
    godine = sorted(first_years)[-5:]
    if godine != list(range(godina - 6, godina - 1)):
        raise ValueError(f"five-year window {godine} does not end two years before {godina}")

    recs = []
    for h_i, h in enumerate(headers):
        hc = _header_cols(rows[h])
        cc = _code_cols(rows[h + 1])
        yc = {y: c for y, c in _year_cols(rows[h]).items() if y in godine}
        yc = {y: yc.get(y, first_years[y]) for y in godine}   # county header omits some labels
        end = headers[h_i + 1] if h_i + 1 < len(headers) else len(rows)
        for i in range(h + 2, end):
            r = rows[i]
            vrsta = TITULA.get(_s(r[hc["titula"]]).upper())
            if not vrsta:
                continue
            rec = {
                "zap_id": int(r[hc["zap_id"]]),
                "zup_id": int(r[hc["zup_id"]]),
                "vrsta": vrsta,
                "naziv_mf": re.sub(r"\s+", " ", _s(r[hc["naziv"]])),
                "stanovnici": int(r[hc["stanovnici"]]),
                "prirez_max": _num(r[hc["prirez_max"]]) if "prirez_max" in hc else None,
                "stopa_max": _num(r[hc["stopa_max"]]) if "stopa_max" in hc else None,
                **{f"kap_{y}": _num(r[c]) or 0.0 for y, c in yc.items()},
                **{k: _num(r[c]) for k, c in cc.items() if k != "A"},
                "red": i + 1,
            }
            recs.append(rec)
    df = pd.DataFrame(recs)

    # published reference values: rows "Općine", "Gradovi", "Županije( bez ZG)"
    ref = {}
    for r in rows:
        for j, v in enumerate(r):
            t = _s(v)
            kind = ("opcina" if t == "Općine" else "grad" if t == "Gradovi"
                    else "zupanija" if t.startswith("Županije") else None)
            if kind and j + 5 < len(r) and all(_num(r[j + k]) is not None for k in range(1, 6)):
                ref[kind] = {"stanovnici": int(r[j + 1]), "P1": float(r[j + 2]),
                             "prosjek": float(r[j + 3]), "faktor": float(r[j + 4]),
                             "referentna": float(r[j + 5])}
    p4 = _code_cols(rows[headers[0] + 1])["P4"]          # Ʃ P4 is printed above the header
    puni_ukupno = next((_num(r[p4]) for r in rows[:headers[0]] if _num(r[p4]) is not None), None)

    ud = next((w for w in wb.worksheets if w.title.strip() == "Udjeli"), None)
    if ud is not None:
        shares = {}
        for r in ud.iter_rows(values_only=True):
            if len(r) > 4 and isinstance(r[1], (int, float)) and _s(r[2]).upper() in TITULA \
                    and isinstance(r[4], (int, float)):
                shares[int(r[1])] = float(r[4])
        df["udio_odluka"] = df["zap_id"].map(shares)
    wb.close()
    df.attrs.update(godina=godina, godine=godine, referentne_mf=ref, puni_ukupno_mf=puni_ukupno)
    return df


# ---------------------------------------------------------------- the formula (čl. 8.-9.)

def kapacitet(df):
    """čl. 8. st. 2. i 5.: five-year average (EUR) and per capita, rounded to cents as MF does."""
    p1 = df[[f"kap_{y}" for y in df.attrs["godine"]]].mean(axis=1)
    return p1, (p1 / df["stanovnici"]).round(2)


def referentne_vrijednosti(df, p1=None):
    """čl. 8. st. 3., 4., 6. i 8.: reference value per type, Grad Zagreb left out.

    Municipalities: average over all municipalities x 1.5; towns and counties: plain average.
    MF rounds the average to cents before applying the 50 % and the result again."""
    p1 = df["P1"] if p1 is None else p1
    out = {}
    for vrsta, faktor in (("opcina", 1.5), ("grad", 1.0), ("zupanija", 1.0)):
        m = df["vrsta"] == vrsta
        prosjek = round(p1[m].sum() / df.loc[m, "stanovnici"].sum(), 2)
        out[vrsta] = round(prosjek * faktor, 2)
    out["zagreb"] = out["grad"]   # Zagreb is compared with towns; its capacity is far above
    return out


def puni_iznos(kapacitet_pc, referentna_pc, stanovnici):
    """čl. 9. st. 1.-3. with čl. 8. st. 1.: (reference - capacity) x population, never below 0."""
    return max(0.0, (referentna_pc - kapacitet_pc) * stanovnici)


def udjeli(puni):
    """čl. 9. st. 4.-5.: each unit's full amount over the sum of all full amounts."""
    puni = pd.Series(puni, dtype=float)
    return puni / puni.sum()


def isplata(udio, iznos_u_proracunu):
    """čl. 9. st. 7.: the amount paid = share x the budget line for that year."""
    return udio * iznos_u_proracunu


# ---------------------------------------------------------------- merger estimate

def stope_spojene(clanice, je_grad):
    """Highest rates (čl. 8. st. 7.) that the merged unit would be assessed at.

    The MF table assesses all five years at the unit's current status (columns "MOGUĆA STOPA
    PRIREZA" and "MAX NIŽA STOPA POREZA"). What the 2027 table shows:
    - income tax rate cap (years from 2024): municipalities 20 %, towns 21 %, county seats and
      towns over 35,000 inhabitants 22 % (Kaštela 37,794 has 22 %, Vinkovci 30,842 has 21 %),
      Zagreb 23 %;
    - surtax cap (years up to 2023): municipalities 10 %, towns 12 %, towns over 30,000 15 %
      (Vinkovci 15 %; Koprivnica keeps 15 % from the 2011 census), Zagreb 18 %.
    The merged unit keeps the highest class any member town has and moves up when the summed
    population passes the threshold. The class rules are read from the table, not the tax law."""
    if not je_grad:
        return {"prirez_max": 10.0, "stopa_max": 0.20}
    s = sum(c["stanovnici"] for c in clanice)
    gradovi = [c for c in clanice if c["vrsta"] == "grad"]
    prirez = max([c.get("prirez_max") or 12.0 for c in gradovi] + [12.0])
    stopa = max([c.get("stopa_max") or 0.21 for c in gradovi] + [0.21])
    if s > 30_000:
        prirez = max(prirez, 15.0)
    if s > 35_000:
        stopa = max(stopa, 0.22)
    return {"prirez_max": prirez, "stopa_max": stopa}


def _faktor(y, stope):
    return 1 + stope["prirez_max"] / 100 if y <= LAST_PRIREZ_YEAR else stope["stopa_max"]


def za_spajanje(clanice, je_grad, *, referentne, preracunaj_stope=True):
    """Full equalization amount of the merged unit vs the sum of its members (čl. 8.-9.).

    clanice: dicts with kapacitet_pc (EUR per inhabitant), stanovnici, vrsta ("opcina"/"grad")
      and optionally kap (dict year -> amount at the member's own highest rates, the MF
      per-year columns) with prirez_max and stopa_max.
    je_grad: the merged unit is a town (merge rule 3: at least one member is a town).
    referentne: reference values per type, {"opcina": ..., "grad": ...}.
    preracunaj_stope: when the members carry kap, reassess every year at the merged unit's
      highest rates (čl. 8. st. 2. i 7.), as MF would for a unit of that status.

    Capacity of the merged unit = Σ (capacity x population) / Σ population, i.e. the summed
    five-year amounts over the summed population. The reference values stay as published.

    Returns vrsta, stanovnici, kapacitet_pc, kapacitet_pc_bez_preracuna, referentna_pc,
    stope (rates the merged unit is assessed at, None without kap), puni_po_clanici,
    puni_clanice, puni_spojena, puni_spojena_bez_preracuna, promjena, promjena_udio and oznake
    (codes for the assumptions taken). With the reference values fixed, the formula never gives
    the merged unit more than the sum of its members. All amounts are full amounts; a payout is
    a share of the budget line (čl. 9. st. 7.), so these are not what a unit receives."""
    clanice = list(clanice)
    if len(clanice) < 2:
        raise ValueError("a merger needs at least two members")
    if any(c["vrsta"] not in ("opcina", "grad") for c in clanice):
        raise ValueError("only municipalities and towns (no counties, no Grad Zagreb)")
    vrsta = "grad" if je_grad else "opcina"
    s = sum(c["stanovnici"] for c in clanice)
    oznake = [f"vrsta_{vrsta}"]

    puni_po = [puni_iznos(c["kapacitet_pc"], referentne[c["vrsta"]], c["stanovnici"])
               for c in clanice]

    # Σ (capacity x population) of the members; kept unrounded, so that two members below
    # their reference value give exactly the sum of their full amounts (the formula is linear)
    zbroj = sum(c["kapacitet_pc"] * c["stanovnici"] for c in clanice)
    kap_bez = zbroj / s

    have_years = all(c.get("kap") for c in clanice)
    stope = None
    changes_rate = any(c["vrsta"] != vrsta for c in clanice)
    if preracunaj_stope and have_years:
        if any(c.get("prirez_max") is None or c.get("stopa_max") is None for c in clanice):
            raise ValueError("kap given without prirez_max and stopa_max")
        stope = stope_spojene(clanice, je_grad)
        changes_rate = any((c["prirez_max"], c["stopa_max"]) != (stope["prirez_max"], stope["stopa_max"])
                           for c in clanice)
    kap = kap_bez
    if stope and changes_rate:
        # each year at the merged unit's highest rates: the MF yearly amounts are linear in them
        delta = 0.0
        for c in clanice:
            own = {"prirez_max": c["prirez_max"], "stopa_max": c["stopa_max"]}
            godine = sorted(c["kap"])
            delta += sum(c["kap"][y] * (_faktor(y, stope) / _faktor(y, own) - 1) for y in godine) / len(godine)
        kap = (zbroj + delta) / s
        oznake.append("kapacitet_preracunat_na_stope_spojene")
    elif changes_rate:
        oznake.append("kapacitet_po_stopama_clanica")
    else:
        oznake.append("kapacitet_zbroj_clanica")
    oznake += ["referentne_nepromijenjene", "puni_iznos_ne_isplata"]

    ref = referentne[vrsta]
    puni_sp = puni_iznos(kap, ref, s)
    puni_cl = sum(puni_po)
    if all(p == 0 for p in puni_po) and puni_sp == 0:
        oznake.append("bez_prava_na_izravnanje")
    elif any(p == 0 for p in puni_po):
        oznake.append("clanica_iznad_referentne")
    return {
        "vrsta": vrsta,
        "stanovnici": s,
        "kapacitet_pc": round(kap, 2),
        "kapacitet_pc_bez_preracuna": round(kap_bez, 2),
        "referentna_pc": ref,
        "stope": stope,
        "puni_po_clanici": [round(p, 2) for p in puni_po],
        "puni_clanice": round(puni_cl, 2),
        "puni_spojena": round(puni_sp, 2),
        "puni_spojena_bez_preracuna": round(puni_iznos(kap_bez, ref, s), 2),
        "promjena": round(puni_sp - puni_cl, 2),
        "promjena_udio": round((puni_sp - puni_cl) / puni_cl, 4) if puni_cl else None,
        "oznake": oznake,
    }


# ---------------------------------------------------------------- joining with the register

def _key(zup_id, vrsta, naziv, loose=False):
    if vrsta == "zupanija":
        return (int(zup_id), "zupanija", "")
    name = match_key(naziv) if loose else bare_name(naziv)
    return (int(zup_id), "grad" if vrsta == "zagreb" else vrsta, slugify(name.rstrip(". ")))


def spoji_sa_sifrarnikom(df, units):
    """Attach OIB and slug from data/build/units.csv.

    The MF table has no OIB, so the key is county + type + name without diacritics (as
    pipeline/openness.py matches the portal): first the bare name, then units.match_key
    (bilingual Istrian names, "VINODOLSKA OPĆINA", "NOVIGRAD." for Novigrad Zadarski).
    The 2027 table has every "BO" replaced by "BL" (SAMOBLR, BLROVO, ZABLK; no name in it
    contains "BO"), so a name that still does not match is tried once more with BL -> BO.
    Column spoj says which step matched."""
    exact, loose = {}, {}
    for u in units.itertuples():
        exact[_key(u.zup_id, u.vrsta, u.naziv_mf)] = (u.oib, u.slug)
        loose.setdefault(_key(u.zup_id, u.vrsta, u.naziv_mf, loose=True), []).append((u.oib, u.slug))
    found = []
    for r in df.itertuples():
        hit = None
        for how, name in (("naziv", r.naziv_mf), ("naziv_BL_u_BO", r.naziv_mf.replace("BL", "BO"))):
            if how != "naziv" and name == r.naziv_mf:
                continue
            if _key(r.zup_id, r.vrsta, name) in exact:
                hit = (*exact[_key(r.zup_id, r.vrsta, name)], how)
                break
            cand = loose.get(_key(r.zup_id, r.vrsta, name, loose=True), [])
            if len(cand) == 1:
                hit = (*cand[0], how + "_labavo")
                break
        found.append(hit or (None, None, None))
    # last step: one remaining register name of the same county and type that is close enough
    # (MF "SVETA NEDJELJA" for Grad Sveta Nedelja)
    taken = {f[0] for f in found if f[0]}
    for i, r in enumerate(df.itertuples()):
        if found[i][0]:
            continue
        pool = [u for u in units.itertuples() if u.oib not in taken and int(u.zup_id) == r.zup_id
                and u.vrsta == ("grad" if r.vrsta == "zagreb" else r.vrsta)]
        score = sorted(((difflib.SequenceMatcher(None, slugify(bare_name(u.naziv_mf)),
                                                 slugify(r.naziv_mf)).ratio(), u) for u in pool),
                       key=lambda t: -t[0])
        if score and score[0][0] >= 0.9 and (len(score) == 1 or score[1][0] < 0.9):
            found[i] = (score[0][1].oib, score[0][1].slug, "slicno")
            taken.add(score[0][1].oib)
    out = df.copy()
    out["oib"], out["slug"], out["spoj"] = zip(*found)
    dup = out["oib"].dropna().duplicated()
    if dup.any():
        raise ValueError(f"two MF rows matched one unit: {out.loc[dup[dup].index, 'naziv_mf'].tolist()}")
    return out


def ucitaj(path=XLSX, units_csv=config.BUILD / "units.csv"):
    df = parse_mf(path)
    units = pd.read_csv(units_csv, dtype={"oib": str, "rkp": str, "sifra": str})
    return spoji_sa_sifrarnikom(df, units)


def clanica(row, godine):
    """One row of the MF table as a member for za_spajanje (MF's own capacity and years)."""
    return {"kapacitet_pc": row["P2"], "stanovnici": int(row["stanovnici"]), "vrsta": row["vrsta"],
            "kap": {y: row[f"kap_{y}"] for y in godine},
            "prirez_max": row["prirez_max"], "stopa_max": row["stopa_max"]}


def procjena(df, slugs):
    """za_spajanje for units given by slug, with MF's capacities and published reference values."""
    rows = df.set_index("slug").loc[list(slugs)]
    ref = {k: v["referentna"] for k, v in df.attrs["referentne_mf"].items()}
    members = [clanica(r, df.attrs["godine"]) for _, r in rows.iterrows()]
    out = za_spajanje(members, any(m["vrsta"] == "grad" for m in members), referentne=ref)
    out["clanice"] = [{"slug": s, "naziv_mf": r["naziv_mf"], "kapacitet_pc": r["P2"],
                       "stanovnici": int(r["stanovnici"]), "puni_mf": r["P4"]}
                      for s, r in rows.iterrows()]
    return out


# ---------------------------------------------------------------- check against MF

def _within(ours, mf, rel=PRAG_OPCINA_GRAD, floor=1.0):
    """|ours - mf| within rel of MF, or within floor (1 EUR for amounts; 0 for shares, which
    are below 1, so a floor in euros would let any share pass)."""
    return abs(ours - mf) <= max(rel * abs(mf), floor)


def provjera(path=XLSX, units_csv=config.BUILD / "units.csv"):
    """Recompute capacity, reference values, full amounts and shares from MF's yearly columns
    and compare them with what MF publishes. Returns a dict with the counts and the units
    that fail, each with a reason."""
    df = parse_mf(path)
    godina = df.attrs["godina"]
    p1, kap = kapacitet(df)
    ref = referentne_vrijednosti(df, p1)
    ours = pd.Series([puni_iznos(k, ref[v], s) for k, v, s in zip(kap, df["vrsta"], df["stanovnici"])],
                     index=df.index)
    ud = udjeli(ours)

    res = {"godina": godina, "godine": df.attrs["godine"], "jedinica": len(df),
           "po_vrsti": df["vrsta"].value_counts().to_dict()}
    res["referentne"] = {k: {"nase": ref[k], "mf": v["referentna"],
                             "jednako": abs(ref[k] - v["referentna"]) < 0.005}
                         for k, v in df.attrs["referentne_mf"].items()}
    res["kapacitet_p1_jednak"] = int(((p1 - df["P1"]).abs() <= 0.01).sum())
    res["kapacitet_pc_jednak"] = int(((kap - df["P2"]).abs() < 0.005).sum())

    ok_puni = [_within(a, b) for a, b in zip(ours, df["P4"])]
    ok_udio = [_within(a, b, PRAG_OPCINA_GRAD, floor=0.0) if b else a == 0
               for a, b in zip(ud, df["udio_odluka"].fillna(df["Z"]))]
    exact = int(((ours - df["P4"]).abs() <= 1.0).sum())
    res["puni"] = {"prolazi": int(sum(ok_puni)), "do_1_eura": exact,
                   "udio_prolazi": round(sum(ok_puni) / len(df), 4),
                   "s_pravom_mf": int((df["P4"] > 0).sum()), "s_pravom_nase": int((ours > 0).sum()),
                   "zbroj_nas": round(float(ours.sum()), 2), "zbroj_mf": df.attrs["puni_ukupno_mf"]}
    res["udjeli"] = {"prolazi": int(sum(ok_udio)),
                     "najvece_odstupanje": float((ud - df["udio_odluka"].fillna(df["Z"])).abs().max()),
                     "odluka_jednaka_tablici": int(((df["udio_odluka"] - df["Z"]).abs() < 1e-12).sum())}

    fails = []
    for i in df.index[~pd.Series(ok_puni, index=df.index) | ~pd.Series(ok_udio, index=df.index)]:
        r = df.loc[i]
        if (r["P4"] or 0) == 0 and ours[i] > 0:
            why = "MF 0, formula > 0 (prag referentne vrijednosti)"
        elif ours[i] == 0 and (r["P4"] or 0) > 0:
            why = "formula 0, MF > 0"
        elif abs(p1[i] - r["P1"]) > 0.01:
            why = "kapacitet se razlikuje (godišnji stupci)"
        else:
            why = "iznos se razlikuje"
        fails.append({"naziv_mf": r["naziv_mf"], "vrsta": r["vrsta"], "zup_id": int(r["zup_id"]),
                      "nase": round(float(ours[i]), 2), "mf": r["P4"], "razlog": why})
    res["ne_prolaze"] = fails

    if units_csv is not None and units_csv.exists():
        units = pd.read_csv(units_csv, dtype={"oib": str, "rkp": str, "sifra": str})
        m = spoji_sa_sifrarnikom(df, units)
        res["spareno"] = int(m["oib"].notna().sum())
        res["nespareno"] = m.loc[m["oib"].isna(), "naziv_mf"].tolist()
        res["sifrarnik_bez_mf"] = sorted(set(units["oib"]) - set(m["oib"].dropna()))
    res["prolazi"] = res["puni"]["udio_prolazi"] >= PRAG_JEDINICA and \
        res["udjeli"]["prolazi"] / len(df) >= PRAG_JEDINICA
    return res


def _print_provjera(res):
    eur = lambda x: f"{x:,.2f}".replace(",", " ")
    n = res["jedinica"]
    print(f"Fiskalno izravnanje {res['godina']}: MF tablica, kapacitet iz godina {res['godine'][0]}-{res['godine'][-1]}")
    print(f"  jedinica u tablici: {n} {res['po_vrsti']}")
    if "spareno" in res:
        print(f"  sparenih sa šifrarnikom (županija + vrsta + naziv): {res['spareno']}/{n}"
              f"{'; nesparene: ' + ', '.join(res['nespareno']) if res['nespareno'] else ''}")
    print(f"  petogodišnji prosjek P1 jednak MF-u (do 1 centa): {res['kapacitet_p1_jednak']}/{n}")
    print(f"  kapacitet po stanovniku P2 jednak MF-u: {res['kapacitet_pc_jednak']}/{n}")
    for k, v in res["referentne"].items():
        print(f"  referentna vrijednost {k}: naša {v['nase']:.2f}, MF {v['mf']:.2f}"
              f" -> {'jednako' if v['jednako'] else 'RAZLIKA'}")
    p = res["puni"]
    print(f"  puni iznos: {p['prolazi']}/{n} unutar 5 % ({100 * p['udio_prolazi']:.1f} %),"
          f" {p['do_1_eura']}/{n} do 1 EUR; s pravom: naše {p['s_pravom_nase']}, MF {p['s_pravom_mf']}")
    print(f"  zbroj punih iznosa: naš {eur(p['zbroj_nas'])} EUR, MF {eur(p['zbroj_mf'])} EUR")
    u = res["udjeli"]
    print(f"  udjeli (odluka, list Udjeli): {u['prolazi']}/{n} unutar 5 %, najveće odstupanje"
          f" {u['najvece_odstupanje']:.2e}; odluka = tablica za {u['odluka_jednaka_tablici']}/{n}")
    if res["ne_prolaze"]:
        print("  ne prolaze:")
        for f in res["ne_prolaze"]:
            print(f"    {f['naziv_mf']} ({f['vrsta']}, žup. {f['zup_id']}): naše {f['nase']}, MF {f['mf']} - {f['razlog']}")
    print(f"  omjer isplate 2026. (proračun / zbroj punih iznosa): {ISPLATA_2026 / PUNI_UKUPNO_2026:.4f}")
    print(f"PROVJERA {'PROŠLA' if res['prolazi'] else 'NIJE PROŠLA'} (prag: {PRAG_JEDINICA:.0%} jedinica unutar"
          f" {PRAG_OPCINA_GRAD:.0%})")


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--provjera", action="store_true", help="formula vs MF table")
    ap.add_argument("--xlsx", default=str(XLSX), help="MF workbook (default: data/raw/izravnanje)")
    ap.add_argument("--spoji", nargs="+", metavar="SLUG", help="estimate a merger of these units")
    a = ap.parse_args(argv)
    from pathlib import Path
    path = Path(a.xlsx)
    if a.provjera:
        res = provjera(path)
        _print_provjera(res)
        if not res["prolazi"]:
            return 1
    if a.spoji:
        out = procjena(ucitaj(path), a.spoji)
        for c in out.pop("clanice"):
            print(f"  {c['naziv_mf']}: {c['stanovnici']} st., kapacitet {c['kapacitet_pc']:.2f} EUR/st.,"
                  f" puni iznos MF {c['puni_mf']:,.2f}")
        for k, v in out.items():
            print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
