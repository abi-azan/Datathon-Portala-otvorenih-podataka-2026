"""DZS workbook "Gradovi i općine u statistici" as the bridge for population years PxWeb lacks
(pipeline/dzs_xlsx.py, decision 4.11.2026, docs/research/12).

The first tests use made-up frames and a made-up workbook. The rest need data/raw/dzs (python -m
pipeline.dzs_xlsx or pipeline.build) and data/build/dzs.parquet; they are skipped without them.
"""
import hashlib
import json

import openpyxl
import pandas as pd
import pytest

from pipeline import config, dzs_xlsx, pxweb

COLS = ["oib", "sifra", "godina", "pokazatelj", "vrijednost", "oznaka", "tablica"]


def frame(rows, tablica):
    return pd.DataFrame([(o, o, y, p, v, s, tablica) for o, y, p, v, s in rows], columns=COLS)


# ---------------------------------------------------------------- precedence, on made-up rows

def test_pxweb_wins_where_both_have_a_year():
    """PxWeb has 2024 (one cell even empty); the workbook has 2024 with other numbers and 2025.
    Only 2025 comes from the workbook, and no PxWeb cell is replaced, not even the empty one."""
    px = frame([("1", 2024, "stanovnici_procjena", 100.0, None),
                ("2", 2024, "stanovnici_procjena", float("nan"), "z")], "SP31_2")
    xl = frame([("1", 2024, "stanovnici_procjena", 999.0, None), ("2", 2024, "stanovnici_procjena", 50.0, None),
                ("1", 2025, "stanovnici_procjena", 101.0, None), ("2", 2025, "stanovnici_procjena", 51.0, None),
                ("1", 2025, "umrli", 3.0, None)], "GUS_TAB2")
    added = dzs_xlsx.bridge(px, xl)
    assert sorted(zip(added.oib, added.godina, added.pokazatelj)) == [
        ("1", 2025, "stanovnici_procjena"), ("1", 2025, "umrli"), ("2", 2025, "stanovnici_procjena")]
    # the indicator decides: PxWeb having 2025 for umrli would stop only umrli
    px2 = pd.concat([px, frame([("1", 2025, "umrli", 4.0, None)], "SV331")])
    added2 = dzs_xlsx.bridge(px2, xl)
    assert set(added2.pokazatelj) == {"stanovnici_procjena"}
    # and once PxWeb has every year, the bridge is empty
    px3 = pd.concat([px2, frame([("1", 2025, "stanovnici_procjena", 101.0, None),
                                 ("2", 2025, "stanovnici_procjena", 51.0, None)], "SP31_2")])
    assert dzs_xlsx.bridge(px3, xl).empty


def _toy_years(xl_2024_pop=100.0, deaths_2025=1.0):
    """One unit: PxWeb 2024, the workbook 2024 and 2025 (100 -> 102 = 3 - 1 + 5 - 5)."""
    px = frame([("1", 2024, p, v, None) for p, v in (("stanovnici_procjena", 100.0), ("zivorodeni", 2.0),
                ("umrli", 2.0), ("doseljeni", 4.0), ("odseljeni", 4.0))], "SP31_2")
    xl = frame([("1", 2024, p, v, None) for p, v in (("stanovnici_procjena", xl_2024_pop), ("zivorodeni", 2.0),
                ("umrli", 2.0), ("doseljeni", 4.0), ("odseljeni", 4.0))]
               + [("1", 2025, p, v, None) for p, v in (("stanovnici_procjena", 102.0), ("zivorodeni", 3.0),
                  ("umrli", deaths_2025), ("doseljeni", 5.0), ("odseljeni", 5.0))], "GUS_TAB2")
    return px, xl


def test_checks_pass_on_consistent_data():
    px, xl = _toy_years()
    rep = dzs_xlsx.checks(px, xl, dzs_xlsx.bridge(px, xl))
    assert rep["ok"] and rep["n_razlika"] == 0 and rep["n_odstupanja"] == 0
    assert rep["zajednicke_celije"] == 5 and rep["dodane_godine"] == [2025]


def test_checks_fail_when_the_workbook_differs_from_pxweb():
    px, xl = _toy_years(xl_2024_pop=101.0)
    rep = dzs_xlsx.checks(px, xl, dzs_xlsx.bridge(px, xl))
    assert not rep["ok"] and rep["n_razlika"] == 1


def test_checks_fail_when_the_balance_does_not_hold():
    px, xl = _toy_years(deaths_2025=2.0)
    rep = dzs_xlsx.checks(px, xl, dzs_xlsx.bridge(px, xl))
    assert not rep["ok"] and rep["n_odstupanja"] == 1 and rep["n_razlika"] == 0


