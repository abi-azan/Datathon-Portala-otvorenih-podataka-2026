"""DZS PxWeb API v1: population estimates, migration, births, deaths, tourism and building permits by unit.

Portal entries (data.gov.hr, Otvorena dozvola): "Stanovništvo", "Turizam" and "Građevinarstvo",
whose pc-axis resources point to the PxWeb database at web.dzs.hr. A GET on a table returns its
variables and value codes; a POST with a query returns the cells as json-stat2. The server sends
Access-Control-Allow-Origin: *, so the browser can ask it live for one unit (dzs_kodovi.json).

One GET (metadata) and one POST (all units, all years from FIRST_YEAR) per table, plus one GET of
the folder listing for the table's "updated" date. Value codes are read from the metadata on every
run, never hard-coded: only the value texts below are. The server throttles (HTTP 429 after about
ten quick calls), so calls are spaced by PAUSE seconds and retried with a growing pause.

Keys: SP31_2, SM31, SV131 and SV331 number their rows 0-576 and carry only names, under a county
header row ("ZAGREBAČKA ŽUPANIJA"); duplicate names carry the county in brackets. They are matched
to the register by (county, name). BS_TU19 (HR + NUTS 2021 county + DGU code, e.g. HR020300833) and
PX14 (county + 1 town / 2 municipality + DGU code, e.g. 01101015; Grad Zagreb is county 22) carry the
5-digit DGU code. Counties take their own row; a county without one would be the sum of its units.

Output (long): data/build/dzs.parquet with oib, sifra, godina, pokazatelj, vrijednost, plus oznaka
(the DZS status symbol of an empty cell, e.g. "-"), tablica and izvor. An empty cell is NaN in the
file; value() and with_symbols() apply the symbol rule (NEMA, TAJNO) for anyone reading it.
izvor is "pxweb" for every row from the API. The population years PxWeb does not have yet (2025
until DZS updates the tables on 30.11.2026) come from the DZS workbook "Gradovi i općine u
statistici" with izvor "xlsx" (pipeline/dzs_xlsx.py; PxWeb always wins). Nothing here enters the score.

    python -m pipeline.pxweb             refresh all tables from the API, write the outputs
    python -m pipeline.pxweb --offline   re-parse data/raw/pxweb
"""
import argparse
import itertools
import json
import re
import sys
import time
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import quote

import pandas as pd
import requests

from . import config, sources, units as units_mod

BASE = "https://web.dzs.hr/PXWeb/api/v1/hr/"
RAW_DIR = config.RAW / "pxweb"
OUT = config.BUILD / "dzs.parquet"
CODES_OUT = config.BUILD / "dzs_kodovi.json"
FIRST_YEAR = 2021
PAUSE = 2.0                       # seconds between calls
PUBLISHER = "Državni zavod za statistiku"
LICENSE = "Otvorena dozvola"
YEAR_VAR = "Godina"
ZAGREB = "01333"
ZAGREB_ZUP = 21

# DZS status symbols of an empty cell (decided 4.11.2026; one place, because the rule may change).
#   "-"  the phenomenon does not exist (no commercial accommodation, no permit issued): counts as 0
#        in values and in peer medians; the symbol is kept so the UI can say "nema".
#   "z"  hidden for confidentiality: stays empty (NaN), never 0; the UI says "podatak nije javan".
NEMA = "-"
TAJNO = "z"
NEMA_JE_NULA = True


def value(vrijednost, oznaka):
    """The number to use for one DZS cell under the symbol rule above (NaN when there is none)."""
    if oznaka == NEMA and NEMA_JE_NULA:
        return 0.0
    return vrijednost


def with_symbols(df):
    """dzs.parquet rows with vrijednost filled by value(): "-" as 0, "z" and other gaps stay NaN."""
    out = df.copy()
    if NEMA_JE_NULA:
        out.loc[out.oznaka == NEMA, "vrijednost"] = 0.0
    return out


def have_raw(tables=None):
    """True when every raw file of the tables is in data/raw/pxweb: the copy a build falls back
    on when DZS does not answer (in CI, the cached data/raw of the previous run)."""
    return all(_raw(t).exists() and _raw(t, ".meta").exists() for t in tables or TABLES)

