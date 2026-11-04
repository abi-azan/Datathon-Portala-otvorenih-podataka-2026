"""Fiscal equalization paid to each unit per year, from the MF yearly decisions.

The legal base ZO (methodology.aux) takes all grants (account 63) out of revenue and adds
fiscal equalization back: since NN 138/20 equalization is a current grant from the state budget
that does not count as a grant for borrowing (Zakon o financiranju JLP(R)S čl. 8.a st. 2.-3.).
Account 6353 "Pomoći fiskalnog izravnanja" is not a reliable record of it. In 2021-2024 almost
nobody books it (Σ 6353 is 0 in 2021-2023 and 37.782 € in 2024); equalization sits in 6331. In
2025, the first year 6353 is in general use, 107 of 445 entitled units still book it elsewhere
(6331, 6352). Their ZO missed the whole amount and their debt service ratio I4 came out too high.
The amount is therefore taken from the minister's yearly decision (čl. 9. st. 7.): each unit's
share x the amount in the state budget for that year, capped at what the unit booked on the
current-grant accounts (stupac()).

Inputs, per year, from https://mfin.gov.hr/istaknute-teme/lokalna-samouprava/fiskalno-izravnanje/202:
- "Tablica udjela po JLP(R)S za fiskalno izravnanje u <godina>" (XLSX): the calculation sheet
  ("Izračun ...", one row per unit with ZAP ID, county, type, name, the full amount and the share
  rounded to 18 decimals, column "Udio zaokružen na 18 decimala") and the sheet "Udjeli" with
  the shares as printed in the decision (point II). parse_tablica() reads both, header-driven,
  and checks that they agree.
- "Odluka o udjelu ... fiskalnog izravnanja ..." (PDF, point II): the budget amount, printed in
  the heading of column 4 ("4 (3 x 2.000.000.000,00)" for 2021). The PDFs are scans, so the
  amounts are typed in PRORACUN below, each with the place it was read from.

isplate() gives one row per unit and year with the amount, the share, the budget amount and the
cell it comes from (file, sheet, row, column), for provenance.py. 2019 and 2020 are not grants
(U_POREZU). A year without a usable table falls back to account 6353 for every unit (izvor
"konto_6353"), and so does a unit that the table does not match; both are reported in
data/build/izravnanje_isplate.json. stupac() gives the wide-table columns p_FI and p_FI_odluka.

CLI: python -m pipeline.izravnanje_isplate [--offline]   (fetch, parse, validate against PR-RAS)
"""
import argparse
import json
import re
import sys
from urllib.parse import quote

import pandas as pd

from . import config, izravnanje, methodology

RAW_DIR = config.RAW / "izravnanje"
OUT_PARQUET = config.BUILD / "izravnanje_isplate.parquet"
OUT_REPORT = config.BUILD / "izravnanje_isplate.json"
PAGE = "https://mfin.gov.hr/istaknute-teme/lokalna-samouprava/fiskalno-izravnanje/202"
META = {"publisher": "Ministarstvo financija", "license": "nije navedena (javni podatak, ZPPI)", "page": PAGE}

HRK_PER_EUR = 7.5345            # fixed conversion rate; the MF PR-RAS series is in EUR for every year

_B = "https://mfin.gov.hr/UserDocsImages//dokumenti/o-ministarstvu/lokalna-samouprava//"
_q = lambda u: quote(u, safe=":/()")
TABLICE = {
    2021: _q(_B + "Tablica za odluku 2021 za fiskalno izravnanje u 2021.xlsx"),
    2022: _q(_B + "Tablica udjela po JLP(R)S za fiskalno izravnanje u 2022.xlsx"),
    2023: _q(_B + "Tablica udjela po JLP(R)S za fiskalno izravnanje u 2023.xlsx"),
    2024: _q(_B + "Tablica udjela po JLP(R)S za fiskalno izravnanje u 2024.xlsx"),
    2025: _q(_B + "Tablica udjela po JLP(R)S za fiskalno izravnanje u 2025.xlsx"),
}
ODLUKE = {
    2021: _q(_B + "Odluka o udjelu fiskalnog izravnanja za pojedinu općinu, grad i županiju s iznosom sredstava "
                  "fiskalnog izravnanja za 2021.pdf"),
    2022: _q(_B + "Odluka o udjelu fiskalnog izravnanja za pojedinu općinu, grad i županiju s iznosom sredstava "
                  "fiskalnog izravnanja za 2022.pdf"),
    2023: _q(_B + "Odluka o udjelu sredstava fiskalnog izravnanja za pojedinu općinu, grad i županiju za 2023.pdf"),
    2024: _q(_B + "Odluka o udjelu sredstava fiskalnog izravnanja za pojedinu općinu, grad i županiju za 2024.pdf"),
    2025: _q(_B + "Odluka o udjelu fiskalnog izravnanja za pojedinu općinu, grad i županiju u ukupnim sredstvima "
                  "fiskalnog izravnanja za 2025.pdf"),
}

