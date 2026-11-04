"""Visible number check (PLAN §5): where every number of the five indicators comes from.

For each unit, jedinice/<slug>/izvor.json (written by publish.py) holds, for the last year:
- each indicator I1-I5 with its formula, its value and the auxiliary quantities it uses;
- each auxiliary quantity (PLAN §3.1: KP, PO, OS, principal, ND, SD, ZO, DO) per year of the
  window, with its formula;
- every input amount: account, year, amount and where it sits in the Ministry of Finance files
  (PR-RAS: workbook in the ZIP, sheet and Excel row; Bilanca: workbook, sheet (year), row and
  column).

The page shows the formula and the table of inputs behind each component, not a single cell
(plan-srijeda, W11). tests/test_provenance.py recomputes I1-I5 from these inputs alone and
compares them with the published results, so the explanation cannot drift from the numbers.
"""
import math
import re

import openpyxl
import pandas as pd

from . import config, methodology

YEARS = [config.LAST_YEAR - k for k in range(len(methodology.WINDOW_WEIGHTS))]   # t, t-1, t-2, t-3
WEIGHTS = dict(zip(YEARS, methodology.WINDOW_WEIGHTS))
ALL_YEARS = sorted(set(YEARS) | {min(YEARS) - 1})      # ZO of t-1 enters I4 for the first window year

PRRAS_FILE = "Lokalci FINALI 2019 2024 EURO.zip"     # MF ZIP (config.MF_PRRAS_ZIP)
BILANCA_FILE = "Bilanca_2019_do_2025_R22_EURO.xlsx"  # MF workbook (config.MF_BILANCA)

KP = "+".join(config.CAPITAL_GRANTS)
QUANTITIES = {
    "KP": f"kapitalne pomoći i donacije u razredu 6: {KP.replace('+', ' + ')}",
    "PO": "6 − KP (tekući prihodi)",
    "OS": "PO − 3 (operativni saldo)",
    "glavnica": "54 (otplata glavnice); kod refinanciranja 54 − 84",
    "ND": "max(0, 26 + 25 − 11) na kraju godine (neto dug, Bilanca)",
    "SD": "341 + 342 + glavnica (servis duga)",
    "ZO": "6 + 7 − 63 + 6353 − 663 − dio 611 (zakonska osnovica, približno)",
    "DO": "23 D + 24 D + 26 D, bez kredita iskazanog kao dospio (pravilo 1)",
}
# result column of each quantity in results.parquet
COLUMN = {"KP": "KP", "PO": "PO", "OS": "OS", "glavnica": "glavnica_adj", "ND": "ND", "SD": "SD", "ZO": "ZO", "DO": "DO"}
INDICATORS = {
    "I1": ("Operativni saldo", "Σ w·OS / Σ w·PO", ["OS", "PO"]),
    "I2": ("Slobodni saldo", "(Σ w·OS − Σ w·glavnica) / Σ w·PO", ["OS", "glavnica", "PO"]),
    "I3": ("Godine otplate duga", "ND(t) / (Σ w·OS / Σ w); 0 kad nema neto duga", ["ND", "OS"]),
    "I4": ("Servis duga", "Σ w·SD(y) / Σ w·ZO(y − 1)", ["SD", "ZO"]),
    "I5": ("Dospjele obveze", "DO(t) / 3(t) (rashodi poslovanja)", ["DO"]),
}
# PR-RAS accounts the five indicators read, and the quantities they feed
PRRAS_USE = {
    "6": ["PO", "ZO"], "3": ["OS", "I5"], **{c: ["KP"] for c in config.CAPITAL_GRANTS},
    "54": ["glavnica"], "84": ["glavnica"], "341": ["SD"], "342": ["SD"],
    "7": ["ZO"], "63": ["ZO"], "6353": ["ZO"], "663": ["ZO"], "dio611": ["ZO"],
}
BILANCA_USE = {"11": ["ND"], "25": ["ND"], "26": ["ND"], "23_D": ["DO"], "24_D": ["DO"], "26_D": ["DO"]}
BILANCA_NAMES = {
    "11": "Novac u banci i blagajni",
    "25": "Obveze za vrijednosne papire",
    "26": "Obveze za kredite i zajmove",
    "23_D": "Obveze za rashode poslovanja, dospjele",
    "24_D": "Obveze za nabavu nefinancijske imovine, dospjele",
    "26_D": "Obveze za kredite i zajmove, dospjele",
}


