"""Karta reforme (pipeline/reforma.py): the greedy rule on a small graph, then the scenario on the
finished build. The build tests are skipped without pipeline.build."""
import json
from types import SimpleNamespace

import pandas as pd
import pytest

from pipeline import config, merge, reforma

needs_build = pytest.mark.skipif(not (config.BUILD / "wide.parquet").exists(), reason="run pipeline.build first")


def toy():
    """Two counties. County 1: 01 (100) between 02 (5000) and 03 (900); 03-04 (2000); 04-05 (300);
    05 next to 06 and 07 (400 each, a tie); 07-10 (400). County 2: 08 (50, its only neighbour 01 is
    across the county border), 09 (200, no neighbour) and the county itself (not a unit to merge)."""
    pops = {"00001": 100, "00002": 5000, "00003": 900, "00004": 2000, "00005": 300, "00006": 400,
            "00007": 400, "00010": 400, "00008": 50, "00009": 200, "Z02": 650}
    zup = {s: 1 for s in pops} | {"00008": 2, "00009": 2, "Z02": 2}
    edges = [("00001", "00002"), ("00001", "00003"), ("00003", "00004"), ("00001", "00008"),
             ("00004", "00005"), ("00005", "00006"), ("00005", "00007"), ("00007", "00010")]
    adj = {s: set() for s in pops}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    units = {f"oib{s}": {"sifra": s, "stanovnici_2021": p, "zup_id": zup[s], "naziv": s,
                         "vrsta": "zupanija" if s.startswith("Z") else "opcina", "zagreb": False}
             for s, p in pops.items()}
    return SimpleNamespace(units=units, oib_of={u["sifra"]: o for o, u in units.items()}, adj=adj,
                           eligible=lambda o: units[o]["vrsta"] != "zupanija")


def test_greedy_rule_on_a_small_graph():
    """Threshold 700: 01 (100) is smallest and joins its smallest neighbour 03 (900), not 02 (5000)
    and not 08 across the county border. 05 (300) has two neighbours of 400: the lower code 06
    wins, and 05+06 reach 700. Then 07 and 10 tie at 400: 07 goes first and joins 10 (400), its
    smallest neighbour, rather than 05+06 (700). 08 and 09 have no neighbour in their county and
    stay below the threshold. Had 07 won the first tie, 06 would have joined 05+07 instead."""
    assert reforma.greedy(toy(), 700) == [("00001", "00003"), ("00002",), ("00004",), ("00005", "00006"),
                                         ("00007", "00010"), ("00008",), ("00009",)]
    # threshold 1000: 05+06 (700) now goes on and joins 07+10 (800), its smaller neighbour than 04
    assert reforma.greedy(toy(), 1000) == [("00001", "00003"), ("00002",), ("00004",),
                                          ("00005", "00006", "00007", "00010"), ("00008",), ("00009",)]
    assert reforma.greedy(toy(), 50) == [(s,) for s in sorted(u["sifra"] for u in toy().units.values())
                                        if s != "Z02"]


@pytest.fixture(scope="module")
def data():
    return merge.Data.load()


@pytest.fixture(scope="module")
def res():
    return pd.read_parquet(config.BUILD / "results.parquet", columns=reforma.OWN_COLS)


@pytest.fixture(scope="module")
def groups(data):
    return {p: reforma.greedy(data, p) for p in reforma.PRAGOVI}


@pytest.fixture(scope="module")
def docs(data, res):
    return {p: reforma.reforma(data, p, res) for p in reforma.PRAGOVI}


def eligible_codes(data):
    return {u["sifra"] for o, u in data.units.items() if data.eligible(o)}


def pop(data, codes):
    return sum(int(data.units[data.oib_of[s]]["stanovnici_2021"]) for s in codes)


def components(data):
    """Connected parts of each county's eligible units (land and sea links), as frozensets."""
    codes = eligible_codes(data)
    zup = {s: data.units[data.oib_of[s]]["zup_id"] for s in codes}
    seen, out = set(), []
    for s in sorted(codes):
        if s in seen:
            continue
        comp, todo = set(), [s]
        while todo:
            x = todo.pop()
            if x not in comp:
                comp.add(x)
                todo += [n for n in data.adj.get(x, ()) if n in codes and zup[n] == zup[s]]
        seen |= comp
        out.append(frozenset(comp))
    return out


