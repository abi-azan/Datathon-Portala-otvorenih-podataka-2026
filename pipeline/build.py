"""Build the fiscal health dataset for all 576 units.

    .venv/Scripts/python -m pipeline.build            # fetch (conditional GET) + build
    .venv/Scripts/python -m pipeline.build --offline  # reuse data/raw, no network

Outputs in data/build/:
  units.csv          the unit register (OIB, RKP, code, name, county, structure)
  prras_long.parquet every PR-RAS value used, with workbook, sheet and row
  results.parquet    one row per unit and year: aux values, indicators, scores, flags
  results.json       the same, nested per unit
  geo/jls.topo.json  simplified boundaries (layers jls, zupanije) for the map
  geo/susjedi.json   land neighbours and sea links per unit (merger simulator, Karta reforme)
  dzs.parquet, dzs_kodovi.json   DZS PxWeb tables by unit (pipeline/pxweb.py; profile context), plus the
                     population years PxWeb does not have yet from the DZS workbook (pipeline/dzs_xlsx.py)
  porezna_dohodak.parquet, porezna_stope.parquet   Porezna uprava (pipeline/porezna.py; profile context)
  simulator/         merger simulator, every group of 2-4 neighbours (pipeline/merge.py)
  reforma/           Karta reforme, one file per threshold (pipeline/reforma.py)
"""
import argparse
import json
import math
import os
import sys

import pandas as pd
import requests

from . import (config, dzs_xlsx, geo, izravnanje, merge, methodology, mf, openness, population, porezna, pxweb,
               reforma, sources, units)

sys.stdout.reconfigure(encoding="utf-8")


def _warn(msg):
    """A warning that stays visible: on the console and, in GitHub Actions, as an annotation."""
    print(f"UPOZORENJE: {msg}")
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::warning::{msg}")


def context_layers(reg, offline):
    """DZS PxWeb and Porezna uprava (profile context, not the score): data/build/dzs.parquet,
    dzs_kodovi.json, porezna_dohodak.parquet, porezna_stope.parquet. Needs units.csv on disk.

    When a server does not answer (after the retries in sources.py), the build falls back on the
    last downloaded copy in data/raw (in CI: the cached data/raw of the previous run) and warns.
    The source log keeps that copy's download time, so the published dates stay true. Without a
    copy the build fails: profiles are never published without these layers."""
    print("DZS PxWeb (procjene stanovništva, migracije, rođeni, umrli, turizam, dozvole) ...")
    if not offline:
        try:
            pxweb.refresh()
        except requests.RequestException as e:
            if not pxweb.have_raw():
                raise
            _warn(f"DZS PxWeb nije odgovorio ({e}); koristim zadnju preuzetu kopiju iz data/raw/pxweb")
        # population years PxWeb does not have yet (pipeline/dzs_xlsx.py); without it PxWeb alone is used
        try:
            dzs_xlsx.fetch()
        except requests.RequestException as e:
            _warn(f"DZS (Gradovi i općine u statistici) nije odgovorio ({e}); "
                  + ("koristim zadnju preuzetu kopiju" if dzs_xlsx.have_raw() else "koristim samo PxWeb"))
    _, report = pxweb.build(reg)
    rep = report.get(dzs_xlsx.LOG_KEY, {})
    if dzs_xlsx.have_raw() and rep.get("razlog"):
        _warn(f"publikacija DZS-a \"{dzs_xlsx.TITLE}\" nije korištena ({rep['razlog']}); koristim samo PxWeb")
    pxweb.print_report(report)
    print("Porezna uprava (neto dohodak, lokalne porezne stope; data.gov.hr) ...")
    if not offline:
        try:
            porezna.dohvati(offline=False)
        except requests.RequestException as e:
            porezna.dohvati(offline=True)          # raises when there is no earlier copy
            _warn(f"Porezna uprava (data.gov.hr) nije odgovorila ({e}); koristim zadnju preuzetu kopiju iz data/raw/porezna")
    doh, st = porezna.build(reg, offline=True)     # files are in data/raw/porezna now
    print(f"  dohodak: {doh.oib.nunique()} jedinica, godine {sorted(doh.godina.unique().tolist())};"
          f" stope: {st.oib.nunique()} jedinica")

