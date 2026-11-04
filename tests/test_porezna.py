"""Porezna uprava layer (pipeline/porezna.py): the parsers on small inputs, and checks on the
built tables data/build/porezna_*.parquet. Run `python -m pipeline.porezna` first; the checks
on data are skipped when the tables are missing."""
import numpy as np
import pandas as pd
import pytest

from pipeline import config, porezna as pz

need_doh = pytest.mark.skipif(not pz.OUT_DOHODAK.exists(), reason="run python -m pipeline.porezna first")
need_stope = pytest.mark.skipif(not pz.OUT_STOPE.exists(), reason="run python -m pipeline.porezna first")
need_raw = pytest.mark.skipif(not (pz.RAW_DIR / pz.RESURSI["porezna_neto_dohodak"][2]).exists(),
                              reason="data/raw/porezna is missing")
GODINE_DOHODAK = [2022, 2023, 2024, 2025]


# ---------------------------------------------------------------- parsers, no data needed

def test_raspon_reads_numbers_and_text_ranges():
    assert pz._raspon(0.03) == (0.03, 0.03)
    assert pz._raspon(5) == (5.0, 5.0)
    assert pz._raspon("3,60 do 4,50") == (3.6, 4.5)
    assert pz._raspon(" 2,00 do 4,00") == (2.0, 4.0)
    assert pz._raspon("1,06  do 1,99") == (1.06, 1.99)
    assert pz._raspon("1,00-3,00%") == pytest.approx((0.01, 0.03))   # Novalja, consumption tax
    lo, hi = pz._raspon("#VALUE!")
    assert np.isnan(lo) and np.isnan(hi)


def test_sifra_pads_the_dgu_code():
    assert pz._sifra(19) == "00019"
    assert pz._sifra(1333.0) == "01333"
    assert pz._sifra("5207") == "05207"
    assert pz._sifra(None) is None and pz._sifra("Rbr.") is None


def test_resource_is_picked_by_pattern_newest_edition_first():
    res = [{"id": "a", "url": "https://x/download/neto-dohodak-stanovnistva2024-5.xlsx"},
           {"id": "b", "url": "https://x/download/pk_neto-dohodak-stanovnistva-2022_2025-30_9_26-1.xlsx"},
           {"id": "c", "url": "https://x/download/neto-dohodak-stanovnistva-2021_2024.xlsx"},
           {"id": "d", "url": "https://x/download/dohodak-po-jls-i-razredima-2023-2024-3.xlsx"}]
    pattern = pz.RESURSI["porezna_neto_dohodak"][1]
    assert pz._izaberi(res, pattern)["id"] == "b"
    assert pz._izaberi(res[:1], pattern) is None


def test_every_rate_workbook_on_the_portal_has_a_pattern():
    names = {
        "porezna_stope_dohodak": "tablica-poreznih-stopa-godinjeg-poreza-na-dohodak-za-2026-godinu-1.xlsx",
        "porezna_stope_usporedba": "stope_poreza_na_dohodak_usporedba-2025-i-2026.xlsx",
        "porezna_potrosnja": "visina-stopa-poreza-na-potronju-za-2026.-godinu.xlsx",
        "porezna_nekretnine": "usporedba-poreza-na-nekretnine-25_26-1.xlsx",
    }
    res = [{"id": k, "url": "https://x/download/" + v} for k, v in names.items()]
    res.append({"id": "pausal", "url": "https://x/download/visina-paualnog-poreza-na-dohodak-po-jls-za-2026.-godinu.xlsx"})
    for key in names:
        assert pz._izaberi(res, pz.RESURSI[key][1])["id"] == key, key


def test_sheet_year_and_currency_must_agree():
    rows = [("NETO DOHODAK STANOVNIŠTVA ... U 2022. GODINI",), (None, "iznosi u kunama ")]
    assert pz._list_godina("2022 HRK", rows) == (2022, "HRK")
    assert pz._list_godina("Napomene", rows) == (None, None)
    with pytest.raises(ValueError):
        pz._list_godina("2023 HRK", rows)
    with pytest.raises(ValueError):
        pz._list_godina("2022 EUR", rows)


