"""Context blocks of the unit profile (pipeline/kontekst.py): known values, DZS symbols, medians.

The data tests run against data/build (pipeline.build first) and are skipped without it."""
import math

import pandas as pd
import pytest

from pipeline import config, dzs_xlsx, izravnanje, kontekst, merge, publish, pxweb

NEEDED = [pxweb.OUT, pxweb.CODES_OUT, config.BUILD / "porezna_dohodak.parquet", config.BUILD / "porezna_stope.parquet",
          config.BUILD / "units.csv", izravnanje.XLSX]
needs_build = pytest.mark.skipif(not all(p.exists() for p in NEEDED), reason="run pipeline.build first")


# ---------------------------------------------------------------- the DZS symbol rule, on made-up cells

def test_symbol_rule():
    assert pxweb.value(float("nan"), "-") == 0.0                    # the phenomenon does not exist
    assert math.isnan(pxweb.value(float("nan"), "z"))               # confidential: never 0
    assert pxweb.value(12.0, None) == 12.0
    df = pd.DataFrame({"vrijednost": [float("nan"), float("nan"), 5.0], "oznaka": ["-", "z", None]})
    out = pxweb.with_symbols(df)
    assert out.vrijednost.iloc[0] == 0.0 and math.isnan(out.vrijednost.iloc[1]) and out.vrijednost.iloc[2] == 5.0
    assert df.vrijednost.isna().sum() == 2                          # the input is not changed


def _toy():
    """Three municipalities of one peer group, a county and Zagreb, tourism nights with each symbol."""
    units = pd.DataFrame({
        "oib": ["1", "2", "3", "4", "5"], "skupina": ["općine do 2.000"] * 3 + ["županije", "Grad Zagreb"],
        "zagreb": [False, False, False, False, True], "stanovnici_2021": [100, 200, 400, 1000, 5000],
    })
    rows = []
    for o in units.oib:
        for y in (2021, 2024):
            rows.append((o, y, "stanovnici_procjena", 100.0, None))
            for p in kontekst.DEMOGRAFIJA:
                rows.append((o, y, p, 1.0, None))
        rows.append((o, 2025, "dozvole_zgrade", 2.0, None))
    nights = {"1": (1000.0, None), "2": (float("nan"), "-"), "3": (float("nan"), "z"), "4": (5000.0, None),
              "5": (50000.0, None)}
    rows += [(o, 2025, "nocenja", v, s) for o, (v, s) in nights.items()]
    dzs = pd.DataFrame(rows, columns=["oib", "godina", "pokazatelj", "vrijednost", "oznaka"])
    doh = pd.DataFrame([(o, 2025, k, n) for o in units.oib for k, n in (("ukupno", 1000.0), ("umirovljenici", 250.0))],
                       columns=["oib", "godina", "vrsta_dohotka", "neto"])
    return units, dzs, doh


def test_symbols_and_medians_on_made_up_units():
    units, dzs, doh = _toy()
    ind = kontekst.indicators(units, dzs, doh)
    assert ind.loc["1", "nocenja_po_stanovniku"] == 10.0
    assert ind.loc["2", "nocenja_po_stanovniku"] == 0.0 and ind.loc["2", "nocenja_po_stanovniku_oznaka"] == "-"
    assert math.isnan(ind.loc["3", "nocenja_po_stanovniku"]) and ind.loc["3", "nocenja_po_stanovniku_oznaka"] == "z"
    med, cnt = kontekst.medians(units, ind)
    # "-" counts as 0 in the median, "z" is left out: median of 10 and 0
    assert med.loc["općine do 2.000", "nocenja_po_stanovniku"] == 5.0
    assert cnt.loc["općine do 2.000", "nocenja_po_stanovniku"] == 2
    assert cnt.loc["općine do 2.000", "dozvole_na_1000"] == 3       # nothing else left out
    assert "Grad Zagreb" not in med.index                           # Zagreb has no peers
    assert med.loc["županije", "nocenja_po_stanovniku"] == 5.0     # a county against counties only
    assert ind.loc["1", "udio_mirovina"] == 0.25
    assert ind.loc["1", "promjena_stanovnistva"] == 0.0 and ind.loc["1", "promjena_od"] == 2021


# ---------------------------------------------------------------- known units, from data/build

@pytest.fixture(scope="module")
def ctx():
    units = pd.read_csv(config.BUILD / "units.csv", dtype={"oib": str, "sifra": str, "rkp": str})
    return units, units.set_index("slug").oib, kontekst.load(units)


