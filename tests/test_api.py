"""The published static API matches its own OpenAPI 3.1 description. Run after pipeline.publish."""
import csv
import json
import re

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from pipeline import config, openapi

API = config.ROOT / "web" / "public" / "api" / "v1"
pytestmark = pytest.mark.skipif(not (API / "openapi.json").exists(), reason="run pipeline.publish first")


@pytest.fixture(scope="module")
def spec():
    return json.loads((API / "openapi.json").read_text(encoding="utf-8"))


def validator(spec, name):
    """Validate against components/schemas/<name>, resolving #/components/... references."""
    registry = Registry().with_resource("urn:openapi", Resource.opaque(spec))
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema",
              "$ref": f"urn:openapi#/components/schemas/{name}"}
    return Draft202012Validator(schema, registry=registry)


def load(path):
    return json.loads((API / path).read_text(encoding="utf-8"))


def test_spec_is_openapi_31_and_documents_every_file(spec):
    assert spec["openapi"].startswith("3.1")
    for path in spec["paths"]:
        if "{" in path:                                     # templated paths are checked below
            continue
        assert (API / path.lstrip("/")).exists(), path
    Draft202012Validator.check_schema(spec["components"]["schemas"]["Jedinica"])


def test_index_matches_schema(spec):
    index = load("jedinice.json")
    v = validator(spec, "Indeks")
    errors = list(v.iter_errors(index))
    assert not errors, errors[:3]
    index["jedinice"][0]["oib"] = "123"                     # the check really looks inside the references
    assert list(v.iter_errors(index))


def test_every_unit_profile_matches_schema(spec):
    v = validator(spec, "Jedinica")
    index = load("jedinice.json")["jedinice"]
    bad = []
    for u in index:
        errs = list(v.iter_errors(load(f"jedinice/{u['slug']}.json")))
        if errs:
            bad.append((u["slug"], errs[0].message))
    assert not bad, bad[:5]


def test_ai_texts_cover_almost_every_profile():
    """After the batch (data/ai/objasnjenja-<year>.json) at least 95 % of the profiles show the
    AI text. Fewer means the fact packs changed after the batch, so texts fell back to the template.
    In CI (GitHub Actions sets CI=true) this only reports the coverage as a warning: after a new MF
    release the changed units rightly show the template until the batch is rerun with --skip, and
    that must not block the deploy or the weekly rebuild. Locally it stays a hard check."""
    import os
    import warnings
    from pipeline import publish
    if not publish.AI_TEXTS.exists():
        pytest.skip("no AI texts imported yet")
    index = load("jedinice.json")["jedinice"]
    sources = [load(f"jedinice/{u['slug']}.json")["objasnjenje"]["izvor"] for u in index]
    n_ai, enough = sources.count("ai"), sources.count("ai") >= 0.95 * len(index)
    msg = f"AI tekst na {n_ai}/{len(index)} profila ({100 * n_ai / len(index):.1f} %; prag 95 %)".replace(".", ",")
    if os.environ.get("CI", "").strip().lower() not in ("", "0", "false"):
        warnings.warn(msg if enough else f"{msg}: ponovi batch s --skip za promijenjene pakete")
        return
    assert enough, msg


def test_groups_match_schema(spec):
    assert not list(validator(spec, "Skupine").iter_errors(load("skupine.json")))