# value texts (not codes) of every variable that is not the unit or the year.
# "fixed": one value kept; "split": value text -> indicator; "indicator": the single indicator otherwise.
TABLES = {
    "SP31_2": {
        "path": "Stanovništvo/Procjene stanovništva/SP31_2.px",
        "portal": "stanovni-tvo", "key": "naziv", "area": "Prostorna jedinica",
        "fixed": {"Spol": "Svega"}, "indicator": "stanovnici_procjena",
    },
    "SM31": {
        "path": "Stanovništvo/Migracije/SM31.px",
        "portal": "stanovni-tvo", "key": "naziv", "area": "Prostorna jedinica",
        "split": ("Doseljeni/Odseljeni", {"Ukupno doseljeni": "doseljeni", "Ukupno odseljeni": "odseljeni"}),
    },
    "SV131": {
        "path": "Stanovništvo/Vitalna statistika/Rođeni/SV131.px",
        "portal": "stanovni-tvo", "key": "naziv", "area": "Prostorna jedinica",
        "fixed": {"Postignuto obrazovanje majke": "Ukupno"}, "indicator": "zivorodeni",
    },
    "SV331": {
        "path": "Stanovništvo/Vitalna statistika/Umrli/SV331.px",
        "portal": "stanovni-tvo", "key": "naziv", "area": "Prostorna jedinica",
        "fixed": {"Spol": "Svega", "Godine starosti": "Ukupno"}, "indicator": "umrli",
    },
    "BS_TU19": {
        "path": "Turizam/Dolasci i noćenja turista u komercijalnim smještajnim objektima/BS_TU19.px",
        "portal": "proizvodnja-orani-nih-usjeva-u-tonama",      # the portal's slug; the title is "Turizam"
        "key": "sifra", "area": "Prostorna jedinica",
        "split": ("Indikatori", {"Broj stalnih postelja": "postelje", "Dolasci turista": "dolasci",
                                 "Noćenja turista": "nocenja"}),
    },
    "PX14": {
        "path": "Građevinarstvo/Građevinske dozvole/PX14.px",
        "portal": "gradevinarstvo", "key": "sifra", "area": "Prostorna Jedinica",
        "fixed": {"Vrsta zgrade": "Ukupno", "Mjerna jedinica": "broj"}, "indicator": "dozvole_zgrade",
    },
}


def table_url(table):
    return BASE + quote(TABLES[table]["path"])


def _log_key(table):
    return "dzs_pxweb_" + table.lower()


def _raw(table, kind=""):
    return RAW_DIR / f"{table}{kind}.json"


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- client

_last_call = [0.0]


def _throttle():
    wait = PAUSE - (time.monotonic() - _last_call[0])
    if wait > 0:
        time.sleep(wait)
    _last_call[0] = time.monotonic()


def _call(key, url, body, dest, stats, meta=None):
    _throttle()
    path = sources.fetch_json(key, url, body, dest, meta=meta, stats=stats)
    _last_call[0] = time.monotonic()
    return _read(path)


def build_query(table, meta):
    """The POST body for all units and all years >= FIRST_YEAR, codes taken from the GET metadata."""
    spec = TABLES[table]
    query = []
    for var in meta["variables"]:
        code, values, texts = var["code"], var["values"], var["valueTexts"]
        by_text = dict(zip(texts, values))
        if code == spec["area"]:
            sel = {"filter": "all", "values": ["*"]}
        elif code == YEAR_VAR:
            sel = {"filter": "item", "values": [c for c, t in zip(values, texts) if int(t) >= FIRST_YEAR]}
        elif code in spec.get("fixed", {}):
            sel = {"filter": "item", "values": [by_text[spec["fixed"][code]]]}
        elif "split" in spec and code == spec["split"][0]:
            sel = {"filter": "item", "values": [by_text[t] for t in spec["split"][1]]}
        else:
            raise ValueError(f"{table}: unexpected variable {code!r}; update TABLES")
        query.append({"code": code, "selection": sel})
    missing = {spec["area"], YEAR_VAR, *spec.get("fixed", {}), *([spec["split"][0]] if "split" in spec else [])}
    missing -= {q["code"] for q in query}
    if missing:
        raise ValueError(f"{table}: variables missing from the metadata: {sorted(missing)}")
    return {"query": query, "response": {"format": "json-stat2"}}


