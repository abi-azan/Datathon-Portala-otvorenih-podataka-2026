"""Porezna uprava (Tax Administration): residents' income by municipality and local tax rates.

Two datasets of the Tax Administration on data.gov.hr, both under the Otvorena dozvola.
Background, URLs, sheet layouts and pitfalls: docs/research/09 §2.1 and §2.3.

A. "Neto dohodak stanovništva po općinama/gradovima prebivališta" (package PKG_DOHODAK).
   One workbook, one sheet per year ("2025 EUR", "2024 EUR", "2023 EUR", "2022 HRK"). Every
   town or municipality has one row per kind of income plus "UKUPNO OPĆINA"; every county
   has the same rows with a blank name and "UKUPNO ŽUPANIJA". Grad Zagreb is county 21 with
   a single unit and no county total. Columns: number of persons, gross, contributions,
   income, tax and net. Key: county code ("13 - ZADARSKA ŽUPANIJA") + name, no code, so the
   names are matched to the register within the county.
   - "Broj posloprimaca" counts distinct OIBs. On the UKUPNO row it is the number of distinct
     persons, not the sum of the kinds (Bedenica 2025: 1,013 against 1,280).
   - Small units have some kinds suppressed (empty cells): those amounts are only in UKUPNO.
     They stay in the output as NaN.
   - 2022 and 2023 have "DOHODAK OD OSIGURANJA" and the tax column "Porez + prirez" (the
     surtax was abolished on 1.1.2024); porez_s_prirezom says which. 2022 is in kuna and is
     converted at the fixed rate HRK_EUR.
   - The headers are read, not assumed: columns by label, year and currency from the sheet.

B. "Usporedba poreznih stopa prema odlukama JLS" (package PKG_STOPE), as decided by the units.
   - income tax rates 2026 ("Tablica JLS 2026", with "Šifra grada/općine" = the DGU code
     without leading zeros, so it joins without names);
   - the comparison 2025/2026 (no code: joined to the 2026 table by row number and name);
   - consumption tax 2025 and 2026, property tax per m² 2025 and 2026 (some written as a
     range "3,60 do 4,50"; kept as _min/_max; who collects it: JLS or PU).
   niza_max, the highest lower rate the unit may set (čl. 8. st. 7. Zakona o financiranju
   JLP(R)S), is read from the MF equalization table (pipeline.izravnanje, column stopa_max),
   not assumed from the unit's status. That table gives the cap for the unit's current
   status, so the same cap is used for 2025 and 2026.

The portal's download URLs send an ETag but answer 200 to If-None-Match and
If-Modified-Since (checked 4.11.2026), so every online run downloads the five files again
(about 1.8 MB together).

Nothing here enters the score. Outputs:
  data/build/porezna_dohodak.parquet  oib, sifra, godina, vrsta_dohotka, osobe, bruto,
      doprinosi, dohodak, porez, neto, porez_s_prirezom, list, red (576 units x 4 years)
  data/build/porezna_stope.parquet    oib, sifra, godina, niza, visa, niza_max,
      ispod_maksimuma, potrosnja_min, potrosnja_max, nekretnine_min, nekretnine_max,
      nekretnine_naplata (556 units x 2026 and 2025)

CLI:
  python -m pipeline.porezna [--offline]
"""
import argparse
import difflib
import re
import sys

import numpy as np
import pandas as pd

from . import config, sources
from .units import bare_name, match_key, slugify

PKG_DOHODAK = "https-porezna-uprava-gov-hr-hr-porez-na-dohodak-4763-4763"
PKG_STOPE = "https-porezna-uprava-gov-hr-hr-odluke-jls-4009"
RAW_DIR = config.RAW / "porezna"
OUT_DOHODAK = config.BUILD / "porezna_dohodak.parquet"
OUT_STOPE = config.BUILD / "porezna_stope.parquet"

HRK_EUR = 7.53450   # fixed conversion rate (NN 85/22)

# key in sources.json -> (CKAN package, regex on the file name of the resource URL, local file).
# The file name changes with every edition (-1, -5, a new date), so the resource is picked by
# pattern; among several matches the one with the highest numbers in the groups wins, then the
# most recently modified.
RESURSI = {
    "porezna_neto_dohodak": (PKG_DOHODAK, r"neto-dohodak-stanovnistva-?(\d{4})_(\d{4})", "neto_dohodak.xlsx"),
    "porezna_stope_dohodak": (PKG_STOPE, r"tablica-poreznih-stopa.*dohodak.*?(\d{4})", "stope_dohodak.xlsx"),
    "porezna_stope_usporedba": (PKG_STOPE, r"stope.*dohodak.*usporedba.*?(\d{4})\D+(\d{4})",
                                "stope_dohodak_usporedba.xlsx"),
    "porezna_potrosnja": (PKG_STOPE, r"porez\w*-na-potro\w*.*?(\d{4})", "porez_potrosnja.xlsx"),
    "porezna_nekretnine": (PKG_STOPE, r"porez\w*-na-nekretnine.*?(\d{2,4})\D(\d{2,4})", "porez_nekretnine.xlsx"),
}

