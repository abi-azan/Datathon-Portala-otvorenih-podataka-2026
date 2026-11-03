"""Parse the Ministry of Finance local-budget workbooks.

PR-RAS + RAS-funkcijski: one workbook per county (01-21), one sheet per unit, one row
per account or function ("Pozicija u obrascu" in column C), one column per year.
Workbook 22 holds the national totals. Bilanca: one sheet per year, one row per unit.

Every PR-RAS value keeps its workbook, sheet and Excel row, so the product can show
exactly where a number comes from.
"""
import re
import zipfile
from pathlib import Path

import openpyxl
import pandas as pd

from . import config

# Bump when parse_prras output changes; build.py then re-parses instead of using the cache.
PRRAS_PARSER_VERSION = 2

_ZIP_UTF8_FLAG = 0x800


def zip_member_name(name, flag_bits=0):
    """Readable name of a ZIP member.

    Without the UTF-8 flag, zipfile decodes member names as CP437. The MF ZIP is
    written in CP852 (Croatian DOS code page), so "Zagrebačka" comes out as
    "Zagrebaƒka". Re-decode as CP852; keep the name as given if that fails."""
    if flag_bits & _ZIP_UTF8_FLAG:
        return name
    try:
        return name.encode("cp437").decode("cp852")
    except UnicodeError:
        return name


def extract_prras(zip_path, out_dir):
    """Unpack the MF ZIP into out_dir/NN.xlsx (NN = county 01-22).

    Member names in the ZIP are CP852 without the UTF-8 flag, so files are chosen by
    the two-digit prefix only; the returned source names are fixed with
    zip_member_name. Osječko-baranjska (14) ships a corrected file next to the
    original; the correction wins."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        members = [m for m in z.namelist() if m.lower().endswith(".xlsx")]
        chosen = {}
        for m in members:
            base = m.rsplit("/", 1)[-1]
            mm = re.match(r"(\d\d) ", base)
            if not mm:
                continue
            nn = mm.group(1)
            if nn in chosen and "ispravak" not in base:
                continue
            chosen[nn] = m
        for nn, m in sorted(chosen.items()):
            target = out_dir / f"{nn}.xlsx"
            with z.open(m) as src, open(target, "wb") as dst:
                dst.write(src.read())
        names = {nn: zip_member_name(m, z.getinfo(m).flag_bits).rsplit("/", 1)[-1] for nn, m in chosen.items()}
    return {nn: out_dir / f"{nn}.xlsx" for nn in chosen}, names


def unit_type(sheet_name):
    if sheet_name.endswith("ŽUPANIJA"):
        return "zupanija"
    if sheet_name.startswith("GRAD "):
        return "grad"
    if sheet_name.startswith("OPĆINA "):
        return "opcina"
    return None


def _parse_sheet(ws, codes):
    """Yield (code, label, row_number, {year: value}) for the wanted codes."""
    year_col = {}
    for rn, r in enumerate(ws.iter_rows(values_only=True), start=1):
        if not year_col:
            for i, c in enumerate(r):
                mm = re.match(r"Ostvareno u (\d{4})", str(c or ""))
                if mm:
                    year_col[int(mm.group(1))] = i
            continue
        # the row under the header numbers the columns (1, 2, 3, ...); its "3" is not account 3
        if len(r) < 3 or r[2] is None or isinstance(r[1], (int, float)):
            continue
        code = str(r[2]).strip()
        if code not in codes:
            continue
        vals = {y: (float(r[i]) if i < len(r) and isinstance(r[i], (int, float)) else 0.0)
                for y, i in year_col.items()}
        yield code, str(r[1] or "").strip(), rn, vals


def parse_prras(files, source_names, codes=None):
    """Long table: zup_id, sheet, vrsta, code, label, year, value, file, row."""
    codes = set(codes or config.PRRAS_CODES)
    rows = []
    for nn, path in sorted(files.items()):
        if nn == "22":
            continue
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        for sn in wb.sheetnames:
            t = unit_type(sn)
            if t is None or sn.startswith(("UKUPNO", "SVEUKUPNO")):
                continue
            for code, label, rn, vals in _parse_sheet(wb[sn], codes):
                for y, v in vals.items():
                    rows.append((int(nn), sn, t, code, label, y, v, source_names[nn], rn))
        wb.close()
        print(f"    PR-RAS {nn}: ok", flush=True)
    return pd.DataFrame(rows, columns=["zup_id", "sheet", "vrsta", "code", "label", "year", "value", "file", "row"])


def parse_national(path, codes=("6", "3", "4", "R1"), sheet="SVEUKUPNO OPĆ_GRAD_ŽUPANIJA"):
    """National totals (all 576 units) from workbook 22: {(code, year): value}."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = {}
    for code, _label, _rn, vals in _parse_sheet(wb[sheet], set(codes)):
        for y, v in vals.items():
            out.setdefault((code, y), v)
    wb.close()
    return out


def parse_bilanca(path):
    """Wide table, one row per unit and year: zup_id, rkp, oib, naziv, year, b_<code>, b_<code>_D, b_<code>_N.

    2025 labels the overdue split "dio 23 D" / "dio 23 N". 2019-2024 label both
    columns "dio 23" and say "- dospjele" / "- nedospjele" in the second header row.
    Both layouts are read, so overdue liabilities exist for every year."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = []
    for sn in wb.sheetnames:
        year = int(sn)
        it = wb[sn].iter_rows(values_only=True)
        h1 = [str(c).strip() if c is not None else "" for c in next(it)]
        h2 = [str(c).strip().lower() if c is not None else "" for c in next(it)]
        col = {}
        for i, c in enumerate(h1):
            if c in config.BILANCA_CODES:
                col.setdefault(f"b_{c}", i)
            mm = re.match(r"dio (\d\d)(?: ([DN]))?$", c)
            if mm and mm.group(1) in config.BILANCA_SPLITS:
                part = mm.group(2)
                if part is None:
                    if "nedospjel" in h2[i]:
                        part = "N"
                    elif "dospjel" in h2[i]:
                        part = "D"
                if part:
                    col.setdefault(f"b_{mm.group(1)}_{part}", i)
        missing = [f"b_{c}_D" for c in config.BILANCA_SPLITS if f"b_{c}_D" not in col]
        if missing:
            raise ValueError(f"Bilanca {year}: overdue columns not found: {missing}")
        for r in it:
            if not isinstance(r[0], (int, float)) or not r[2]:
                continue
            rec = {"zup_id": int(r[0]), "rkp": str(r[1]).strip(), "oib": str(r[2]).strip().zfill(11),
                   "naziv_bilanca": str(r[3]).strip(), "year": year}
            for k, i in col.items():
                v = r[i] if i < len(r) else None
                rec[k] = float(v) if isinstance(v, (int, float)) else 0.0
            rows.append(rec)
    wb.close()
    return pd.DataFrame(rows)