def refresh(tables=None, stats=None):
    """Fetch metadata, folder date and data for each table into data/raw/pxweb, logging every call."""
    stats = {} if stats is None else stats
    folders = {}
    for table in tables or TABLES:
        spec = TABLES[table]
        url = table_url(table)
        key = _log_key(table)
        base_meta = {"publisher": PUBLISHER, "license": LICENSE, "px_table": table,
                     "ckan_package": spec["portal"]}
        meta = _call(key + "_meta", url, None, _raw(table, ".meta"), stats,
                     meta={**base_meta, "api": "PxWeb v1 (metapodaci)"})
        folder, name = spec["path"].rsplit("/", 1)
        if folder not in folders:
            folders[folder] = _folder(folder, stats)
        updated = next((t.get("updated") for t in folders[folder] if t.get("id") == name), None)
        body = build_query(table, meta)
        _call(key, url, body, _raw(table), stats,
              meta={**base_meta, "api": "PxWeb v1 (json-stat2)", "title": meta.get("title"),
                    "px_updated": updated, "px_updated_url": BASE + quote(folder)})
        print(f"  {table}: preuzeto (DZS: ažurirano {updated})")
    return stats


def _folder(folder, stats):
    """The folder listing: table ids and the date DZS last updated each table. Only that date is
    kept, in the table's log entry (px_updated, px_updated_url)."""
    _throttle()
    for attempt in range(6):
        stats["calls"] = stats.get("calls", 0) + 1
        r = requests.get(BASE + quote(folder), headers=sources.UA, timeout=60)
        if r.status_code not in sources.RETRY_STATUS or attempt == 5:
            break
        stats["429"] = stats.get("429", 0) + (r.status_code == 429)
        time.sleep(5 * 2 ** attempt)
    _last_call[0] = time.monotonic()
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------- parsing

def jsonstat_frame(js):
    """json-stat2 dataset -> DataFrame: per dimension its code and its label ("<dim>|tekst"),
    then vrijednost (None for an empty cell) and oznaka (the status symbol, if any)."""
    dims, sizes = js["id"], js["size"]
    cats = []
    for d in dims:
        cat = js["dimension"][d]["category"]
        idx = cat.get("index")
        codes = sorted(idx, key=idx.get) if isinstance(idx, dict) else list(idx or cat["label"])
        labels = cat.get("label", {})
        cats.append([(c, labels.get(c, c)) for c in codes])
    if [len(c) for c in cats] != list(sizes):
        raise ValueError(f"json-stat2 sizes {sizes} do not match the categories")
    values, status = js.get("value", []), js.get("status") or {}
    if isinstance(status, list):
        status = {str(i): s for i, s in enumerate(status) if s}
    elif isinstance(status, str):
        status = {str(i): status for i in range(len(values))}
    rows = []
    for i, combo in enumerate(itertools.product(*cats)):
        v = values.get(str(i)) if isinstance(values, dict) else values[i]
        row = {}
        for d, (c, t) in zip(dims, combo):
            row[d], row[d + "|tekst"] = c, t
        row["vrijednost"] = v
        row["oznaka"] = status.get(str(i))
        rows.append(row)
    return pd.DataFrame(rows)


def _plain(s):
    s = str(s).replace("đ", "dj").replace("Đ", "DJ")
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def name_key(name):
    """Loose name: no county in brackets, no Grad/Općina, no diacritics, hyphens as spaces.
    'Otok (Vukovarsko-srijemska županija)' -> 'OTOK'; 'Malinska-Dubašnica' -> 'MALINSKA DUBASNICA'."""
    s = re.sub(r"\s*\([^)]*\)\s*$", "", str(name))
    s = _plain(units_mod.bare_name(s))
    return re.sub(r"[\s\-–]+", " ", s).strip()


def _exact_key(name):
    return units_mod.bare_name(re.sub(r"\s*\([^)]*\)\s*$", "", str(name)))


def _bilingual_key(name):
    """First part of a bilingual Istrian name ('Kaštelir-Labinci-Castellie-S.Domenica' -> 'KASTELIR')."""
    return _plain(units_mod.match_key(re.sub(r"\s*\([^)]*\)\s*$", "", str(name))))


MATCHERS = [("naziv", _exact_key), ("naziv_bez_dijakritika", name_key), ("prvi_dio_naziva", _bilingual_key)]