# Kinds of income as labelled in column "Grupacija" -> code in the output
VRSTE = {
    "IZ JOPPD - ZAPOSLENICI": "zaposlenici",
    "IZ JOPPD - UMIROVLJENICI": "umirovljenici",
    "OBRT I SLOBODNA ZANIMANJA (POSL.KNJIGE)": "obrt",
    "SAMOSTALNA DJELATNOST (PAUŠALNO)": "pausalisti",
    "DOHODAK OD KAPITALA": "kapital",
    "DRUGI DOHODAK": "drugi_dohodak",
    "DOHODAK OD IMOVINE I IMOVINSKIH PRAVA": "imovina",
    "DOHODAK OD OSIGURANJA": "osiguranje",
    "POVREMENI RAD - IMOVINA": "povremeni_rad_imovina",
}
UKUPNO = "ukupno"
IZNOSI = ["bruto", "doprinosi", "dohodak", "porez", "neto"]
STUPCI = ["osobe", *IZNOSI]

# header label -> column; matched on the label in lower case, spaces collapsed
_ZAGLAVLJE = [
    (r"^naziv županije", "zupanija"),
    (r"^naziv općine", "naziv"),
    (r"^grupacija", "grupacija"),
    (r"^broj ", "osobe"),
    (r"^brut+o", "bruto"),
    (r"^doprinos", "doprinosi"),
    (r"^dohodak", "dohodak"),
    (r"^porez", "porez"),
    (r"^net+o", "neto"),
]

# Sample from research 09 §2.1, checked in the tests: Pag, 2025, row UKUPNO OPĆINA
UZORAK_PAG_2025 = {"osobe": 4198, "porez": 3_197_794.81}


def _s(v):
    return re.sub(r"\s+", " ", str(v)).strip() if v is not None else ""


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else np.nan


# ---------------------------------------------------------------- download

def _izaberi(resources, pattern):
    """The resource whose URL file name matches pattern, highest numbers first, then newest."""
    found = []
    for r in resources:
        name = (r.get("url") or "").rsplit("/", 1)[-1]
        m = re.search(pattern, name, re.I)
        if m:
            nums = tuple(int(g) for g in m.groups() if g)
            found.append((nums, r.get("last_modified") or r.get("created") or "", r))
    if not found:
        return None
    return max(found, key=lambda t: (t[0], t[1]))[2]


def dohvati(offline=False):
    """Download the five workbooks with conditional GET into data/raw/porezna/.

    Returns {key: path}. Offline, the files already in data/raw/porezna/ are used."""
    paths = {k: RAW_DIR / f for k, (_, _, f) in RESURSI.items()}
    if offline:
        missing = [str(p) for p in paths.values() if not p.exists()]
        if missing:
            raise FileNotFoundError(f"offline, but missing: {missing}")
        return paths
    packages = {}
    for key, (pkg, pattern, _) in RESURSI.items():
        if pkg not in packages:
            packages[pkg] = sources.ckan("package_show", id=pkg)["resources"]
        res = _izaberi(packages[pkg], pattern)
        if res is None:
            raise RuntimeError(f"{key}: no resource matching {pattern!r} in CKAN package {pkg}")
        sources.ckan_resource(key, pkg, lambda r, rid=res["id"]: r["id"] == rid, paths[key])
    return paths


# ---------------------------------------------------------------- A. income by municipality

def _list_godina(title, rows):
    """Year and currency of a sheet: from its title ("2025 EUR"), checked against the title
    row ("... U 2025. GODINI") and the unit row ("iznosi u eurima" / "u kunama")."""
    m = re.match(r"^\s*(\d{4})\s*(EUR|HRK)\s*$", title, re.I)
    if not m:
        return None, None
    godina, valuta = int(m.group(1)), m.group(2).upper()
    text = " ".join(_s(v) for r in rows[:12] for v in r if v is not None).lower()
    t = re.search(r"u (\d{4})\. godini", text)
    if t and int(t.group(1)) != godina:
        raise ValueError(f"sheet {title!r} says year {t.group(1)} in its title row")
    if ("u kunama" in text and valuta != "HRK") or ("u eurima" in text and valuta != "EUR"):
        raise ValueError(f"sheet {title!r}: currency in the sheet does not match the title")
    return godina, valuta


