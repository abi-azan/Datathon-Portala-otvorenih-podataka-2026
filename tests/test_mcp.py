"""MCP server Fiskalna karta (fiskalna_mcp) over the local API, through the SDK's in-memory client.
Run after pipeline.publish; skipped when web/public/api/v1/jedinice.json is missing."""
import json
from pathlib import Path

import pytest

anyio = pytest.importorskip("anyio")
pytest.importorskip("mcp")
from mcp import Client  # noqa: E402

from fiskalna_mcp import create_server  # noqa: E402

API = Path(__file__).resolve().parents[1] / "web" / "public" / "api" / "v1"
pytestmark = pytest.mark.skipif(not (API / "jedinice.json").exists(), reason="run pipeline.publish first")

TOOLS = {"pronadi_jedinicu", "pregled_jedinice", "usporedi", "scenarij_spajanja", "karta_reforme", "izvor_brojke"}


@pytest.fixture(scope="module")
def server():
    return create_server(str(API))


def run(server, *calls):
    """Call tools in one in-memory session; returns the structured results in order."""
    async def go():
        out = []
        async with Client(server) as c:
            for name, args in calls:
                r = await c.call_tool(name, args)
                assert not r.is_error, r.content
                data = r.structured_content
                assert data == json.loads(r.content[0].text)     # text and structured output agree
                out.append(data)
        return out
    return anyio.run(go)


def test_tool_list(server):
    async def go():
        async with Client(server) as c:
            tools = (await c.list_tools()).tools
            resources = (await c.list_resources()).resources
            return tools, resources
    tools, resources = anyio.run(go)
    assert {t.name for t in tools} == TOOLS
    assert all(t.description and t.annotations.read_only_hint for t in tools)
    assert "fiskalna://metodologija" in {str(r.uri) for r in resources}


def test_povljana_grade_and_points(server):
    (r,) = run(server, ("pregled_jedinice", {"jedinica": "opcina-povljana", "godina": 2025}))
    assert r["godina"] == 2025
    assert r["ocjena"] == 2 and r["bodovi"] == 39.9
    assert r["ogranicenje_do"] is True
    assert [s["oznaka"] for s in r["sastavnice"]] == ["I1", "I2", "I3", "I4", "I5"]
    assert r["poveznice"]["stranica"].endswith("#/jedinica/opcina-povljana")
    assert r["poveznice"]["izvor"].endswith("jedinice/opcina-povljana/izvor.json")
    assert r["objasnjenje"]["tekst"]


def test_unit_by_name_and_code(server):
    by_name, by_code = run(server, ("pregled_jedinice", {"jedinica": "Povljana"}),
                           ("pregled_jedinice", {"jedinica": "05738"}))
    assert by_name["jedinica"]["slug"] == by_code["jedinica"]["slug"] == "opcina-povljana"


def test_merge_pag_povljana(server):
    (r,) = run(server, ("scenarij_spajanja", {"jedinice": "05738,03166"}))
    assert "greska" not in r
    assert r["poslije"]["ocjena"] == 5
    assert {m["sifra_dgu"] for m in r["prije"]} == {"03166", "05738"}
    assert r["usteda_na_upravi"]["raspon_eur_godisnje"][0] == 0
    assert r["poveznice"]["kljuc"] == "03166-05738"


@pytest.mark.parametrize("jedinice, rijec", [
    (["Povljana", "Osijek"], "iste županije"),
    (["Povljana", "Benkovac"], "jednu cjelinu"),
    (["grad-zagreb", "grad-sveta-nedelja"], "Zagreb"),
    (["Povljana"], "2 do 4"),
])
def test_invalid_merge_is_a_message(server, jedinice, rijec):
    (r,) = run(server, ("scenarij_spajanja", {"jedinice": jedinice}))
    assert rijec in r["greska"]


def test_search_without_diacritics(server):
    povljana, osijek, dakovo = run(server, ("pronadi_jedinicu", {"naziv": "povljana"}),
                                   ("pronadi_jedinicu", {"naziv": "osijek"}),
                                   ("pronadi_jedinicu", {"naziv": "dakovo"}))
    assert povljana["jedinice"][0]["slug"] == "opcina-povljana"
    assert osijek["jedinice"][0]["slug"] == "grad-osijek"
    assert dakovo["jedinice"][0]["naziv"] == "Grad Đakovo"


def test_ambiguous_name_lists_candidates(server):
    (r,) = run(server, ("pregled_jedinice", {"jedinica": "Privlaka"}))
    assert "greska" in r and len(r["kandidati"]) == 2


def test_compare_and_reform_and_source(server):
    cmp_, reform, bad, src = run(
        server,
        ("usporedi", {"jedinice": ["Pag", "Povljana"]}),
        ("karta_reforme", {"prag": 5000, "jedinica": "Povljana"}),
        ("karta_reforme", {"prag": 3000}),
        ("izvor_brojke", {"jedinica": "Povljana", "pokazatelj": "dospjele obveze"}))
    assert [u["slug"] for u in cmp_["jedinice"]] == ["grad-pag", "opcina-povljana"]
    assert set(cmp_["medijani_skupina"]) == {"gradovi 2.000-5.000", "općine do 2.000"}
    assert reform["n_poslije"] < reform["n_prije"]
    assert "05738" in [m["sifra_dgu"] for m in reform["jedinica"]["skupina"]["clanice"]]
    assert "greska" in bad
    assert src["pokazatelj"]["oznaka"] == "I5"
    assert any(x["konto"] == "26 D" and x["redak"] and x["list"] for x in src["ulazi"])


def test_methodology_resource_error_is_valid_json(tmp_path):
    """A broken metodologija.json (e.g. read while publish rewrites it) gives a JSON error object."""
    (tmp_path / "metodologija.json").write_text("{", encoding="utf-8")

    async def go():
        async with Client(create_server(str(tmp_path))) as c:
            return (await c.read_resource("fiskalna://metodologija")).contents[0].text
    assert "greska" in json.loads(anyio.run(go))
