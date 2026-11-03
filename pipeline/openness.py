"""Openness layer from the data.gov.hr CKAN API: what each unit publishes on the portal.

For every unit: number of datasets, last update, share of machine-readable resources
and a link to its newest budget dataset. All of it comes from package_search, paged,
so the layer is a direct use of the portal API and refreshes with every build.
"""
import json
import re

import pandas as pd

from . import config, sources
from .units import match_key, norm_name, slugify

MACHINE_READABLE = {"CSV", "XLSX", "XLS", "JSON", "XML", "ODS", "GEOJSON", "API", "SHP", "ZIP"}
PAGE = 1000

# county abbreviations used in portal organization titles, e.g. "Općina Privlaka (ZD)"
COUNTY_ABBR = {"ZG": 1, "KZ": 2, "SK": 3, "SM": 3, "KA": 4, "VZ": 5, "KC": 6, "KK": 6, "BJ": 7, "BB": 7,
               "RI": 8, "PG": 8, "GS": 9, "LS": 9, "VT": 10, "VP": 10, "PZ": 11, "PS": 11, "SB": 12, "BP": 12,
               "ZD": 13, "OS": 14, "OB": 14, "SI": 15, "VU": 16, "VS": 16, "ST": 17, "SD": 17,
               "PU": 18, "IS": 18, "DU": 19, "DN": 19, "CK": 20, "ME": 20}


def fold(s):
    """Diacritic-insensitive key: the portal writes "Konjšćina", MF writes "KONJŠČINA"."""
    return slugify(s)


def fetch_packages(offline=False):
    """All portal datasets, raw pages saved under data/raw/ckan/ (one file per page)."""
    pages, start = [], 0
    while True:
        dest = config.RAW / "ckan" / f"package_search_{start:05d}.json"
        url = f"{config.CKAN}package_search?rows={PAGE}&start={start}&sort=name%20asc"
        if not (offline and dest.exists()):
            sources.fetch(f"ckan_package_search_{start:05d}", url, dest,
                          meta={"publisher": "data.gov.hr (CKAN API v3)", "api": "package_search"})
        body = json.loads(dest.read_text(encoding="utf-8"))["result"]
        pages.extend(body["results"])
        start += PAGE
        if start >= body["count"]:
            return pages


def _org_unit_key(title):
    """Organization title -> (vrsta, folded key, county id or None), or None if not a local unit."""
    t = norm_name(title.replace("\xa0", " "))
    zup = None
    mm = re.search(r"\s*\(([A-ZČŠŽ]{2})\)$", t)
    if mm:
        zup = COUNTY_ABBR.get(fold(mm.group(1)).upper())
        t = t[:mm.start()]
    if t.endswith("ŽUPANIJA") and not t.startswith(("ŽUPANIJSKI", "URED ")):
        return "zupanija", fold(t), zup
    if t.startswith("GRAD "):
        return "grad", fold(match_key(t)), zup
    if t.startswith("OPĆINA "):
        return "opcina", fold(match_key(t)), zup
    return None


def build_openness(units, packages):
    """units: the šifrarnik (build_units output). Returns one row per unit."""
    lookup = {}
    for u in units.itertuples():
        k = (u.vrsta, fold(u.naziv) if u.vrsta == "zupanija" else fold(match_key(u.naziv_mf)))
        lookup.setdefault(k, []).append((u.zup_id, u.oib))
    per_org = {}
    for p in packages:
        org = p.get("organization") or {}
        if not org.get("title"):
            continue
        d = per_org.setdefault(org["name"], {"title": org["title"], "pkgs": []})
        d["pkgs"].append(p)
    rows, unmatched = [], []
    for name, d in per_org.items():
        k = _org_unit_key(d["title"])
        if k is None:
            continue
        cands = lookup.get(k[:2], [])
        if k[2] is not None:
            cands = [c for c in cands if c[0] == k[2]]
        if len(cands) != 1:
            unmatched.append(d["title"])
            continue
        oib = cands[0][1]
        pk = d["pkgs"]
        fmts = [(r.get("format") or "").upper().strip(".") for p in pk for r in p.get("resources", [])]
        budget = [p for p in pk if re.search(r"proračun|proracun", (p.get("title") or "").lower())]
        budget.sort(key=lambda p: p.get("metadata_modified") or "", reverse=True)
        rows.append({
            "oib": oib,
            "ckan_org": name,
            "ckan_org_naziv": d["title"].strip(),
            "portal_skupova": len(pk),
            "portal_zadnje_azuriranje": max((p.get("metadata_modified") or "")[:10] for p in pk),
            "portal_resursa": len(fmts),
            "portal_strojno_citljivo": round(sum(f in MACHINE_READABLE for f in fmts) / len(fmts), 3) if fmts else None,
            "portal_skupova_proracun": len(budget),
            "portal_url_org": f"https://data.gov.hr/ckan/organization/{name}",
            "portal_url_proracun": f"https://data.gov.hr/ckan/dataset/{budget[0]['name']}" if budget else None,
        })
    df = pd.DataFrame(rows)
    # an organization can appear twice (old and new account); keep the bigger one
    df = df.sort_values("portal_skupova", ascending=False).drop_duplicates("oib")
    out = units[["oib"]].merge(df, on="oib", how="left")
    out["portal_skupova"] = out["portal_skupova"].fillna(0).astype(int)
    out["portal_objavljuje"] = out["portal_skupova"] > 0
    return out, sorted(set(unmatched))