def _stupci_dohodak(header):
    cols, labels = {}, {}
    for j, v in enumerate(header):
        t = _s(v).lower()
        for pat, name in _ZAGLAVLJE:
            if re.match(pat, t) and name not in cols:
                cols[name] = j
                labels[name] = _s(v)
                break
    missing = [n for _, n in _ZAGLAVLJE if n not in cols]
    if missing:
        raise ValueError(f"income sheet header without {missing}: {header}")
    return cols, labels


def parse_dohodak(path):
    """Read every "<year> EUR|HRK" sheet into one long table (amounts in EUR).

    Columns: zup_id, naziv_pu (blank for county rows), razina ("jls", "zupanija", "rh",
    "nerezidenti"), godina, vrsta_dohotka, grupacija (label as printed), osobe, bruto,
    doprinosi, dohodak, porez, neto, porez_s_prirezom, list, red (Excel row).
    df.attrs["nepoznate_vrste"] lists labels not in VRSTE (kept under a slug)."""
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    recs, unknown = [], set()
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        godina, valuta = _list_godina(ws.title, rows)
        if godina is None:
            continue
        h = next((i for i, r in enumerate(rows) if any(_s(v).lower() == "naziv županije" for v in r)), None)
        if h is None:
            raise ValueError(f"sheet {ws.title!r}: no header row with 'Naziv županije'")
        cols, labels = _stupci_dohodak(rows[h])
        s_prirezom = "prirez" in labels["porez"].lower()
        faktor = 1 / HRK_EUR if valuta == "HRK" else 1.0
        for i in range(h + 1, len(rows)):
            r = rows[i]
            zup, naziv, grup = _s(r[cols["zupanija"]]), _s(r[cols["naziv"]]), _s(r[cols["grupacija"]])
            if not grup:
                continue
            m = re.match(r"^(\d{1,2})\s*-\s*\S", zup)
            if m:
                zup_id = int(m.group(1))
                razina = "jls" if naziv else "zupanija"
            elif zup.upper().startswith("REPUBLIKA"):
                zup_id, razina = None, "rh"
            elif zup.lower().startswith("nerezident"):
                zup_id, razina = None, "nerezidenti"
            else:
                continue
            g = grup.upper()
            if g.startswith("UKUPNO"):
                vrsta = UKUPNO
                expect = {"jls": "UKUPNO OPĆINA", "zupanija": "UKUPNO ŽUPANIJA"}.get(razina)
                if expect and g != expect:
                    raise ValueError(f"{ws.title} row {i + 1}: {grup!r} on a {razina} row")
            else:
                vrsta = VRSTE.get(g)
                if vrsta is None:
                    unknown.add(grup)
                    vrsta = slugify(grup).replace("-", "_")
            rec = {"zup_id": zup_id, "naziv_pu": naziv, "razina": razina, "godina": godina,
                   "vrsta_dohotka": vrsta, "grupacija": grup,
                   "osobe": _num(r[cols["osobe"]]),
                   **{k: _num(r[cols[k]]) * faktor for k in IZNOSI},
                   "porez_s_prirezom": s_prirezom, "list": ws.title, "red": i + 1}
            recs.append(rec)
    wb.close()
    df = pd.DataFrame(recs)
    if df.empty:
        raise ValueError(f"{path}: no '<year> EUR|HRK' sheet")
    df["zup_id"] = df["zup_id"].astype("Int64")
    df["osobe"] = df["osobe"].round().astype("Int64")
    df.attrs["nepoznate_vrste"] = sorted(unknown)
    return df


def _kljuc(naziv):
    return slugify(bare_name(naziv).rstrip(". "))


def _kljuc_labavo(naziv):
    return slugify(match_key(naziv).rstrip(". "))