def _match_county(rows, cand):
    """rows: [(code, label)] of one county; cand: register rows of that county's towns and municipalities.
    Matches one to one, with the strictest key first. Returns {code: (sifra, method)}."""
    out, left_rows = {}, list(rows)
    left_cand = dict(zip(cand.sifra, cand.naziv))
    for method, key in MATCHERS:
        if not left_rows:
            break
        rk = Counter(key(t) for _, t in left_rows)
        ck = {}
        for sifra, naziv in left_cand.items():
            ck.setdefault(key(naziv), []).append(sifra)
        for code, label in left_rows:
            k = key(label)
            if rk[k] == 1 and len(ck.get(k, [])) == 1:
                out[code] = (ck[k][0], method)
        left_rows = [r for r in left_rows if r[0] not in out]
        for sifra, _ in out.values():
            left_cand.pop(sifra, None)
    return out, left_rows, list(left_cand.values())


def area_map(table, area, reg):
    """area: [(code, label)] in table order; reg: the register (units.csv).
    Returns a DataFrame kod, naziv_dzs, razina (rh/zupanija/jls/regija), sifra, nacin."""
    zup_by_key = {name_key(z): int(i) for i, z in reg.groupby("zup_id").zupanija.first().items()}
    jls = reg[reg.vrsta != "zupanija"]
    county_sifra = reg[reg.vrsta == "zupanija"].set_index("zup_id").sifra.to_dict()
    out = []
    if TABLES[table]["key"] == "naziv":
        groups, current = {}, None
        for code, label in area:
            if code == area[0][0]:
                out.append((code, label, "rh", None, None))
            elif label.isupper():
                current = zup_by_key.get(name_key(label))
                if current is None:
                    raise ValueError(f"{table}: unknown county header {label!r}")
                if current == ZAGREB_ZUP:        # one row, county and city at once
                    out.append((code, label, "jls", ZAGREB, "grad_zagreb"))
                else:
                    out.append((code, label, "zupanija", county_sifra[current], "zaglavlje_zupanije"))
                    groups[current] = []
            else:
                if current is None or current == ZAGREB_ZUP:
                    raise ValueError(f"{table}: unit {label!r} outside a county")
                groups[current].append((code, label))
        problems = []
        for z, rows in groups.items():
            hit, left_rows, left_cand = _match_county(rows, jls[jls.zup_id == z])
            if left_rows or left_cand:
                problems.append((z, [t for _, t in left_rows], left_cand))
            out += [(c, t, "jls", *hit[c]) for c, t in rows if c in hit]
        if problems:
            raise ValueError(f"{table}: names without a unique match (county, PxWeb, register): {problems}")
    else:
        known = set(jls.sifra)
        for code, label in area:
            if table == "BS_TU19":
                if len(code) == 11:
                    out.append((code, label, "jls", code[-5:], "sifra"))
                elif len(code) == 6:
                    z = int(code[4:6])
                    out.append((code, label, "zupanija", county_sifra.get(z), "sifra_zupanije") if z != ZAGREB_ZUP
                               else (code, label, "regija", None, None))
                else:
                    out.append((code, label, "rh" if code == "HR" else "regija", None, None))
            else:  # PX14: ZZ + T + DGU code; T 0 county, 1 towns, 2 municipalities
                z = int(code[:2])
                if code == "00000000":
                    out.append((code, label, "rh", None, None))
                elif code[-5:] != "00000":
                    out.append((code, label, "jls", code[-5:], "sifra"))
                elif code[2] == "0" and z in county_sifra:
                    out.append((code, label, "zupanija", county_sifra[z], "sifra_zupanije"))
                else:                               # " GRADOVI:" / " OPĆINE:" headers, Grad Zagreb as county 22
                    out.append((code, label, "regija", None, None))
        bad = [r for r in out if r[2] == "jls" and r[3] not in known]
        if bad:
            raise ValueError(f"{table}: codes not in the register: {bad}")
    m = pd.DataFrame(out, columns=["kod", "naziv_dzs", "razina", "sifra", "nacin"])
    dup = m[m.sifra.notna() & m.sifra.duplicated(keep=False)]
    if len(dup):
        raise ValueError(f"{table}: a unit matched twice: {dup.values.tolist()}")
    return m


