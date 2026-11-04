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
                    "nepoznate": {"type": "array", "items": {"type": "string"}},
                    "sadrzaj": {"type": "array", "items": {"type": "string"},
                                "description": "Neslaganja sa činjenicama: najslabija sastavnica, jake strane, ograničenje ocjene."}}}}},
        },
    },
    "Skupine": {
        "type": "object",
        "description": "Medijani po usporednoj skupini i godini: bodovi, I1-I5, trošak uprave, udio pomoći.",
        "additionalProperties": {"type": "object", "additionalProperties": {
            "type": "object", "additionalProperties": NUM}},
    },
    "Skup": {
        "type": "object",
        "description": "Jedan korišteni (ili planirani) skup podataka. Izvor je data/reference/skupovi.csv.",
        "required": ["naziv", "izdavatelj", "url", "licenca", "pristup"],
        "properties": {
            "kljuc": {"type": "string", "pattern": "^[a-z0-9_]+$",
                      "description": "Ključ izvora; isti kao u izvori.json kad ETL izvor preuzima sam."},
            "naziv": {"type": "string", "minLength": 1},
            "izdavatelj": {"type": "string", "minLength": 1},
            "url": {"type": "string", "pattern": "^https://", "description": "Datoteka, API ili model."},
            "portal_url": {"type": ["string", "null"], "description": "Stranica skupa (portal ili izdavatelj)."},
            "licenca": {"type": "string", "minLength": 1},
            "licenca_url": {"type": ["string", "null"], "pattern": "^https://",
                            "description": "Tekst licence ili uvjeta, odnosno propis na kojem se temelji ponovna uporaba."},
            "licenca_dokaz": {"type": ["string", "null"], "pattern": "^https://",
                              "description": "Gdje izdavatelj navodi licencu ili uvjete (metapodaci, uvjeti korištenja)."},
            "zadnja_izmjena": {"type": ["string", "null"], "format": "date",
                               "description": "Datum zadnje izmjene kako ga navodi izdavatelj: HTTP Last-Modified "
                                              "datoteke ili datum revizije u metapodacima. Otvorena dozvola traži da se "
                                              "navede. Prazno za izvore koji se stalno mijenjaju (katalog portala, OSM): "
                                              "vrijedi stanje pri preuzimanju."},
            "pristup": {"type": "string", "enum": ["API (CKAN)", "API (OGC WFS)", "datoteka (XLSX/ZIP)",
                                                   "datoteka (PDF)", "vektorske pločice", "model"]},
            "uloga": STR,
            "koristi_se": {"type": "boolean", "description": "false: planirano, još nije u kodu."},
            "zadnje_preuzimanje": {"type": "string", "format": "date-time"},
            "zadnja_provjera": {"type": "string", "format": "date-time",
                                "description": "Zadnji uvjetni GET (304 znači da se datoteka nije promijenila)."},
            "bajtova": {"type": "integer"},
            "sha256": {"anyOf": [{"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                 {"type": "array", "items": {"type": "string", "pattern": "^[0-9a-f]{64}$"}}],
                       "description": "sha256 preuzete datoteke; za izvor u stranicama (CKAN) jedan po stranici."},
            "stranica": {"type": "integer", "description": "Broj stranica kad se izvor preuzima u dijelovima."},
        },
    },
    "Skupovi": {"type": "array", "minItems": 1, "items": {"$ref": "#/components/schemas/Skup"}},
    "Spajanje": {
        "type": "object",
        "description": "Zamišljena jedinica nastala spajanjem 2-4 susjedne jedinice iste županije (pipeline/merge.py). "
                       "Tokovi i stanja zbrajaju se po godini, a ocjena se računa istom metodologijom kao za "
                       "postojeće jedinice. Pravilo 1 primjenjuje se po članici prije zbrajanja.",
        "required": ["clanice", "vrsta", "skupina", "stanovnici", "godina", "ocjene", "bodovi", "zadnja"],
        "properties": {
            "clanice": {"type": "array", "minItems": 2, "maxItems": 4,
                        "items": {"type": "string", "pattern": "^[0-9]{5}$"},
                        "description": "Šifre DGU članica, poredane."},
            "vrsta": {"enum": ["grad", "opcina"], "description": "Grad ako je barem jedna članica grad."},
            "skupina": {"type": "string", "description": "Usporedna skupina po vrsti i ukupnom broju stanovnika."},
            "stanovnici": {"type": "integer", "minimum": 1},
            "godina": {"type": "integer", "description": "Zadnja godina koju imaju sve članice."},
            "ocjene": BY_YEAR_INT,
            "bodovi": BY_YEAR_NUM,
            "zadnja": {
                "type": "object",
                "description": "Rezultat za zadnju godinu: bodovi, ocjena, pokazatelji I1-I5, bodovi S1-S5, zastavice, "
                             "kontekst i rang u skupini bez samih članica.",
                "required": ["ocjena", "bodovi", "rang", "n_skupine"],
                "properties": {
                    "ocjena": {"type": "integer", "minimum": 1, "maximum": 5},
                    "bodovi": {"type": "number"},
                    "rang": {"type": "integer", "minimum": 1},
                    "n_skupine": {"type": "integer", "minimum": 1},
                    "percentil": NUM,
                    "zastavice": {"type": "array", "items": {"type": "string"}},
                    "kvaliteta": {"type": "array", "items": {"type": "string"}},
                    **{f"I{i}": NUM for i in range(1, 6)}, **{f"S{i}": NUM for i in range(1, 6)},
                },
            },
        },
    },
    "SimulatorZupanija": {
        "type": "object",
        "required": ["zup_id", "zupanija", "skupine"],
        "properties": {
            "zup_id": {"type": "integer", "minimum": 1, "maximum": 21},
            "zupanija": {"type": "string"},
            "skupine": {
                "type": "object",
                "description": "Sve dopuštene skupine u županiji. Ključ su šifre članica, poredane i spojene crticom "
                               "(npr. \"05738-05746\").",
                "propertyNames": {"pattern": "^[0-9]{5}(-[0-9]{5}){1,3}$"},
                "additionalProperties": {"$ref": "#/components/schemas/Spajanje"},
            },
        },
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
                "Portala otvorenih podataka (CKAN API). Popis svih skupova s licencama je skupovi.json. "
                "Metodologija: PLAN §3 u repozitoriju. "
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
            "/skupovi.json": _get("Popis skupova podataka",
                                  "Svi skupovi podataka koje projekt koristi: naziv, izdavatelj, poveznica, licenca, "
                                  "način pristupa i uloga. Uz izvore koje ETL preuzima sam stoje vrijeme zadnjeg "
                                  "preuzimanja i sha256.", "Skupovi"),
            "/simulator/zup-{id}.json": {
                "parameters": [{"name": "id", "in": "path", "required": True,
                                "schema": {"type": "string", "pattern": "^[0-9]{2}$"},
                                "description": "Dvoznamenkasti zup_id, npr. 13 za Zadarsku županiju."}],
                **_get("Simulator spajanja za jednu županiju",
                       "Unaprijed izračunati rezultati svih skupina od 2-4 susjedne jedinice unutar županije "
                       "(bez županija i Grada Zagreba).", "SimulatorZupanija"),
            },
            "/geo/jls.topo.json": _get("Granice (TopoJSON)",
                                       "Slojevi jls (556 općina i gradova, svojstva sifra, naziv, slug, oib, zup_id) "
                                       "i zupanije (21). Izvor: DZS INSPIRE WFS, Otvorena dozvola; pojednostavljeno "
                                       "mapshaperom.", schema={"type": "object"}),
        },
        "components": {"schemas": SCHEMAS},
    }