@needs_build
def test_pag(ctx):
    units, oib, k = ctx
    b = k["stanovnistvo_gospodarstvo"][oib["grad-pag"]]
    p = b["pokazatelji"]
    assert b["skupina"] == "gradovi 2.000-5.000"
    assert b["procjene"]["2021"] == 3156 and b["procjene"]["2024"] == 3352      # research 09 §2.2
    assert b["procjene"]["2025"] == 3358                                        # research 12 §2.3 (publication)
    assert p["promjena_stanovnistva"]["vrijednost"] == pytest.approx(3358 / 3156 - 1)
    assert round(p["promjena_stanovnistva"]["vrijednost"], 3) == 0.064          # +6,4 %
    assert (p["promjena_stanovnistva"]["od_godine"], p["promjena_stanovnistva"]["godina"]) == (2021, 2025)
    assert b["izvor_po_godini"] == {"2021": "pxweb", "2022": "pxweb", "2023": "pxweb", "2024": "pxweb", "2025": "xlsx"}
    assert {k: p[k]["izvor"] for k in kontekst.DEMO_IZVOR} == dict.fromkeys(kontekst.DEMO_IZVOR, "xlsx")
    pub = [s for s in b["izvori"] if s["tablica"] == dzs_xlsx.SOURCE_ID]
    assert len(pub) == 1 and pub[0]["godine"] == [2025] and pub[0]["url"] == dzs_xlsx.URL
    assert round(p["neto_dohodak_pc"]["vrijednost"]) == 9574                     # research 09 §2.1
    assert p["neto_migracija"]["broj"] == 190 - 156                             # 2025, research 12 §2.3
    assert p["neto_migracija"]["godina"] == p["prirodni_prirast"]["godina"] == 2025
    assert p["prirodni_prirast"]["broj"] == 21 - 49
    assert round(p["prirodni_prirast"]["vrijednost"], 1) == -8.8 and round(p["neto_migracija"]["vrijednost"], 1) == 10.7
    assert p["nocenja_po_stanovniku"]["broj"] == 776716                         # BS_TU19 2025
    assert p["dozvole_na_1000"]["broj"] == 41                                   # PX14 2025
    assert p["neto_dohodak_pc"]["n_medijan"] == 21
    q = b["uzivo"]
    assert q["url"] == pxweb.table_url("SP31_2") and q["kod"] == "312" and q["naziv"] == "Pag"
    assert {"filter": "item", "values": ["312"]} in [x["selection"] for x in q["upit"]["query"]]
    assert {"filter": "all", "values": ["*"]} in [x["selection"] for x in q["upit"]["query"]]
    e = k["izravnanje"][oib["grad-pag"]]
    assert (e["kapacitet_pc"], e["referentna_pc"], e["vrsta_reference"]) == (993.68, 686.33, "grad")
    assert e["isplata"] == 0.0
    assert e["stopa"]["niza"] == 0.2 and e["stopa"]["ispod_maksimuma"] is True


@needs_build
def test_bogdanovci(ctx):
    units, oib, k = ctx
    p = k["stanovnistvo_gospodarstvo"][oib["opcina-bogdanovci"]]["pokazatelji"]
    assert round(p["neto_dohodak_pc"]["vrijednost"]) == 6592
    assert round(p["udio_mirovina"]["vrijednost"], 3) == 0.365
    assert p["promjena_stanovnistva"]["broj"] == 1427 - 1551                     # 2021 -> 2025, research 12 §2.3
    assert round(p["promjena_stanovnistva"]["vrijednost"], 3) == -0.080          # −8,0 %
    assert p["nocenja_po_stanovniku"]["oznaka"] == "z" and p["nocenja_po_stanovniku"]["vrijednost"] is None
    e = k["izravnanje"][oib["opcina-bogdanovci"]]
    assert (e["kapacitet_pc"], e["referentna_pc"]) == (222.99, 699.84)
    assert round(e["isplata"] / 1000) == 401
    assert e["stopa"]["ispod_maksimuma"] is False


@needs_build
def test_payout_is_the_simulators(ctx):
    """The profile payout is merge.payout for a 'merger' of one unit, and all payouts add up to the budget line."""
    units, oib, k = ctx
    e = k["izravnanje"][oib["opcina-bogdanovci"]]
    total = sum(x["puni_iznos"] for x in k["izravnanje"].values())
    sim = merge.payout([e["puni_iznos"]], e["puni_iznos"], total)
    assert e["isplata"] == pytest.approx(sim["isplata_po_clanici"][0])
    assert sum(x["isplata"] for x in k["izravnanje"].values()) == pytest.approx(izravnanje.ISPLATA_2026)
    assert len(k["izravnanje"]) == 576


