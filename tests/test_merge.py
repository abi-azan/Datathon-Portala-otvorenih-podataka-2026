"""Merger simulator (pipeline/merge.py) against the finished build. Run pipeline.build first."""
import json
import math
import random

import pandas as pd
import pytest

from pipeline import config, merge, methodology

pytestmark = pytest.mark.skipif(not (config.BUILD / "wide.parquet").exists(), reason="run pipeline.build first")


@pytest.fixture(scope="module")
def data():
    return merge.Data.load()


@pytest.fixture(scope="module")
def res():
    return pd.read_parquet(config.BUILD / "results.parquet").set_index(["oib", "year"])


def by_name(data, naziv):
    return next(o for o, u in data.units.items() if u["naziv"] == naziv)


def close(a, b):
    if a == b:                                  # also inf == inf (I3 when debt has no surplus)
        return True
    if a is None or b is None or (isinstance(a, float) and math.isnan(a)):
        return (a is None or math.isnan(a)) and (b is None or (isinstance(b, float) and math.isnan(b)))
    return abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))


def test_one_member_reproduces_the_published_result(data, res):
    """Summing a single unit with the simulator's inputs gives exactly its own result, for
    every unit and year: no input the methodology reads is left out, and rule 1 carried as an
    amount behaves like rule 1 tested on the row."""
    for oib, u in data.units.items():
        got = methodology.evaluate_unit(merge.merged_rows(data, [oib]), u["stanovnici_2021"])
        for y, r in got.items():
            want = res.loc[(oib, y)]
            for k in ("bodovi", "ocjena", "DO", "PO", "SD", "ND", "I1", "I3", "I5"):
                assert close(r[k], want[k]), (u["naziv"], y, k, r[k], want[k])
            assert ",".join(r["zastavice"]) == (want["zastavice"] or ""), (u["naziv"], y)
            assert ",".join(r["kvaliteta"]) == (want["kvaliteta"] or ""), (u["naziv"], y)


def test_pag_island_example(data):
    """The example from the 4.11. explanation: Povljana (općina) + Pag (grad) is a city."""
    m = merge.merge(data, [by_name(data, "Općina Povljana"), by_name(data, "Grad Pag")])
    assert m["vrsta"] == "grad"
    assert m["stanovnici"] == 669 + 3175
    assert m["skupina"] == "gradovi 2.000-5.000"
    last = m["godine"][config.LAST_YEAR]
    assert 1 <= last["rang"] <= last["n_skupine"]


@pytest.mark.parametrize("names, message", [
    (["Općina Kolan", "Grad Novalja"], "iste županije"),                     # neighbours across a county border
    (["Općina Povljana", "Zadarska županija"], "županije i Grad Zagreb"),
    (["Grad Zagreb", "Grad Velika Gorica"], "županije i Grad Zagreb"),
    (["Općina Povljana", "Općina Kolan"], "jednu cjelinu"),                 # same county, not touching
    (["Općina Povljana"], "2 do"),
])
def test_rules(data, names, message):
    with pytest.raises(ValueError, match=message):
        merge.merge(data, [by_name(data, n) for n in names])


def test_order_of_members_does_not_matter(data):
    rng = random.Random(1)
    for g in rng.sample(merge.groups(data, 3), 40):
        oibs = [data.oib_of[s] for s in g]
        a = merge.merge(data, oibs)
        b = merge.merge(data, list(reversed(oibs)))
        assert json.dumps(merge.summary(a), sort_keys=True) == json.dumps(merge.summary(b), sort_keys=True)


def test_overdue_debt_is_the_sum_of_the_members(data, res):
    """Rule 1 per member: the merged unit's overdue liabilities (DO) are exactly the members'
    DO added up, also when a member has a loan reported as overdue but repaid (rule 1)."""
    rule1 = {o for (o, y), r in res.iterrows() if r["kredit_iskazan_dospio"]}
    assert rule1, "the build has no unit where rule 1 applies"
    checked = 0
    for g in merge.groups(data, 2):
        oibs = [data.oib_of[s] for s in g]
        if not rule1 & set(oibs):
            continue
        m = merge.merge(data, oibs)
        for y, r in m["godine"].items():
            assert close(r["DO"], sum(res.loc[(o, y), "DO"] for o in oibs)), (g, y)
            members_flagged = any(res.loc[(o, y), "kredit_iskazan_dospio"] for o in oibs)
            assert r["kredit_iskazan_dospio"] == members_flagged, (g, y)
            checked += 1
    assert checked > 0


