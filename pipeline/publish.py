"""Static API for the web app and for anyone else: web/public/api/v1/.

    .venv/Scripts/python -m pipeline.publish     # after pipeline.build
    .venv/Scripts/python -m pipeline.publish --ai other.json   # publish AI texts from another file

  jedinice.json            index of all 576 units: names, codes, grade and points per year
  jedinice/<slug>.json     full profile: every year's results, fact pack, peer medians,
                           neighbours, openness layer, explanation (AI text from
                           data/ai/objasnjenja-<year>.json when it still matches, else template)
  skupine.json             peer-group medians per year (points and the five indicators)
  geo/jls.topo.json        boundaries (layers jls, zupanije)
  simulator/zup-<id>.json  merger simulator: every group of 2-4 neighbouring units in the county
  reforma/prag-<N>.json    Karta reforme: every unit after the greedy merger scenario for the
                           threshold N = 2500, 5000, 10000 inhabitants (pipeline/reforma.py)
  sifrarnik.csv            unit register: OIB, RKP, DGU/DZS code, name, type, county, slug
  rezultati.csv            one row per unit and year: grade, points, I1-I5, S1-S5, flags
  izvori.json              provenance of every download: URL, time, ETag, sha256, CKAN metadata
  skupovi.json             every dataset the project uses (data/reference/skupovi.csv): publisher,
                           link, licence with its text and evidence, the publisher's last-change date,
                           access, role, plus last download and sha256
  openapi.json             OpenAPI 3.1 description of all of the above (pipeline/openapi.py)

The files are generated, not committed: CI builds them before deploying the site.
The same run rewrites docs/skupovi-podataka.md, the dataset table for the submission.
"""
import argparse
import csv
import json
import math
import re
import shutil
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

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


AI_TEXTS = explain.AI_DIR / f"objasnjenja-{config.LAST_YEAR}.json"


def load_ai_texts(path=AI_TEXTS):
    """{oib: entry} from data/ai/objasnjenja-<year>.json (pipeline.explain --import-batch), or {}."""
    path = Path(path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))["tekstovi"]


def explanation(pack, ai=None):
    """The unit's AI text when it was checked on Kaggle, was written from this very pack and
    passes the number check here too; otherwise the template. Always shipped with its check."""
    if not pack:
        return None
    if ai and ai.get("izvor") == "ai" and ai.get("pack_sha256") == explain.pack_sha256(pack):
        check = verify.verify(ai["tekst"], pack)
        if check["ok"]:
            return {"tekst": ai["tekst"], "izvor": "ai", "model": ai.get("model"), "provjera": check}
    text = explain.template(pack)
    return {"tekst": text, "izvor": "predlozak", "model": None, "provjera": verify.verify(text, pack)}