def test_csv_exports():
    with open(API / "sifrarnik.csv", encoding="utf-8", newline="") as f:
        reg = list(csv.DictReader(f))
    assert len(reg) == 576 and len({r["oib"] for r in reg}) == 576
    assert all(len(r["oib"]) == 11 for r in reg)            # leading zeros kept
    with open(API / "rezultati.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 576 * len(config.YEARS)
    assert not any("e+" in v for r in rows for v in r.values() if v)   # no scientific notation


def test_spec_module_and_file_agree(spec):
    assert spec["components"]["schemas"] == json.loads(json.dumps(openapi.SCHEMAS))


def dataset_rows():
    with open(config.REFERENCE / "skupovi.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_every_downloaded_source_is_a_listed_and_used_dataset():
    if not config.SOURCES_LOG.exists():
        pytest.skip("no data/raw/sources.json")
    log = json.loads(config.SOURCES_LOG.read_text(encoding="utf-8"))
    keys = {re.sub(r"^(ckan_package_search)_\d+$", r"\1", k) for k in log}
    rows = dataset_rows()
    assert keys <= {r["kljuc"] for r in rows}, keys - {r["kljuc"] for r in rows}
    assert keys <= {r["kljuc"] for r in rows if r["koristi_se"] == "da"}


def test_dataset_list_is_complete_where_it_must_be():
    rows = dataset_rows()
    assert len({r["kljuc"] for r in rows}) == len(rows)
    assert {r["koristi_se"] for r in rows} <= {"da", "ne"}
    for r in rows:
        if r["koristi_se"] == "da":
            assert r["url"].startswith("https://") and r["licenca"].strip(), r["kljuc"]
            assert r["naziv"].strip() and r["izdavatelj"].strip() and r["uloga"].strip(), r["kljuc"]
            # every licence claim has its text and the place where the publisher states it
            assert r["licenca_url"].startswith("https://") and r["licenca_dokaz"].startswith("https://"), r["kljuc"]
        assert re.fullmatch(r"(\d{4}-\d{2}-\d{2})?", r["zadnja_izmjena"]), r["kljuc"]


def test_dataset_list_matches_schema_and_csv(spec):
    data = load("skupovi.json")
    v = validator(spec, "Skupovi")
    assert not list(v.iter_errors(data)), list(v.iter_errors(data))[:3]
    assert [d["kljuc"] for d in data] == [r["kljuc"] for r in dataset_rows()]
    ckan = next(d for d in data if d["kljuc"] == "ckan_package_search")
    assert isinstance(ckan["sha256"], list) and ckan["stranica"] == len(ckan["sha256"]) > 1
    del data[0]["licenca"]                                  # the check really enforces the required fields
    assert list(v.iter_errors(data))


def test_audit_layer_matches_the_known_cases():
    """DUR layer (pipeline/dur.py): about 330 units have a financial audit since 2019; Povljana's
    is the 2024 audit with an adverse opinion (docs/research/05)."""
    from pipeline import publish
    if not publish.AUDITS.exists():
        pytest.skip("no data/reference/dur_revizije.json")
    index = load("jedinice.json")["jedinice"]
    audited = [u for u in index if load(f"jedinice/{u['slug']}.json")["revizija"]]
    assert len(audited) >= 300
    pov = load("jedinice/opcina-povljana.json")["revizija"]
    assert pov["misljenje"] == "nepovoljno" and pov["revidirana_godina"] == 2024 and pov["url"].startswith("https://www.revizija.hr/")
    # two municipalities are called Privlaka; the 2021 report names Vukovarsko-srijemska županija
    privlaka = {u["zupanija"]: load(f"jedinice/{u['slug']}.json")["revizija"] for u in index if u["naziv"] == "Općina Privlaka"}
    assert privlaka["Vukovarsko-srijemska županija"]["revidirana_godina"] == 2020
    assert privlaka["Zadarska županija"] is None
    assert "Državni ured za reviziju" in (config.ROOT / "docs" / "skupovi-podataka.md").read_text(encoding="utf-8")


def test_dcat_catalogue_lists_what_is_published():
    """DCAT-AP mandatory properties are present and every downloadable distribution exists."""
    cat = load("dcat.jsonld")
    assert cat["@type"] == "dcat:Catalog" and cat["dct:title"] and cat["dct:description"] and cat["dct:publisher"]
    assert len(cat["dcat:dataset"]) >= 6
    base = "https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/api/v1/"
    for ds in cat["dcat:dataset"]:
        assert ds["dct:title"]["@value"] and ds["dct:description"]["@value"] and ds["dcat:distribution"]
        assert ds["dct:source"], ds["dct:identifier"]
        for d in ds["dcat:distribution"]:
            url = d["dcat:accessURL"]["@id"]
            assert url.startswith(base)
            if "dcat:downloadURL" in d:
                assert (API / url[len(base):]).exists(), url


def test_methodology_file_matches_the_code(spec):
    from pipeline import explain, methodology
    doc = load("metodologija.json")
    assert not list(validator(spec, "Metodologija").iter_errors(doc))
    assert {p["oznaka"]: p["ponder"] for p in doc["pokazatelji"]} == methodology.SCENARIOS["osnovni"]
    assert doc["ai"]["prompt_sha256"] == explain.prompt_sha256() and doc["ai"]["sustav"] == explain.SYSTEM


def test_every_unit_has_a_source_file(spec):
    """Visible number check: jedinice/<slug>/izvor.json for every unit, valid against the schema."""
    v = validator(spec, "Izvor")
    index = load("jedinice.json")["jedinice"]
    bad = []
    for u in index:
        errs = list(v.iter_errors(load(f"jedinice/{u['slug']}/izvor.json")))
        if errs:
            bad.append((u["slug"], errs[0].message))
    assert not bad, bad[:5]


def test_simulator_files_match_schema(spec):
    v = validator(spec, "SimulatorZupanija")
    files = sorted((API / "simulator").glob("zup-*.json"))
    assert len(files) == 20
    for f in files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        errors = list(v.iter_errors(doc))
        assert not errors, (f.name, errors[0].message)
        assert f.name == f"zup-{doc['zup_id']:02d}.json"


def test_reforma_files_match_schema(spec):
    v = validator(spec, "Reforma")
    files = sorted((API / "reforma").glob("prag-*.json"))
    assert [f.name for f in files] == ["prag-10000.json", "prag-2500.json", "prag-5000.json"]
    for f in files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        errors = list(v.iter_errors(doc))
        assert not errors, (f.name, errors[0].message)
        assert f.name == f"prag-{doc['prag']}.json"
    doc["jedinice"][0]["clanice"] = []                      # the check really looks inside the references
    assert list(v.iter_errors(doc))