def test_unreadable_or_missing_workbook_leaves_pxweb_alone(tmp_path):
    px, _ = _toy_years()
    reg = pd.DataFrame({"oib": ["1"], "sifra": ["1"], "vrsta": ["opcina"], "zup_id": [1],
                        "zupanija": ["Zadarska županija"], "naziv": ["Općina X"], "stanovnici_2021": [100]})
    bad = tmp_path / "x.xlsx"
    bad.write_bytes(b"not a workbook")
    for path in (bad, tmp_path / "missing.xlsx"):
        out, rep = dzs_xlsx.extend(px, reg, path)
        assert not rep["ok"] and rep["razlog"] and rep["dodane_godine"] == []
        assert len(out) == len(px) and set(out.izvor) == {dzs_xlsx.IZVOR_PXWEB}


def test_year_sources():
    d = pd.DataFrame({"pokazatelj": ["x"] * 3, "godina": [2024, 2025, 2025], "izvor": ["pxweb", "xlsx", "xlsx"]})
    assert dzs_xlsx.year_sources(d, "x") == {2024: "pxweb", 2025: "xlsx"}
    assert dzs_xlsx.year_sources(d.drop(columns="izvor"), "x") == {2024: "pxweb", 2025: "pxweb"}
    with pytest.raises(ValueError):
        dzs_xlsx.year_sources(d.assign(izvor=["pxweb", "pxweb", "xlsx"]), "x")


# ---------------------------------------------------------------- header-driven parsing, on a made-up sheet