def read_datasets():
    with open(DATASETS, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def datasets(rows, log):
    """skupovi.json: the dataset list plus download time and sha256 from the provenance log.

    A source fetched in pages (ckan_package_search_00000, _01000, ...) is one dataset:
    the latest download time, the summed size and one sha256 per page.
    zadnja_izmjena comes from the server's Last-Modified when the log has one (the publisher's
    own date, newer than what the CSV says); otherwise it stays as typed into the CSV."""
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
            modified = [parsedate_to_datetime(h["last_modified"]) for h in hits if h.get("last_modified")]
            if modified:
                rec["zadnja_izmjena"] = max(modified).date().isoformat()
        out.append(rec)
    return out


SOURCE_STATEMENT = (
    "Sadrži informacije tijela javne vlasti u skladu s Otvorenom dozvolom (https://data.gov.hr/otvorena-dozvola): "
    "Ministarstvo financija, Državni zavod za statistiku, Državna geodetska uprava i Portal otvorenih podataka. "
    "Indeks razvijenosti: Ministarstvo regionalnoga razvoja i fondova Europske unije (razvoj.gov.hr). "
    "Poveznice na skupove i datumi zadnje izmjene: docs/skupovi-podataka.md. "
    "Izmjene: podaci su spojeni po jedinici i preračunati u pokazatelje, bodove i ocjene, a granice su "
    "pojednostavljene (mapshaper). Ocjene su izračun autora, a ne službena ocjena tih tijela."
)


def datasets_markdown(recs):
    """docs/skupovi-podataka.md: the dataset tables for the submission, from the records of skupovi.json."""
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
            lic = f"[{cell(r['licenca'])}]({r['licenca_url']})" if r.get("licenca_url") else cell(r["licenca"])
            lines.append("| " + " | ".join([cell(r["naziv"]), cell(r["izdavatelj"]), links, lic,
                                            cell(r["pristup"]), cell(r["uloga"])]) + " |")
        return "\n".join(lines)

    def evidence(rs):
        lines = ["| Skup | Gdje izdavatelj navodi licencu ili uvjete | Zadnja izmjena (prema izdavatelju) |",
                 "|---|---|---|"]
        for r in rs:
            proof = f"[{urlparse(r['licenca_dokaz']).netloc}]({r['licenca_dokaz']})" if r.get("licenca_dokaz") else ""
            lines.append(f"| {cell(r['naziv'])} | {proof} | {r.get('zadnja_izmjena') or '—'} |")
        return "\n".join(lines)

    used = [r for r in recs if r["koristi_se"]]
    planned = [r for r in recs if not r["koristi_se"]]
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
    ]
    if planned:
        parts += ["", f"## Planirano, još nije u kodu ({len(planned)})", "", table(planned)]
    parts += [
        "",
        "## Licence: dokaz i datum zadnje izmjene",
        "",
        "Provjereno 4.11.2026. Datum za datoteke MF-a dolazi automatski iz zaglavlja Last-Modified "
        "(`izvori.json`). Za ostale je to datum revizije ili metapodataka koji navodi izdavatelj. Katalog "
        "portala i OSM mijenjaju se stalno, pa za njih vrijedi stanje pri preuzimanju.",
        "",
        evidence(recs),
        "",
        "## Izjava o izvoru",
        "",
        "Otvorena dozvola (t. II. i III.) i Pravilnik NN 67/17 (čl. 5.) traže: naziv tijela, poveznicu na skup, "
        "datum zadnje izmjene, oznaku i poveznicu na Otvorenu dozvolu te naznaku izmjena. Tijela nisu propisala "
        "vlastitu izjavu, pa koristimo rečenicu iz dozvole. Ista izjava je u podnožju aplikacije i u "
        "`LICENSE-DATA.md`:",
        "",
        "> " + SOURCE_STATEMENT,
        "",
        "## Napomene",
        "",
        "- **Ministarstvo financija** ne navodi licencu i ove datoteke ne objavljuje na data.gov.hr. Stranica "
        "\"Uvjeti korištenja\" na mfin.gov.hr je prazna. Pravna osnova za ponovnu uporabu:",
        "  - ZPPI (NN 25/13, 85/15, 69/22), čl. 27. st. 1.: svaki korisnik ima pravo na ponovnu uporabu "
        "informacija u komercijalne ili nekomercijalne svrhe;",
        "  - ZPPI, čl. 31. st. 1.: tijelo daje podatke za ponovnu uporabu bez ograničenja i za slobodnu uporabu;",
        "  - Pravilnik o vrstama i sadržaju dozvola (NN 67/17), čl. 4. st. 1.: informacije za ponovnu uporabu "
        "dostupne su uz Otvorenu dozvolu. Druge uvjete tijelo mora objaviti na svojoj stranici (čl. 6.), a MF "
        "ih nije objavio. Zato poštujemo uvjete Otvorene dozvole;",
        "  - objavljena izvješća su službeni tekstovi, koji nakon objave nisu zaštićeni autorskim pravom "
        "(ZAPSP, NN 111/21, čl. 18. st. 3.).",
        "- **DZS (WFS):** polje licence u CKAN-u je prazno, ali metapodaci (`access_constraints`) i "
        "GetCapabilities servisa (`Fees`) navode Otvorenu dozvolu.",
        "- **Katalog portala:** metapodaci su uvijek pod Otvorenom dozvolom, bez obzira na licencu skupa na koji "
        "se odnose (Pravilnik NN 67/17, čl. 4. st. 5.; tekst Otvorene dozvole: \"kao i na metapodatke\").",
        "- **Indeks razvijenosti:** uvjeti korištenja razvoj.gov.hr kažu: \"Sadržaji s ovih stranica mogu se "
        "prenositi bez posebne dozvole uz navođenje izvora\".",
        "- **DUR (planirano):** ni revizija.hr ne navodi licencu. Vrijedi ista osnova kao za MF.",
        "- **OpenStreetMap i OpenFreeMap:**",
        "  - ODbL traži navođenje \"© OpenStreetMap\" s poveznicom na openstreetmap.org/copyright. "
        "OpenFreeMap traži \"OpenFreeMap © OpenMapTiles Data from OpenStreetMap\".",
        "  - MapLibre taj natpis prikazuje u kutu karte. Sažme ga u gumb \"i\" tek kad korisnik pomakne kartu, "
        "što smjernice OSMF-a dopuštaju.",
        "  - Na snimkama zaslona i u videu natpis mora biti vidljiv ili dopisan.",
        "  - OSM podaci nisu u našim rezultatima ni u API-ju. Služe samo kao podloga u sučelju.",
        "- **Gemma 4:** Apache-2.0 prema kartici modela na Kaggleu (https://ai.google.dev/gemma/docs/gemma_4_license). "
        "Koristi se varijanta v2. Model ne distribuiramo, nego samo tekstove koje je napisao, a Apache-2.0 ne "
        "ograničava izlaze.",
        "- Upravne jedinice i indeks razvijenosti preuzeti su jednom. Iz njih je složena "
        "`data/reference/jls_master.csv`, a ETL ih ne preuzima pri svakom pokretanju.",
    ]
    return "\n".join(parts) + "\n"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ai", default=AI_TEXTS, metavar="JSON",
                    help="AI texts to publish (default data/ai/objasnjenja-<year>.json)")
    ai_texts = load_ai_texts(ap.parse_args().ai)
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
            "objasnjenje": explanation(pack, ai_texts.get(u["oib"])),
        })
        write(API / "jedinice" / f"{u['slug']}.json", detail)

    (API / "geo").mkdir(parents=True, exist_ok=True)
    shutil.copy(config.BUILD / "geo" / "jls.topo.json", API / "geo" / "jls.topo.json")

    # merger simulator, precomputed by build.py (pipeline/merge.py): one file per county
    shutil.rmtree(API / "simulator", ignore_errors=True)
    shutil.copytree(config.BUILD / "simulator", API / "simulator")

    # Karta reforme, precomputed by build.py (pipeline/reforma.py): one file per threshold
    reforma_dir = config.BUILD / "reforma"
    if reforma_dir.exists():
        shutil.copytree(reforma_dir, API / "reforma")
    else:
        print(f"Karta reforme: nema {reforma_dir}, preskačem (pokreni python -m pipeline.reforma)")

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
    recs = datasets(rows, json.loads(config.SOURCES_LOG.read_text(encoding="utf-8")))
    write(API / "skupovi.json", recs)
    DATASETS_DOC.write_text(datasets_markdown(recs), encoding="utf-8", newline="\n")
    write(API / "openapi.json", openapi.spec(generated))
    size = sum(p.stat().st_size for p in API.rglob("*") if p.is_file())
    print(f"Statični API: {API} ({len(index)} jedinica, {size / 1e6:.1f} MB)")
    n_used = sum(r["koristi_se"] == "da" for r in rows)
    print(f"Skupovi podataka: {n_used} korištenih, {len(rows) - n_used} planiranih -> {DATASETS_DOC.name}")


if __name__ == "__main__":
    main()