def spoji_nazive(pairs, units):
    """Match (zup_id, name) pairs of towns and municipalities to the register.

    Within the county: the bare name (without GRAD/OPĆINA, no diacritics) against naziv_mf
    and naziv, then units.match_key (bilingual Istrian names, "SV.", en dashes), then one
    remaining name of the county that is close enough (difflib >= 0.9 and clearly the best).
    Returns a DataFrame zup_id, naziv_pu, oib, sifra, spoj (which step matched)."""
    jls = units[units.vrsta != "zupanija"]
    exact, loose = {}, {}
    for u in jls.itertuples():
        for n in {u.naziv_mf, u.naziv}:
            exact.setdefault((int(u.zup_id), _kljuc(n)), set()).add(u.oib)
            loose.setdefault((int(u.zup_id), _kljuc_labavo(n)), set()).add(u.oib)
    by_oib = jls.set_index("oib")
    out = []
    for z, n in pairs:
        hit = None
        for how, idx, key in (("naziv", exact, _kljuc(n)), ("labavo", loose, _kljuc_labavo(n))):
            c = idx.get((int(z), key), set())
            if len(c) == 1:
                hit = (next(iter(c)), how)
                break
        out.append([int(z), n, *(hit or (None, None))])
    taken = {o[2] for o in out if o[2]}
    for o in out:
        if o[2]:
            continue
        pool = [u for u in jls.itertuples() if int(u.zup_id) == o[0] and u.oib not in taken]
        score = sorted(((max(difflib.SequenceMatcher(None, _kljuc(o[1]), _kljuc(nm)).ratio()
                             for nm in (u.naziv_mf, u.naziv)), u.oib) for u in pool), reverse=True)
        if score and score[0][0] >= 0.9 and (len(score) == 1 or score[1][0] < 0.9):
            o[2], o[3] = score[0][1], "slicno"
            taken.add(score[0][1])
    df = pd.DataFrame(out, columns=["zup_id", "naziv_pu", "oib", "spoj"])
    df["sifra"] = df["oib"].map(by_oib["sifra"])
    return df


def spoji_dohodak(raw, units):
    """Attach oib and sifra to the parsed income table (towns, municipalities and counties).

    Returns (table with oib and sifra, match report per year). Rows of the Republic and of
    non-residents are kept apart in attrs["rh"] for the checks."""
    jls_pairs = raw.loc[raw.razina == "jls", ["zup_id", "naziv_pu"]].drop_duplicates()
    m = spoji_nazive(list(jls_pairs.itertuples(index=False, name=None)), units)
    if m["oib"].isna().any():
        bad = m[m.oib.isna()][["zup_id", "naziv_pu"]].values.tolist()
        raise ValueError(f"income rows without a unit in the register: {bad}")
    dup = m[m.oib.duplicated(keep=False)]
    if len(dup):
        raise ValueError(f"two names matched one unit: {dup.values.tolist()}")
    zup = units[units.vrsta == "zupanija"].assign(zup_id=lambda d: d.zup_id.astype(int))
    zmap = zup.set_index("zup_id")[["oib", "sifra"]]

    jls = raw[raw.razina == "jls"].merge(m[["zup_id", "naziv_pu", "oib", "sifra", "spoj"]],
                                         on=["zup_id", "naziv_pu"], how="left")
    zu = raw[raw.razina == "zupanija"].copy()
    zu["oib"] = zu["zup_id"].astype(int).map(zmap["oib"])
    zu["sifra"] = zu["zup_id"].astype(int).map(zmap["sifra"])
    zu["spoj"] = "sifra_zupanije"
    if zu["oib"].isna().any():
        raise ValueError(f"county rows without a county in the register: {sorted(zu[zu.oib.isna()].zup_id.unique())}")
    out = pd.concat([jls, zu], ignore_index=True)
    report = (out[out.vrsta_dohotka == UKUPNO].groupby(["godina", "spoj"]).size()
              .unstack(fill_value=0))
    out.attrs["rh"] = raw[raw.razina.isin(["rh", "nerezidenti"])].reset_index(drop=True)
    out.attrs["nepoznate_vrste"] = raw.attrs.get("nepoznate_vrste", [])
    return out, report


COLS_DOHODAK = ["oib", "sifra", "godina", "vrsta_dohotka", *STUPCI, "porez_s_prirezom", "list", "red"]


def dohodak(path, units):
    """Parsed, matched and checked income table in the output shape (plus attrs)."""
    raw = parse_dohodak(path)
    m, report = spoji_dohodak(raw, units)
    out = (m.sort_values(["godina", "sifra", "red"])[COLS_DOHODAK + ["zup_id", "spoj"]]
           .reset_index(drop=True))
    out.attrs.update(m.attrs, spoj=report)
    return out


# ---------------------------------------------------------------- B. local tax rates

def _rows(path):
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    return ws.title, rows


def _header(rows, must):
    for i, r in enumerate(rows):
        if any(must in _s(v).lower() for v in r):
            return i, [_s(v).lower() for v in r]
    raise ValueError(f"no header row with {must!r}")


def _raspon(v):
    """A rate or amount, or a range written as text ("3,60 do 4,50", "1,00-3,00%") -> (min, max).
    A percent sign turns the numbers into shares (3 % -> 0.03), as the numeric cells are."""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v), float(v)
    t = _s(v)
    nums = [float(x.replace(",", ".")) for x in re.findall(r"\d+(?:[.,]\d+)?", t)]
    if not nums or len(nums) > 2:
        return np.nan, np.nan
    if "%" in t:
        nums = [x / 100 for x in nums]
    return min(nums), max(nums)


