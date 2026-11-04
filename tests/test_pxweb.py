"""DZS PxWeb layer (pipeline/pxweb.py).

The first tests need no network and no build. The rest check data/build/dzs.parquet and the raw
answers in data/raw/pxweb; run `python -m pipeline.pxweb` first, or they are skipped.
"""
import hashlib
import json

import pandas as pd
import pytest

from pipeline import config, pxweb


# ---------------------------------------------------------------- without data

@pytest.mark.parametrize("a, b", [
    ("Malinska-Dubašnica", "Općina Malinska Dubašnica"),
    ("Zlatar-Bistrica", "Zlatar Bistrica"),
    ("Otok (Vukovarsko-srijemska županija)", "Općina Otok"),
    ("Ližnjan- Lisignano", "Općina Ližnjan - Lisignano"),
    ("GRAD ZAGREB", "Grad Zagreb"),
])
def test_name_key(a, b):
    assert pxweb.name_key(a) == pxweb.name_key(b)


def test_bilingual_key_takes_the_croatian_part():
    assert pxweb._bilingual_key("Kaštelir-Labinci-Castellie-S.Domenica") == \
        pxweb._bilingual_key("Općina Kaštelir-Labinci - Castelliere-S. Domenica")


def test_jsonstat_frame_keeps_empty_cells_and_their_symbol():
    js = {"id": ["A", "Godina"], "size": [2, 2],
          "dimension": {"A": {"category": {"index": {"x": 0, "y": 1}, "label": {"x": "X", "y": "Y"}}},
                        "Godina": {"category": {"index": {"24": 0, "": 1}, "label": {"24": "2024", "": "2025"}}}},
          "value": [1, None, 3, None], "status": {"1": "-", "3": "z"}}
    f = pxweb.jsonstat_frame(js)
    assert f[["A", "Godina|tekst"]].values.tolist() == [["x", "2024"], ["x", "2025"], ["y", "2024"], ["y", "2025"]]
    assert f.vrijednost.tolist()[0::2] == [1, 3]
    assert f.vrijednost.isna().tolist() == [False, True, False, True]
    assert f.oznaka.fillna("").tolist() == ["", "-", "", "z"]


def test_build_query_reads_codes_from_the_metadata():
    meta = {"variables": [
        {"code": "Prostorna Jedinica", "values": ["00000000"], "valueTexts": ["REPUBLIKA HRVATSKA"]},
        {"code": "Godina", "values": ["19", "20", "21", ""], "valueTexts": ["2019", "2020", "2021", "2025"]},
        {"code": "Vrsta zgrade", "values": ["1", "2"], "valueTexts": ["Ukupno", "Stambene zgrade"]},
        {"code": "Mjerna jedinica", "values": ["1", "2"], "valueTexts": ["broj", "površina,m2"]},
    ]}
    sel = {q["code"]: q["selection"]["values"] for q in pxweb.build_query("PX14", meta)["query"]}
    assert sel == {"Prostorna Jedinica": ["*"], "Godina": ["21", ""], "Vrsta zgrade": ["1"], "Mjerna jedinica": ["1"]}
    meta["variables"].append({"code": "Novo", "values": ["0"], "valueTexts": ["?"]})
    with pytest.raises(ValueError, match="unexpected variable"):
        pxweb.build_query("PX14", meta)


def test_table_urls_are_encoded():
    assert pxweb.table_url("SP31_2") == ("https://web.dzs.hr/PXWeb/api/v1/hr/Stanovni%C5%A1tvo/"
                                         "Procjene%20stanovni%C5%A1tva/SP31_2.px")


# ---------------------------------------------------------------- built data

built = pytest.mark.skipif(not pxweb.OUT.exists() or not (config.BUILD / "units.csv").exists(),
                           reason="run python -m pipeline.pxweb first")


@pytest.fixture(scope="module")
def reg():
    return pxweb.load_register()


@pytest.fixture(scope="module")
def dzs():
    return pd.read_parquet(pxweb.OUT)


@pytest.fixture(scope="module")
def obs(reg):
    return {t: pxweb.observations(t, reg) for t in pxweb.TABLES}


def value(dzs, reg, slug, year, indicator):
    oib = reg.set_index("slug").loc[slug, "oib"]
    hit = dzs[(dzs.oib == oib) & (dzs.godina == year) & (dzs.pokazatelj == indicator)]
    assert len(hit) == 1, (slug, year, indicator)
    return hit.iloc[0]