def test_groups_are_connected_same_county_and_unique(data):
    gs = merge.groups(data)
    assert len(gs) == len(set(gs))
    sizes = pd.Series([len(g) for g in gs]).value_counts().to_dict()
    assert set(sizes) == {2, 3, 4}
    rng = random.Random(2)
    for g in rng.sample(gs, 300):
        merge.check(data, [data.oib_of[s] for s in g])   # raises if a rule is broken


def test_precomputed_files_cover_every_group(data):
    files = sorted((config.BUILD / "simulator").glob("zup-*.json"))
    assert len(files) == 20
    keys = set()
    for f in files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        for k, v in doc["skupine"].items():
            assert k == "-".join(v["clanice"]) and v["clanice"] == sorted(v["clanice"])
            assert v["zadnja"]["ocjena"] in (1, 2, 3, 4, 5)
            keys.add(k)
    assert keys == {"-".join(g) for g in merge.groups(data)}


def test_savings_stay_inside_their_bounds(data):
    """research/08 §7.1 (decided 4.11.): the realistic upper end is at most 10 % of the summed
    administration cost and never above the scale effect; scale effect and the gap without
    merging are never negative."""
    rng = random.Random(3)
    for g in rng.sample(merge.groups(data), 400):
        u = merge.merge(data, [data.oib_of[s] for s in g])["usteda"]
        assert u["godina"] == config.LAST_YEAR
        assert u["razmjer"] >= 0 and u["jaz_bez_spajanja"] >= 0
        assert 0 <= u["realno_do"] <= merge.SAVINGS_SHARE * u["uprava_zbroj"] + 1e-6
        assert u["realno_do"] <= u["razmjer"] + 1e-6
        assert abs(u["razmjer"] - max(0.0, u["ocekivano_clanice"] - u["ocekivano"])) < 1e-6
        assert abs(u["ocekivano"] - u["medijan_pc"] * sum(data.units[data.oib_of[s]]["stanovnici_2021"] for s in g)) < 1e-6


def test_savings_count_only_the_scale_effect(data, res):
    """Dubrovnik + Mljet (research/08 §7.1): almost all of the old gap was Dubrovnik spending
    above large cities, which exists without merging. Mljet is valued at the median of cities
    of its size, the merged city at the median of large cities."""
    oibs = [by_name(data, "Grad Dubrovnik"), by_name(data, "Općina Mljet")]
    u = merge.merge(data, oibs)["usteda"]
    y = config.LAST_YEAR
    med = data.uprava_median
    n = {o: data.units[o]["stanovnici_2021"] for o in oibs}
    expected_members = med[("veliki gradovi", y)] * n[oibs[0]] + med[("gradovi do 2.000", y)] * n[oibs[1]]
    assert abs(u["ocekivano_clanice"] - expected_members) < 1e-6
    assert u["ocekivano"] == med[("veliki gradovi", y)] * sum(n.values())
    assert 150_000 < u["realno_do"] < 250_000                       # was 1,55 mil. € with the old formula
    own_gap = sum(max(0.0, (res.loc[(o, y), "uprava_pc"] - med[(data.units[o]["skupina"], y)]) * n[o]) for o in oibs)
    assert abs(u["jaz_bez_spajanja"] - own_gap) < 1e-6 and u["jaz_bez_spajanja"] > 30 * u["realno_do"]


