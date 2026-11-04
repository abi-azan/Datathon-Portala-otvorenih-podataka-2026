"""Fiscal equalization formula (pipeline/izravnanje.py) on invented numbers, plus the check
against the MF table when data/raw/izravnanje/ is there."""
import pandas as pd
import pytest

from pipeline import config, izravnanje as iz

REF = {"opcina": 700.0, "grad": 650.0}
YEARS = [2021, 2022, 2023, 2024, 2025]


def unit(kap, st, vrsta="opcina"):
    return {"kapacitet_pc": kap, "stanovnici": st, "vrsta": vrsta}


def with_years(kap, st, vrsta, prirez, stopa):
    """A member with MF-style yearly amounts: equal amounts every year, at its own rates."""
    return {**unit(kap, st, vrsta), "kap": {y: kap * st for y in YEARS},
            "prirez_max": prirez, "stopa_max": stopa}


def test_full_amount_is_gap_times_population_and_never_negative():
    assert iz.puni_iznos(400.0, 700.0, 1000) == pytest.approx(300_000.0)
    assert iz.puni_iznos(800.0, 700.0, 1000) == 0.0          # čl. 8. st. 1.: no entitlement above
    assert iz.puni_iznos(700.0, 700.0, 1000) == 0.0


def test_both_below_reference_the_sum_does_not_change():
    a, b = unit(400.0, 2000), unit(250.0, 600)
    r = iz.za_spajanje([a, b], False, referentne=REF)
    assert r["puni_clanice"] == pytest.approx(300 * 2000 + 450 * 600)
    assert r["puni_spojena"] == pytest.approx(r["puni_clanice"])
    assert r["promjena"] == pytest.approx(0.0, abs=0.01)
    assert r["kapacitet_pc"] == pytest.approx((400 * 2000 + 250 * 600) / 2600, abs=0.005)
    assert "kapacitet_zbroj_clanica" in r["oznake"] and "clanica_iznad_referentne" not in r["oznake"]


def test_linear_also_with_cents_that_do_not_divide():
    r = iz.za_spajanje([unit(419.41, 2673), unit(270.54, 1002)], False, referentne={"opcina": 699.84})
    assert r["promjena"] == pytest.approx(0.0, abs=0.01)


def test_one_member_above_reference_lowers_equalization():
    poor, rich = unit(400.0, 1000), unit(900.0, 1000)
    r = iz.za_spajanje([poor, rich], False, referentne=REF)
    assert r["puni_clanice"] == pytest.approx(300_000.0)     # the rich one has 0, not a negative amount
    assert r["kapacitet_pc"] == pytest.approx(650.0)          # the rich member's surplus fills the gap
    assert r["puni_spojena"] == pytest.approx(50 * 2000)
    assert r["promjena"] == pytest.approx(-200_000.0)
    assert "clanica_iznad_referentne" in r["oznake"]


def test_one_above_but_merged_still_below_keeps_part():
    r = iz.za_spajanje([unit(400.0, 3000), unit(800.0, 1000)], False, referentne=REF)
    assert r["kapacitet_pc"] == pytest.approx(500.0)
    assert r["puni_spojena"] == pytest.approx(200 * 4000)
    assert r["promjena"] == pytest.approx(200 * 4000 - 300 * 3000)


def test_municipality_into_town_takes_the_town_reference_value():
    town, muni = unit(500.0, 4000, "grad"), unit(500.0, 1000)
    r = iz.za_spajanje([town, muni], True, referentne=REF)
    assert r["vrsta"] == "grad" and r["referentna_pc"] == REF["grad"]
    # the municipality was measured against 700, the merged town against 650
    assert r["puni_clanice"] == pytest.approx(150 * 4000 + 200 * 1000)
    assert r["puni_spojena"] == pytest.approx(150 * 5000)
    assert r["promjena"] == pytest.approx(-50 * 1000)
    assert "kapacitet_po_stopama_clanica" in r["oznake"]      # no yearly amounts, no rate recompute


def test_two_municipalities_becoming_a_town_by_decision():
    r = iz.za_spajanje([unit(500.0, 1000), unit(500.0, 1000)], True, referentne=REF)
    assert r["promjena"] == pytest.approx(-2 * 50 * 1000)


