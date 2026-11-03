"""Static API for the web app and for anyone else: web/public/api/v1/.

    .venv/Scripts/python -m pipeline.publish     # after pipeline.build

  jedinice.json            index of all 576 units: names, codes, grade and points per year
  jedinice/<slug>.json     full profile: every year's results, fact pack, peer medians,
                           neighbours, openness layer, template explanation
  skupine.json             peer-group medians per year (points and the five indicators)
  geo/jls.topo.json        boundaries (layers jls, zupanije)
  sifrarnik.csv            unit register: OIB, RKP, DGU/DZS code, name, type, county, slug
  rezultati.csv            one row per unit and year: grade, points, I1-I5, S1-S5, flags
  izvori.json              provenance of every download: URL, time, ETag, sha256, CKAN metadata
  skupovi.json             every dataset the project uses (data/reference/skupovi.csv): publisher,
                           link, licence, access, role, plus last download and sha256
  openapi.json             OpenAPI 3.1 description of all of the above (pipeline/openapi.py)

The files are generated, not committed: CI builds them before deploying the site.
The same run rewrites docs/skupovi-podataka.md, the dataset table for the submission.
"""
import csv
import json
import math
import re
import shutil
import sys
from datetime import datetime, timezone

import pandas as pd

from . import config, explain, facts, openapi, verify

API = config.ROOT / "web" / "public" / "api" / "v1"
DATASETS = config.REFERENCE / "skupovi.csv"
DATASETS_DOC = config.ROOT / "docs" / "skupovi-podataka.md"


def clean(x):
    if isinstance(x, float):
        return None if (math.isnan(x) or math.isinf(x)) else round(x, 6)
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    if hasattr(x, "item"):                      # numpy scalars
        return clean(x.item())
    return x


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean(obj), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def group_medians(res):
    """skupine.json from the same medians the fact packs use (facts.peer_medians)."""
    med = facts.peer_medians(res).reset_index()
    out = {}
    for r in med.to_dict("records"):
        out.setdefault(r["skupina"], {})[str(int(r["year"]))] = {c: r[c] for c in med.columns if c not in ("skupina", "year")}
    return out


def explanation(pack):
    """Template text until the AI texts exist; always shipped with its number check."""
    if not pack:
        return None
    text = explain.template(pack)
    return {"tekst": text, "izvor": "predlozak", "provjera": verify.verify(text, pack)}