def test_names_are_matched_within_the_county():
    units = pd.DataFrame([
        ("1", "13", "OPĆINA PRIVLAKA", "Općina Privlaka", "opcina", 13),
        ("2", "16", "OPĆINA PRIVLAKA", "Općina Privlaka", "opcina", 16),
        ("3", "18", "OPĆINA BALE", "Općina Bale - Valle", "opcina", 18),
        ("4", "18", "OPĆINA KAŠTELIR-LABINCI", "Općina Kaštelir-Labinci - Castelliere-S. Domenica", "opcina", 18),
        ("5", "Z13", "ZADARSKA ŽUPANIJA", "Zadarska županija", "zupanija", 13),
    ], columns=["oib", "sifra", "naziv_mf", "naziv", "vrsta", "zup_id"])
    m = pz.spoji_nazive([(16, "PRIVLAKA"), (13, "PRIVLAKA"), (18, "BALE - VALLE"),
                         (18, "KAŠTELIR-LABINCI - CASTELLIERE-S. D")], units)
    assert m.oib.tolist() == ["2", "1", "3", "4"]
    assert m.spoj.tolist() == ["naziv", "naziv", "naziv", "labavo"]
    assert pz.spoji_nazive([(13, "BALE - VALLE")], units).oib.isna().all()   # wrong county


# ---------------------------------------------------------------- built data

@pytest.fixture(scope="module")
def units():
    return pd.read_csv(config.BUILD / "units.csv", dtype={"oib": str, "rkp": str, "sifra": str})


@pytest.fixture(scope="module")
def doh():
    return pd.read_parquet(pz.OUT_DOHODAK)


@pytest.fixture(scope="module")
def stope():
    return pd.read_parquet(pz.OUT_STOPE)


def _jedinica(doh, units, slug, godina, vrsta=pz.UKUPNO):
    sifra = units.set_index("slug").loc[slug, "sifra"]
    r = doh[(doh.sifra == sifra) & (doh.godina == godina) & (doh.vrsta_dohotka == vrsta)]
    assert len(r) == 1
    return r.iloc[0]


@need_doh
def test_income_covers_all_576_units_every_year(doh, units):
    assert sorted(doh.godina.unique()) == GODINE_DOHODAK
    tot = doh[doh.vrsta_dohotka == pz.UKUPNO]
    for g, d in tot.groupby("godina"):
        assert d.oib.nunique() == len(d) == 576, g
        assert set(d.oib) == set(units.oib), g
    assert (doh.set_index("oib").sifra == units.set_index("oib").sifra.reindex(doh.oib)).all()


@need_doh
def test_income_has_no_duplicate_keys(doh):
    assert not doh.duplicated(["oib", "godina", "vrsta_dohotka"]).any()
    assert doh.groupby(["oib", "godina"]).size().isin([9, 10]).all()   # 8 or 9 kinds + UKUPNO


@need_doh
def test_income_structure_follows_the_headers(doh):
    by_year = doh.groupby("godina")
    assert by_year.porez_s_prirezom.all().to_dict() == {2022: True, 2023: True, 2024: False, 2025: False}
    assert by_year.porez_s_prirezom.any().to_dict() == {2022: True, 2023: True, 2024: False, 2025: False}
    osig = set(doh.loc[doh.vrsta_dohotka == "osiguranje", "godina"])
    assert osig == {2022, 2023}                          # "DOHODAK OD OSIGURANJA" only until 2023
    assert set(doh.vrsta_dohotka) == {*pz.VRSTE.values(), pz.UKUPNO}


@need_doh
def test_income_county_sums(doh, units):
    """UKUPNO of the towns and municipalities of a county = UKUPNO ŽUPANIJA. The amounts add up to
    the cent; persons are distinct OIBs, and the units' counts add up to a little more."""
    z = pz.zbrojevi_zupanija(doh, units)
    assert len(z) == 20 * len(GODINE_DOHODAK) * len(pz.STUPCI)
    iznosi = z[z.stupac != "osobe"]
    assert (iznosi.razlika.abs() <= 1.0).all(), iznosi.loc[iznosi.razlika.abs().idxmax()].to_dict()
    osobe = z[z.stupac == "osobe"]
    rel = osobe.razlika / osobe.zupanija
    assert (rel >= 0).all() and (rel <= 0.06).all(), osobe.loc[rel.idxmax()].to_dict()


@need_doh
def test_income_kinds_add_up_to_the_total_where_nothing_is_suppressed(doh):
    kinds = doh[doh.vrsta_dohotka != pz.UKUPNO]
    suppressed = kinds.groupby(["oib", "godina"]).osobe.apply(lambda s: s.isna().any())
    s = kinds.groupby(["oib", "godina"])[pz.IZNOSI].sum(min_count=1)[~suppressed]
    t = doh[doh.vrsta_dohotka == pz.UKUPNO].set_index(["oib", "godina"])[pz.IZNOSI].loc[s.index]
    assert len(s) > 2000
    assert ((s - t).abs() <= 1.0).all().all()
    # a suppressed kind is empty in all columns, never a zero
    empty = kinds[kinds.osobe.isna()]
    assert empty[pz.IZNOSI].isna().all().all()