@needs_build
def test_every_eligible_unit_is_in_exactly_one_group(data, groups):
    want = eligible_codes(data)
    for p, gs in groups.items():
        flat = [s for g in gs for s in g]
        assert len(flat) == len(set(flat)) and set(flat) == want, p


@needs_build
def test_groups_are_connected_and_inside_one_county(data, groups):
    for p, gs in groups.items():
        for g in gs:
            if len(g) > 1:
                merge.check(data, [data.oib_of[s] for s in g], max_members=None)   # raises if broken


@needs_build
def test_every_group_reaches_the_threshold_unless_its_whole_component_is_below(data, groups):
    comps = components(data)
    for p, gs in groups.items():
        for g in gs:
            if pop(data, g) < p:
                comp = next(c for c in comps if g[0] in c)
                assert set(g) == comp and pop(data, comp) < p, (p, g)


@needs_build
def test_two_runs_give_the_same_result(data, res, groups, docs):
    p = 5000
    assert reforma.greedy(data, p) == groups[p]
    assert json.dumps(reforma.reforma(data, p, res), sort_keys=True) == json.dumps(docs[p], sort_keys=True)
    f = config.BUILD / "reforma" / f"prag-{p}.json"           # written by another process (other hash seed)
    if f.exists():
        assert [j["clanice"] for j in json.loads(f.read_text(encoding="utf-8"))["jedinice"]] == \
               [j["clanice"] for j in docs[p]["jedinice"]]


@needs_build
def test_higher_threshold_never_gives_more_units(groups):
    counts = [len(groups[p]) for p in sorted(groups)]
    assert counts == sorted(counts, reverse=True) and counts[0] > counts[-1]


@needs_build
def test_zagreb_and_counties_are_not_in_the_result(data, docs):
    zagreb = next(u["sifra"] for o, u in data.units.items() if u["zagreb"] and u["vrsta"] != "zupanija")
    for p, d in docs.items():
        codes = {s for j in d["jedinice"] for s in j["clanice"]}
        assert zagreb not in codes and all(len(s) == 5 and s.isdigit() for s in codes)
        assert all(data.eligible(data.oib_of[s]) for s in codes)


@needs_build
def test_header_matches_the_list(data, groups, docs):
    total = pop(data, eligible_codes(data))
    for p, d in docs.items():
        js = d["jedinice"]
        merged = [j for j in js if len(j["clanice"]) > 1]
        assert d["prag"] == p and d["godina"] == config.LAST_YEAR
        assert d["n_poslije"] == len(js) == len(groups[p])
        assert d["n_prije"] == sum(len(j["clanice"]) for j in js) == len(eligible_codes(data))
        assert d["n_spojenih_skupina"] == len(merged)
        assert d["stanovnika_u_spojenima"] == sum(j["stanovnici"] for j in merged)
        assert sum(j["stanovnici"] for j in js) == total
        assert d["n_ispod_praga"] == sum(j["stanovnici"] < p for j in js)
        assert abs(d["usteda_realno_do_zbroj"] - sum(j["usteda"]["realno_do"] for j in merged)) < 1.0
        assert abs(d["razmjer_zbroj"] - sum(j["usteda"]["razmjer"] for j in merged)) < 1.0
        assert abs(d["jaz_bez_spajanja_zbroj"] - sum(j["usteda"]["jaz_bez_spajanja"] for j in merged)) < 1.0
        assert 0 <= d["usteda_realno_do_zbroj"] <= d["razmjer_zbroj"]
        assert abs(d["poticaj_godisnje_zbroj"] - sum(j["poticaj"]["godisnje"] or 0 for j in merged)) < 1.0


