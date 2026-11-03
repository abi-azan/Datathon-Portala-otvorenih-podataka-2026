"""OpenAPI 3.1 description of the static API (web/public/api/v1/openapi.json).

The API is a set of static files on GitHub Pages: no server, no key, CORS open. OpenAPI 3.1
uses JSON Schema 2020-12, so tests/test_api.py validates the published files against the
same schemas that are documented here.
"""

PAGES = "https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/api/v1"
REPO = "https://github.com/abi-azan/Datathon-Portala-otvorenih-podataka-2026"

NUM = {"type": ["number", "null"]}
INT = {"type": ["integer", "null"]}
STR = {"type": ["string", "null"]}
BY_YEAR_INT = {"type": "object", "description": "Po godini (ključ je godina, npr. \"2025\").",
               "additionalProperties": INT}
BY_YEAR_NUM = {"type": "object", "description": "Po godini (ključ je godina, npr. \"2025\").",
               "additionalProperties": NUM}

SCHEMAS = {
    "Vrsta": {"type": "string", "enum": ["opcina", "grad", "zupanija"]},
    "JedinicaKratko": {
        "type": "object",
        "required": ["oib", "sifra", "slug", "naziv", "vrsta", "zup_id", "zupanija", "stanovnici", "skupina",
                     "ocjena", "bodovi"],
        "properties": {
            "oib": {"type": "string", "pattern": "^[0-9]{11}$", "description": "OIB jedinice (primarni ključ)."},
            "sifra": {"type": "string", "pattern": "^([0-9]{5}|Z[0-9]{2})$",
                      "description": "Peteroznamenkasta šifra DGU/DZS za općine i gradove; Z01-Z20 za županije."},
            "slug": {"type": "string", "pattern": "^[a-z0-9-]+$"},
            "naziv": {"type": "string"},
            "vrsta": {"$ref": "#/components/schemas/Vrsta"},
            "zup_id": {"type": "integer", "minimum": 1, "maximum": 21},
            "zupanija": {"type": "string"},
            "stanovnici": {"type": "integer", "description": "Popis stanovništva 2021."},
            "skupina": {"type": "string", "description": "Usporedna skupina (vrsta i razred veličine)."},
            "ocjena": {**BY_YEAR_INT, "description": "Ocjena 1-5 po godini (5 = vrlo stabilno)."},
            "bodovi": {**BY_YEAR_NUM, "description": "Bodovi 0-100 po godini."},
            "uprava_pc": {**NUM, "description": "Trošak opće uprave po stanovniku u zadnjoj godini, €."},
            "udio_tekucih_pomoci": {**NUM, "description": "Udio tekućih pomoći u tekućim prihodima, zadnja godina."},
        },
    },
    "Indeks": {
        "type": "object",
        "required": ["generirano", "zadnja_godina", "jedinice"],
        "properties": {
            "generirano": {"type": "string", "format": "date-time"},
            "zadnja_godina": {"type": "integer"},
            "jedinice": {"type": "array", "minItems": 576, "maxItems": 576,
                         "items": {"$ref": "#/components/schemas/JedinicaKratko"}},
        },
    },
    "Godina": {
        "type": "object",
        "description": "Rezultat za jednu godinu: pomoćne veličine, pokazatelji I1-I5, bodovi S1-S5, ocjena, "
                       "zastavice i kontekst (PLAN §3).",
        "required": ["ocjena", "bodovi", "zastavice", "kvaliteta"],
        "properties": {
            "ocjena": {"type": ["integer", "null"], "minimum": 1, "maximum": 5},
            "ocjena_rijec": STR,
            "bodovi": NUM,
            "bodovi_bez_ogranicenja": NUM,
            "ogranicenje_do": {"type": "boolean", "description": "Pravilo 2: dospjele obveze >= 30 % rashoda."},
            "rang": NUM, "n_skupine": NUM, "percentil": NUM,
            **{f"I{i}": NUM for i in range(1, 6)},
            **{f"S{i}": NUM for i in range(1, 6)},
            "DO": {**NUM, "description": "Dospjele obveze nakon pravila 1, €."},
            "DO_iskazano": {**NUM, "description": "Dospjele obveze kako ih je jedinica iskazala, €."},
            "zastavice": {"type": "array", "items": {"type": "string", "enum": ["Z1", "Z2", "Z3", "Z4"]}},
            "oznake": {"type": "array", "items": {"type": "string"}},
            "kvaliteta": {"type": "array", "items": {"type": "string"}},
        },
    },
    "Cinjenica": {"type": "object", "required": ["label", "value"],
                  "properties": {"label": {"type": "string"}, "value": {"type": "string"}}},
    "Jedinica": {
        "type": "object",
        "description": "Svjedodžba jedinice: šifre, struktura, sve godine, paket činjenica i objašnjenje.",
        "required": ["oib", "sifra", "slug", "naziv", "vrsta", "zupanija", "skupina", "stanovnici_2021", "godine",
                     "susjedi"],
        "properties": {
            "oib": {"type": "string", "pattern": "^[0-9]{11}$"},
            "rkp": {"type": "string", "description": "Broj u Registru proračunskih korisnika (Ministarstvo financija)."},
            "sifra": {"type": "string"},
            "slug": {"type": "string"},
            "naziv": {"type": "string"},
            "vrsta": {"$ref": "#/components/schemas/Vrsta"},
            "zupanija": {"type": "string"},
            "skupina": {"type": "string"},
            "stanovnici_2021": {"type": "integer"},
            "povrsina_km2": NUM,
            "otok": {"type": ["boolean", "null"]},
            "godine": {"type": "object", "additionalProperties": {"$ref": "#/components/schemas/Godina"}},
            "susjedi": {"type": "array", "items": {
                "type": "object", "required": ["slug", "naziv", "vrsta", "km"],
                "properties": {"slug": {"type": "string"}, "naziv": {"type": "string"},
                               "vrsta": {"type": "string", "enum": ["kopno", "more"],
                                         "description": "kopno: zajednička granica (km); more: veza preko mora (udaljenost, km)."},
                               "km": {"type": "number"}}}},
            "cinjenice": {"type": ["object", "null"], "properties": {
                "facts": {"type": "array", "items": {"$ref": "#/components/schemas/Cinjenica"}}}},
            "objasnjenje": {"type": ["object", "null"], "required": ["tekst", "izvor"], "properties": {
                "tekst": {"type": "string"},
                "izvor": {"type": "string", "enum": ["ai", "predlozak"]},
                "provjera": {"type": "object", "required": ["ok", "n_brojki", "nepoznate"], "properties": {
                    "ok": {"type": "boolean"}, "n_brojki": {"type": "integer"},
                    "nepoznate": {"type": "array", "items": {"type": "string"}}}}}},
        },
    },
    "Skupine": {
        "type": "object",
        "description": "Medijani po usporednoj skupini i godini: bodovi, I1-I5, trošak uprave, udio pomoći.",
        "additionalProperties": {"type": "object", "additionalProperties": {
            "type": "object", "additionalProperties": NUM}},
    },
}


