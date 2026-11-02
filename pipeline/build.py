"""Build fiscal health indicators for every Croatian local and regional self-government unit.

Inputs:
  --mf-dir    Ministry of Finance PR-RAS + RAS-funkcijski workbooks, one per county,
              one sheet per unit, 2019-2025 ("Lokalci FINALI ... EURO.zip", unpacked)
  --bilanca   Ministry of Finance balance sheets 2019-2025, one sheet per year
  --pop       DZS Popis 2021, population by town/municipality (data.gov.hr)

Outputs (in --out):
  jls_years.csv   one row per unit and year, raw values and indicators
  jls.json        the same data nested per unit, for the dashboard
"""
import argparse
import json
import math
import os
import re
import sys
from pathlib import Path

import openpyxl
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

YEARS = list(range(2019, 2026))

# PR-RAS position codes we keep (accounts, functional classes, derived rows)
PRRAS_KEYS = {
    "6": "prihodi_poslovanja",
    "61": "porezi",
    "611": "porez_na_dohodak",
    "613": "porezi_na_imovinu",
    "63": "pomoci",
    "6353": "fiskalno_izravnanje",
    # capital grants and donations: excluded from current revenue (KDZ "laufende Gebarung")
    "6312": "kap_pomoci_6312",
    "6322": "kap_pomoci_6322",
    "6324": "kap_pomoci_6324",
    "6332": "kap_pomoci_6332",
    "6342": "kap_pomoci_6342",
    "6352": "kap_pomoci_6352",
    "6362": "kap_pomoci_6362",
    "6382": "kap_pomoci_6382",
    "6632": "kap_pomoci_6632",
    "64": "prihodi_od_imovine",
    "65": "pristojbe_i_naknade",
    "7": "prihodi_od_prodaje_nefin",
    "3": "rashodi_poslovanja",
    "31": "rashodi_zaposleni",
    "32": "materijalni_rashodi",
    "342": "kamate",
    "4": "rashodi_nefin_imovina",
    "84": "primici_od_zaduzivanja",
    "54": "otplata_glavnice",
    "01": "f01_opce_javne_usluge",
    "Z006": "zaposleni_u_tijelima",
}

# Balance sheet columns (position codes in the header row)
BILANCA_KEYS = {
    "11": "novac",
    "23": "obveze_rashodi_poslovanja",
    "dio 23 D": "dospjele_obveze_poslovanja",
    "26": "obveze_krediti_zajmovi",
    "dio 26 D": "dospjele_obveze_krediti",
    "9221": "visak_akumulirani",
    "9222": "manjak_akumulirani",
}