@needs_build
def test_units_show_the_members_before_and_the_merged_result_after(data, res, docs):
    """Grades before come from results.parquet; a unit that stays alone keeps its own result;
    a merged group carries exactly what the simulator's merge() computes."""
    own = res[res.year == config.LAST_YEAR].set_index("oib")
    d = docs[5000]
    for j in d["jedinice"]:
        assert j["clanice"] == sorted(j["clanice"])
        assert j["ocjene_prije"] == {s: int(own.loc[data.oib_of[s], "ocjena"]) for s in j["clanice"]}
        if len(j["clanice"]) == 1:
            u = data.units[data.oib_of[j["clanice"][0]]]
            assert j["naziv"] == u["naziv"] and j["usteda"] is None
            assert j["ocjena"] == own.loc[u["oib"], "ocjena"]
    merged = [j for j in d["jedinice"] if len(j["clanice"]) > 1]
    for j in merged[::15]:
        m = merge.summary(merge.merge(data, [data.oib_of[s] for s in j["clanice"]], max_members=None))
        assert (j["ocjena"], j["bodovi"], j["rang"], j["usteda"]) == \
               (m["zadnja"]["ocjena"], m["zadnja"]["bodovi"], m["zadnja"]["rang"], m["usteda"])
        assert j["vrsta"] == m["vrsta"] and j["skupina"] == m["skupina"] and j["stanovnici"] == m["stanovnici"]
        assert " + " in j["naziv"] and not j["naziv"].startswith(("Grad ", "Općina "))


@needs_build
def test_karta_reforme_payout_moves_money_but_saves_nothing(docs):
    """The payout of the whole scenario: merged groups lose what the units that stay alone gain."""
    for p, d in docs.items():
        if "izravnanje_isplata_spojene_promjena" not in d:
            continue
        assert abs(d["izravnanje_isplata_spojene_promjena"] + d["izravnanje_isplata_ostale_promjena"]) < 1e-6
        merged = [j for j in d["jedinice"] if len(j["clanice"]) > 1 and j.get("izravnanje")]
        assert abs(sum(j["izravnanje"]["isplata_promjena"] for j in merged) - d["izravnanje_isplata_spojene_promjena"]) < 1.0
        assert all(j["izravnanje"]["omjer_poslije"] == d["izravnanje_omjer_poslije"] for j in merged)


needs_dzs = pytest.mark.skipif(not merge.DZS_PARQUET.exists(), reason="run pipeline.pxweb first (dzs.parquet)")


@needs_build
@needs_dzs
def test_demography_of_units_and_header(data, docs):
    """Each unit carries merge.demography of its members (also a unit that stays alone); the header
    sums the first and last year over the merged groups and over the others."""
    d = docs[5000]
    by_code = {s: j for j in d["jedinice"] for s in j["clanice"]}
    pag = by_code["03166"]                                   # Pag + Nin + Vrsi + Kolan + Povljana at 5.000
    assert len(pag["clanice"]) > 1
    assert pag["demografija"] == merge._compact(merge.demography(data, [data.oib_of[s] for s in pag["clanice"]]))
    vukovar = by_code["05185"]
    assert vukovar["clanice"] == ["05185"] and vukovar["demografija"]["promjena"] == -0.017   # Vukovar −1,7 %
    for p, doc in docs.items():
        h = doc["demografija"]
        for part, js in (("spojene", [j for j in doc["jedinice"] if len(j["clanice"]) > 1]),
                         ("ostale", [j for j in doc["jedinice"] if len(j["clanice"]) == 1])):
            assert h[part]["stanovnici_od"] == sum(j["demografija"]["stanovnici"][0] for j in js), (p, part)
            assert h[part]["stanovnici_do"] == sum(j["demografija"]["stanovnici"][-1] for j in js), (p, part)
            assert h[part]["promjena"] == round(h[part]["stanovnici_do"] / h[part]["stanovnici_od"] - 1, 3)


@needs_build
def test_demography_missing_is_none(data, res, monkeypatch):
    monkeypatch.setattr(data, "demo", None)
    doc = reforma.reforma(data, 2500, res)
    assert doc["demografija"] is None
    assert all(j["demografija"] is None for j in doc["jedinice"])
