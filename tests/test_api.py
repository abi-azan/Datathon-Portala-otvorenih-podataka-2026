"""The published static API matches its own OpenAPI 3.1 description. Run after pipeline.publish."""
import csv
import json

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
        if "{slug}" in path:
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