def test_rate_recompute_raises_municipality_capacity_at_town_rates():
    town = with_years(500.0, 4000, "grad", 12.0, 0.21)
    muni = with_years(500.0, 1000, "opcina", 10.0, 0.20)
    r = iz.za_spajanje([town, muni], True, referentne=REF)
    assert r["stope"] == {"prirez_max": 12.0, "stopa_max": 0.21}
    # municipality years 2021-2023 x 1.12/1.10, 2024-2025 x 0.21/0.20
    f = (3 * 1.12 / 1.10 + 2 * 0.21 / 0.20) / 5
    assert r["kapacitet_pc"] == pytest.approx((500 * 4000 + 500 * 1000 * f) / 5000, abs=0.005)
    assert r["kapacitet_pc"] > r["kapacitet_pc_bez_preracuna"]
    assert r["puni_spojena"] < r["puni_spojena_bez_preracuna"]
    assert "kapacitet_preracunat_na_stope_spojene" in r["oznake"]
    plain = iz.za_spajanje([town, muni], True, referentne=REF, preracunaj_stope=False)
    assert plain["puni_spojena"] == pytest.approx(r["puni_spojena_bez_preracuna"])


def test_same_rates_no_recompute():
    a = with_years(400.0, 1000, "opcina", 10.0, 0.20)
    b = with_years(300.0, 1000, "opcina", 10.0, 0.20)
    r = iz.za_spajanje([a, b], False, referentne=REF)
    assert "kapacitet_zbroj_clanica" in r["oznake"] and r["promjena"] == pytest.approx(0.0, abs=0.01)


def test_rate_class_of_merged_town():
    small = [with_years(500, 4000, "grad", 12.0, 0.21), with_years(500, 1000, "opcina", 10.0, 0.20)]
    assert iz.stope_spojene(small, True) == {"prirez_max": 12.0, "stopa_max": 0.21}
    seat = [with_years(500, 20000, "grad", 12.0, 0.22), with_years(500, 1000, "opcina", 10.0, 0.20)]
    assert iz.stope_spojene(seat, True) == {"prirez_max": 12.0, "stopa_max": 0.22}
    big = [with_years(500, 31000, "grad", 15.0, 0.21), with_years(500, 5000, "opcina", 10.0, 0.20)]
    assert iz.stope_spojene(big, True) == {"prirez_max": 15.0, "stopa_max": 0.22}   # 36,000 > 35,000
    assert iz.stope_spojene(small[1:] * 2, False) == {"prirez_max": 10.0, "stopa_max": 0.20}


def test_no_counties_no_zagreb_no_single_member():
    with pytest.raises(ValueError):
        iz.za_spajanje([unit(1, 1, "zupanija"), unit(1, 1)], False, referentne=REF)
    with pytest.raises(ValueError):
        iz.za_spajanje([unit(1, 1, "zagreb"), unit(1, 1, "grad")], True, referentne=REF)
    with pytest.raises(ValueError):
        iz.za_spajanje([unit(1, 1)], False, referentne=REF)


def test_reference_values_leave_out_zagreb_and_add_half_for_municipalities():
    df = pd.DataFrame({
        "vrsta": ["opcina", "opcina", "grad", "grad", "zagreb", "zupanija"],
        "stanovnici": [1000, 3000, 2000, 2000, 10000, 8000],
        "P1": [200_000.0, 600_000.0, 800_000.0, 1_200_000.0, 50_000_000.0, 800_000.0],
    })
    ref = iz.referentne_vrijednosti(df)
    assert ref["opcina"] == pytest.approx(200.0 * 1.5)
    assert ref["grad"] == pytest.approx(500.0)           # Zagreb's 5,000/inhabitant left out
    assert ref["zupanija"] == pytest.approx(100.0)


def test_shares_and_payout():
    u = iz.udjeli([300.0, 100.0, 0.0])
    assert list(u) == pytest.approx([0.75, 0.25, 0.0])
    assert iz.isplata(u[0], 1000.0) == pytest.approx(750.0)


# ---------------------------------------------------------------- real MF table

needs_mf = pytest.mark.skipif(not iz.XLSX.exists(), reason="no data/raw/izravnanje (download the MF table)")


@needs_mf
def test_mf_table_parses_all_units():
    df = iz.parse_mf()
    assert len(df) == 576
    assert df["vrsta"].value_counts().to_dict() == {"opcina": 428, "grad": 127, "zupanija": 20, "zagreb": 1}
    assert df.attrs["godine"] == list(range(config.MF_FI_YEAR - 6, config.MF_FI_YEAR - 1))
    assert set(df.attrs["referentne_mf"]) == {"opcina", "grad", "zupanija"}


@needs_mf
def test_formula_reproduces_mf():
    res = iz.provjera(units_csv=None)
    assert res["prolazi"]
    assert res["puni"]["udio_prolazi"] >= iz.PRAG_JEDINICA
    assert all(v["jednako"] for v in res["referentne"].values())


@needs_mf
@pytest.mark.skipif(not (config.BUILD / "units.csv").exists(), reason="run pipeline.build first")
def test_every_unit_matches_the_register():
    m = iz.ucitaj()
    assert m["oib"].notna().all(), m.loc[m["oib"].isna(), "naziv_mf"].tolist()
    assert m["oib"].is_unique
