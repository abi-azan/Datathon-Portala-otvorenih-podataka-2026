"""Context in the fact packs (pipeline/facts.py): population change and net income per inhabitant,
only when the unit stands out from its peer group, marked as context and placed last."""
import pandas as pd
import pytest

from pipeline import config, facts


def block(change, change_med, income, income_med, first=2021, last=2024, skupina="x"):
    """A stanovnistvo_gospodarstvo block as pipeline/kontekst.py publishes it (only the fields used)."""
    return {"skupina": skupina, "pokazatelji": {
        "promjena_stanovnistva": {"godina": last, "od_godine": first, "vrijednost": change, "medijan": change_med},
        "neto_dohodak_pc": {"godina": 2025, "vrijednost": income, "medijan": income_med}}}


# the profile values quoted when the feature was asked for (population 2021-2024)
PAG = block(0.062104, 0.01024, 9574.433562, 9164.48412, skupina="gradovi 2.000-5.000")
BOGDANOVCI = block(-0.082527, -0.029422, 6591.760149, 7226.673355, skupina="općine do 2.000")
ZAGREB = block(0.013738, None, 12826.274261, None, skupina=None)
ISTRA = block(0.049461, -0.005218, 10791.644916, 8617.51688, skupina="županije")


def test_signed_percentages_as_on_the_profile():
    assert facts.signed_pct(0.062104) == "+6,2 %" and facts.signed_pct(-0.082527) == "−8,3 %"
    assert facts.signed_pct(-0.0004) == "0,0 %" and facts.eur(9574.433562) == "9.574 €"


def test_pag_population_is_notable_income_is_not():
    # 6,2 - 1,0 = 5,2 points over 3 years >= 1,5 a year; income 4,5 % above the median < 20 %
    assert facts.context_facts(PAG) == [
        ("Kontekst", facts.CONTEXT_NOTE),
        ("Kontekst: broj stanovnika", "od 2021. do 2024. povećao se za 6,2 %, što je iznad medijana skupine (+1,0 %)")]


def test_bogdanovci_population_is_notable_over_three_years_but_not_over_four():
    assert facts.context_facts(BOGDANOVCI)[1:] == [
        ("Kontekst: broj stanovnika", "od 2021. do 2024. smanjio se za 8,3 %, što je ispod medijana skupine (−2,9 %)")]
    # the same gap of 5,4 points over 2021-2025 is under 1,5 points a year: nothing, not even the framing line
    assert facts.context_facts(block(-0.082527, -0.029422, 6591.76, 7226.67, last=2025)) == []


def test_income_far_from_the_median_and_a_county_against_counties():
    rich = facts.context_facts(block(0.0, 0.0, 12000.0, 9000.0))
    assert rich[1:] == [("Kontekst: neto dohodak po stanovniku",
                         "u 2025. iznosio je 12.000 €, što je iznad medijana skupine (9.000 €)")]
    poor = facts.context_facts(block(0.0, 0.0, 7000.0, 9000.0))
    assert poor[1][1].endswith("ispod medijana skupine (9.000 €)")              # 22 % below
    assert facts.context_facts(block(0.0, 0.0, 7300.0, 9000.0)) == []          # 19 % below: not notable
    labels = [k for k, _ in facts.context_facts(ISTRA)]
    assert labels == ["Kontekst", "Kontekst: broj stanovnika", "Kontekst: neto dohodak po stanovniku"]


def test_no_peer_median_no_context():
    assert facts.context_facts(ZAGREB) == [] and facts.context_facts(None) == []
    hidden = block(None, 0.01, None, 9000.0)                                    # DZS "z": value withheld
    assert facts.context_facts(hidden) == []


@pytest.fixture(scope="module")
def build():
    if not (config.BUILD / "results.parquet").exists():
        pytest.skip("no build")
    units = pd.read_csv(config.BUILD / "units.csv", dtype={"oib": str, "sifra": str})
    return units, pd.read_parquet(config.BUILD / "results.parquet")


def test_packs_carry_context_last_and_marked(build):
    units, res = build
    by_name = units.set_index("naziv").oib
    ctx = {by_name["Grad Pag"]: PAG, by_name["Općina Bogdanovci"]: BOGDANOVCI,
           by_name["Grad Zagreb"]: ZAGREB, by_name["Istarska županija"]: ISTRA}
    sub = units[units.oib.isin(ctx)]
    packs = {p["naziv"]["nom"]: p for p in facts.build_all(sub, res, config.LAST_YEAR, context=ctx)}
    for name, n in (("Grad Pag", 2), ("Općina Bogdanovci", 2), ("Grad Zagreb", 0), ("Istarska županija", 3)):
        items = packs[name]["facts"]
        marked = [f for f in items if f.get("kontekst")]
        assert len(marked) == n, name
        assert items[len(items) - n:] == marked                                  # after the fiscal story
    assert {"label": "Kontekst", "value": facts.CONTEXT_NOTE, "kontekst": True} in packs["Grad Pag"]["facts"]
    # without context the pack is exactly the fiscal one
    bare = {p["naziv"]["nom"]: p for p in facts.build_all(sub, res, config.LAST_YEAR, context={})}
    assert bare["Grad Pag"]["facts"] == packs["Grad Pag"]["facts"][:-2]


def test_real_packs_follow_the_profile_blocks(build):
    """The default context is the block the profile shows (kontekst.load): context exactly when the
    rule says so, none for Grad Zagreb, counties against counties, and a third to a half of the units
    with context (re-calibrate CONTEXT_* in facts.py when the data move this out of range)."""
    units, res = build
    ctx = facts.load_context(units)
    packs = facts.build_all(units, res, config.LAST_YEAR, context=ctx)
    with_ctx = 0
    for p in packs:
        b = ctx[p["oib"]]
        has = any(f.get("kontekst") for f in p["facts"])
        assert has == bool(facts.context_facts(b))
        with_ctx += has
        if p["naziv"]["nom"] == "Grad Zagreb":
            assert not has and b["skupina"] is None
        if p["naziv"]["nom"].endswith("županija"):
            assert b["skupina"] == "županije"
    assert len(packs) * 0.25 <= with_ctx <= len(packs) * 0.6, with_ctx


def test_no_pack_names_a_strength_as_the_weakest_indicator(build):
    """Grad Rovinj, 6.11.: 100 points of 100, and the text said 'Ocjenu najviše spušta pokazatelj
    „operativni saldo”' and then 'Jake strane jedinice su: operativni saldo, …' (68 texts). A pack
    names the weakest indicator only when it is not among the strengths; with all five indicators
    strong there is none to name."""
    units, res = build
    packs = {p["naziv"]["nom"]: {f["label"]: f["value"] for f in p["facts"]}
             for p in facts.build_all(units, res, config.LAST_YEAR, context={})}
    without = 0
    for name, f in packs.items():
        weakest, strong = f.get("Najslabiji pokazatelj"), f.get("Jake strane", "").split(", ")
        assert weakest not in strong, name
        without += weakest is None
        if weakest is None:
            assert f.get("Jake strane"), name          # left out only because it is a strength
    assert "Najslabiji pokazatelj" not in packs["Grad Rovinj - Rovigno"]
    assert packs["Općina Povljana"]["Najslabiji pokazatelj"] == "dospjele obveze"
    assert 0 < without < len(packs) / 4               # 68 of 576 on the data of 6.11.
