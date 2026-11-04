"""DZS "Gradovi i općine u statistici" (XLSX): population years the PxWeb API does not have yet.

DZS publishes the estimate of 31.12. and the year's births, deaths and migration by town and
municipality first in this workbook (30.9.), and in the PxWeb tables SP31_2, SV131, SV331 and SM31
only about two months later (30.11.; docs/research/12). Decision 4.11.2026 (option A): PxWeb stays
the primary source; the workbook only fills the (indicator, year) pairs PxWeb does not have.

    Tab-2.  Procjena stanovništva (31.12.), Živorođeni, Umrli: one column per year
    Tab-3.  Doseljeni / Odseljeni per year, of which the "ukupno" column (8 columns per year)

Columns are found by their header texts (section, year, "ukupno"), never by position. Rows are
matched to the register by (county, name) with pxweb's matchers; Grad Zagreb is one row. Every
match is checked against the register's Popis 2021 figure, which the workbook repeats. The workbook
has no county rows, so a county is the sum of its towns and municipalities (in PxWeb the county row
equals that sum: research 12 §2.3).

Precedence (bridge): for every indicator, a year PxWeb has is taken from PxWeb only, for all units,
even where a PxWeb cell is empty. The workbook adds only the years PxWeb lacks (>= pxweb.FIRST_YEAR),
so when PxWeb publishes 2025 the bridge for 2025 disappears by itself. The added rows carry
tablica GUS_TAB2 / GUS_TAB3 and izvor "xlsx" in dzs.parquet (PxWeb rows: izvor "pxweb").

The bridge is used only when two checks pass (checks()):
  1. the workbook equals PxWeb in every common cell of the towns and municipalities;
  2. in every added year, population change = births - deaths + in - out for every unit, against
     the previous year's estimate (from PxWeb or the workbook).
Otherwise the build warns and dzs.parquet stays PxWeb only. Nothing here enters the score.

    python -m pipeline.dzs_xlsx             fetch (conditional GET) and print the checks
    python -m pipeline.dzs_xlsx --offline   re-parse data/raw/dzs
"""
import argparse
import re
import sys
from collections import Counter

import openpyxl
import pandas as pd

from . import config, pxweb, sources

URL = "https://podaci.dzs.hr/media/bz5hplcj/gradovi-u-statistici.xlsx"
PORTAL = "statistika-u-nizu-gradovi-u-statistici"
LOG_KEY = "dzs_gradovi_u_statistici"
RAW = config.RAW / "dzs" / "gradovi-u-statistici.xlsx"
TITLE = "Gradovi i općine u statistici"
TABLICE = {"Tab-2.": "GUS_TAB2", "Tab-3.": "GUS_TAB3"}
SOURCE_ID = "GUS"                  # the workbook in the profile's list of sources (kontekst.sources)
IZVOR_PXWEB, IZVOR_XLSX = "pxweb", "xlsx"

# header texts -> indicator (Tab-2.: section of the year columns; Tab-3.: direction, then "ukupno")
TAB2 = {"Procjena stanovništva": "stanovnici_procjena", "Živorođeni": "zivorodeni", "Umrli": "umrli"}
TAB3 = {"Doseljeni": "doseljeni", "Odseljeni": "odseljeni"}
TAB3_TOTAL = "ukupno"
POPIS = "Popis 2021."
COUNTY_HEAD, NAME_HEAD = "Županije", "Gradovi/općine"
ZAGREB_ROW = "Grad Zagreb"
INDICATORS = list(TAB2.values()) + list(TAB3.values())
YEAR = re.compile(r"^(\d{4})\.?$")


def fetch():
    """Conditional GET of the workbook into data/raw/dzs, logged in sources.json."""
    return sources.fetch(LOG_KEY, URL, RAW, meta={
        "publisher": pxweb.PUBLISHER, "license": pxweb.LICENSE, "ckan_package": PORTAL, "title": TITLE})


def have_raw():
    return RAW.exists()


# ---------------------------------------------------------------- parsing

def _text(c):
    return str(c).strip() if c is not None else ""


def _header(rows, first_data):
    """Per column, the header texts of every row above the data: (as written, filled), where filled
    carries each row's last non-empty text to the right, as a merged cell does ("2011." spans the 8
    columns of that year in Tab-3., "Umrli" the 15 year columns in Tab-2.)."""
    width = max(len(r) for r in rows[:first_data])
    raw, filled = [[] for _ in range(width)], [[] for _ in range(width)]
    for r in rows[:first_data]:
        last = ""
        for i in range(width):
            t = _text(r[i]) if i < len(r) else ""
            if t:
                last = t
            raw[i].append(t)
            filled[i].append(last)
    return raw, filled


