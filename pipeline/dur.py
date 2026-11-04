"""State Audit Office layer (PLAN §6 SHOULD, decision 12): the latest financial audit of each unit.

    .venv/Scripts/python -m pipeline.dur      # writes data/reference/dur_revizije.json (PDFs cached in data/raw/dur/)

The Državni ured za reviziju (DUR) lists its reports as HTML, 40 per page, per publication year
(https://www.revizija.hr/izvjesca/10?godinaID=<id>&page=N). The links are Windows-style paths whose
folders say what a report is: financial audits of local units sit under FIN_REVIZIJE or
FINANCIJSKE_REVIZIJE, then LOKALNE_JEDINICE or JLPRS, then OPCINE / GRADOVI / ZUPANIJE (2019:
LOKALNE_JEDINICE/POJEDINACNA_IZVJESCA/...). Follow-up checks (PROVJERE...), budget users and
companies are skipped.

For each unit only the newest report is downloaded. Its text gives the opinion (bezuvjetno,
uvjetno, nepovoljno, or suzdržavanje od izražavanja mišljenja) and the audited year, which is not
the publication year. The result is shown on the profile with a link to the report; a unit
without a financial audit since 2019 says so.
"""
import json
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from urllib.parse import quote

import pandas as pd
import requests

from . import config, sources
from .units import slugify

SITE = "https://www.revizija.hr/"
LIST = SITE + "izvjesca/10?pojamIzvjesce=&godinaID={id}&page={page}"
YEAR_IDS = {2026: 3164, 2025: 3035, 2024: 2901, 2023: 2810, 2022: 2686, 2021: 1465, 2020: 1275, 2019: 1276}
RAW = config.RAW / "dur"
# committed like data/ai: scraping about 300 MB of PDFs on every CI run would be wasteful
OUT = config.REFERENCE / "dur_revizije.json"

LINK = re.compile(r"UserDocsImages[^'\"<>]*?\.pdf", re.IGNORECASE)
# 2020-2026: ...\FIN_REVIZIJE or FINANCIJSKE_REVIZIJE\LOKALNE_JEDINICE or JLPRS\OPCINE\<name>.pdf
# 2019:      ...\Revizije - 2019\LOKALNE_JEDINICE\POJEDINACNA_IZVJESCA\GRADOVI\<name>.pdf
PATH = re.compile(r"\\(?:(?:FIN_REVIZIJE|FINANCIJSKE_REVIZIJE)\\(?:LOKALNE_JEDINICE|JLPRS)"
                  r"|Revizije - 2019\\LOKALNE_JEDINICE\\POJEDINACNA_IZVJESCA)\\"
                  r"(OPCINE|OPĆINE|GRADOVI|ZUPANIJE|ŽUPANIJE)\\([^\\]+)\.pdf$", re.IGNORECASE)
KIND = {"opcine": "opcina", "gradovi": "grad", "zupanije": "zupanija"}
OPINIONS = [("nepovoljno", re.compile(r"nepovoljno\s+mi[sš]ljenje")),
            ("suzdržano", re.compile(r"suzdr[zž]a\w*\s+od\s+izra[zž]avanja\s+mi[sš]ljenja")),
            ("uvjetno", re.compile(r"(?<!bez)uvjetno\s+mi[sš]ljenje")),
            ("bezuvjetno", re.compile(r"bezuvjetno\s+mi[sš]ljenje"))]
# the audited year: the report title ("...o obavljenoj financijskoj reviziji grada Bjelovara za 2018."),
# else the first "za 2023. godinu"
AUDITED = [re.compile(r"financijsk\w*\s+revizij\w*[^.]{0,120}?\bza\s+(20[12]\d)\.", re.IGNORECASE),
           re.compile(r"za\s+(20[12]\d)\.\s*godin", re.IGNORECASE)]


def _fold(s):
    s = unicodedata.normalize("NFKD", s.replace("Đ", "DJ").replace("đ", "dj")).encode("ascii", "ignore").decode()
    return s.lower()


def _key(name, kind):
    """Comparable key of a report file name or a unit name: no type word, no diacritics, Đ = DJ,
    underscores as spaces, and for towns and municipalities only the first part of a bilingual
    name ("Vodnjan – Dignano")."""
    n = _fold(re.sub(r"[–—]", "-", name)).replace("_", " ")    # folding would drop the en dash
    n = re.sub(r"^(opcina|grad)\s+", "", n)
    if kind == "zupanija":
        n = re.sub(r"\s+zupanija$|^zupanija\s+", "", n)
        return slugify(n.replace("dj", "d"))              # "Bjelovarsko-bilogorska" keeps its hyphen
    n = re.split(r"\s*[-–—]\s*|,", n)[0]
    return slugify(n.replace("dj", "d"))


