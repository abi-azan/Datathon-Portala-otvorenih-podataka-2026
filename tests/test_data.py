"""Checks against the built data (PLAN §3.7). Run after `python -m pipeline.build`."""
import json

import pandas as pd
import pytest

from pipeline import config

pytestmark = pytest.mark.skipif(not (config.BUILD / "results.parquet").exists(), reason="run pipeline.build first")


@pytest.fixture(scope="module")
def units():
    return pd.read_csv(config.BUILD / "units.csv", dtype={"oib": str, "sifra": str})


@pytest.fixture(scope="module")
def prras():
    return pd.read_parquet(config.BUILD / "prras_long.parquet")


def test_576_units_with_unique_keys(units):
    assert len(units) == 576
    assert units.vrsta.value_counts().to_dict() == {"opcina": 428, "grad": 128, "zupanija": 20}
    for col in ("oib", "rkp", "sifra", "slug"):
        assert units[col].is_unique, col


def test_population_matches_census(units):
    jls = units[units.vrsta != "zupanija"]
    assert jls.stanovnici_2021.sum() == config.POPULATION_RH_2021


@pytest.mark.parametrize("code", ["6", "3"])
def test_unit_sums_match_national_totals(prras, code):
    nat = pd.read_parquet(config.BUILD / "national_totals.parquet")
    for y in config.YEARS:
        ours = prras[(prras.code == code) & (prras.year == y)].value.sum()
        theirs = nat[(nat.code == code) & (nat.year == y)].value.sum()
        assert abs(ours - theirs) < 1.0, (code, y, ours, theirs)


def test_functions_match_spending_for_almost_all(units):
    res = pd.read_parquet(config.BUILD / "results.parquet")
    bad = res.kvaliteta.str.contains("funkcije_ne_odgovaraju_rashodima").sum()
    assert bad / len(res) < 0.02


def test_openness_layer_covers_portal_publishers(units):
    assert units.portal_objavljuje.sum() > 250
    assert units.ckan_org.dropna().is_unique


def test_overdue_rules_match_the_units_own_notes():
    """docs/research/05: Sveta Marija reports its whole loan as overdue in Bilanca 2025,
    while its notes say overdue liabilities were 1.625,85 €. Povljana's debt stays overdue."""
    res = pd.read_parquet(config.BUILD / "results.parquet")
    last = res[res.year == 2025].set_index("naziv")
    sm = last.loc["Općina Sveta Marija"]
    assert sm.kredit_iskazan_dospio and abs(sm.DO - 1625.85) < 1.0
    pov = last.loc["Općina Povljana"]
    assert not pov.kredit_iskazan_dospio and pov.ogranicenje_do and pov.ocjena == 2


def test_geometry_covers_every_town_and_municipality(units):
    topo = json.loads((config.BUILD / "geo" / "jls.topo.json").read_text(encoding="utf-8"))
    codes = {g["properties"]["sifra"] for g in topo["objects"]["jls"]["geometries"]}
    assert codes == set(units[units.vrsta != "zupanija"].sifra)
    assert len(topo["objects"]["zupanije"]["geometries"]) == 21
    # official areas add up to the DZS total for Croatia (56.561,5 km²)
    assert abs(units[units.vrsta != "zupanija"].povrsina_km2.sum() - 56_561.5) < 1


def test_neighbours_are_symmetric_and_every_county_is_connected(units):
    s = json.loads((config.BUILD / "geo" / "susjedi.json").read_text(encoding="utf-8"))
    for a, v in s.items():
        for kind in ("kopno", "more"):
            for b, km in v[kind].items():
                assert s[b][kind][a] == km, (a, b, kind)
    jls = units[units.vrsta != "zupanija"]
    for zup, grp in jls.groupby("zup_id"):
        codes = set(grp.sifra)
        seen, stack = set(), [next(iter(codes))]
        while stack:
            c = stack.pop()
            if c not in seen:
                seen.add(c)
                stack += [n for kind in ("kopno", "more") for n in s[c][kind] if n in codes]
        assert seen == codes, zup


def test_islands_match_the_map(units):
    jls = units[units.vrsta != "zupanija"].set_index("naziv")
    no_land = set(jls[jls.n_susjeda == 0].index)
    assert no_land == {"Općina Lastovo", "Općina Mljet", "Općina Sali", "Općina Šolta", "Općina Vir"}
    assert jls.otok.astype(bool).sum() == 44
    assert jls.loc["Grad Krk", "otok"] and not jls.loc["Općina Orebić", "otok"]   # Pelješac is a peninsula


def test_every_unit_has_a_grade_in_last_year():
    res = pd.read_parquet(config.BUILD / "results.parquet")
    last = res[res.year == config.LAST_YEAR]
    assert last.ocjena.notna().all()