# Until 31.12.2020 fiscal equalization was not a grant: it was the 17 % share of income tax set aside
# for it (NN 127/17 čl. 5. st. 2. t. 4.), paid out through the income tax distribution, so units
# book it in 611 (taxes) and ZO never took it out. NN 138/20 (from 1.1.2021) dropped that share and
# moved equalization to the state budget (new čl. 8.a): a current grant from the state budget
# (st. 2.), which for borrowing is not counted as a grant (st. 3.), hence the add-back in ZO.
# The PR-RAS data agree: Σ 6331 over all units is 102 mil. € in 2019 and 189 mil. € in 2020, less
# than the full equalization amounts of those years (295 and 301 mil. €), and jumps to 396 mil. € in
# 2021 when the 265 mil. € grant starts. For these years p_FI stays account 6353 as booked (izvor
# "porez_na_dohodak"; 6353 is used by Grad Osijek and Osječko-baranjska županija only), so ZO is unchanged.
U_POREZU = {2019: "NN 127/17 čl. 5. st. 2. t. 4.: udio za fiskalno izravnanje 17 % poreza na dohodak",
            2020: "NN 127/17 čl. 5. st. 2. t. 4.: udio za fiskalno izravnanje 17 % poreza na dohodak"}

# Budget amount per year (point II of the decision), in the currency printed there.
PRORACUN = {
    2021: {"iznos": 2_000_000_000.0, "valuta": "HRK",
           "gdje": "odluka za 2021., točka II, stupac 4 \"(3 x 2.000.000.000,00)\""},
    2022: {"iznos": 2_000_000_000.0, "valuta": "HRK",
           "gdje": "odluka za 2022., točka II, stupac 4 \"(3 x 2.000.000.000,00)\"; tablica, list Udjeli, redak 6"},
    2023: {"iznos": 265_445_617.0, "valuta": "EUR",
           "gdje": "odluka za 2023., točka II, stupac 4 \"(3 x 265.445.617 EUR)\""},
    2024: {"iznos": 265_445_617.0, "valuta": "EUR",
           "gdje": "odluka za 2024., točka II, stupac 4 \"(3 x 265.445.617 EUR)\""},
    2025: {"iznos": 280_445_617.0, "valuta": "EUR",
           "gdje": "odluka za 2025., točka II, stupac 4 \"(3 x 280.445.617 EUR)\""},
    2026: {"iznos": 280_445_617.0, "valuta": "EUR",
           "gdje": "odluka za 2026., točka II, stupac 4 \"(3 x 280.445.617 EUR)\""},
}


def tablica_path(godina):
    return RAW_DIR / f"fi_{godina}.xlsx"


def odluka_path(godina):
    return RAW_DIR / f"odluka_{godina}.pdf"


def fetch(godine=None):
    """Download the tables and decisions through sources.fetch (conditional GET, logged in
    data/raw/sources.json). A year that fails is skipped with a message; isplate() then falls
    back to account 6353 for it."""
    from . import sources
    failed = []
    for y in sorted(godine or TABLICE):
        for key, url, dest in ((f"mf_fi_tablica_{y}", TABLICE.get(y), tablica_path(y)),
                               (f"mf_fi_odluka_{y}", ODLUKE.get(y), odluka_path(y))):
            if not url:
                continue
            try:
                sources.fetch(key, url, dest, meta=META)
            except Exception as e:          # network or HTTP error: keep an earlier copy if there is one
                failed.append((key, str(e)))
                print(f"  {key}: preuzimanje nije uspjelo ({e}){'; koristim postojeću kopiju' if dest.exists() else ''}")
    return failed