@needs_build
def test_zagreb_and_a_county(ctx):
    units, oib, k = ctx
    z = k["stanovnistvo_gospodarstvo"][oib["grad-zagreb"]]
    assert z["skupina"] is None
    assert all(v["medijan"] is None and v["n_medijan"] == 0 for v in z["pokazatelji"].values())
    assert all(v["vrijednost"] is not None for v in z["pokazatelji"].values())
    zp = z["pokazatelji"]
    assert z["procjene"]["2025"] == 778184 and zp["promjena_stanovnistva"]["broj"] == 778184 - 766824
    assert round(zp["promjena_stanovnistva"]["vrijednost"], 3) == 0.015          # +1,5 %, research 12 §2.3
    assert (zp["prirodni_prirast"]["broj"], zp["neto_migracija"]["broj"]) == (7036 - 8608, 21675 - 19278)
    assert z["uzivo"]["naziv"] == "GRAD ZAGREB"                                  # SP31_2: county and city in one row
    ez = k["izravnanje"][oib["grad-zagreb"]]
    assert ez["vrsta_reference"] == "grad" and ez["referentna_pc"] == 686.33 and ez["isplata"] == 0.0
    c = k["stanovnistvo_gospodarstvo"][oib["vukovarsko-srijemska-zupanija"]]
    assert c["skupina"] == "županije" and c["pokazatelji"]["promjena_stanovnistva"]["n_medijan"] == 20
    assert c["pokazatelji"]["promjena_stanovnistva"]["godina"] == 2025 and c["procjene"]["2025"] is not None
    ec = k["izravnanje"][oib["vukovarsko-srijemska-zupanija"]]
    assert ec["vrsta_reference"] == "zupanija" and ec["isplata"] > 0 and ec["stopa"] is None
    assert k["porezne_stope"].get(oib["vukovarsko-srijemska-zupanija"]) is None


@needs_build
def test_medians_leave_out_only_empty_cells(ctx):
    """Per peer group, the median counts every unit with a value: all of them for population and income,
    all but the confidential ("z") ones for tourism, and "-" units are in as 0."""
    units, oib, k = ctx
    blocks = k["stanovnistvo_gospodarstvo"]
    peers = units[~units.zagreb.astype(bool)]
    for g, members in peers.groupby("skupina"):
        b = [blocks[o]["pokazatelji"] for o in members.oib]
        for key in ("promjena_stanovnistva", "neto_dohodak_pc", "dozvole_na_1000"):
            assert b[0][key]["n_medijan"] == sum(x[key]["vrijednost"] is not None for x in b) == len(members), (g, key)
        nights = [x["nocenja_po_stanovniku"] for x in b]
        assert nights[0]["n_medijan"] == sum(x["oznaka"] != "z" and x["vrijednost"] is not None for x in nights), g
        vals = sorted(x["vrijednost"] for x in nights if x["vrijednost"] is not None)
        assert nights[0]["medijan"] == pytest.approx(pd.Series(vals).median()), g
    assert any(x["pokazatelji"]["nocenja_po_stanovniku"]["oznaka"] == "-" and
               x["pokazatelji"]["nocenja_po_stanovniku"]["vrijednost"] == 0.0 for x in blocks.values())


# ---------------------------------------------------------------- the dataset list

def test_dataset_dates_and_metadata_calls():
    """PxWeb's "updated" date is the publisher's date; the metadata call is not a dataset of its own."""
    rows = [{"kljuc": "dzs_pxweb_sp31_2", "koristi_se": "da", "zadnja_izmjena": "2020-01-01"},
            {"kljuc": "porezna_neto_dohodak", "koristi_se": "da", "zadnja_izmjena": ""}]
    entry = {"retrieved": "2026-11-04T15:42:40+00:00", "bytes": 10, "sha256": "a" * 64}
    log = {"dzs_pxweb_sp31_2": {**entry, "px_updated": "2025-11-27T16:06:28"},
           "dzs_pxweb_sp31_2_meta": {**entry, "sha256": "b" * 64},
           "porezna_neto_dohodak": {**entry, "last_modified": "Fri, 16 Oct 2026 08:42:25 GMT"}}
    out = {r["kljuc"]: r for r in publish.datasets(rows, log)}
    assert out["dzs_pxweb_sp31_2"]["zadnja_izmjena"] == "2025-11-27"
    assert out["dzs_pxweb_sp31_2"]["sha256"] == "a" * 64 and "stranica" not in out["dzs_pxweb_sp31_2"]
    assert out["porezna_neto_dohodak"]["zadnja_izmjena"] == "2026-10-16"


