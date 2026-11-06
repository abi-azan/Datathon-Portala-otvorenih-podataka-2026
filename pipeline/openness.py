"""Openness layer from the data.gov.hr CKAN API: what each unit publishes on the portal.

For every unit: number of datasets, last update, share of machine-readable resources
and a link to its newest budget dataset. All of it comes from package_search, paged,
so the layer is a direct use of the portal API and refreshes with every build.
"""
import json
import os
import re
import time

import pandas as pd
import requests

from . import config, sources
from .units import match_key, norm_name, slugify

MACHINE_READABLE = {"CSV", "XLSX", "XLS", "JSON", "XML", "ODS", "GEOJSON", "API", "SHP", "ZIP"}
PAGE = 1000
LOG_PREFIX = "ckan_package_search_"
MIN_SHARE = 0.8   # a fresh count under 80 % of the saved one means a half-built search index

# county abbreviations used in portal organization titles, e.g. "Općina Privlaka (ZD)"
COUNTY_ABBR = {"ZG": 1, "KZ": 2, "SK": 3, "SM": 3, "KA": 4, "VZ": 5, "KC": 6, "KK": 6, "BJ": 7, "BB": 7,
               "RI": 8, "PG": 8, "GS": 9, "LS": 9, "VT": 10, "VP": 10, "PZ": 11, "PS": 11, "SB": 12, "BP": 12,
               "ZD": 13, "OS": 14, "OB": 14, "SI": 15, "VU": 16, "VS": 16, "ST": 17, "SD": 17,
               "PU": 18, "IS": 18, "DU": 19, "DN": 19, "CK": 20, "ME": 20}


def fold(s):
    """Diacritic-insensitive key: the portal writes "Konjšćina", MF writes "KONJŠČINA"."""
    return slugify(s)


def _page_dest(start):
    return config.RAW / "ckan" / f"package_search_{start:05d}.json"


def _read_pages():
    """Datasets from the pages saved by an earlier build, or None if they are missing or empty."""
    pages, start = [], 0
    while True:
        try:
            body = json.loads(_page_dest(start).read_text(encoding="utf-8"))["result"]
        except (OSError, ValueError, KeyError):
            return None
        pages.extend(body["results"])
        start += PAGE
        if start >= body["count"]:
            return pages or None


def _download(min_count):
    """Fetch every page; None if the portal fails or answers with fewer than min_count datasets."""
    pages, start = [], 0
    while True:
        dest = _page_dest(start)
        url = f"{config.CKAN}package_search?rows={PAGE}&start={start}&sort=name%20asc"
        try:
            sources.fetch(f"{LOG_PREFIX}{start:05d}", url, dest,
                          meta={"publisher": "data.gov.hr (CKAN API v3)", "api": "package_search"})
            body = json.loads(dest.read_text(encoding="utf-8"))["result"]
            count, results = body["count"], body["results"]
        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"  package_search od {start}: neispravan odgovor ({type(e).__name__}: {e})")
            return None
        if count < min_count or not results:
            print(f"  package_search od {start}: {count} skupova, {len(results)} na stranici "
                  f"(očekuje se barem {min_count})")
            return None
        pages.extend(results)
        start += PAGE
        if start >= count:
            return pages


def fetch_packages(offline=False, tries=4, wait=30):
    """All portal datasets, raw pages saved under data/raw/ckan/ (one file per page).

    While the portal rebuilds its search index, package_search answers with no datasets or only
    part of them (6.11.2026 at 1 h: count 0, and the CI build stopped). Such an answer, or an HTTP
    error, is retried. If the portal is still wrong after `tries` attempts, the pages and log
    entries of the previous build are put back and used, so the "Izvori" page keeps the date the
    data really comes from. A fresh count below MIN_SHARE of the saved one counts as wrong."""
    saved = _read_pages()
    if offline and saved:
        return saved
    backup = {p: p.read_bytes() for p in (config.RAW / "ckan").glob("package_search_*.json")} if saved else {}
    entries = sources.log_entries(LOG_PREFIX) if saved else {}
    min_count = max(1, int(MIN_SHARE * len(saved))) if saved else 1
    for attempt in range(tries):
        pages = _download(min_count)
        if pages:
            return pages
        if attempt < tries - 1:
            time.sleep(wait * (attempt + 1))
    if not saved:
        raise RuntimeError(f"data.gov.hr package_search nije vratio skupove ni nakon {tries} pokušaja, "
                           "a spremljene kopije nema")
    for p in (config.RAW / "ckan").glob("package_search_*.json"):
        if p not in backup:
            p.unlink()
    for p, data in backup.items():
        p.write_bytes(data)
    sources.restore_log_entries(LOG_PREFIX, entries)
    when = max((e.get("retrieved") or "" for e in entries.values()), default="?")
    msg = (f"data.gov.hr package_search ni nakon {tries} pokušaja ne vraća ispravan popis; "
           f"koristi se spremljena kopija od {when} ({len(saved)} skupova)")
    print(f"::warning::{msg}" if os.environ.get("GITHUB_ACTIONS") else f"  UPOZORENJE: {msg}")
    return saved


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