# ---------------------------------------------------------------- parsing

def _s(v):
    return re.sub(r"\s+", " ", str(v)).strip() if v is not None else ""


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _letter(j):
    from openpyxl.utils import get_column_letter
    return get_column_letter(j + 1)


def _calc_cols(header):
    cols = {}
    for j, v in enumerate(header):
        t = _s(v)
        tl = t.lower()
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
        elif tl.startswith("optimalni iznos"):
            cols["puni"] = j
        elif tl.startswith("udio zaokružen"):
            cols["udio"] = j
    missing = {"zap_id", "zup_id", "titula", "naziv", "puni", "udio"} - set(cols)
    if missing:
        raise ValueError(f"calculation sheet: no column {sorted(missing)}")
    return cols


def _decision_sheet(ws):
    """Shares as printed in the decision: [{vrsta, naziv, udio, zap_id, iznos, red}]."""
    rows = list(ws.iter_rows(values_only=True))
    hi = next((i for i, r in enumerate(rows) if any(_s(v).startswith("Udio jedinice u ukupnim") for v in r)
               and any(_s(v) == "Naziv jedinice" for v in r)), None)
    if hi is None:
        raise ValueError("sheet Udjeli: no header row")
    cols = {}
    for j, v in enumerate(rows[hi]):
        t = _s(v)
        k = t.lower().replace(" ", "")
        if t == "O/G/Ž":
            cols["titula"] = j
        elif t == "Naziv jedinice":
            cols["naziv"] = j
        elif t.startswith("Udio jedinice u ukupnim"):
            cols["udio"] = j
        elif k == "zapid":
            cols["zap_id"] = j
        elif t.startswith("Iznos"):
            cols["iznos"] = j
    out = []
    for i in range(hi + 1, len(rows)):
        r = rows[i]
        get = lambda k: r[cols[k]] if k in cols and cols[k] < len(r) else None
        vrsta = izravnanje.TITULA.get(_s(get("titula")).upper())
        udio = _num(get("udio"))
        if not vrsta or udio is None:
            continue
        zap = _num(get("zap_id"))
        out.append({"vrsta": vrsta, "naziv": _s(get("naziv")), "udio": udio,
                    "zap_id": int(zap) if zap is not None else None, "iznos": _num(get("iznos")), "red": i + 1})
    return out, cols


