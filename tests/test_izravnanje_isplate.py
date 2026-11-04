"""Fiscal equalization from the MF decisions (pipeline/izravnanje_isplate.py) and its use in ZO.

The pure parts run always; the parts that read the MF tables need data/raw/izravnanje (online
build), and the ones on units need data/build (pipeline.build)."""
import math

import pandas as pd
import pytest

from pipeline import config, izravnanje_isplate as ii, methodology as m

HAVE_TABLES = all(ii.tablica_path(y).exists() for y in ii.PRORACUN if y in config.YEARS)
HAVE_BUILD = (config.BUILD / "wide.parquet").exists() and (config.BUILD / "units.csv").exists()
need_tables = pytest.mark.skipif(not (HAVE_TABLES and HAVE_BUILD), reason="run pipeline.build (online) first")

OTOCAC, DOMASINEC, KRNJAK, VUKOVAR, BELISCE = "14180718952", "37004222770", "71767746351", "50041264710", "70663673307"
ANDRIJASEVCI, SV_JURAJ, POVLJANA = "47372067408", "23610091824", "47207249296"


def row(**kw):
    base = {"p_6": 1000.0, "p_7": 0.0, "p_63": 300.0, "p_633": 250.0, "p_6332": 50.0, "p_6352": 0.0,
            "p_6353": 0.0, "p_663": 0.0, "p_dio611": 0.0}
    return {**base, **kw}


# ---------------------------------------------------------------- methodology (pure)

def test_zo_adds_back_the_decision_amount_not_6353():
    no_fi = m.aux(row())["ZO"]
    assert m.aux(row(p_FI=120.0, p_FI_odluka=120.0))["ZO"] == pytest.approx(no_fi + 120.0)
    # 6353 = 0 (booked on 6331): the decision amount still goes back in
    assert m.aux(row(p_6353=0.0, p_FI=120.0))["ZO"] == pytest.approx(no_fi + 120.0)


def test_without_p_fi_zo_falls_back_to_6353():
    a = m.aux(row(p_6353=80.0))
    assert a["ZO"] == pytest.approx(1000 - 300 + 80)
    assert m.aux(row(p_6353=80.0, p_FI=float("nan")))["ZO"] == pytest.approx(a["ZO"])


def test_context_share_uses_the_decision_amount():
    r = row(p_FI=100.0, p_FI_odluka=150.0)        # capped add-back 100, paid 150
    a = m.aux(r)
    assert m.context(r, a, 1000)["udio_fiskalnog_izravnanja"] == pytest.approx(150.0 / a["PO"])
    assert m.context(row(p_6353=30.0), m.aux(row(p_6353=30.0)), 1000)["udio_fiskalnog_izravnanja"] == \
        pytest.approx(30.0 / m.aux(row(p_6353=30.0))["PO"])


def test_equalization_notes():
    r = row(p_633=250_000.0, p_6332=50_000.0)                                 # room 6331 = 200.000
    assert m.equalization_notes({**r, "p_FI_odluka": 200_000.0}, 2025) == ["izravnanje_na_drugom_kontu"]
    assert m.equalization_notes({**r, "p_FI_odluka": 200_000.0}, 2024) == []  # 6353 not in use before 2025
    assert m.equalization_notes({**r, "p_FI_odluka": 500_000.0}, 2023) == ["izravnanje_nije_medu_pomocima"]
    big = row(p_633=100_000.0, p_6332=0.0, p_6353=90_000.0)
    assert m.equalization_notes({**big, "p_FI_odluka": 90_000.0}, 2025) == []
    assert m.equalization_notes({**big, "p_FI_odluka": 50_000.0}, 2025) == ["konto_6353_vise_od_odluke"]
    assert m.equalization_notes({**big, "p_FI_odluka": 85_000.0}, 2025) == []  # within 10 %
    assert m.equalization_notes({**row(p_6353=900.0), "p_FI_odluka": 0.0}, 2025) == []   # within 1.000 €
    assert m.equalization_notes(row(p_6353=5_000.0), 2025) == []             # no decision amount


def test_merge_sums_the_equalization_columns():
    from pipeline import merge
    assert {"p_FI", "p_FI_odluka", "p_633", "p_6332", "p_6352", "p_6353"} <= set(merge.KEYS)


# ---------------------------------------------------------------- stupac(): cap and fallback

def test_stupac_caps_and_falls_back(monkeypatch):
    wide = pd.DataFrame([
        {"oib": "A", "year": 2025, "p_633": 1_000.0, "p_6332": 0.0, "p_6352": 0.0, "p_6353": 0.0},     # on 6331
        {"oib": "B", "year": 2025, "p_633": 100.0, "p_6332": 0.0, "p_6352": 0.0, "p_6353": 0.0},       # in taxes
        {"oib": "A", "year": 2020, "p_633": 1_000.0, "p_6332": 0.0, "p_6352": 0.0, "p_6353": 40.0},    # no decision
    ])
    tab = pd.DataFrame([{"oib": "A", "year": 2025, "FI_odluka": 500.0}, {"oib": "B", "year": 2025, "FI_odluka": 300.0}])
    monkeypatch.setattr(ii, "isplate", lambda units, godine=None: (tab, {2025: {"izvor": "odluka"}}))
    fi, odl = ii.stupac(wide, None, write=False)
    assert fi.tolist() == [500.0, 100.0, 40.0]
    assert odl.iloc[0] == 500.0 and odl.iloc[1] == 300.0 and math.isnan(odl.iloc[2])


