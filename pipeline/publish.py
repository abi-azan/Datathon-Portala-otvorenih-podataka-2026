"""Static API for the web app and for anyone else: web/public/api/v1/.

    .venv/Scripts/python -m pipeline.publish     # after pipeline.build

  jedinice.json            index of all 576 units: names, codes, grade and points per year
  jedinice/<slug>.json     full profile: every year's results, fact pack, peer medians,
                           neighbours, openness layer, template explanation
  skupine.json             peer-group medians per year (points and the five indicators)
  geo/jls.topo.json        boundaries (layers jls, zupanije)

The files are generated, not committed: CI builds them before deploying the site.
"""
import json
import math
import shutil
import sys
from datetime import datetime, timezone

import pandas as pd

from . import config, explain, facts, verify

API = config.ROOT / "web" / "public" / "api" / "v1"
INDICATORS = ["I1", "I2", "I3", "I4", "I5"]


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
    finite = res.assign(I3=res.I3.where(~res.I3.map(lambda v: isinstance(v, float) and math.isinf(v))))
    cols = ["bodovi", *INDICATORS, "uprava_pc", "udio_tekucih_pomoci"]
    med = finite.groupby(["skupina", "year"])[cols].median().reset_index()
    out = {}
    for r in med.to_dict("records"):
        out.setdefault(r["skupina"], {})[str(int(r["year"]))] = {c: r[c] for c in cols}
    return out


def explanation(pack):
    """Template text until the AI texts exist; always shipped with its number check."""
    if not pack:
        return None
    text = explain.template(pack)
    return {"tekst": text, "izvor": "predlozak", "provjera": verify.verify(text, pack)}


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

    ranks = {(r["oib"], str(int(r["year"]))): {"rang": r["rang"], "n_skupine": r["n_skupine"], "percentil": r["percentil"]}
             for r in res[["oib", "year", "rang", "n_skupine", "percentil"]].to_dict("records")}
    for u in units.to_dict("records"):
        n = nested[u["oib"]]
        for y, r in n["godine"].items():
            r.update(ranks.get((u["oib"], y), {}))
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
    size = sum(p.stat().st_size for p in API.rglob("*") if p.is_file())
    print(f"Statični API: {API} ({len(index)} jedinica, {size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