def parse_tablica(path, godina):
    """One row per unit of the MF table for `godina`: zap_id, zup_id, vrsta, naziv_mf, stanovnici,
    puni (full amount, in the table's currency), udio (share, 18 decimals), red and stupac (Excel row
    and column of the share), list (sheet). attrs: godina, list, puni_ukupno, odluka (the "Udjeli"
    check: n, jednako, najvece_odstupanje, zbroj, iznosi = amounts printed there or None)."""
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = next(w for w in wb.worksheets if w.title.startswith("Izra"))
    rows = list(ws.iter_rows(values_only=True))
    headers = [i for i, r in enumerate(rows) if any(_s(v) == "Titula" for v in r)]
    if not headers:
        raise ValueError(f"{path.name}: no header row with 'Titula'")
    recs = []
    for h_i, h in enumerate(headers):
        c = _calc_cols(rows[h])
        end = headers[h_i + 1] if h_i + 1 < len(headers) else len(rows)
        for i in range(h + 1, end):
            r = rows[i]
            vrsta = izravnanje.TITULA.get(_s(r[c["titula"]]).upper())
            zap = _num(r[c["zap_id"]])
            if not vrsta or zap is None:
                continue
            udio = _num(r[c["udio"]])
            recs.append({"zap_id": int(zap), "zup_id": int(r[c["zup_id"]]), "vrsta": vrsta,
                         "naziv_mf": _s(r[c["naziv"]]),
                         "stanovnici": _num(r[c["stanovnici"]]) if "stanovnici" in c else None,
                         "puni": _num(r[c["puni"]]) or 0.0, "udio": udio or 0.0,
                         "red": i + 1, "stupac": _letter(c["udio"])})
    df = pd.DataFrame(recs)
    if df["zap_id"].duplicated().any():
        raise ValueError(f"{path.name}: duplicate ZAP ID")
    df["list"] = ws.title

    # the decision's shares (sheet "Udjeli") must be the table's shares
    chk = {"n": 0, "jednako": 0, "najvece_odstupanje": None, "zbroj": None, "iznosi": False}
    ud = next((w for w in wb.worksheets if w.title.strip() == "Udjeli"), None)
    if ud is not None:
        dec, dcols = _decision_sheet(ud)
        chk["n"] = len(dec)
        chk["zbroj"] = sum(d["udio"] for d in dec)
        chk["iznosi"] = "iznos" in dcols
        if dec and all(d["zap_id"] is not None for d in dec):
            # 2022 on: the decision sheet carries ZAP ID, and its share is the one the decision
            # prints. In 2024 it differs from the calculation sheet in the 7th significant digit
            # (largest gap 1.8e-6), so the decision sheet's share and cell are used.
            by = {d["zap_id"]: d for d in dec}
            diffs = [abs(by[z]["udio"] - u) if z in by else float("nan") for z, u in zip(df.zap_id, df.udio)]
            df["udio_tablica"] = df["udio"]
            for i, z in enumerate(df["zap_id"]):
                if z in by:
                    df.loc[i, ["udio", "red", "stupac", "list"]] = [by[z]["udio"], by[z]["red"],
                                                                    _letter(dcols["udio"]), ud.title]
        else:                                           # 2019-2021: no ZAP ID, compare per type and name
            key = lambda v, n: (v, izravnanje.slugify(izravnanje.bare_name(n).rstrip(". ")))
            mine, theirs = {}, {}
            for v, n, u in zip(df.vrsta, df.naziv_mf, df.udio):
                mine.setdefault(key(v, n), []).append(u)
            for d in dec:
                theirs.setdefault(key(d["vrsta"], d["naziv"]), []).append(d["udio"])
            diffs = []
            for k, v in theirs.items():
                m = mine.get(k)
                if m is None or len(m) != len(v):
                    diffs += [float("nan")] * len(v)
                else:
                    diffs += [abs(a - b) for a, b in zip(sorted(m), sorted(v))]
        ok = [d for d in diffs if d == d]
        chk["usporedeno"] = len(ok)
        chk["jednako"] = int(sum(d < 1e-12 for d in ok))
        chk["najvece_odstupanje"] = float(max(ok)) if ok else None
        if chk["iznosi"]:
            chk["iznos_zbroj"] = sum(d["iznos"] or 0.0 for d in dec)
    wb.close()
    df.attrs.update(godina=godina, list=ws.title, puni_ukupno=float(df["puni"].sum()), odluka=chk)
    return df


def proracun_eur(godina):
    """Budget amount of the year in EUR (PRORACUN)."""
    p = PRORACUN[godina]
    return p["iznos"] / HRK_PER_EUR if p["valuta"] == "HRK" else p["iznos"]


# ---------------------------------------------------------------- per unit and year

def isplate(units, godine=config.YEARS):
    """Long table oib, year, FI (EUR), udio, proracun_eur, datoteka, list, redak, stupac, izvor
    ("odluka"), for every unit the year's table matches. Returns (table, report); the report says
    per year which file was used, how many units matched and why a year is missing."""
    rows, report = [], {}
    for y in godine:
        if y in U_POREZU:
            report[y] = {"izvor": "porez_na_dohodak", "razlog": U_POREZU[y]}
            continue
        path = tablica_path(y)
        if y not in PRORACUN or not path.exists():
            report[y] = {"izvor": "konto_6353", "razlog": "nema tablice" if y in PRORACUN else "nema iznosa odluke"}
            continue
        try:
            t = parse_tablica(path, y)
            m = izravnanje.spoji_sa_sifrarnikom(t, units)
        except Exception as e:                       # unreadable layout: fall back for the year
            report[y] = {"izvor": "konto_6353", "razlog": f"tablica nije pročitana: {e!r}"}
            continue
        a = proracun_eur(y)
        m = m[m["oib"].notna()]
        for r in m.itertuples():
            rows.append({"oib": r.oib, "year": y, "FI_odluka": r.udio * a, "udio": r.udio, "proracun_eur": a,
                         "datoteka": path.name, "url": TABLICE[y], "list": r.list, "redak": int(r.red),
                         "stupac": r.stupac, "izvor": "odluka"})
        report[y] = {"izvor": "odluka", "datoteka": path.name, "list": t.attrs["list"], "proracun_eur": a,
                     "proracun_gdje": PRORACUN[y]["gdje"], "jedinica_u_tablici": len(t),
                     "spareno": len(m), "nespareno": sorted(set(units["oib"]) - set(m["oib"])),
                     "s_pravom": int((t["udio"] > 0).sum()), "zbroj_udjela": float(t["udio"].sum()),
                     "udjeli_odluke": t.attrs["odluka"]}
    return pd.DataFrame(rows), report


