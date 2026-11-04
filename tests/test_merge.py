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
