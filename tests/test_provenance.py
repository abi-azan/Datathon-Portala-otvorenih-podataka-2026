"""Visible number check (pipeline/provenance.py): the inputs listed for a unit are enough to get
back its published indicators. Run after `python -m pipeline.build`."""
import math
from collections import defaultdict

import pandas as pd
import pytest

from pipeline import config, provenance

pytestmark = pytest.mark.skipif(not (config.BUILD / "results.parquet").exists(), reason="run pipeline.build first")


@pytest.fixture(scope="module")
def built():
    units = pd.read_csv(config.BUILD / "units.csv", dtype={"oib": str, "sifra": str, "rkp": str})
    res = pd.read_parquet(config.BUILD / "results.parquet")
    out = provenance.build(units, pd.read_parquet(config.BUILD / "prras_long.parquet"),
                           pd.read_parquet(config.BUILD / "wide.parquet"), res)
    return units, res.set_index(["oib", "year"]), out


def close(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))


def recompute(d):
    """I1-I5 from the listed inputs only, with the formulas the file states."""
    v = defaultdict(float)
    for u in d["ulazi"]:
        v[(u["konto"], u["godina"])] += u["iznos"]
    t = d["godina"]
    years, weights = d["prozor"]["godine"], d["prozor"]["ponderi"]
    refi = d["velicine"]["glavnica"]["refinanciranje"]
    kp = lambda y: sum(v[(c, y)] for c in config.CAPITAL_GRANTS)
    po = lambda y: v[("6", y)] - kp(y)
    os_ = lambda y: po(y) - v[("3", y)]
    principal = lambda y: max(0.0, v[("54", y)] - v[("84", y)]) if refi.get(str(y)) else v[("54", y)]
    sd = lambda y: v[("341", y)] + v[("342", y)] + principal(y)
    # FI: the MF decision amount, at most 6331 + 6352 + 6353 (6331 = 633 - 6332); without a decision 6353
    room = lambda y: max(0.0, v[("633", y)] - v[("6332", y)] + v[("6352", y)] + v[("6353", y)])
    fi_src = d["velicine"]["FI"]["izvor"]
    fi = lambda y: min(v[(provenance.FI_KONTO, y)], room(y)) if fi_src.get(str(y)) == "odluka" else v[("6353", y)]
    zo = lambda y: (v[("6", y)] + v[("7", y)] - v[("63", y)] + fi(y) - v[("663", y)] - v[("dio611", y)])
    s_po = sum(w * po(y) for w, y in zip(weights, years))
    s_os = sum(w * os_(y) for w, y in zip(weights, years))
    s_pr = sum(w * principal(y) for w, y in zip(weights, years))
    nd = max(0.0, v[("26", t)] + v[("25", t)] - v[("11", t)])
    do = v[("23 D", t)] + v[("24 D", t)] + v[("26 D", t)] - (d["velicine"]["DO"]["pravilo1_iskljuceno"] or 0.0)
    zo_years = d["velicine"]["ZO"]["godine"]
    pairs = [(w, y) for w, y in zip(weights, years) if str(y - 1) in zo_years]
    s_sd, s_zo = sum(w * sd(y) for w, y in pairs), sum(w * zo(y - 1) for w, y in pairs)
    os_avg = s_os / sum(weights)
    i3 = 0.0 if nd <= 0 else (nd / os_avg if os_avg > 0 else None)      # inf is published as null
    return {"I1": s_os / s_po if s_po > 0 else None, "I2": (s_os - s_pr) / s_po if s_po > 0 else None,
            "I3": i3, "I4": s_sd / s_zo if s_zo > 0 else None,
            "I5": do / v[("3", t)] if v[("3", t)] > 0 else None}


def test_inputs_give_back_every_published_indicator(built):
    units, res, out = built
    assert len(out) == len(units) == 576
    bad = []
    for o, d in out.items():
        got = recompute(d)
        for k, p in d["pokazatelji"].items():
            if not close(got[k], p["vrijednost"]):
                bad.append((o, k, got[k], p["vrijednost"]))
    assert not bad, bad[:5]


def test_published_values_are_the_results(built):
    units, res, out = built
    for o, d in out.items():
        r = res.loc[(o, config.LAST_YEAR)]
        for k, p in d["pokazatelji"].items():
            want = None if pd.isna(r[k]) or math.isinf(r[k]) else float(r[k])
            assert close(p["vrijednost"], want), (o, k)


def test_every_input_points_to_a_cell(built):
    units, res, out = built
    for o, d in out.items():
        for u in d["ulazi"]:
            assert u["konto"] in d["konta"] and isinstance(u["redak"], int) and u["redak"] > 1, (o, u)
            if d["konta"][u["konto"]]["izvor"] == "Bilanca":
                assert u["stupac"], (o, u)
    pov = out[units.set_index("naziv").loc["Općina Povljana", "oib"]]
    assert pov["izvori"]["PR-RAS"]["list"] == "OPĆINA POVLJANA"
    assert pov["izvori"]["PR-RAS"]["datoteka"].endswith("13 Zadarska.xlsx")
    assert {u["konto"] for u in pov["ulazi"] if u["godina"] == config.LAST_YEAR} >= {"6", "3", "23 D", "26 D"}