def _find(cols, *tests):
    """Indices of the columns whose header texts pass every test (each test is a predicate on one text)."""
    return [i for i, texts in enumerate(cols) if all(any(t(x) for x in texts) for t in tests)]


def _year_of(texts):
    years = {int(m.group(1)) for x in texts if (m := YEAR.match(x))}
    return years.pop() if len(years) == 1 else None


def _cell(v):
    """(value, symbol): a number (int, float or numeric text); "-" none (0 under pxweb.value), "z" hidden."""
    if v is None:
        return float("nan"), None
    if isinstance(v, (int, float)):
        return float(v), None
    t = str(v).strip()
    if t in (pxweb.NEMA, pxweb.TAJNO):
        return float("nan"), t
    if re.fullmatch(r"\d+", t):
        return float(t), None
    raise ValueError(f"unexpected cell {v!r}")


def read_sheet(ws, sheet):
    """One sheet in long form: zupanija, naziv, popis_2021, godina, pokazatelj, vrijednost, oznaka."""
    rows = [tuple(r) for r in ws.iter_rows(values_only=True)]
    head = next(i for i, r in enumerate(rows) if _text(r[0] if r else None) == COUNTY_HEAD)
    first = head + 1
    while first < len(rows) and not any(isinstance(c, (int, float)) for c in rows[first]):
        first += 1                                  # Tab-3. has an English header row under it
    raw, cols = _header(rows, first)
    county = _find(raw, lambda x: x == COUNTY_HEAD)
    name = _find(raw, lambda x: x.startswith(NAME_HEAD))
    popis = _find(raw, lambda x: x == POPIS)
    if len(county) != 1 or len(name) != 1 or len(popis) != 1:
        raise ValueError(f"{sheet}: header columns not found (county {county}, name {name}, Popis 2021 {popis})")
    want = {}
    if sheet == "Tab-2.":
        found = [(i, ind) for text, ind in TAB2.items() for i in _find(cols, lambda x, t=text: x.startswith(t))]
    else:
        total = set(_find(raw, lambda x: x.lower().startswith(TAB3_TOTAL)))
        found = [(i, ind) for text, ind in TAB3.items() for i in _find(cols, lambda x, t=text: x == t) if i in total]
    for i, ind in found:
        if want.setdefault(i, ind) != ind:
            raise ValueError(f"{sheet}: column {i} is both {want[i]} and {ind}")
    spec = {}
    for i, ind in want.items():
        y = _year_of(cols[i])
        if y is None:
            raise ValueError(f"{sheet}: column {i} ({ind}) has no single year in its header")
        if (ind, y) in spec:
            raise ValueError(f"{sheet}: two columns for {ind} {y}")
        spec[(ind, y)] = i
    out = []
    for r in rows[first:]:
        if not r or not _text(r[name[0]]) or not isinstance(r[popis[0]], (int, float)):
            continue
        z, n, p = _text(r[county[0]]), _text(r[name[0]]), int(r[popis[0]])
        for (ind, y), i in spec.items():
            v, s = _cell(r[i] if i < len(r) else None)
            out.append((z, n, p, y, ind, v, s))
    df = pd.DataFrame(out, columns=["zupanija", "naziv", "popis_2021", "godina", "pokazatelj", "vrijednost", "oznaka"])
    df["tablica"] = TABLICE[sheet]
    return df


def match_rows(names, reg):
    """names: DataFrame zupanija, naziv (one row per unit). Returns {(zupanija, naziv): sifra}."""
    jls = reg[reg.vrsta != "zupanija"]
    zup_by_key = {pxweb.name_key(z): int(i) for i, z in reg.groupby("zup_id").zupanija.first().items()}
    out, problems = {}, []
    for z, g in names.groupby("zupanija"):
        if z == ZAGREB_ROW:
            if len(g) != 1:
                raise ValueError(f"{len(g)} rows for Grad Zagreb")
            out[(z, g.naziv.iloc[0])] = pxweb.ZAGREB
            continue
        zid = zup_by_key.get(pxweb.name_key(z + " županija"))
        if zid is None or zid == pxweb.ZAGREB_ZUP:
            raise ValueError(f"unknown county {z!r}")
        rows = list(enumerate(g.naziv))
        hit, left_rows, left_cand = pxweb._match_county(rows, jls[jls.zup_id == zid])
        if left_rows or left_cand:
            problems.append((z, [t for _, t in left_rows], left_cand))
        out.update({(z, t): hit[i][0] for i, t in rows if i in hit})
    if problems:
        raise ValueError(f"names without a unique match (county, workbook, register): {problems}")
    dup = [s for s, c in Counter(out.values()).items() if c > 1]
    if dup:
        raise ValueError(f"a unit matched twice: {dup}")
    return out