@need_doh
def test_income_sample_pag_2025(doh, units):
    """Research 09 §2.1: Pag 2025, UKUPNO OPĆINA: 4,198 persons, tax 3,197,794.81 EUR."""
    r = _jedinica(doh, units, "grad-pag", 2025)
    assert r.osobe == pz.UZORAK_PAG_2025["osobe"]
    assert r.porez == pytest.approx(pz.UZORAK_PAG_2025["porez"], abs=0.005)
    z = _jedinica(doh, units, "grad-pag", 2025, "zaposlenici")
    assert z.osobe == 2164 and z.porez == pytest.approx(1_800_703.52, abs=0.005)


@need_doh
def test_income_2022_is_converted_from_kuna(doh, units):
    """Bedenica 2022, UKUPNO OPĆINA: tax 4,071,101.93 kn, persons 1,004."""
    r = _jedinica(doh, units, "opcina-bedenica", 2022)
    assert r.osobe == 1004
    assert r.porez == pytest.approx(4_071_101.93 / pz.HRK_EUR, abs=0.005)


@need_doh
@need_raw
def test_income_counties_and_zagreb_add_up_to_the_republic(doh):
    raw = pz.parse_dohodak(pz.RAW_DIR / pz.RESURSI["porezna_neto_dohodak"][2])
    r = pz.zbroj_republike(doh, raw[raw.razina == "rh"])
    assert len(r) == len(GODINE_DOHODAK) * len(pz.STUPCI)
    assert (r[r.stupac != "osobe"].razlika.abs() <= 1.0).all()


@need_stope
def test_rates_cover_all_556_units_every_year(stope, units):
    jls = units[units.vrsta != "zupanija"]
    assert sorted(stope.godina.unique()) == [2025, 2026]
    for g, d in stope.groupby("godina"):
        assert len(d) == d.oib.nunique() == 556, g
        assert set(d.oib) == set(jls.oib), g
        assert d[["niza", "visa", "niza_max", "potrosnja_max", "nekretnine_max"]].notna().all().all(), g
    assert not stope.duplicated(["oib", "godina"]).any()


@need_stope
def test_rates_against_the_cap(stope, units):
    assert ((stope.niza >= 0.15 - 1e-9) & (stope.niza <= stope.niza_max + 1e-9)).all()
    assert (stope.visa > stope.niza).all()
    assert (stope.ispod_maksimuma == (stope.niza < stope.niza_max - 1e-9)).all()
    assert set(stope.niza_max.round(4)) <= {0.20, 0.21, 0.22, 0.23}
    s26 = stope[stope.godina == 2026].merge(units[["oib", "slug", "vrsta"]], on="oib").set_index("slug")
    assert s26.loc["grad-zagreb", "niza_max"] == pytest.approx(0.23)
    assert (s26.loc[s26.vrsta == "opcina", "niza_max"] == 0.20).all()
    # research 09 §2.3
    assert s26.loc["grad-split", ["niza", "niza_max"]].tolist() == pytest.approx([0.215, 0.22])
    assert s26.loc["grad-karlovac", ["niza", "niza_max"]].tolist() == pytest.approx([0.19, 0.22])
    assert s26.loc["opcina-baska", ["niza", "visa"]].tolist() == pytest.approx([0.15, 0.25])
    assert bool(s26.loc["grad-rijeka", "ispod_maksimuma"]) and bool(s26.loc["grad-osijek", "ispod_maksimuma"])
    assert 100 <= int(s26.ispod_maksimuma.sum()) <= 150


@need_stope
def test_consumption_and_property_tax(stope, units):
    s26 = stope[stope.godina == 2026].merge(units[["oib", "slug"]], on="oib").set_index("slug")
    assert (stope.potrosnja_min <= stope.potrosnja_max).all() and (stope.potrosnja_max <= 0.03 + 1e-9).all()
    assert s26.loc["grad-novalja", ["potrosnja_min", "potrosnja_max"]].tolist() == pytest.approx([0.01, 0.03])
    assert (stope.nekretnine_min <= stope.nekretnine_max).all()
    assert set(stope.nekretnine_naplata) == {"JLS", "PU"}
    assert s26.loc["grad-pag", ["nekretnine_min", "nekretnine_max"]].tolist() == pytest.approx([5.0, 6.25])