def test_incentive_follows_nn_88_2022(data):
    """The largest member annexes; only annexed members in development groups I-V bring
    2 x their equalization (estimated payout) for five years and the capital amount."""
    vukovar, bogdanovci = by_name(data, "Grad Vukovar"), by_name(data, "Općina Bogdanovci")
    m = merge.merge(data, [vukovar, bogdanovci])
    p = m["poticaj"]
    assert p["pripaja"] == data.units[vukovar]["sifra"]
    assert p["s_pravom"] == [data.units[bogdanovci]["sifra"]]
    if m["izravnanje"] is not None:
        i = m["clanice"].index(data.units[bogdanovci]["sifra"])
        assert abs(p["izravnanje_isplata"] - m["izravnanje"]["puni_po_clanici"][i] * p["omjer_isplate"]) < 1e-6
        assert abs(p["godisnje"] - 2 * p["izravnanje_isplata"]) < 1e-6 and abs(p["ukupno"] - 5 * p["godisnje"]) < 1e-6
        assert 0.4 < p["omjer_isplate"] < 0.8
    assert p["kapitalni_do"] == merge.INCENTIVE_CAPITAL
    # Povljana (development group VI or higher) joining Pag brings nothing
    q = merge.merge(data, [by_name(data, "Grad Pag"), by_name(data, "Općina Povljana")])["poticaj"]
    assert q["s_pravom"] == [] and q["kapitalni_do"] == 0


def test_pag_island_savings(data, res):
    """Povljana + Pag: the block sums the members' administration and compares it with the
    median of 'gradovi 2.000-5.000'."""
    oibs = [by_name(data, "Općina Povljana"), by_name(data, "Grad Pag")]
    u = merge.merge(data, oibs)["usteda"]
    members = sum(res.loc[(o, config.LAST_YEAR), "uprava_pc"] * data.units[o]["stanovnici_2021"] for o in oibs)
    assert abs(u["uprava_zbroj"] - members) < 1.0
    peers = res.xs(config.LAST_YEAR, level="year")
    assert u["medijan_pc"] == peers[peers.skupina == "gradovi 2.000-5.000"].uprava_pc.median()
    assert u["uprava_zbroj"] > 0 and u["realno_do"] > 0 and not u["iznad_10000"]


def test_no_size_limit_for_karta_reforme(data):
    """merge(max_members=None) takes any connected group of one county (Karta reforme); the
    county, Zagreb and connectivity rules still hold."""
    g = min(g for g in merge.groups(data, 4) if len(g) == 4)
    oibs = [data.oib_of[s] for s in g]
    zup = data.units[oibs[0]]["zup_id"]
    extra = next(data.oib_of[n] for s in g for n in data.adj[s]
                 if data.oib_of[n] not in oibs and data.eligible(data.oib_of[n])
                 and data.units[data.oib_of[n]]["zup_id"] == zup)
    with pytest.raises(ValueError, match="2 do 4"):
        merge.merge(data, oibs + [extra])
    m = merge.merge(data, oibs + [extra], max_members=None)
    assert len(m["clanice"]) == 5 and m["usteda"] is not None
    with pytest.raises(ValueError, match="barem 2"):
        merge.merge(data, oibs[:1], max_members=None)
    with pytest.raises(ValueError, match="županije i Grad Zagreb"):
        merge.merge(data, [by_name(data, "Grad Zagreb"), by_name(data, "Grad Velika Gorica")], max_members=None)


@pytest.mark.skipif(not merge.izravnanje.XLSX.exists(), reason="MF equalization table not downloaded")
def test_equalization_block(data):
    """N5b (decision 17, docs/research/07): the full amount under the formula never grows with a
    merger (reference values fixed), is linear when every member is below its reference value
    and drops when a member is above it."""
    m = merge.merge(data, [by_name(data, "Općina Povljana"), by_name(data, "Grad Pag")])["izravnanje"]
    assert m["godina"] == data.fi["godina"] and "bez_prava_na_izravnanje" in m["oznake"] and m["promjena"] == 0
    jv = merge.merge(data, [by_name(data, "Općina Jelenje"), by_name(data, "Općina Viškovo")])["izravnanje"]
    assert jv["puni_po_clanici"][1] == 0 and jv["promjena"] < -0.9 * jv["puni_clanice"]
    bt = merge.merge(data, [by_name(data, "Općina Barilović"), by_name(data, "Općina Tounj")])["izravnanje"]
    assert abs(bt["promjena"]) < 0.01 and bt["puni_clanice"] > 0
    rng = random.Random(4)
    for g in rng.sample(merge.groups(data), 300):
        e = merge.merge(data, [data.oib_of[s] for s in g])["izravnanje"]
        assert e["promjena"] <= 0.01 and abs(sum(e["puni_po_clanici"]) - e["puni_clanice"]) < 0.05