def observations(reg, path=RAW):
    """All indicator-years of the workbook for the 556 towns and municipalities, in dzs.parquet form
    (oib, sifra, godina, pokazatelj, vrijednost, oznaka, tablica). Fails when a header, a name or
    a Popis 2021 figure does not match."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        df = pd.concat([read_sheet(wb[s], s) for s in TABLICE], ignore_index=True)
    finally:
        wb.close()
    names = df.drop_duplicates(["zupanija", "naziv"])[["zupanija", "naziv", "popis_2021"]]
    m = match_rows(names, reg)
    df["sifra"] = [m[k] for k in zip(df.zupanija, df.naziv)]
    jls = reg[reg.vrsta != "zupanija"].set_index("sifra")
    if len(set(m.values())) != len(jls):
        raise ValueError(f"{len(set(m.values()))} of {len(jls)} units in the workbook")
    popis = names.assign(sifra=[m[k] for k in zip(names.zupanija, names.naziv)]).set_index("sifra").popis_2021
    bad = popis[popis != jls.stanovnici_2021.reindex(popis.index).astype(int)]
    if len(bad):
        raise ValueError(f"Popis 2021 differs from the register for {bad.index.tolist()[:5]}")
    df["oib"] = df.sifra.map(jls.oib)
    df = df[df.godina >= pxweb.FIRST_YEAR]
    return df[["oib", "sifra", "godina", "pokazatelj", "vrijednost", "oznaka", "tablica"]].reset_index(drop=True)


def county_sums(obs, reg):
    """County rows as the sum of their towns and municipalities, per indicator and year. A "-" cell
    counts as 0 (pxweb.value); a hidden "z" cell makes the county value empty with "z"."""
    z = reg[reg.vrsta == "zupanija"]
    j = obs.merge(reg[["sifra", "zup_id"]], on="sifra")
    j = j[j.zup_id.isin(z.zup_id)]
    vals = pxweb.with_symbols(j)
    key = ["zup_id", "godina", "pokazatelj", "tablica"]
    s = vals.groupby(key).vrijednost.sum(min_count=1).rename("vrijednost").reset_index()
    hidden = j.assign(h=j.oznaka == pxweb.TAJNO).groupby(key).h.any().reset_index()
    s = s.merge(hidden, on=key)
    s.loc[s.h, "vrijednost"] = float("nan")
    s["oznaka"] = s.h.map({True: pxweb.TAJNO, False: None})
    s = s.merge(z[["zup_id", "sifra", "oib"]], on="zup_id")
    return s[["oib", "sifra", "godina", "pokazatelj", "vrijednost", "oznaka", "tablica"]]


# ---------------------------------------------------------------- precedence and checks

def bridge(px, xl):
    """The rows of xl for the (indicator, year) pairs px does not have at all. PxWeb always wins:
    a year PxWeb has, for an indicator, is never taken from the workbook, not even for one unit."""
    have = set(zip(px.pokazatelj, px.godina))
    keep = [(p, y) not in have for p, y in zip(xl.pokazatelj, xl.godina)]
    return xl[keep].reset_index(drop=True)


def checks(px, xl, added):
    """The two conditions for using the bridge (module docstring), on towns and municipalities.
    px: PxWeb rows; xl: all workbook rows; added: bridge(px, xl). Returns a report dict with ok."""
    key = ["oib", "godina", "pokazatelj"]
    a = pxweb.with_symbols(px[px.pokazatelj.isin(INDICATORS)]).set_index(key).vrijednost
    b = pxweb.with_symbols(xl).set_index(key).vrijednost
    common = a.index.intersection(b.index)
    x, y = a.loc[common], b.loc[common]
    same = (x == y) | (x.isna() & y.isna())
    differ = common[~same.to_numpy()]

    both = pd.concat([px[px.pokazatelj.isin(INDICATORS)], added], ignore_index=True)
    w = pxweb.with_symbols(both).pivot_table(index=["oib", "godina"], columns="pokazatelj", values="vrijednost")
    years = sorted(added.godina.unique().tolist())
    bad, n = [], 0
    pop = w["stanovnici_procjena"] if "stanovnici_procjena" in w else None
    for yr in years:
        for o in added.loc[added.godina == yr, "oib"].unique():
            n += 1
            try:
                lhs = pop[(o, yr)] - pop[(o, yr - 1)]
                r = w.loc[(o, yr)]
                rhs = r["zivorodeni"] - r["umrli"] + r["doseljeni"] - r["odseljeni"]
            except KeyError:
                bad.append((o, yr))
                continue
            if not lhs == rhs:
                bad.append((o, yr))
    return {"ok": len(differ) == 0 and not bad and len(common) > 0,
            "zajednicke_celije": int(len(common)), "razlike": [tuple(k) for k in differ[:10]],
            "n_razlika": int(len(differ)), "jednadzba_jedinica_godina": n, "jednadzba_odstupanja": bad[:10],
            "n_odstupanja": len(bad), "dodane_godine": years,
            "dodani_pokazatelji": sorted(added.pokazatelj.unique().tolist())}


def extend(px, reg, path=RAW):
    """px (dzs.parquet rows from PxWeb, with counties) plus the bridged workbook rows, each with izvor.
    Returns (frame, report). Without the workbook, when it cannot be read or when a check fails, px
    alone (report["razlog"] says why)."""
    px = px.assign(izvor=IZVOR_PXWEB)
    if not path.exists():
        return px, {"ok": False, "razlog": f"nema datoteke {path.name}", "dodane_godine": []}
    try:
        xl = observations(reg, path)
    except Exception as e:                     # a changed layout must not stop the build: PxWeb alone
        return px, {"ok": False, "razlog": f"datoteka nije pročitana: {e!r}"[:300], "dodane_godine": []}
    jls = set(reg.loc[reg.vrsta != "zupanija", "oib"])
    added = bridge(px, xl)
    rep = checks(px[px.oib.isin(jls)], xl, added)
    if not rep["ok"] or added.empty:
        rep.setdefault("razlog", None if rep["ok"] else "provjera nije prošla")
        return px, {**rep, "dodane_godine": [] if not rep["ok"] else rep["dodane_godine"]}
    rows = pd.concat([added, county_sums(added, reg)], ignore_index=True).assign(izvor=IZVOR_XLSX)
    out = pd.concat([px, rows], ignore_index=True).sort_values(["oib", "pokazatelj", "godina"]).reset_index(drop=True)
    return out, rep


def year_sources(dzs, pokazatelj):
    """{year: "pxweb" | "xlsx"} for one indicator of dzs.parquet (one source per year by construction)."""
    d = dzs[dzs.pokazatelj == pokazatelj]
    col = d["izvor"] if "izvor" in d else pd.Series(IZVOR_PXWEB, index=d.index)
    by = col.groupby(d.godina).agg(lambda s: sorted(set(s)))
    out = {}
    for y, s in by.items():
        if len(s) != 1:
            raise ValueError(f"{pokazatelj} {y}: more than one source {s}")
        out[int(y)] = s[0]
    return out


def print_report(rep):
    if not rep.get("dodane_godine"):
        print(f"  XLSX \"{TITLE}\": ništa dodano ({rep.get('razlog') or 'PxWeb ima sve godine'})"
              + (f"; razlika s PxWebom {rep['n_razlika']}, odstupanja jednadžbe {rep['n_odstupanja']}"
                 if "n_razlika" in rep else ""))
        return
    print(f"  XLSX \"{TITLE}\": dodane godine {rep['dodane_godine']} ({', '.join(rep['dodani_pokazatelji'])});"
          f" jednako PxWebu u {rep['zajednicke_celije']:,} zajedničkih ćelija (razlika {rep['n_razlika']});"
          f" jednadžba stanovništva {rep['jednadzba_jedinica_godina']} jedinica-godina, odstupanja {rep['n_odstupanja']}")


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--offline", action="store_true", help="re-parse data/raw/dzs without downloading")
    args = ap.parse_args(argv)
    if not args.offline:
        fetch()
    reg = pxweb.load_register()
    px = pd.read_parquet(pxweb.OUT)
    if "izvor" in px:
        px = px[px.izvor == IZVOR_PXWEB].drop(columns="izvor")
    _, rep = extend(px, reg)
    print_report(rep)


if __name__ == "__main__":
    main()