def read_datasets():
    with open(DATASETS, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def datasets(rows, log):
    """skupovi.json: the dataset list plus download time and sha256 from the provenance log.

    A source fetched in pages (ckan_package_search_00000, _01000, ...) is one dataset:
    the latest download time, the summed size and one sha256 per page."""
    out = []
    for r in rows:
        rec = {k: (v or None) for k, v in r.items()}
        rec["koristi_se"] = r["koristi_se"] == "da"
        hits = [v for k, v in sorted(log.items()) if re.sub(r"_\d{5}$", "", k) == r["kljuc"]]
        if hits:
            rec["zadnje_preuzimanje"] = max(h["retrieved"] for h in hits)
            rec["zadnja_provjera"] = max(h.get("checked") or h["retrieved"] for h in hits)
            rec["bajtova"] = sum(h["bytes"] for h in hits)
            rec["sha256"] = hits[0]["sha256"] if len(hits) == 1 else [h["sha256"] for h in hits]
            if len(hits) > 1:
                rec["stranica"] = len(hits)
        out.append(rec)
    return out


def datasets_markdown(rows):
    """docs/skupovi-podataka.md: the dataset table for the submission, from the same CSV."""
    def cell(s):
        return (s or "").replace("|", "\\|").replace("\n", " ")

    def table(rs):
        lines = ["| Naziv | Izdavatelj | Poveznica | Licenca | Način pristupa | Čemu služi |",
                 "|---|---|---|---|---|---|"]
        for r in rs:
            direct = "poziv API-ja" if r["pristup"].startswith("API") else {
                "vektorske pločice": "stil karte", "model": "model"}.get(r["pristup"], "datoteka")
            links = f"[{direct}]({r['url']})"
            if r["portal_url"]:
                links = f"[stranica skupa]({r['portal_url']}), " + links
            lines.append("| " + " | ".join(cell(x) for x in (
                r["naziv"], r["izdavatelj"], links, r["licenca"], r["pristup"], r["uloga"])) + " |")
        return "\n".join(lines)

    used = [r for r in rows if r["koristi_se"] == "da"]
    planned = [r for r in rows if r["koristi_se"] != "da"]
    parts = [
        "# Korišteni skupovi podataka",
        "",
        "> Ova datoteka se generira. Izvor je `data/reference/skupovi.csv`, a piše je "
        "`python -m pipeline.publish`. Izmjene upisati u CSV, ne ovdje.",
        "",
        "Popis svih skupova podataka koje Fiskalna karta JLS koristi, s izdavateljem, poveznicom i licencom. "
        "Isti popis je u otvorenom API-ju kao `api/v1/skupovi.json`, uz vrijeme zadnjeg preuzimanja i sha256. "
        "Za izvore koje ETL preuzima sam, cijeli zapis preuzimanja (URL, vrijeme, ETag, sha256) je u "
        "`api/v1/izvori.json`.",
        "",
        f"## Korišteno ({len(used)})",
        "",
        table(used),
        "",
        "Napomene:",
        "",
        "- Otvorena dozvola traži navođenje izvora, datuma preuzimanja i izmjena. Izvor i datum su u "
        "`izvori.json`. Izmjene: podatke smo spojili po jedinici, preračunali u pokazatelje, a granice "
        "pojednostavili (mapshaper).",
        "- Ministarstvo financija ne navodi licencu za ove datoteke i ne objavljuje ih na data.gov.hr. "
        "Koristimo ih kao javne informacije prema Zakonu o pravu na pristup informacijama (ZPPI; NN 25/13, "
        "85/15, 69/22), uz navođenje izvora.",
        "- Upravne jedinice i indeks razvijenosti preuzeti su jednom. Iz njih je složena "
        "`data/reference/jls_master.csv`, a ETL ih ne preuzima pri svakom pokretanju.",
    ]
    if planned:
        parts += ["", f"## Planirano, još nije u kodu ({len(planned)})", "", table(planned)]
    return "\n".join(parts) + "\n"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    units = pd.read_csv(config.BUILD / "units.csv", dtype={"oib": str, "sifra": str, "rkp": str})
    res = pd.read_parquet(config.BUILD / "results.parquet")
    nested = {u["oib"]: u for u in json.loads((config.BUILD / "results.json").read_text(encoding="utf-8"))}
    susjedi = json.loads((config.BUILD / "geo" / "susjedi.json").read_text(encoding="utf-8"))
    packs = {p["oib"]: p for p in facts.build_all(units, res, config.LAST_YEAR)}
    by_code = units.set_index("sifra")
    if API.exists():
        shutil.rmtree(API)

    index = []
    for u in units.to_dict("records"):
        years = nested[u["oib"]]["godine"]
        index.append({
            "oib": u["oib"], "sifra": u["sifra"], "slug": u["slug"], "naziv": u["naziv"], "vrsta": u["vrsta"],
            "zup_id": u["zup_id"], "zupanija": u["zupanija"], "stanovnici": u["stanovnici_2021"],
            "skupina": u["skupina"],
            "ocjena": {y: r["ocjena"] for y, r in years.items()},
            "bodovi": {y: r["bodovi"] for y, r in years.items()},
            "uprava_pc": years[str(config.LAST_YEAR)]["uprava_pc"],
            "udio_tekucih_pomoci": years[str(config.LAST_YEAR)]["udio_tekucih_pomoci"],
        })
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    write(API / "jedinice.json", {"generirano": generated, "zadnja_godina": config.LAST_YEAR, "jedinice": index})
    write(API / "skupine.json", group_medians(res))

    for u in units.to_dict("records"):
        n = nested[u["oib"]]
        nb = susjedi.get(u["sifra"], {"kopno": {}, "more": {}})
        neighbours = [{"slug": by_code.loc[c, "slug"], "naziv": by_code.loc[c, "naziv"], "vrsta": vrsta, "km": km}
                      for vrsta in ("kopno", "more") for c, km in nb[vrsta].items()]
        pack = packs.get(u["oib"])
        detail = {k: v for k, v in n.items() if k != "godine"}
        detail.update({
            "godine": n["godine"],
            "susjedi": neighbours,
            "cinjenice": pack,
            "objasnjenje": explanation(pack),
        })
        write(API / "jedinice" / f"{u['slug']}.json", detail)

    (API / "geo").mkdir(parents=True, exist_ok=True)
    shutil.copy(config.BUILD / "geo" / "jls.topo.json", API / "geo" / "jls.topo.json")

    reg_cols = ["oib", "rkp", "sifra", "naziv", "vrsta", "zup_id", "zupanija", "slug", "stanovnici_2021"]
    units[reg_cols].to_csv(API / "sifrarnik.csv", index=False, encoding="utf-8")
    res_cols = ["oib", "naziv", "year", "ocjena", "ocjena_rijec", "bodovi", "bodovi_bez_ogranicenja", "ogranicenje_do",
                "skupina", "rang", "n_skupine", *[f"I{i}" for i in range(1, 6)], *[f"S{i}" for i in range(1, 6)],
                "DO", "DO_iskazano", "zastavice", "kvaliteta"]
    out = res[res_cols].rename(columns={"year": "godina"}).sort_values(["oib", "godina"])
    out = out.replace([math.inf, -math.inf], float("nan"))   # I3 is infinite for debt without operating surplus
    out.to_csv(API / "rezultati.csv", index=False, encoding="utf-8", float_format="%.10g")
    shutil.copy(config.SOURCES_LOG, API / "izvori.json")
    rows = read_datasets()
    write(API / "skupovi.json", datasets(rows, json.loads(config.SOURCES_LOG.read_text(encoding="utf-8"))))
    DATASETS_DOC.write_text(datasets_markdown(rows), encoding="utf-8", newline="\n")
    write(API / "openapi.json", openapi.spec(generated))
    size = sum(p.stat().st_size for p in API.rglob("*") if p.is_file())
    print(f"Statični API: {API} ({len(index)} jedinica, {size / 1e6:.1f} MB)")
    n_used = sum(r["koristi_se"] == "da" for r in rows)
    print(f"Skupovi podataka: {n_used} korištenih, {len(rows) - n_used} planiranih -> {DATASETS_DOC.name}")


if __name__ == "__main__":
    main()