@pytest.mark.skipif(not merge.izravnanje.XLSX.exists(), reason="MF equalization table not downloaded")
def test_equalization_payout_is_a_share_of_a_fixed_budget(data):
    """Odluka 4.11.: the product shows the payout. It is the share of the sum of all full amounts
    times the budget line, so a merger moves money between units and the state budget is unchanged."""
    budget, total = merge.izravnanje.ISPLATA_2026, data.fi["puni_ukupno"]
    jv = merge.merge(data, [by_name(data, "Općina Jelenje"), by_name(data, "Općina Viškovo")])["izravnanje"]
    assert abs(jv["isplata_clanice"] - jv["puni_clanice"] * budget / total) < 1e-6
    after_total = total - jv["puni_clanice"] + jv["puni_spojena"]
    assert abs(jv["isplata_spojena"] - jv["puni_spojena"] * budget / after_total) < 1e-6
    assert -320_000 < jv["isplata_promjena"] < -300_000           # about -312.500 € (docs: explanation 4.11.)
    # what the other units receive after the merger is exactly what the merged one loses
    others_before = budget - jv["isplata_clanice"]
    others_after = budget - jv["isplata_spojena"]
    assert abs((others_after - others_before) + jv["isplata_promjena"]) < 1e-6
    bt = merge.merge(data, [by_name(data, "Općina Barilović"), by_name(data, "Općina Tounj")])["izravnanje"]
    assert abs(bt["isplata_promjena"]) < 0.01                       # linear case: nothing moves


needs_dzs = pytest.mark.skipif(not merge.DZS_PARQUET.exists(), reason="run pipeline.pxweb first (dzs.parquet)")


def test_dzs_symbols():
    """'-' (the phenomenon does not exist) counts as 0; any other empty cell, e.g. 'z' (hidden), is None."""
    assert merge.dzs_value(12.0, None) == 12.0
    assert merge.dzs_value(float("nan"), "-") == 0.0
    assert merge.dzs_value(float("nan"), "z") is None
    assert merge.dzs_value(None, None) is None


@needs_dzs
def test_demography_pag_povljana(data):
    """#/simulator?j=05738,03166: estimates summed per year, change 2021 -> 2025, births - deaths and
    in - out migration for 2025 summed; each member keeps only its own change (Pag 3.156 -> 3.358).
    2021-2024 are PxWeb, 2025 the DZS publication (docs/research/12 §2.3)."""
    m = merge.merge(data, [by_name(data, "Općina Povljana"), by_name(data, "Grad Pag")])
    d = merge.summary(m)["demografija"]
    assert m["clanice"] == ["03166", "05738"]
    assert (d["od"], d["do"]) == (2021, 2025)
    assert d["stanovnici"] == [3156 + 674, 3176 + 661, 3238 + 666, 3352 + 690, 3358 + 726]
    assert d["promjena"] == round(4084 / 3830 - 1, 3) == 0.066
    assert d["prirodna"] == (21 + 4) - (49 + 12)
    assert d["migracije"] == (190 + 70) - (156 + 26)
    assert d["clanice"] == [round(3358 / 3156 - 1, 3), round(726 / 674 - 1, 3)] == [0.064, 0.077]
    assert data.demo["izvor_po_godini"] == {"2021": "pxweb", "2022": "pxweb", "2023": "pxweb", "2024": "pxweb",
                                            "2025": "xlsx"}
    assert "oznake" not in d
    assert m["stanovnici"] == 669 + 3175                     # the score still uses Popis 2021