@built
@pytest.mark.parametrize("table", list(pxweb.TABLES))
def test_every_unit_in_every_table_and_year(dzs, reg, table):
    d = dzs[dzs.tablica == table]
    jls = set(reg.loc[reg.vrsta != "zupanija", "oib"])
    zup = set(reg.loc[reg.vrsta == "zupanija", "oib"])
    assert len(jls) == 556 and len(zup) == 20
    for (year, ind), g in d.groupby(["godina", "pokazatelj"]):
        assert set(g.oib) == jls | zup, (table, year, ind)
    assert d.godina.min() == pxweb.FIRST_YEAR
    assert d.godina.max() >= 2024


@built
def test_no_duplicate_keys(dzs):
    assert not dzs.duplicated(["oib", "godina", "pokazatelj"]).any()
    assert dzs.oib.notna().all() and dzs.sifra.notna().all()
    assert set(dzs.pokazatelj) == {"stanovnici_procjena", "doseljeni", "odseljeni", "zivorodeni", "umrli",
                                   "postelje", "dolasci", "nocenja", "dozvole_zgrade"}


@built
@pytest.mark.parametrize("table", list(pxweb.TABLES))
def test_units_add_up_to_the_national_row(obs, table):
    """Towns and municipalities, and counties plus Grad Zagreb, both sum to the RH row. Arrivals and
    nights in BS_TU19 hide small units ("z"), so their unit sum falls short by up to about 1.5 %."""
    o = obs[table]
    key = ["godina", "pokazatelj"]
    rh = o[o.razina == "rh"].groupby(key).vrijednost.sum()
    jls = o[o.razina == "jls"].groupby(key).vrijednost.sum()
    zg = o[(o.razina == "jls") & (o.sifra == pxweb.ZAGREB)].groupby(key).vrijednost.sum()
    zup = o[o.razina == "zupanija"].groupby(key).vrijednost.sum() + zg
    assert len(rh) > 0
    pd.testing.assert_series_equal(zup, rh, check_names=False)
    for k, total in rh.items():
        hidden = table == "BS_TU19" and k[1] in ("dolasci", "nocenja")
        if hidden:
            assert 0.985 * total <= jls[k] < total, (table, k, jls[k], total)
        else:
            assert jls[k] == total, (table, k, jls[k], total)


@built
@pytest.mark.parametrize("table", list(pxweb.TABLES))
def test_counties_equal_their_units_where_nothing_is_hidden(obs, reg, table):
    o = obs[table]
    zup_of = reg.set_index("sifra").zup_id
    j = o[o.razina == "jls"].assign(zup_id=lambda d: d.sifra.map(zup_of))
    s = j[j.oznaka != "z"].groupby(["zup_id", "godina", "pokazatelj"]).vrijednost.sum()
    hidden = set(j.loc[j.oznaka == "z", ["zup_id", "godina", "pokazatelj"]].itertuples(index=False, name=None))
    z = o[o.razina == "zupanija"].assign(zup_id=lambda d: d.sifra.map(zup_of))
    for r in z.itertuples():
        k = (r.zup_id, r.godina, r.pokazatelj)
        if k in hidden:
            assert s[k] < r.vrijednost, (table, k)
        else:
            assert s[k] == r.vrijednost, (table, k, s[k], r.vrijednost)


@built
@pytest.mark.parametrize("slug, year, indicator, expected", [
    # docs/research/09-portal-dodatni-izvori.md §2.2 and §2.4
    ("grad-novalja", 2021, "stanovnici_procjena", 3722),
    ("grad-novalja", 2024, "stanovnici_procjena", 4285),
    ("grad-pag", 2021, "stanovnici_procjena", 3156),
    ("grad-pag", 2024, "stanovnici_procjena", 3352),
    ("grad-pag", 2024, "doseljeni", 255),
    ("grad-pag", 2024, "odseljeni", 115),
    ("opcina-bedenica", 2024, "doseljeni", 35),
    ("opcina-bedenica", 2024, "odseljeni", 31),
    ("grad-novalja", 2025, "nocenja", 1_890_591),
    ("grad-novalja", 2025, "postelje", 25_726),
    ("grad-pag", 2025, "nocenja", 776_716),
    ("grad-pag", 2025, "postelje", 10_814),
    ("opcina-bedenica", 2025, "postelje", 19),
    ("grad-novalja", 2024, "dozvole_zgrade", 91),
    ("grad-novalja", 2025, "dozvole_zgrade", 44),
    ("grad-pag", 2024, "dozvole_zgrade", 31),
    ("grad-pag", 2025, "dozvole_zgrade", 41),
    ("opcina-bedenica", 2024, "dozvole_zgrade", 1),
    ("opcina-bedenica", 2025, "dozvole_zgrade", 2),
])
def test_known_values(dzs, reg, slug, year, indicator, expected):
    assert value(dzs, reg, slug, year, indicator).vrijednost == expected