def _sifra(v):
    if isinstance(v, (int, float)) and not isinstance(v, bool) and float(v).is_integer():
        return f"{int(v):05d}"
    t = _s(v)
    return t.zfill(5) if t.isdigit() else None


def parse_stope_dohodak(path):
    """Income tax rates as decided by the units: rbr, sifra, naziv_pu, godina, niza, visa,
    nn, na_snazi_od, red. Years and columns from the header ("Niža stopa 2026.")."""
    _, rows = _rows(path)
    h, head = _header(rows, "šifra grada")
    col = {"rbr": next(j for j, t in enumerate(head) if t.startswith("rbr")),
           "sifra": next(j for j, t in enumerate(head) if t.startswith("šifra")),
           "naziv": next(j for j, t in enumerate(head) if t.startswith("ime"))}
    nn = next((j for j, t in enumerate(head) if "nn" in t.split()), None)
    snaga = next((j for j, t in enumerate(head) if t.startswith("stupanje")), None)
    stope = _stope_stupci(head)
    recs = []
    for i in range(h + 1, len(rows)):
        r = rows[i]
        s = _sifra(r[col["sifra"]])
        if not s:
            continue
        for godina, (jn, jv) in stope.items():
            recs.append({"rbr": _s(r[col["rbr"]]).rstrip("."), "sifra": s, "naziv_pu": _s(r[col["naziv"]]),
                         "godina": godina, "niza": _num(r[jn]), "visa": _num(r[jv]),
                         "nn": _s(r[nn]) if nn is not None else None,
                         "na_snazi_od": _s(r[snaga]) if snaga is not None else None, "red": i + 1})
    return pd.DataFrame(recs)


def _stope_stupci(head):
    """{year: (column of the lower rate, column of the higher rate)} from the header."""
    niza = {int(m.group(1)): j for j, t in enumerate(head) if (m := re.match(r"^niža stopa (\d{4})", t))}
    visa = {int(m.group(1)): j for j, t in enumerate(head) if (m := re.match(r"^viša stopa (\d{4})", t))}
    if not niza or set(niza) != set(visa):
        raise ValueError(f"rate columns do not pair up: {head}")
    return {y: (niza[y], visa[y]) for y in sorted(niza)}


def parse_usporedba(path):
    """The 2025/2026 comparison (no code column): rbr, naziv_pu, godina, niza, visa, red."""
    _, rows = _rows(path)
    h, head = _header(rows, "ime grada")
    rbr = next(j for j, t in enumerate(head) if t.startswith("rbr"))
    naziv = next(j for j, t in enumerate(head) if t.startswith("ime"))
    stope = _stope_stupci(head)
    recs = []
    for i in range(h + 1, len(rows)):
        r = rows[i]
        if not _s(r[naziv]) or not _s(r[rbr]):
            continue
        for godina, (jn, jv) in stope.items():
            recs.append({"rbr": _s(r[rbr]).rstrip("."), "naziv_pu": _s(r[naziv]), "godina": godina,
                         "niza": _num(r[jn]), "visa": _num(r[jv]), "red": i + 1})
    return pd.DataFrame(recs)


def parse_potrosnja(path):
    """Consumption tax rate per unit and year (columns headed "2025", "2026"):
    sifra, godina, potrosnja_min, potrosnja_max (shares; a range like Novalja's 1-3 % kept)."""
    _, rows = _rows(path)
    h, head = _header(rows, "šifra grada")
    js = next(j for j, t in enumerate(head) if t.startswith("šifra"))
    years = {int(t): j for j, t in enumerate(head) if re.fullmatch(r"\d{4}", t)}
    if not years:
        raise ValueError(f"no year columns in the consumption tax header: {head}")
    recs = []
    for i in range(h + 1, len(rows)):
        s = _sifra(rows[i][js])
        if not s:
            continue
        for y, j in years.items():
            lo, hi = _raspon(rows[i][j])
            recs.append({"sifra": s, "godina": y, "potrosnja_min": lo, "potrosnja_max": hi})
    return pd.DataFrame(recs)