@needs_dzs
def test_demography_matches_the_long_table(data):
    """Vukovar + Bogdanovci recomputed straight from dzs.parquet."""
    df = pd.read_parquet(merge.DZS_PARQUET)
    oibs = [by_name(data, "Grad Vukovar"), by_name(data, "Općina Bogdanovci")]
    d = merge.merge(data, oibs)["demografija"]
    x = df[df.oib.isin(oibs)].groupby(["pokazatelj", "godina"]).vrijednost.sum()
    last = d["do"]
    assert d["stanovnici"] == [int(x[("stanovnici_procjena", y)]) for y in range(2021, last + 1)]
    assert d["prirodna"] == x[("zivorodeni", last)] - x[("umrli", last)]
    assert d["migracije"] == x[("doseljeni", last)] - x[("odseljeni", last)]
    bogdanovci = data.units[oibs[1]]["sifra"]
    i = merge.merge(data, oibs)["clanice"].index(bogdanovci)
    assert d["clanice"][i] == round(1427 / 1551 - 1, 3) == -0.08   # Bogdanovci −8,0 % (2021 -> 2025)


@needs_dzs
def test_demography_dash_counts_as_zero_and_is_kept(data):
    """Žumberak reports '-' live births in the last year (2025, DZS publication): 0 in the sum, the
    symbol listed in oznake. Its neighbour Samobor has births, so only one symbol."""
    last = data.demo["do"]
    cells = data.demo["celije"]
    zumberak, samobor = by_name(data, "Općina Žumberak"), by_name(data, "Grad Samobor")
    assert cells[(zumberak, "zivorodeni", last)] == (0.0, "-")
    d = merge.merge(data, [zumberak, samobor])["demografija"]
    want = cells[(samobor, "zivorodeni", last)][0] - cells[(samobor, "umrli", last)][0] - cells[(zumberak, "umrli", last)][0]
    assert d["prirodna"] == want
    assert d["oznake"] == [f"05401:zivorodeni:{last}:-"]


@needs_dzs
def test_demography_hidden_value_makes_the_sum_null(data, monkeypatch):
    """A member with a hidden ('z') estimate: its change and the merged change are null, the other
    member's change and the sums that do not use that cell stay."""
    pag, povljana = by_name(data, "Grad Pag"), by_name(data, "Općina Povljana")
    cells = dict(data.demo["celije"])
    last = data.demo["do"]
    cells[(povljana, "stanovnici_procjena", last)] = (merge.dzs_value(float("nan"), "z"), "z")
    monkeypatch.setattr(data, "demo", {**data.demo, "celije": cells})
    d = merge.merge(data, [pag, povljana])["demografija"]
    assert d["stanovnici"][-1] is None and d["promjena"] is None
    assert d["clanice"] == [0.064, None]
    assert d["prirodna"] == (21 + 4) - (49 + 12) and f"05738:stanovnici_procjena:{last}:z" in d["oznake"]


def test_demography_missing_is_none(data, monkeypatch):
    """Without dzs.parquet the block is None and nothing else changes."""
    assert merge.load_demography(config.BUILD / "nema.parquet") is None
    oibs = [by_name(data, "Općina Povljana"), by_name(data, "Grad Pag")]
    with_demo = merge.summary(merge.merge(data, oibs))
    monkeypatch.setattr(data, "demo", None)
    m = merge.merge(data, oibs)
    assert m["demografija"] is None
    s = merge.summary(m)
    assert s["demografija"] is None
    assert {k: v for k, v in s.items() if k != "demografija"} == {k: v for k, v in with_demo.items() if k != "demografija"}


@needs_dzs
def test_precomputed_files_carry_the_demography():
    for f in sorted((config.BUILD / "simulator").glob("zup-*.json")):
        for k, v in json.loads(f.read_text(encoding="utf-8"))["skupine"].items():
            d = v["demografija"]
            assert len(d["clanice"]) == len(v["clanice"]) and len(d["stanovnici"]) == d["do"] - d["od"] + 1, k