def bilanca_cells(path):
    """{(year, oib): {code: (row, column letter)}} for the Bilanca columns above, located with the
    same header rules as mf.parse_bilanca (2025: "dio 26 D"; earlier: "dio 26" plus a second
    header row "- dospjele")."""
    out = {}
    if not path.exists():
        return out
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for sn in wb.sheetnames:
        year = int(sn)
        if year not in ALL_YEARS:
            continue
        it = wb[sn].iter_rows(values_only=True)
        h1 = [str(c).strip() if c is not None else "" for c in next(it)]
        h2 = [str(c).strip().lower() if c is not None else "" for c in next(it)]
        col = {}
        for i, c in enumerate(h1):
            if c in ("11", "25", "26"):
                col.setdefault(c, i)
            m = re.match(r"dio (\d\d)(?: ([DN]))?$", c)
            if m and m.group(1) in ("23", "24", "26"):
                part = m.group(2) or ("N" if "nedospjel" in h2[i] else "D" if "dospjel" in h2[i] else None)
                if part == "D":
                    col.setdefault(f"{m.group(1)}_D", i)
        letters = {k: openpyxl.utils.get_column_letter(i + 1) for k, i in col.items()}
        for n, r in enumerate(it, start=3):
            if not isinstance(r[0], (int, float)) or not r[2]:
                continue
            out[(year, str(r[2]).strip().zfill(11))] = {k: (n, letters[k]) for k in col}
    wb.close()
    return out


def _num(v):
    return None if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))) else float(v)


def build(units, prras, wide, res, bilanca_path=config.RAW / "mf" / "bilanca.xlsx"):
    """{oib: izvor dict} for every unit. units: units.csv; prras: prras_long; wide: wide.parquet;
    res: results.parquet."""
    cells = bilanca_cells(bilanca_path)
    pr = prras[prras.code.isin(PRRAS_USE) & prras.year.isin(ALL_YEARS)]
    pr = pr.merge(units[["oib", "zup_id", "naziv_mf"]], left_on=["zup_id", "sheet"], right_on=["zup_id", "naziv_mf"])
    pr_by = {o: g for o, g in pr.groupby("oib")}
    wd = {(r["oib"], int(r["year"])): r for r in wide[wide.year.isin(ALL_YEARS)].to_dict("records")}
    rs = {(r["oib"], int(r["year"])): r for r in res[res.year.isin(ALL_YEARS)].to_dict("records")}
    out = {}
    for u in units.to_dict("records"):
        o = u["oib"]
        last = rs.get((o, config.LAST_YEAR))
        if last is None:
            continue
        konta, ulazi = {}, []
        prr = pr_by[o].sort_values(["year", "row"]) if o in pr_by else pd.DataFrame(columns=pr.columns)
        sheet = {"datoteka": None, "list": None}
        for r in prr.to_dict("records"):
            sheet = {"datoteka": f"{PRRAS_FILE} / {r['file']}", "list": r["sheet"]}
            konta.setdefault(r["code"], {"naziv": r["label"], "izvor": "PR-RAS", "za": PRRAS_USE[r["code"]]})
            v = _num(r["value"])
            if v:                              # a zero changes no sum; leaving it out keeps the file small
                ulazi.append({"konto": r["code"], "godina": int(r["year"]), "iznos": round(v, 2), "redak": int(r["row"])})
        w = wd.get((o, config.LAST_YEAR))       # ND and DO are read at the end of year t only
        pos = cells.get((config.LAST_YEAR, o), {})
        for code, use in BILANCA_USE.items():
            k = code.replace("_", " ")
            konta[k] = {"naziv": BILANCA_NAMES[code], "izvor": "Bilanca", "za": use}
            v = _num(w.get(f"b_{code}")) if w is not None else None
            if v:
                row, letter = pos.get(code, (None, None))
                ulazi.append({"konto": k, "godina": config.LAST_YEAR, "iznos": round(v, 2), "redak": row, "stupac": letter})
        velicine = {}
        for q, formula in QUANTITIES.items():
            years = [config.LAST_YEAR] if q in ("ND", "DO") else ALL_YEARS if q in ("ZO", "KP", "PO") else YEARS
            velicine[q] = {"formula": formula,
                           "godine": {str(y): _num(rs[(o, y)][COLUMN[q]]) for y in years if (o, y) in rs}}
        velicine["glavnica"]["refinanciranje"] = {str(y): bool(rs[(o, y)]["refinanciranje"]) for y in YEARS if (o, y) in rs}
        velicine["DO"]["iskazano"] = _num(last["DO_iskazano"])
        velicine["DO"]["pravilo1_iskljuceno"] = _num(last["DO_iskazano"] - last["DO"])
        pokazatelji = {k: {"naziv": n, "formula": f, "vrijednost": _num(last[k]), "bodovi": _num(last[f"S{k[1]}"]),
                           "velicine": v} for k, (n, f, v) in INDICATORS.items()}
        out[o] = {"godina": config.LAST_YEAR,
                  "prozor": {"godine": [y for y in YEARS if (o, y) in rs], "ponderi": [WEIGHTS[y] for y in YEARS if (o, y) in rs]},
                  "pokazatelji": pokazatelji, "velicine": velicine,
                  "izvori": {"PR-RAS": sheet,
                             "Bilanca": {"datoteka": BILANCA_FILE, "list": str(config.LAST_YEAR)}},
                  "konta": konta, "ulazi": ulazi,
                  "napomena": "Iznosi su u eurima, iz izvještaja jedinica kako ih objavljuje Ministarstvo financija "
                              "(PR-RAS i Bilanca, razina 22). Konta s iznosom 0 nisu navedena. Formule su u "
                              "PLAN §3 i na stranici metodologije."}
    return out