def parse_nekretnine(path):
    """Property tax in EUR per m² per unit and year, and who collects it (column
    "Nadležnost" after each amount column: JLS itself or PU, the Tax Administration):
    sifra, godina, nekretnine_min, nekretnine_max, nekretnine_naplata."""
    _, rows = _rows(path)
    h, head = _header(rows, "šifra grada")
    js = next(j for j, t in enumerate(head) if t.startswith("šifra"))
    amount = {}
    for j, t in enumerate(head):
        m = re.match(r"^iznos poreza.*?(\d{4})", t)
        if m:
            amount[int(m.group(1))] = [j, None]
        elif t.startswith("nadležnost") and amount:
            last = max(amount, key=lambda y: amount[y][0])
            amount[last][1] = j
    if not amount:
        raise ValueError(f"no amount columns in the property tax header: {head}")
    recs = []
    for i in range(h + 1, len(rows)):
        s = _sifra(rows[i][js])
        if not s:
            continue
        for y, (ja, jn) in amount.items():
            lo, hi = _raspon(rows[i][ja])
            recs.append({"sifra": s, "godina": y, "nekretnine_min": lo, "nekretnine_max": hi,
                         "nekretnine_naplata": _s(rows[i][jn]).upper() or None if jn is not None else None})
    return pd.DataFrame(recs)


COLS_STOPE = ["oib", "sifra", "godina", "niza", "visa", "niza_max", "ispod_maksimuma",
              "potrosnja_min", "potrosnja_max", "nekretnine_min", "nekretnine_max", "nekretnine_naplata"]


def stope(paths, units, fi):
    """Lower and higher income tax rate per unit for every year in the two rate workbooks,
    with the cap from the MF equalization table and the consumption and property taxes.

    paths: from dohvati(). fi: izravnanje.ucitaj() (needs oib and stopa_max).
    The 2026 table carries the code; the comparison 2025/2026 is joined to it by row number
    and name (both lists are the same alphabetical list, with Otok, Privlaka and Sveta Nedelja
    twice), and its 2026 rates must equal the 2026 table's.
    attrs: provjera (counts for the report)."""
    t = parse_stope_dohodak(paths["porezna_stope_dohodak"])
    usp = parse_usporedba(paths["porezna_stope_usporedba"])
    kod = t[["rbr", "naziv_pu", "sifra"]].drop_duplicates()
    if kod.duplicated(["rbr", "naziv_pu"]).any() or kod.sifra.duplicated().any():
        raise ValueError("the 2026 rate table has duplicate rows or codes")
    usp = usp.merge(kod, on=["rbr", "naziv_pu"], how="left")
    if usp.sifra.isna().any():
        raise ValueError(f"comparison rows not in the 2026 table: {usp[usp.sifra.isna()].naziv_pu.unique()[:10]}")
    both = usp.merge(t[["sifra", "godina", "niza", "visa"]], on=["sifra", "godina"], how="inner",
                     suffixes=("", "_t"))
    razlike = both[((both.niza - both.niza_t).abs() > 1e-9) | ((both.visa - both.visa_t).abs() > 1e-9)]
    rates = pd.concat([t[["sifra", "godina", "niza", "visa"]],
                       usp.loc[~usp.godina.isin(t.godina.unique()), ["sifra", "godina", "niza", "visa"]]],
                      ignore_index=True)

    jls = units[units.vrsta != "zupanija"]
    rates = rates.merge(jls[["sifra", "oib"]], on="sifra", how="left")
    if rates.oib.isna().any():
        raise ValueError(f"rate codes not in the register: {sorted(rates[rates.oib.isna()].sifra.unique())}")
    # the names are not the key, but they should agree with the register
    names = kod.merge(jls[["sifra", "naziv_mf", "naziv"]], on="sifra")
    name_ok = [_kljuc(a) in (_kljuc(b), _kljuc(c)) or _kljuc_labavo(a) in (_kljuc_labavo(b), _kljuc_labavo(c))
               for a, b, c in zip(names.naziv_pu, names.naziv_mf, names.naziv)]
    drugaciji_naziv = names.loc[[not x for x in name_ok], ["sifra", "naziv_pu", "naziv"]].values.tolist()

    cap = fi.dropna(subset=["oib"]).set_index("oib")["stopa_max"]
    rates["niza_max"] = rates["oib"].map(cap)
    rates["ispod_maksimuma"] = (rates["niza"] < rates["niza_max"] - 1e-9).where(rates["niza_max"].notna())

    pot = parse_potrosnja(paths["porezna_potrosnja"])
    nek = parse_nekretnine(paths["porezna_nekretnine"])
    for extra in (pot, nek):
        if extra.duplicated(["sifra", "godina"]).any():
            raise ValueError("duplicate codes in a tax workbook")
    out = rates.merge(pot, on=["sifra", "godina"], how="left").merge(nek, on=["sifra", "godina"], how="left")
    out = out[COLS_STOPE].sort_values(["godina", "sifra"], ascending=[False, True]).reset_index(drop=True)
    out["ispod_maksimuma"] = out["ispod_maksimuma"].astype("boolean")
    out.attrs["provjera"] = {
        "godine": sorted(out.godina.unique().tolist()),
        "usporedba_razlike_prema_tablici": razlike[["sifra", "godina", "niza", "niza_t", "visa", "visa_t"]].values.tolist(),
        "drugaciji_naziv": drugaciji_naziv,
        "potrosnja_bez_sifre_u_registru": sorted(set(pot.sifra) - set(jls.sifra)),
        "nekretnine_bez_sifre_u_registru": sorted(set(nek.sifra) - set(jls.sifra)),
    }
    return out