def _get(summary, description, schema_ref=None, media="application/json", schema=None):
    content = {media: {"schema": schema or {"$ref": f"#/components/schemas/{schema_ref}"}}} if (schema_ref or schema) \
        else {media: {}}
    return {"get": {"summary": summary, "description": description,
                    "responses": {"200": {"description": "OK", "content": content},
                                  "404": {"description": "Nema takve datoteke"}}}}


def spec(generated):
    return {
        "openapi": "3.1.0",
        "jsonSchemaDialect": "https://json-schema.org/draft/2020-12/schema",
        "info": {
            "title": "Fiskalna karta JLS: otvoreni API",
            "version": "1.0.0",
            "summary": "Ocjena financijske stabilnosti 576 općina, gradova i županija, kao statične datoteke.",
            "description": (
                "Statični API bez ključa i bez poslužitelja (GitHub Pages, CORS otvoren). Svi podaci izračunati su iz "
                "otvorenih podataka Ministarstva financija (PR-RAS, Bilanca), DZS-a (Popis 2021., INSPIRE WFS) i "
                "Portala otvorenih podataka (CKAN API). Metodologija: PLAN §3 u repozitoriju. "
                f"Datoteke su generirane {generated}."),
            "license": {"name": "CC BY 4.0", "identifier": "CC-BY-4.0"},
            "contact": {"name": "Fiskalna karta JLS", "url": REPO},
        },
        "externalDocs": {"description": "Kod i metodologija (EUPL-1.2)", "url": REPO},
        "servers": [{"url": PAGES, "description": "GitHub Pages"}, {"url": "./", "description": "Relativno"}],
        "paths": {
            "/jedinice.json": _get("Popis svih jedinica",
                                   "Šifre, nazivi, ocjene i bodovi po godini za svih 576 jedinica.", "Indeks"),
            "/jedinice/{slug}.json": {
                "parameters": [{"name": "slug", "in": "path", "required": True, "schema": {"type": "string"},
                                "description": "Slug jedinice iz jedinice.json, npr. grad-zagreb."}],
                **_get("Svjedodžba jedinice", "Sve godine, paket činjenica, objašnjenje i susjedi jedne jedinice.",
                       "Jedinica"),
            },
            "/skupine.json": _get("Medijani usporednih skupina", "Medijani po skupini i godini.", "Skupine"),
            "/sifrarnik.csv": _get("Šifrarnik jedinica",
                                   "OIB, RKP, šifra DGU/DZS, naziv, vrsta, županija i slug (UTF-8, zarez).",
                                   media="text/csv"),
            "/rezultati.csv": _get("Rezultati po jedinici i godini",
                                   "Ocjena, bodovi, pokazatelji I1-I5, bodovi S1-S5 i zastavice; jedan red po jedinici "
                                   "i godini (UTF-8, zarez).", media="text/csv"),
            "/izvori.json": _get("Zapis izvora",
                                 "Za svaki preuzeti izvor: URL, vrijeme preuzimanja i zadnje provjere, ETag ili "
                                 "Last-Modified, veličina, sha256, izdavatelj, licenca i CKAN metapodaci.",
                                 schema={"type": "object", "additionalProperties": {
                                     "type": "object", "required": ["url", "retrieved", "sha256"]}}),
            "/geo/jls.topo.json": _get("Granice (TopoJSON)",
                                       "Slojevi jls (556 općina i gradova, svojstva sifra, naziv, slug, oib, zup_id) "
                                       "i zupanije (21). Izvor: DZS INSPIRE WFS, Otvorena dozvola; pojednostavljeno "
                                       "mapshaperom.", schema={"type": "object"}),
        },
        "components": {"schemas": SCHEMAS},
    }