def observations(table, reg, js=None, meta=None):
    """All cells of a table in long form, with the register keys where the row is a unit or county.
    Columns: tablica, kod, naziv_dzs, razina, sifra, oib, nacin, godina, pokazatelj, vrijednost, oznaka."""
    spec = TABLES[table]
    js = js if js is not None else _read(_raw(table))
    meta = meta if meta is not None else _read(_raw(table, ".meta"))
    area_var = next(v for v in meta["variables"] if v["code"] == spec["area"])
    amap = area_map(table, list(zip(area_var["values"], area_var["valueTexts"])), reg)
    f = jsonstat_frame(js)
    if "split" in spec:
        dim, names = spec["split"]
        f["pokazatelj"] = f[dim + "|tekst"].map(names)
    else:
        f["pokazatelj"] = spec["indicator"]
    if f.pokazatelj.isna().any():
        raise ValueError(f"{table}: cells without an indicator")
    f["godina"] = f[YEAR_VAR + "|tekst"].astype(int)
    f = f.rename(columns={spec["area"]: "kod"})[["kod", "godina", "pokazatelj", "vrijednost", "oznaka"]]
    f = f.merge(amap, on="kod", how="left", validate="many_to_one")
    if f.razina.isna().any():
        raise ValueError(f"{table}: data rows not in the metadata: {f[f.razina.isna()].kod.unique()[:5]}")
    f["vrijednost"] = pd.to_numeric(f["vrijednost"], errors="coerce").astype(float)
    oib = reg.set_index("sifra").oib
    f["oib"] = f.sifra.map(oib)
    f["tablica"] = table
    return f[["tablica", "kod", "naziv_dzs", "razina", "sifra", "oib", "nacin", "godina", "pokazatelj",
              "vrijednost", "oznaka"]]


def _county_sums(obs, reg):
    """Counties a table has no row for: the sum of their units (NaN when no unit has a value)."""
    have = set(obs.loc[obs.razina == "zupanija", "sifra"])
    zup = reg[reg.vrsta == "zupanija"]
    missing = zup[~zup.sifra.isin(have)]
    if missing.empty:
        return obs.iloc[:0]
    j = obs[obs.razina == "jls"].merge(reg[["sifra", "zup_id"]], on="sifra")
    s = (j[j.zup_id.isin(missing.zup_id)].groupby(["zup_id", "godina", "pokazatelj"]).vrijednost
         .sum(min_count=1).reset_index())
    s = s.merge(missing[["zup_id", "sifra", "oib"]], on="zup_id")
    s["tablica"], s["razina"], s["nacin"], s["oznaka"] = obs.tablica.iloc[0], "zupanija", "zbroj_jedinica", "zbroj"
    return s


def load_register():
    return pd.read_csv(config.BUILD / "units.csv", dtype={"oib": str, "sifra": str})


def build(reg=None, tables=None, xlsx=True):
    """Parse data/raw/pxweb into dzs.parquet and dzs_kodovi.json, plus the population years PxWeb
    does not have yet from the DZS workbook (xlsx=False: PxWeb only). Returns (long frame, report)."""
    reg = load_register() if reg is None else reg
    parts, report, codes, names = [], {}, {}, {}
    for table in tables or TABLES:
        obs = observations(table, reg)
        keep = obs[obs.razina.isin(["jls", "zupanija"])]
        keep = pd.concat([keep, _county_sums(keep, reg)], ignore_index=True)
        parts.append(keep)
        units_rows = obs[obs.razina.isin(["jls", "zupanija"])].drop_duplicates("sifra")
        codes[table] = units_rows.set_index("oib").kod.to_dict()
        names[table] = units_rows.set_index("oib").naziv_dzs.to_dict()
        jls = keep[keep.razina == "jls"]
        report[table] = {
            "jls": jls.oib.nunique(), "zupanije": keep[keep.razina == "zupanija"].oib.nunique(),
            "nacin": units_rows[units_rows.razina == "jls"].nacin.value_counts().to_dict(),
            "godine": sorted(keep.godina.unique().tolist()), "pokazatelji": sorted(keep.pokazatelj.unique()),
            "prazno": int(jls.vrijednost.isna().sum()), "celija": len(jls),
            "oznake": jls.oznaka.dropna().value_counts().to_dict(),
        }
    df = pd.concat(parts, ignore_index=True)
    df = df[["oib", "sifra", "godina", "pokazatelj", "vrijednost", "oznaka", "tablica"]]
    # population years PxWeb does not have yet, from the DZS workbook (PxWeb wins; pipeline/dzs_xlsx.py)
    from . import dzs_xlsx
    df, report[dzs_xlsx.LOG_KEY] = dzs_xlsx.extend(df, reg) if xlsx else (df.assign(izvor=dzs_xlsx.IZVOR_PXWEB), {
        "ok": False, "razlog": "isključeno", "dodane_godine": []})
    df = df.sort_values(["oib", "pokazatelj", "godina"]).reset_index(drop=True)
    if df.duplicated(["oib", "godina", "pokazatelj"]).any():
        raise ValueError("duplicate (oib, godina, pokazatelj)")
    config.BUILD.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    CODES_OUT.write_text(json.dumps(codes_document(reg, codes, names), ensure_ascii=False, indent=1), encoding="utf-8")
    return df, report