def list_reports(session, pause=0.5):
    """Every financial-audit report of a local unit: (publication year, kind, file name, path)."""
    out = []
    for year, yid in sorted(YEAR_IDS.items()):
        seen, page = set(), 1
        while True:
            html = session.get(LIST.format(id=yid, page=page), timeout=60).text
            new = [p for p in (m.group(0) for m in LINK.finditer(html)) if p not in seen]
            if not new:
                break
            seen |= set(new)
            for path in new:
                m = PATH.search(path)
                if m and "PROVJER" not in path.upper():
                    out.append((year, KIND[_fold(m.group(1))], m.group(2).strip(), path))
            page += 1
            time.sleep(pause)
    return out


def url_of(path):
    return SITE + quote(path.replace("\\", "/"))


def _download(session, year, name, path):
    """The report PDF, from the cache in data/raw/dur/<year>/ or downloaded once."""
    dest = RAW / str(year) / (slugify(name) + ".pdf")
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        r = session.get(url_of(path), timeout=120)
        r.raise_for_status()
        dest.write_bytes(r.content)
        time.sleep(0.3)
    return dest


def _text(pdf_path, max_pages):
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    return " ".join((p.extract_text() or "") for p in reader.pages[:max_pages])


def read_opinion(pdf_path, max_pages=8):
    """(opinion, audited year) from the first pages of a report; None where not found."""
    text = re.sub(r"\s+", " ", _text(pdf_path, max_pages).replace("-\n", "")).lower()
    hits = [(m.start(), name) for name, rx in OPINIONS for m in [rx.search(text)] if m]
    opinion = min(hits)[1] if hits else None            # the first opinion stated in the report
    year = next((m for rx in AUDITED for m in [rx.search(text)] if m), None)
    return opinion, int(year.group(1)) if year else None


def match(reports, units):
    """{oib: (year, name, path)} of each unit's newest report, matched by type and name key, and
    the reports that did not match exactly one unit, with their candidates."""
    by_key, first = {}, {}
    for u in units.itertuples():
        k = _key(u.naziv, u.vrsta)
        by_key.setdefault((u.vrsta, k), []).append(u)
        first.setdefault((u.vrsta, k.split("-")[0]), []).append(u)
    best, ambiguous = {}, {}
    for year, kind, name, path in reports:
        key = _key(name, kind)
        cands = by_key.get((kind, key)) or first.get((kind, key.split("-")[0]), [])
        if len(cands) != 1:                              # main() reads the county from the PDF
            ambiguous[(year, kind, name, path)] = cands
            continue
        o = cands[0].oib
        if o not in best or year > best[o][0]:
            best[o] = (year, name, path)
    return best, ambiguous


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    units = pd.read_csv(config.BUILD / "units.csv", dtype={"oib": str, "sifra": str, "rkp": str})
    session = requests.Session()
    session.headers.update(sources.UA)
    reports = list_reports(session)
    print(f"DUR: {len(reports)} financijskih revizija jedinica na popisima {min(YEAR_IDS)}.-{max(YEAR_IDS)}.")
    best, ambiguous = match(reports, units)
    # a name two units share (Privlaka in Zadarska and Vukovarsko-srijemska): the county in the report
    for (year, kind, name, path), cands in sorted(ambiguous.items()):
        if len(cands) < 2:
            continue
        text = _fold(_text(_download(session, year, name, path), 3))
        hit = [u for u in cands if _fold(u.zupanija.replace(" županija", "")) in text]
        if len(hit) == 1 and (hit[0].oib not in best or year > best[hit[0].oib][0]):
            best[hit[0].oib] = (year, name, path)
    unmatched = sorted({(k, n) for (y, k, n, p), c in ambiguous.items() if len(c) < 2})
    print(f"  spojeno s {len(best)} jedinica; nespojeno {len(unmatched)}: {unmatched[:12]}")
    out = {}
    for i, (oib, (year, name, path)) in enumerate(sorted(best.items()), 1):
        dest = _download(session, year, name, path)
        try:
            opinion, audited = read_opinion(dest)
        except Exception as e:                           # a broken PDF: keep the link, no opinion
            print(f"  {name}: {e!r}")
            opinion, audited = None, None
        out[oib] = {"objavljeno": year, "revidirana_godina": audited, "misljenje": opinion, "url": url_of(path)}
        if i % 25 == 0:
            print(f"  {i}/{len(best)}", flush=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    counts = pd.Series([v["misljenje"] for v in out.values()]).value_counts(dropna=False).to_dict()
    print(f"DUR -> {OUT}: {len(out)} jedinica, mišljenja {counts}")
    # one provenance entry for the whole layer (the list pages and the PDFs it read)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    log = sources._log()
    log["dur_revizije"] = {"url": SITE + "izvjesca/10", "file": str(OUT.relative_to(config.ROOT)).replace("\\", "/"),
                           "retrieved": now, "checked": now, "bytes": OUT.stat().st_size,
                           "sha256": sources._sha256(OUT), "izvjesca": len(reports), "pdf": len(out)}
    sources._save_log(log)


if __name__ == "__main__":
    main()