# ---------------------------------------------------------------- checks and diagnostics

def zbrojevi_zupanija(doh, units=None):
    """Sum of the UKUPNO rows of the towns and municipalities of a county against the
    county's UKUPNO row, per year and column. Returns a DataFrame godina, sifra (county),
    stupac, jls, zupanija, razlika (jls - zupanija). Grad Zagreb has no county row.

    The amounts add up to the cent. osobe does not: the county row counts distinct persons
    in the county, and the towns' rows add up to 1-5 % more, presumably because a person
    who moved during the year is counted in both units."""
    if "zup_id" not in doh.columns:
        doh = doh.merge(units[["oib", "zup_id"]], on="oib", how="left")
    u = doh[doh.vrsta_dohotka == UKUPNO]
    zup = u[u.sifra.str.startswith("Z")].set_index(["godina", "zup_id"])
    jls = u[~u.sifra.str.startswith("Z")].groupby(["godina", "zup_id"])[STUPCI].sum(min_count=1)
    recs = []
    for (g, z), r in zup.iterrows():
        for c in STUPCI:
            a = float(jls.loc[(g, z), c]) if (g, z) in jls.index else np.nan
            b = float(r[c])
            recs.append({"godina": g, "sifra": r["sifra"], "stupac": c, "jls": a, "zupanija": b, "razlika": a - b})
    return pd.DataFrame(recs)


def zbroj_republike(doh, rh):
    """Sum of the 20 county totals and Grad Zagreb against the row UKUPNO REPUBLIKA.
    rh: the rows of the Republic (attrs["rh"] of dohodak(), or parse_dohodak() filtered)."""
    u = doh[doh.vrsta_dohotka == UKUPNO]
    parts = u[u.sifra.str.startswith("Z") | (u.sifra == "01333")].groupby("godina")[STUPCI].sum()
    tot = rh[(rh.razina == "rh") & (rh.vrsta_dohotka == UKUPNO)].set_index("godina")[STUPCI]
    recs = [{"godina": g, "stupac": c, "dijelovi": float(parts.loc[g, c]), "rh": float(tot.loc[g, c]),
             "razlika": float(parts.loc[g, c] - tot.loc[g, c])} for g in tot.index for c in STUPCI]
    return pd.DataFrame(recs)


def omjer_611(doh, wide_path=config.BUILD / "wide.parquet", godina=2025):
    """Diagnostic: income tax booked by the unit (PR-RAS account 611) over the income tax paid
    by its residents (this table, UKUPNO), per unit. Not a check that fails.
    Returns oib, sifra, porez, p_611, omjer, or None without data/build/wide.parquet."""
    if not wide_path.exists():
        return None
    w = pd.read_parquet(wide_path, columns=["oib", "year", "p_611"])
    w = w[w.year == godina]
    u = doh[(doh.vrsta_dohotka == UKUPNO) & (doh.godina == godina)][["oib", "sifra", "porez"]]
    m = u.merge(w, on="oib", how="inner")
    m = m[m.porez > 0]
    m["omjer"] = m["p_611"] / m["porez"]
    return m