def test_years_before_2021_are_income_tax():
    assert set(ii.U_POREZU) == {2019, 2020}
    assert not set(ii.U_POREZU) & set(ii.PRORACUN)
    assert ii.proracun_eur(2021) == pytest.approx(2_000_000_000 / 7.5345)
    assert ii.proracun_eur(2025) == 280_445_617.0


# ---------------------------------------------------------------- the MF tables and the build

@pytest.fixture(scope="module")
def built():
    units = pd.read_csv(config.BUILD / "units.csv", dtype={"oib": str, "rkp": str, "sifra": str})
    wide = pd.read_parquet(config.BUILD / "wide.parquet")
    fi, odl = ii.stupac(wide, units, write=False)
    w = wide.assign(p_FI=fi, p_FI_odluka=odl, year=wide["year"].astype(int)).set_index(["oib", "year"])
    tab, report = ii.isplate(units)
    return units, w, tab, report


@need_tables
def test_every_year_matches_all_576_units_and_sums_to_the_budget(built):
    units, w, tab, report = built
    for y in ii.PRORACUN:
        if y not in config.YEARS:
            continue
        r = report[y]
        assert r["izvor"] == "odluka" and r["spareno"] == 576 and not r["nespareno"], y
        assert r["zbroj_udjela"] == pytest.approx(1.0, abs=1e-9), y
        t = tab[tab.year == y]
        assert t["FI_odluka"].sum() == pytest.approx(ii.proracun_eur(y), abs=1.0), y     # national sum
        assert r["udjeli_odluke"]["najvece_odstupanje"] < 2e-6, y                          # decision = table


@need_tables
def test_2025_decision_amount_is_what_units_book_on_6353(built):
    units, w, tab, report = built
    e = w.xs(2025, level="year")
    e = e[(e.p_FI_odluka > 0) & (e.p_6353 > 0)]
    within = ((e.p_6353 - e.p_FI_odluka).abs() <= 0.01 * e.p_FI_odluka).sum()
    assert within >= 250 and within / len(e) > 0.75
    # Andrijaševci books exactly the decision amount on 6353, so nothing changes for it
    a = w.loc[(ANDRIJASEVCI, 2025)]
    assert a.p_FI == pytest.approx(a.p_6353, rel=0.01)


@need_tables
def test_units_without_6353_get_the_decision_amount(built):
    units, w, tab, report = built
    for oib in (OTOCAC, DOMASINEC, KRNJAK, VUKOVAR, BELISCE):
        r = w.loc[(oib, 2025)]
        assert (r.p_6353 or 0) == 0 and r.p_FI > 100_000, oib
        rec = {k: v for k, v in r.items()}
        assert m.aux(rec)["ZO"] == pytest.approx(m.aux({**rec, "p_FI": float("nan")})["ZO"] + r.p_FI)
    o = w.loc[(OTOCAC, 2025)]
    assert 1_200_000 < o.p_FI_odluka < 1_260_000                 # share 0,00438... x 280.445.617 €
    assert o.p_FI == pytest.approx(min(o.p_FI_odluka, o.p_633 - o.p_6332 + o.p_6352 + o.p_6353))
    assert m.equalization_notes(dict(o.items()), 2025) == ["izravnanje_na_drugom_kontu"]
    b = w.loc[(BELISCE, 2025)]                        # Belišće books it on 6352
    assert b.p_FI == pytest.approx(b.p_FI_odluka, rel=1e-9) and b.p_6352 >= b.p_FI_odluka * 0.9


@need_tables
def test_equalization_booked_under_taxes_is_not_added_twice(built):
    units, w, tab, report = built
    s = w.loc[(SV_JURAJ, 2022)]
    assert s.p_FI_odluka > 300_000 and s.p_FI < 10_000          # 2.927 € on 6331, the rest in 6111
    assert m.equalization_notes(dict(s.items()), 2022) == ["izravnanje_nije_medu_pomocima"]


@need_tables
def test_2019_and_2020_keep_6353(built):
    units, w, tab, report = built
    old = w[w.index.get_level_values("year").isin([2019, 2020])]
    assert old.p_FI_odluka.isna().all()
    assert (old.p_FI == old.p_6353.fillna(0.0)).all()
    assert report[2019]["izvor"] == report[2020]["izvor"] == "porez_na_dohodak"


@need_tables
def test_povljana_has_no_equalization(built):
    units, w, tab, report = built
    for y in (2021, 2022, 2023, 2024, 2025):
        assert w.loc[(POVLJANA, y)].p_FI == 0.0, y