@built
def test_national_samples(obs):
    rh = obs["SP31_2"]
    rh = rh[rh.razina == "rh"].set_index("godina").vrijednost
    assert rh[2021] == 3_862_305 and rh[2024] == 3_874_350


@built
def test_empty_cells_are_nan_with_their_symbol(dzs, reg):
    """DZS writes no zeros: "-" (nema pojave) and "z" (hidden) cells are NaN and keep the symbol."""
    assert not (dzs.vrijednost == 0).any()
    assert dzs.vrijednost.isna().sum() == dzs.oznaka.isin(["-", "z"]).sum()
    assert set(dzs.oznaka.dropna()) <= {"-", "z"}
    b = value(dzs, reg, "opcina-bedenica", 2025, "nocenja")
    assert pd.isna(b.vrijednost) and b.oznaka == "z"
    t = dzs[dzs.tablica == "BS_TU19"].pivot_table(index=["oib", "godina"], columns="pokazatelj",
                                                  values="oznaka", aggfunc="first")
    dash = t.postelje == "-"           # no beds, so no arrivals and no nights either
    assert dash.any() and (t.loc[dash, "dolasci"] == "-").all() and (t.loc[dash, "nocenja"] == "-").all()


@built
def test_code_keyed_tables_agree_with_the_register(obs, reg):
    """The DGU code and the name point to the same unit. Bilingual names are compared by their
    Croatian part, because BS_TU19 writes "Motovun - Montana" (Montona)."""
    names = reg.set_index("sifra").naziv.map(pxweb.name_key)
    first = reg.set_index("sifra").naziv.map(pxweb._bilingual_key)
    vrsta = reg.set_index("sifra").vrsta
    for table in ("BS_TU19", "PX14"):
        o = obs[table].drop_duplicates("kod")
        j = o[o.razina == "jls"]
        bad = j[(j.naziv_dzs.map(pxweb.name_key) != j.sifra.map(names))
                & (j.naziv_dzs.map(pxweb._bilingual_key) != j.sifra.map(first))]
        assert bad.empty, (table, bad[["naziv_dzs", "sifra"]].values.tolist())
        z = o[o.razina == "zupanija"]
        assert (z.naziv_dzs.map(pxweb.name_key) == z.sifra.map(names)).all(), table
    px = obs["PX14"].drop_duplicates("kod")
    px = px[px.razina == "jls"]
    assert (px.kod.str[2].map({"1": "grad", "2": "opcina"}) == px.sifra.map(vrsta)).all()


@built
def test_codes_document(reg):
    doc = json.loads(pxweb.CODES_OUT.read_text(encoding="utf-8"))
    units = doc["jedinice"]
    assert set(units) == set(reg.oib)
    pag = units[reg.set_index("slug").loc["grad-pag", "oib"]]
    assert pag["sifra"] == "03166" and pag["BS_TU19"] == "HR031303166" and pag["PX14"] == "13103166"
    for table, t in doc["meta"]["tablice"].items():
        codes = [u[table] for u in units.values() if table in u]
        assert len(codes) == 576 and len(set(codes)) == 576, table
        assert t["url"] == pxweb.table_url(table)
        area = [q for q in t["upit"]["query"] if q["code"] == t["varijabla"]]
        assert area[0]["selection"] == {"filter": "item", "values": ["{kod}"]}
        meta = json.loads(pxweb._raw(table, ".meta").read_text(encoding="utf-8"))
        var = next(v for v in meta["variables"] if v["code"] == t["varijabla"])
        label = dict(zip(var["values"], var["valueTexts"]))
        assert pxweb.name_key(label[pag[table]]) == "PAG", table
        assert pag["nazivi"][table] == label[pag[table]], table        # the browser checks this label live


@built
def test_every_call_is_in_the_provenance_log():
    log = json.loads(config.SOURCES_LOG.read_text(encoding="utf-8"))
    for table in pxweb.TABLES:
        for key, method in ((pxweb._log_key(table), "POST"), (pxweb._log_key(table) + "_meta", "GET")):
            e = log[key]
            assert e["url"] == pxweb.table_url(table) and e["method"] == method, key
            assert {"retrieved", "sha256", "bytes", "file", "publisher", "license"} <= set(e), key
            data = (config.ROOT / e["file"]).read_bytes()
            assert hashlib.sha256(data).hexdigest() == e["sha256"], f"{key}: file changed after download"
        assert log[pxweb._log_key(table)]["body"]["response"] == {"format": "json-stat2"}