def fetch_all(offline):
    mf_dir = config.RAW / "mf"
    if not offline:
        print("Preuzimanje izvora ...")
        meta = {"publisher": "Ministarstvo financija", "license": "nije navedena (javni podatak, ZPPI)"}
        sources.fetch("mf_prras_zip", config.MF_PRRAS_ZIP, mf_dir / "prras.zip", meta=meta)
        sources.fetch("mf_bilanca", config.MF_BILANCA, mf_dir / "bilanca.xlsx", meta=meta)
        # fiscal equalization table: inputs of the merger simulator's equalization estimate
        sources.fetch("mf_fiskalno_izravnanje", config.MF_FI_XLSX, izravnanje.XLSX, meta=meta)
    return mf_dir / "prras.zip", mf_dir / "bilanca.xlsx"


def load_prras(zip_path):
    cache = config.BUILD / "prras_long.parquet"
    stamp = config.BUILD / "prras_long.sha256"
    log = json.loads(config.SOURCES_LOG.read_text(encoding="utf-8")) if config.SOURCES_LOG.exists() else {}
    sha = log.get("mf_prras_zip", {}).get("sha256", "")
    key = f"{sha}:v{mf.PRRAS_PARSER_VERSION}"  # re-parse when the ZIP or the parser changes
    if cache.exists() and stamp.exists() and stamp.read_text() == key:
        print("PR-RAS: iz predmemorije")
        return pd.read_parquet(cache), None
    print("PR-RAS: raspakiravanje i čitanje (oko 3 min) ...")
    files, names = mf.extract_prras(zip_path, config.RAW / "mf" / "prras")
    df = mf.parse_prras(files, names)
    national = mf.parse_national(files["22"]) if "22" in files else None
    config.BUILD.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache, index=False)
    stamp.write_text(key)
    if national:
        pd.DataFrame([{"code": c, "year": y, "value": v} for (c, y), v in national.items()]).to_parquet(
            config.BUILD / "national_totals.parquet", index=False)
    return df, national


peer_group = methodology.peer_group