# ---------------------------------------------------------------- tax at the highest rates (decision S1)

@needs_build
def test_highest_rates_reproduce_research_11(ctx):
    """docs/research/11 §2.5: 124 units, about 88,7 mil. € together; Rijeka 9,43, Samobor 6,80 (5,7-6,9),
    Osijek 6,37 mil. €. Units at the maximum get none."""
    units, oib, k = ctx
    est = {o: e["uz_najvise_stope"] for o, e in k["izravnanje"].items() if e["uz_najvise_stope"]}
    below = {o for o, e in k["izravnanje"].items() if e["stopa"] and e["stopa"]["ispod_maksimuma"]}
    assert set(est) == below and len(est) == 124
    assert sum(x["procjena"] for x in est.values()) / 1e6 == pytest.approx(88.7, abs=0.2)
    for slug, mil in (("grad-rijeka", 9.43), ("grad-samobor", 6.80), ("grad-osijek", 6.37)):
        assert est[oib[slug]]["procjena"] / 1e6 == pytest.approx(mil, abs=0.01), slug
    sam = est[oib["grad-samobor"]]
    assert (round(sam["od"] / 1e6, 1), round(sam["do"] / 1e6, 1)) == (5.7, 6.9)
    assert (sam["niza"], sam["visa"], sam["niza_max"], sam["visa_max"]) == (0.18, 0.27, 0.22, 0.32)
    assert all(x["od"] <= x["procjena"] <= x["do"] for x in est.values())
    assert k["izravnanje"][oib["opcina-bogdanovci"]]["uz_najvise_stope"] is None     # at the maximum


def test_highest_rates_use_only_kinds_that_pay_the_local_rate():
    """Capital, renting and selling property and lump-sum taxpayers pay a fixed 12 %: more of their tax
    changes nothing. With no taxpayer above the threshold, the estimate is T_lok x (max / lower - 1) x share."""
    stope = pd.DataFrame([{"oib": "1", "godina": 2026, "niza": 0.18, "visa": 0.28, "niza_max": 0.20,
                           "ispod_maksimuma": True}])
    razredi = pd.DataFrame([{"oib": "1", "godina": 2024, "granica": 50400.0, "ispod": 1000.0, "iznad": float("nan")}])

    def doh(kapital):
        kinds = {"zaposlenici": 900.0, "umirovljenici": 50.0, "obrt": 30.0, "drugi_dohodak": 20.0,
                 "kapital": kapital, "povremeni_rad_imovina": 100.0, "pausalisti": 10.0}
        rows = [("1", 2025, k, v) for k, v in kinds.items()] + [("1", 2025, "ukupno", 2000.0)]
        return pd.DataFrame(rows, columns=["oib", "godina", "vrsta_dohotka", "porez"])

    a = kontekst.highest_rates(doh(100.0), stope, razredi, {"1": 1400.0})["1"]
    b = kontekst.highest_rates(doh(5000.0), stope, razredi, {"1": 1400.0})["1"]
    assert a["procjena"] == pytest.approx(1000.0 * (0.20 / 0.18 - 1) * 0.7)
    assert b["procjena"] == pytest.approx(a["procjena"])                   # only the 611 share would move it
    assert a["od"] == pytest.approx(a["procjena"] * kontekst.PONASANJE) and a["do"] == pytest.approx(a["procjena"])
    assert a["visa_max"] == 0.30


@pytest.mark.skipif(not (config.RAW / "porezna" / "dohodak_razredi.xlsx").exists(), reason="no bracket workbook")
def test_bracket_workbook():
    from pipeline import porezna
    units = pd.read_csv(config.BUILD / "units.csv", dtype={"oib": str, "sifra": str, "rkp": str})
    rz = porezna.parse_razredi(config.RAW / "porezna" / "dohodak_razredi.xlsx", units)
    assert rz.groupby("godina").oib.nunique().to_dict() == {2023: 556, 2024: 556}
    assert set(rz.groupby("godina").granica.first().round(2).items()) == {(2023, 47780.28), (2024, 50400.0)}
    sam = rz[(rz.oib == units.set_index("slug").oib["grad-samobor"]) & (rz.godina == 2024)].iloc[0]
    assert (sam.ispod, sam.iznad) == (19344, 324)                                   # research 11 §2.3