def test_columns_are_found_by_header_not_position():
    """Tab-2.-like sheet with the sections in another order and an extra column: the parser still
    finds the year columns of each indicator by their headers. Numbers given as text and "-" are read."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Tab-2."])
    ws.append([None, None, None, "Broj stanovnika,", "Umrli", None, "Bilo što", "Procjena stanovništva, stanje 31.12.",
               None, "Živorođeni", None])
    ws.append([None, None, None, "Popis 2021."])
    ws.append(["Županije", "County of", "Gradovi/općine\nTowns", "x", "2024.", "2025.", "2025.", "2024.", "2025.",
               "2024.", "2025."])
    ws.append(["Zadarska", "Zadar", "Pag", 3175, 50, "49", 7, 3352, 3358, 23, "-"])
    rows = dzs_xlsx.read_sheet(ws, "Tab-2.")
    got = {(r.pokazatelj, r.godina): (r.vrijednost, r.oznaka if isinstance(r.oznaka, str) else None)
           for r in rows.itertuples()}
    assert got[("stanovnici_procjena", 2025)] == (3358.0, None)
    assert got[("umrli", 2025)] == (49.0, None) and got[("umrli", 2024)] == (50.0, None)
    v, s = got[("zivorodeni", 2025)]
    assert pd.isna(v) and s == "-"
    assert len(got) == 6 and set(rows.popis_2021) == {3175}


# ---------------------------------------------------------------- the real workbook

have = pytest.mark.skipif(not dzs_xlsx.RAW.exists() or not pxweb.OUT.exists()
                          or not (config.BUILD / "units.csv").exists(),
                          reason="run python -m pipeline.dzs_xlsx (and pipeline.pxweb) first")


@pytest.fixture(scope="module")
def reg():
    return pxweb.load_register()


@pytest.fixture(scope="module")
def xl(reg):
    return dzs_xlsx.observations(reg)


@pytest.fixture(scope="module")
def dzs():
    return pd.read_parquet(pxweb.OUT)


@have
def test_every_unit_once(xl, reg):
    jls = reg[reg.vrsta != "zupanija"]
    assert set(xl.oib) == set(jls.oib) and len(jls) == 556
    assert not xl.duplicated(["oib", "godina", "pokazatelj"]).any()
    assert set(xl.pokazatelj) == set(dzs_xlsx.INDICATORS)
    assert xl.godina.min() == pxweb.FIRST_YEAR and xl.godina.max() >= 2025


@have
def test_workbook_equals_pxweb_in_every_common_cell(xl, dzs):
    """docs/research/12 §2.3: 2021-2024, 556 units, 5 indicators: no difference ("-" is 0 on both sides)."""
    px = dzs[(dzs.izvor == dzs_xlsx.IZVOR_PXWEB) & dzs.oib.isin(set(xl.oib))]
    key = ["oib", "godina", "pokazatelj"]
    a = pxweb.with_symbols(px[px.pokazatelj.isin(dzs_xlsx.INDICATORS)]).set_index(key).vrijednost
    b = pxweb.with_symbols(xl).set_index(key).vrijednost
    common = a.index.intersection(b.index)
    assert len(common) >= 556 * 5 * 4                                # 11.120 today
    x, y = a.loc[common], b.loc[common]
    assert ((x == y) | (x.isna() & y.isna())).all(), x[x != y].head()
    assert {g for _, g, _ in common} >= {2021, 2022, 2023, 2024}


@have
def test_population_balance_in_the_workbook(xl):
    """Change of the estimate = live births − deaths + in − out, every unit, every year 2022-2025."""
    w = pxweb.with_symbols(xl).pivot_table(index=["oib", "godina"], columns="pokazatelj", values="vrijednost")
    years = sorted(w.index.get_level_values(1).unique())
    bad, n = [], 0
    for y in years[1:]:
        cur, prev = w.xs(y, level=1), w.xs(y - 1, level=1)
        lhs = cur.stanovnici_procjena - prev.stanovnici_procjena.reindex(cur.index)
        rhs = cur.zivorodeni - cur.umrli + cur.doseljeni - cur.odseljeni
        n += len(cur)
        bad += [(o, y) for o in cur.index[(lhs != rhs).to_numpy()]]
    assert n >= 556 * 4 and not bad, bad[:5]


@have
@pytest.mark.parametrize("slug, y2021, y2025, change", [
    ("grad-pag", 3156, 3358, 0.064),                 # research 12 §2.3
    ("opcina-bogdanovci", 1551, 1427, -0.080),
    ("grad-zagreb", 766824, 778184, 0.015),
])
def test_known_2025_estimates(dzs, reg, slug, y2021, y2025, change):
    oib = reg.set_index("slug").oib[slug]
    s = dzs[(dzs.oib == oib) & (dzs.pokazatelj == "stanovnici_procjena")].set_index("godina")
    assert s.vrijednost[2021] == y2021 and s.vrijednost[2025] == y2025
    assert s.izvor[2021] == dzs_xlsx.IZVOR_PXWEB and s.tablica[2021] == "SP31_2"
    assert s.izvor[2025] == dzs_xlsx.IZVOR_XLSX and s.tablica[2025] == "GUS_TAB2"
    assert round(y2025 / y2021 - 1, 3) == change


@have
def test_bridge_in_dzs_parquet(dzs, reg):
    """One source per indicator and year; the workbook fills only years PxWeb lacks, for all 576 units
    (counties as the sum of their units); the 2025 totals are the DZS release (STAN-2026-1-1)."""
    demo = dzs[dzs.pokazatelj.isin(dzs_xlsx.INDICATORS)]
    src = demo.groupby(["pokazatelj", "godina"]).izvor.agg(set)
    assert (src.map(len) == 1).all()
    for (p, y), s in src.items():
        px_years = set(demo[(demo.pokazatelj == p) & (demo.izvor == dzs_xlsx.IZVOR_PXWEB)].godina)
        if s == {dzs_xlsx.IZVOR_XLSX}:
            assert y > max(px_years), (p, y)
    assert set(dzs.loc[~dzs.pokazatelj.isin(dzs_xlsx.INDICATORS), "izvor"]) == {dzs_xlsx.IZVOR_PXWEB}
    added = demo[demo.izvor == dzs_xlsx.IZVOR_XLSX]
    if added.empty:
        pytest.skip("PxWeb has every year: no bridge")
    assert set(added.tablica) <= set(dzs_xlsx.TABLICE.values())
    for (p, y), g in added.groupby(["pokazatelj", "godina"]):
        assert set(g.oib) == set(reg.oib), (p, y)
    jls = added[added.oib.isin(set(reg.loc[reg.vrsta != "zupanija", "oib"]))]
    tot = pxweb.with_symbols(jls)[jls.godina == 2025].groupby("pokazatelj").vrijednost.sum()
    assert (tot.zivorodeni, tot.umrli) == (32_479, 50_007)
    zup = reg[reg.vrsta == "zupanija"].set_index("oib").zup_id
    j = pxweb.with_symbols(jls).merge(reg[["oib", "zup_id"]], on="oib")
    sums = j.groupby(["zup_id", "godina", "pokazatelj"]).vrijednost.sum()
    for r in added[added.oib.isin(zup.index)].itertuples():
        assert r.vrijednost == sums[(zup[r.oib], r.godina, r.pokazatelj)]


@have
def test_download_is_in_the_provenance_log():
    e = json.loads(config.SOURCES_LOG.read_text(encoding="utf-8"))[dzs_xlsx.LOG_KEY]
    assert e["url"] == dzs_xlsx.URL and e["publisher"] == pxweb.PUBLISHER and e["license"] == pxweb.LICENSE
    assert hashlib.sha256((config.ROOT / e["file"]).read_bytes()).hexdigest() == e["sha256"]
    assert e.get("etag") or e.get("last_modified")