def prostor(df):
    """Current-grant accounts that can hold equalization (methodology.FI_ROOM): 6331 (= 633 - 6332;
    čl. 8.a st. 2.: a current grant from the state budget), 6352 (Grad Belišće 2025) and 6353.
    df: a DataFrame with those p_ columns (missing columns and values count as 0). Never below 0."""
    zero = pd.Series(0.0, index=df.index)
    return sum(sign * (df[k].fillna(0.0) if k in df else zero) for k, sign in methodology.FI_ROOM.items()).clip(lower=0.0)


def stupac(wide, units, godine=config.YEARS, write=True):
    """The equalization columns of the wide table (oib, year), as Series on wide's index:

    - p_FI_odluka: the decision amount (share x budget amount), NaN where there is none;
    - p_FI: what ZO adds back. The decision amount, but never more than the unit booked on the
      current-grant accounts (prostor()): ZO takes 63 out, so adding back more than 63 holds
      would count equalization booked under taxes twice (Općina Sveti Juraj na Bregu 2022: 389.000 €
      of equalization, 2.927 € on 6331, the rest in 6111). Without a decision amount p_FI is 6353.

    Writes izravnanje_isplate.parquet (the decision rows, for provenance.py) and .json (the
    report per year) to data/build when write is set."""
    tab, report = isplate(units, godine)
    years = wide["year"].astype(int)
    key = pd.MultiIndex.from_arrays([wide["oib"], years])
    booked = wide["p_6353"].fillna(0.0) if "p_6353" in wide else pd.Series(0.0, index=wide.index)
    odl = (pd.Series(tab.set_index(["oib", "year"])["FI_odluka"].reindex(key).to_numpy(), index=wide.index)
           if len(tab) else pd.Series(float("nan"), index=wide.index))
    room = prostor(wide)
    fi = odl.clip(upper=room).where(odl.notna(), booked)
    for y in sorted(set(years)):
        sel = years == y
        rep = report.setdefault(int(y), {"izvor": "konto_6353"})
        d = odl[sel]
        rep.update(zbroj_odluka=float(d.sum()), zbroj_FI=float(fi[sel].sum()), zbroj_6353=float(booked[sel].sum()),
                   bez_odluke=int(d.isna().sum()),
                   ograniceno_prostorom=int(((d - room[sel]) > 0.005).sum()))
    if write:
        config.BUILD.mkdir(parents=True, exist_ok=True)
        tab.to_parquet(OUT_PARQUET, index=False)
        OUT_REPORT.write_text(json.dumps({str(k): v for k, v in sorted(report.items())}, ensure_ascii=False,
                                         indent=1, default=float), encoding="utf-8")
    return fi, odl


def za_build(wide, units, offline=False):
    """pipeline/build.py: download (unless offline), then stupac() with its files written.
    Prints one line per year and warns about years that fall back to account 6353."""
    if not offline:
        print("Fiskalno izravnanje: tablice i odluke MF-a ...")
        fetch()
    fi, odl = stupac(wide, units)
    rep = json.loads(OUT_REPORT.read_text(encoding="utf-8"))
    for y, r in rep.items():
        if r["izvor"] == "odluka":
            print(f"  izravnanje {y}: odluka, spareno {r['spareno']}/{r['jedinica_u_tablici']},"
                  f" Σ {r['zbroj_odluka']:,.0f} €, ograničeno na pomoći {r['ograniceno_prostorom']}")
        else:
            print(f"  izravnanje {y}: {r['izvor']} ({r.get('razlog', '')})")
            if r["izvor"] == "konto_6353":
                print(f"UPOZORENJE: fiskalno izravnanje {y} nema odluku MF-a; ZO koristi konto 6353")
    return fi, odl