def codes_document(reg, codes, names=None):
    """dzs_kodovi.json: per unit its PxWeb value code in each table (and, under "nazivi", the label
    DZS gives that code), and a query template per table. The browser replaces "{kod}" in the template
    and POSTs it to the table URL (CORS: *); it checks the label in the answer, so that a renumbering of
    the rows on the DZS side cannot show another unit's numbers."""
    log = sources._log()
    tables = {}
    for table, spec in TABLES.items():
        if table not in codes:
            continue
        meta = _read(_raw(table, ".meta"))
        body = build_query(table, meta)
        for q in body["query"]:
            if q["code"] == spec["area"]:
                q["selection"] = {"filter": "item", "values": ["{kod}"]}
        entry = log.get(_log_key(table), {})
        tables[table] = {"url": table_url(table), "naslov": meta.get("title"), "varijabla": spec["area"],
                         "upit": body, "dzs_azurirano": entry.get("px_updated"),
                         "preuzeto": entry.get("retrieved")}
    units = {}
    for r in reg.itertuples():
        units[r.oib] = {"sifra": r.sifra, "slug": r.slug,
                        **{t: c[r.oib] for t, c in codes.items() if r.oib in c},
                        "nazivi": {t: n[r.oib] for t, n in (names or {}).items() if r.oib in n}}
    return {
        "meta": {
            "opis": "PxWeb kod vrijednosti svake jedinice u tablicama DZS-a i predložak upita. "
                    "U predlošku zamijeni \"{kod}\" kodom jedinice i pošalji POST na url tablice; "
                    "odgovor je json-stat2.",
            "izdavatelj": PUBLISHER, "licenca": LICENSE,
            "generirano": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "tablice": tables,
        },
        "jedinice": units,
    }


def print_report(report):
    from . import dzs_xlsx
    for t, r in report.items():
        if t == dzs_xlsx.LOG_KEY:
            dzs_xlsx.print_report(r)
            continue
        print(f"  {t:8} JLS {r['jls']}/556  županije {r['zupanije']}/20  godine {r['godine'][0]}-{r['godine'][-1]}"
              f"  {', '.join(r['pokazatelji'])}")
        print(f"           spojeno: {r['nacin']}  prazno {r['prazno']}/{r['celija']} {r['oznake'] or ''}")


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--offline", action="store_true", help="re-parse data/raw/pxweb without calling the API")
    args = ap.parse_args(argv)
    t0 = time.monotonic()
    stats = {}
    if not args.offline:
        print(f"DZS PxWeb: {len(TABLES)} tablica, pauza {PAUSE} s")
        refresh(stats=stats)
        from . import dzs_xlsx
        dzs_xlsx.fetch()
    fetched = time.monotonic() - t0
    df, report = build()
    print_report(report)
    print(f"  {OUT.relative_to(config.ROOT)}: {len(df):,} redaka; {CODES_OUT.relative_to(config.ROOT)}")
    if not args.offline:
        print(f"  dohvat {fetched:.0f} s, poziva {stats.get('calls', 0)}, HTTP 429: {stats.get('429', 0)}; "
              f"ukupno {time.monotonic() - t0:.0f} s")


if __name__ == "__main__":
    main()