def build(units, offline=False, fi=None, out_dir=config.BUILD):
    """Fetch, parse, match and write both tables. Returns (dohodak, stope) with attrs.

    units: data/build/units.csv. fi: izravnanje.ucitaj() (read here when not given)."""
    from . import izravnanje

    paths = dohvati(offline)
    doh = dohodak(paths["porezna_neto_dohodak"], units)
    st = stope(paths, units, izravnanje.ucitaj() if fi is None else fi)
    out_dir.mkdir(parents=True, exist_ok=True)
    for df, cols, name in ((doh, COLS_DOHODAK, OUT_DOHODAK.name), (st, COLS_STOPE, OUT_STOPE.name)):
        out = df[cols].copy()
        out.attrs = {}                      # attrs hold DataFrames, which parquet cannot store
        out.to_parquet(out_dir / name, index=False)
    return doh, st


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--offline", action="store_true", help="use data/raw/porezna, no network")
    a = ap.parse_args(argv)

    units = pd.read_csv(config.BUILD / "units.csv", dtype={"oib": str, "rkp": str, "sifra": str})
    doh, st = build(units, a.offline)

    print("A. Neto dohodak stanovništva (Porezna uprava)")
    if doh.attrs["nepoznate_vrste"]:
        print(f"  UPOZORENJE: nepoznate vrste dohotka (zadržane pod slugom): {doh.attrs['nepoznate_vrste']}")
    print("  spojeno po godini i načinu (redak UKUPNO):")
    print("   " + doh.attrs["spoj"].to_string().replace("\n", "\n   "))
    for g, d in doh[doh.vrsta_dohotka == UKUPNO].groupby("godina"):
        print(f"  {g}: {d.oib.nunique()}/{len(units)} jedinica; prazno zbog zaštite podataka"
              f" {int(doh[(doh.godina == g)].osobe.isna().sum())} redaka po vrsti dohotka")
    z = zbrojevi_zupanija(doh)
    zi, zo = z[z.stupac != "osobe"], z[z.stupac == "osobe"]
    rel = zo.razlika / zo.zupanija
    print(f"  zbroj općina i gradova = UKUPNO ŽUPANIJA: iznosi {int((zi.razlika.abs() <= 1.0).sum())}/{len(zi)}"
          f" do 1 EUR (najveća razlika {zi.razlika.abs().max():.2f} EUR); osobe: zbroj veći za"
          f" {100 * rel.min():.1f}-{100 * rel.max():.1f} % (broj različitih osoba, ne zbroj)")
    r = zbroj_republike(doh, doh.attrs["rh"])
    if len(r):
        print(f"  zbroj 20 županija i Zagreba = UKUPNO REPUBLIKA: najveća razlika iznosa"
              f" {r[r.stupac != 'osobe'].razlika.abs().max():.2f} EUR")
    pag = doh[(doh.sifra == units.set_index("slug").loc["grad-pag", "sifra"]) & (doh.godina == 2025)
              & (doh.vrsta_dohotka == UKUPNO)].iloc[0]
    print(f"  uzorak Pag 2025.: {pag.osobe} osoba, porez {pag.porez:,.2f} EUR (list {pag.list}, red {pag.red})")
    print(f"  -> {OUT_DOHODAK.relative_to(config.ROOT)} ({len(doh):,} redaka)")

    m = omjer_611(doh)
    if m is not None:
        j = m[~m.sifra.str.startswith("Z")]
        print(f"  dijagnostika: PR-RAS 611 (2025.) / porez stanovnika (2025.), {len(j)} općina i gradova:"
              f" medijan {j.omjer.median():.3f}, p10 {j.omjer.quantile(.1):.3f}, p90 {j.omjer.quantile(.9):.3f}")
        for sifra, name in (("01333", "Grad Zagreb"), (pag.sifra, "Grad Pag")):
            x = m[m.sifra == sifra]
            if len(x):
                print(f"    {name}: {x.omjer.iloc[0]:.3f}")
        zz = m[m.sifra.str.startswith("Z")]
        if len(zz):
            print(f"    županije ({len(zz)}): medijan {zz.omjer.median():.3f},"
                  f" raspon {zz.omjer.min():.3f}-{zz.omjer.max():.3f}")

    print("B. Lokalne porezne stope (Porezna uprava)")
    p = st.attrs["provjera"]
    gradovi = set(units.loc[units.vrsta == "grad", "oib"])
    for g, d in st.groupby("godina"):
        n_max = int(d.niza_max.notna().sum())
        ispod = d[d.ispod_maksimuma.fillna(False)]
        print(f"  {g}: {d.oib.nunique()}/556 jedinica po šifri; najviša niža stopa iz MF tablice za {n_max};"
              f" ispod maksimuma {len(ispod)}/{n_max} (gradova {int(ispod.oib.isin(gradovi).sum())});"
              f" porez na potrošnju za {int(d.potrosnja_max.notna().sum())}, na nekretnine za"
              f" {int(d.nekretnine_max.notna().sum())}")
    print(f"  usporedba 2025./2026. prema tablici 2026.: {len(p['usporedba_razlike_prema_tablici'])} razlika;"
          f" nazivi drugačiji od šifrarnika: {len(p['drugaciji_naziv'])} {p['drugaciji_naziv'][:5]}")
    print(f"  -> {OUT_STOPE.relative_to(config.ROOT)} ({len(st):,} redaka)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