def izvor_godine(godina):
    """Where p_FI of a unit without a decision row comes from in that year."""
    return "porez_na_dohodak" if godina in U_POREZU else "konto_6353"


def ucitaj():
    """The decision rows written by stupac() (provenance.py), or an empty table."""
    if OUT_PARQUET.exists():
        return pd.read_parquet(OUT_PARQUET)
    return pd.DataFrame(columns=["oib", "year", "FI_odluka", "udio", "proracun_eur", "datoteka", "url", "list",
                                 "redak", "stupac", "izvor"])


# ---------------------------------------------------------------- validation against PR-RAS

def provjera(wide, units, godine=config.YEARS):
    """Per year, against PR-RAS: the decision total and Σ 6353; of the entitled units, how many
    book exactly the decision amount on 6353 (within 1 %), more, less or nothing; how many have
    6331 within 1 % of it (2021-2024, before 6353); and for how many the decision amount is more
    than the current-grant accounts hold (prostor(), where stupac() caps it)."""
    p_fi, odl = stupac(wide, units, godine, write=False)
    _, report = isplate(units, godine)
    w = wide.assign(FI=odl, p_FI=p_fi, room=prostor(wide), year=wide["year"].astype(int))
    w["x_6331"] = w["p_633"].fillna(0.0) - w["p_6332"].fillna(0.0)
    w["p_6353"] = w["p_6353"].fillna(0.0)
    within = lambda a, b: (a - b).abs() <= 0.01 * b
    out = {}
    for y, g in w.groupby("year"):
        e = g[g.FI > 0]
        on = e[e.p_6353 > 0]
        rep = report.get(int(y), {})
        out[int(y)] = {
            "izvor": rep.get("izvor"), "proracun_eur": rep.get("proracun_eur"), "spareno": rep.get("spareno"),
            "udjeli_odluke": rep.get("udjeli_odluke"),
            "zbroj_odluka": round(float(g.FI.sum()), 2), "zbroj_FI": round(float(g.p_FI.sum()), 2),
            "zbroj_6353": round(float(g.p_6353.sum()), 2), "zbroj_6331": round(float(g.x_6331.sum()), 2),
            "s_pravom": len(e), "6353_veci_od_0": len(on),
            "6353_unutar_1_posto": int(within(on.p_6353, on.FI).sum()),
            "6353_vise": int((on.p_6353 > 1.01 * on.FI).sum()),
            "6353_manje": int((on.p_6353 < 0.99 * on.FI).sum()),
            "6353_nula": int((e.p_6353 == 0).sum()),
            "6331_unutar_1_posto": int(within(e.x_6331, e.FI).sum()),
            "vise_od_prostora": int((e.FI > e.room + 0.005).sum()),
            "vise_od_prostora_iznos": round(float((e.FI - e.room).clip(lower=0).sum()), 2),
        }
    return out


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--offline", action="store_true", help="do not download, use data/raw/izravnanje")
    a = ap.parse_args(argv)
    if not a.offline:
        fetch()
    units = pd.read_csv(config.BUILD / "units.csv", dtype={"oib": str, "rkp": str, "sifra": str})
    wide = pd.read_parquet(config.BUILD / "wide.parquet")
    for y, r in provjera(wide, units).items():
        u = r["udjeli_odluke"] or {}
        print(f"{y}: {r['izvor']}, proračun {r['proracun_eur'] or 0:,.0f} €, spareno {r['spareno']},"
              f" udjeli odluke = tablica {u.get('jednako')}/{u.get('n')}")
        print(f"   Σ odluka {r['zbroj_odluka']:,.0f} €, Σ p_FI {r['zbroj_FI']:,.0f} €, Σ 6353 {r['zbroj_6353']:,.0f} €,"
              f" Σ 6331 {r['zbroj_6331']:,.0f} €")
        print(f"   s pravom {r['s_pravom']}: 6353 > 0 {r['6353_veci_od_0']} (unutar 1 % {r['6353_unutar_1_posto']},"
              f" više {r['6353_vise']}, manje {r['6353_manje']}), 6353 = 0 {r['6353_nula']};"
              f" 6331 unutar 1 % {r['6331_unutar_1_posto']}; odluka > 6331 + 6352 + 6353: {r['vise_od_prostora']}"
              f" ({r['vise_od_prostora_iznos']:,.0f} €)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