def norm_name(s):
    s = str(s).upper().strip()
    s = re.sub(r"\s*-\s*", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s


def unit_type(sheet_name):
    if sheet_name.endswith("ŽUPANIJA"):
        return "zupanija"
    if sheet_name.startswith("GRAD "):
        return "grad"
    if sheet_name.startswith("OPĆINA "):
        return "opcina"
    return None


def bare_name(full):
    full = norm_name(full)
    for p in ("GRAD ", "OPĆINA "):
        if full.startswith(p):
            return full[len(p):]
    return full


def match_key(name):
    """Loose key for names that differ between sources: bilingual Istrian names,
    en dashes, "SV." abbreviations and county suffixes."""
    s = bare_name(name).replace("–", "-")
    s = re.sub(r"^SV\. ?", "SVETI ", s)
    s = re.sub(r" ZADARSKI$| OPĆINA$", "", s)
    return re.split(r"\s*-\s*", s)[0].strip()


def parse_prras(mf_dir):
    """Return {(county_id, sheet_name): {field: {year: value}}}."""
    files = sorted(os.listdir(mf_dir))
    out = {}
    for f in files:
        m = re.match(r"(\d\d) ", f)
        if not m or not f.endswith(".xlsx") or m.group(1) == "22":
            continue
        # Osječko-baranjska ships a corrected file next to the original
        if m.group(1) == "14" and "ispravak" not in f and any(
            x.startswith("14 ") and "ispravak" in x for x in files
        ):
            continue
        county_id = int(m.group(1))
        wb = openpyxl.load_workbook(Path(mf_dir) / f, read_only=True, data_only=True)
        for sn in wb.sheetnames:
            if sn.startswith(("UKUPNO", "SVEUKUPNO")) or unit_type(sn) is None:
                continue
            year_col = {}
            data = {}
            for r in wb[sn].iter_rows(values_only=True):
                if not year_col:
                    for i, c in enumerate(r):
                        mm = re.match(r"Ostvareno u (\d{4})", str(c or ""))
                        if mm:
                            year_col[int(mm.group(1))] = i
                    continue
                key = r[2]
                if key is None:
                    continue
                key = str(key).strip()
                if key in PRRAS_KEYS:
                    data[PRRAS_KEYS[key]] = {
                        y: float(r[i]) if isinstance(r[i], (int, float)) else 0.0
                        for y, i in year_col.items()
                    }
            out[(county_id, sn)] = data
        wb.close()
        print(f"  {f}: done", flush=True)
    return out


def parse_bilanca(path):
    """Return {(county_id, name): {"oib", "rkp", field: {year: value}}}."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = {}
    for sn in wb.sheetnames:
        year = int(sn)
        it = wb[sn].iter_rows(values_only=True)
        codes = [str(c).strip() if c is not None else "" for c in next(it)]
        col = {BILANCA_KEYS[c]: i for i, c in enumerate(codes) if c in BILANCA_KEYS}
        for r in it:
            if not isinstance(r[0], (int, float)) or not r[2]:
                continue
            key = (int(r[0]), norm_name(r[3]))
            u = out.setdefault(key, {"oib": str(r[2]), "rkp": str(r[1])})
            for field, i in col.items():
                v = r[i]
                u.setdefault(field, {})[year] = float(v) if isinstance(v, (int, float)) else 0.0
    wb.close()
    return out


def parse_population(path):
    """Return ({(county_id, type, bare_name): population}, {county_id: county_name})."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["1."]
    county_ids, pop, county_totals = {}, {}, {}
    for r in ws.iter_rows(min_row=9, values_only=True):
        county, kind, name, total = r[0], r[1], r[4], r[5]
        if not county or county == "Republika Hrvatska":
            continue
        if county not in county_ids:
            county_ids[county] = len(county_ids) + 1
        cid = county_ids[county]
        if kind in ("Grad", "Općina") and isinstance(total, (int, float)):
            t = "grad" if kind == "Grad" else "opcina"
            pop[(cid, t, norm_name(name))] = int(total)
        elif cid not in county_totals:
            # county total row: first number after the name columns
            nums = [c for c in r[1:8] if isinstance(c, (int, float))]
            if nums:
                county_totals[cid] = int(nums[0])
    wb.close()
    return pop, county_totals, {v: k for k, v in county_ids.items()}


def lookup(table, cid, t, name):
    """Exact match on the bare name first, then on match_key."""
    if (cid, t, bare_name(name)) in table:
        return table[(cid, t, bare_name(name))]
    k = match_key(name)
    hits = [v for (c, tt, n), v in table.items() if c == cid and tt == t and match_key(n) == k]
    return hits[0] if len(hits) == 1 else None


def div(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


def band(x, cuts, higher_is_better):
    """Score 1 (best) to 5 (worst) using four cut points."""
    if x is None:
        return None
    if higher_is_better:
        for score, c in enumerate(cuts, start=1):
            if x >= c:
                return score
        return 5
    for score, c in enumerate(cuts, start=1):
        if x <= c:
            return score
    return 5


def indicators(v, pop):
    """v: dict of raw values for one unit-year. Returns indicator dict."""
    g = lambda k: v.get(k) or 0.0
    kap = sum(g(k) for k in v if k.startswith("kap_pomoci_"))
    rev = g("prihodi_poslovanja") - kap  # current revenue
    op = rev - g("rashodi_poslovanja")
    debt = g("obveze_krediti_zajmovi")
    ind = {
        "kapitalne_pomoci": kap,
        "tekuci_prihodi": rev,
        "operativni_saldo": div(op, rev),
        "slobodni_saldo": div(op - g("otplata_glavnice"), rev),
        "dug_prema_prihodima": div(debt, rev),
        "godine_otplate": (0.0 if debt == 0 else (div(debt, op) if op > 0 else math.inf)),
        "teret_otplate": div(g("kamate") + g("otplata_glavnice"), rev),
        "dospjele_obveze_udio": div(g("dospjele_obveze_poslovanja") + g("dospjele_obveze_krediti"), g("rashodi_poslovanja")),
        "udio_pomoci": div(g("pomoci"), g("prihodi_poslovanja")),
        "udio_tekucih_pomoci": div(g("pomoci") - kap + g("kap_pomoci_6632"), rev),
        "investicijska_kvota": div(g("rashodi_nefin_imovina"), g("rashodi_poslovanja") + g("rashodi_nefin_imovina")),
        "prihodi_pc": div(rev, pop),
        "vlastiti_prihodi_pc": div(g("porezi") + g("prihodi_od_imovine") + g("pristojbe_i_naknade"), pop),
        "admin_pc": div(g("f01_opce_javne_usluge"), pop),
        "zaposleni_pc": div(g("rashodi_zaposleni"), pop),
        "djelatnici_na_1000": div(g("zaposleni_u_tijelima") * 1000, pop),
    }
    scores = [
        band(ind["operativni_saldo"], [0.15, 0.10, 0.05, 0.0], True),
        band(ind["slobodni_saldo"], [0.10, 0.05, 0.0, -0.05], True),
        band(ind["godine_otplate"], [2, 5, 10, 20], False),
        band(ind["teret_otplate"], [0.02, 0.05, 0.10, 0.20], False),
        band(ind["dospjele_obveze_udio"], [0.01, 0.03, 0.07, 0.15], False),
    ]
    valid = [s for s in scores if s is not None]
    ind["bodovi"] = scores
    ind["ocjena"] = round(sum(valid) / len(valid), 2) if len(valid) >= 4 else None
    return ind


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mf-dir", required=True)
    ap.add_argument("--bilanca", required=True)
    ap.add_argument("--pop", required=True)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "data" / "processed"))
    a = ap.parse_args()

    print("PR-RAS ...", flush=True)
    prras = parse_prras(a.mf_dir)
    print(f"  {len(prras)} units")
    print("Bilanca ...", flush=True)
    bil = parse_bilanca(a.bilanca)
    print("Popis 2021 ...", flush=True)
    pop, county_pop, county_names = parse_population(a.pop)
    bil = {(cid, unit_type(n), bare_name(n)): v for (cid, n), v in bil.items()}

    rows, units, unmatched = [], [], []
    for (cid, sn), data in sorted(prras.items()):
        t = unit_type(sn)
        name = norm_name(sn)
        b = lookup(bil, cid, t, name)
        if t == "zupanija":
            p = county_pop.get(cid)
        else:
            p = lookup(pop, cid, t, name)
            # Grad Zagreb is both a city and a county; DZS lists it only as a county
            if p is None and name == "GRAD ZAGREB":
                p = county_pop.get(cid)
        if b is None or p is None:
            unmatched.append((cid, sn, "bilanca" if b is None else "popis"))
        unit = {
            "oib": b["oib"] if b else None,
            "rkp": b["rkp"] if b else None,
            "naziv": sn,
            "vrsta": t,
            "zupanija_id": cid,
            "zupanija": county_names.get(cid),
            "stanovnici_2021": p,
            "godine": {},
        }
        for y in YEARS:
            v = {k: d.get(y) for k, d in data.items()}
            if b:
                v.update({k: b[k].get(y) for k in BILANCA_KEYS.values() if k in b})
            ind = indicators(v, p)
            unit["godine"][y] = {**v, **ind}
            rows.append({k: unit[k] for k in ("oib", "naziv", "vrsta", "zupanija_id", "stanovnici_2021")}
                        | {"godina": y} | v | {k: x for k, x in ind.items() if k != "bodovi"})
        units.append(unit)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "jls_years.csv", index=False, encoding="utf-8")
    def finite(x):
        if isinstance(x, float) and not math.isfinite(x):
            return None
        if isinstance(x, dict):
            return {k: finite(v) for k, v in x.items()}
        if isinstance(x, list):
            return [finite(v) for v in x]
        return x

    with open(out / "jls.json", "w", encoding="utf-8") as f:
        json.dump(finite(units), f, ensure_ascii=False)
    print(f"{len(units)} units written to {out}")
    if unmatched:
        print(f"{len(unmatched)} unmatched:")
        for u in unmatched:
            print("  ", u)


if __name__ == "__main__":
    main()