def clean(x):
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()

    zip_path, bilanca_path = fetch_all(a.offline)
    prras, _ = load_prras(zip_path)
    print("Bilanca ...")
    bil = mf.parse_bilanca(bilanca_path)
    print("Popis 2021 (DZS WFS) ...")
    pop = population.fetch_population(a.offline)

    master = pd.read_csv(config.REFERENCE / "jls_master.csv", dtype={"jls_code": str, "oib": str, "rkp": str})
    sheets = prras[["zup_id", "sheet", "vrsta"]].drop_duplicates()
    reg = units.build_units(sheets, bil, master)
    reg = reg.merge(pop, on="sifra", how="left")
    county_pop = reg[reg.vrsta != "zupanija"].groupby("zup_id")["stanovnici_2021"].sum()
    is_cty = reg.vrsta == "zupanija"
    reg.loc[is_cty, "stanovnici_2021"] = reg.loc[is_cty, "zup_id"].map(county_pop)
    reg["stanovnici_2021"] = reg["stanovnici_2021"].astype(int)
    reg["skupina"] = [peer_group(u) for u in reg.itertuples()]
    print(f"Šifrarnik: {len(reg)} jedinica, {reg.vrsta.value_counts().to_dict()}")

    print("Granice i susjedstvo (DZS WFS) ...")
    reg = reg.merge(geo.build_geo(reg, a.offline), on="sifra", how="left")
    is_cty = reg.vrsta == "zupanija"
    county_area = reg[~is_cty].groupby("zup_id")["povrsina_km2"].sum()
    reg.loc[is_cty, "povrsina_km2"] = reg.loc[is_cty, "zup_id"].map(county_area).round(3)
    jls_geo = reg[~is_cty]
    print(f"  {len(jls_geo)} poligona, {int(jls_geo.n_susjeda.sum()) // 2} parova susjeda, "
          f"{int(jls_geo.morske_veze.sum()) // 2} veza preko mora, {int(jls_geo.otok.sum())} otočnih jedinica")

    print("Otvorenost (data.gov.hr CKAN API) ...")
    opn, unmatched = openness.build_openness(reg, openness.fetch_packages(a.offline))
    if unmatched:
        print(f"  organizacije bez para: {unmatched}")
    print(f"  {int(opn.portal_objavljuje.sum())} jedinica objavljuje na portalu")
    reg = reg.merge(opn, on="oib", how="left")

    # wide unit-year table
    key = prras.merge(reg[["naziv_mf", "zup_id", "oib"]], left_on=["sheet", "zup_id"], right_on=["naziv_mf", "zup_id"])
    wide = key.pivot_table(index=["oib", "year"], columns="code", values="value", aggfunc="sum")
    wide.columns = [f"p_{c}" for c in wide.columns]
    bcols = [c for c in bil.columns if c.startswith("b_")]
    wide = wide.join(bil.set_index(["oib", "year"])[bcols], how="left").reset_index()
    from . import izravnanje_isplate      # fiscal equalization from the MF decisions: ZO adds back p_FI
    wide["p_FI"], wide["p_FI_odluka"] = izravnanje_isplate.za_build(wide, reg, offline=a.offline)

    rows = []
    results = {}
    popmap = reg.set_index("oib")["stanovnici_2021"].to_dict()
    for oib, grp in wide.groupby("oib"):
        recs = {int(r["year"]): r for r in grp.to_dict("records")}
        res = methodology.evaluate_unit(recs, popmap[oib])
        results[oib] = res
        for y, r in res.items():
            rows.append({"oib": oib, "year": y, **{k: v for k, v in r.items()
                                                    if not isinstance(v, (list, dict))},
                         "zastavice": ",".join(r["zastavice"]), "oznake": ",".join(r["oznake"]),
                         "kvaliteta": ",".join(r["kvaliteta"])})
    res_df = pd.DataFrame(rows).merge(reg[["oib", "naziv", "vrsta", "skupina", "zup_id", "stanovnici_2021"]], on="oib")

    # rank and percentile inside the peer group, per year
    res_df["rang"] = res_df.groupby(["skupina", "year"])["bodovi"].rank(ascending=False, method="min")
    res_df["n_skupine"] = res_df.groupby(["skupina", "year"])["bodovi"].transform("count")
    res_df["percentil"] = res_df.groupby(["skupina", "year"])["bodovi"].rank(pct=True) * 100
    for r in res_df[["oib", "year", "rang", "n_skupine", "percentil"]].to_dict("records"):
        results[r["oib"]][int(r["year"])].update(rang=r["rang"], n_skupine=r["n_skupine"], percentil=r["percentil"])

    config.BUILD.mkdir(parents=True, exist_ok=True)
    reg.to_csv(config.BUILD / "units.csv", index=False, encoding="utf-8")
    res_df.to_parquet(config.BUILD / "results.parquet", index=False)
    wide.to_parquet(config.BUILD / "wide.parquet", index=False)   # unit-year inputs, for merge.py
    nested = []
    for u in reg.to_dict("records"):
        nested.append({**u, "godine": {str(y): r for y, r in results[u["oib"]].items()}})
    (config.BUILD / "results.json").write_text(json.dumps(clean(nested), ensure_ascii=False), encoding="utf-8")

    # before the simulator: merge.py reads data/build/dzs.parquet
    context_layers(reg, a.offline)

    print("Simulator spajanja: sve skupine od 2-4 susjedne jedinice iste županije ...")
    susjedi = json.loads((config.BUILD / "geo" / "susjedi.json").read_text(encoding="utf-8"))
    sim = merge.Data(reg, wide, res_df, susjedi, fi=merge.load_equalization())
    n_groups = merge.precompute(sim, config.BUILD / "simulator")
    print(f"  {n_groups} skupina")
    print("Karta reforme: pohlepno spajanje do praga 2.500, 5.000 i 10.000 stanovnika ...")
    reforma.report(reforma.write_all(sim, res_df, config.BUILD / "reforma"))

    last = res_df[res_df.year == config.LAST_YEAR]
    print(f"\nOcjene {config.LAST_YEAR} (5 = najbolje):")
    print(pd.crosstab(last.vrsta, last.ocjena, margins=True).to_string())
    print("\nStabilnost:", last.stabilnost.value_counts().to_dict())
    print("Zastavice:", {z: int(last.zastavice.str.contains(z).sum()) for z in ["Z1", "Z2", "Z3", "Z4"]})
    print("Dospjele obveze: kredit iskazan kao dospio (pravilo 1):", int(last.kredit_iskazan_dospio.sum()),
          "| ocjena ograničena (pravilo 2):", int(last.ogranicenje_do.sum()))
    print(f"\nGotovo: {config.BUILD}")


if __name__ == "__main__":
    main()
