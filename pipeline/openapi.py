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
            "uprava_pc_po_godini": {**BY_YEAR_NUM, "description": "Trošak opće uprave po stanovniku po godini, €."},
            "udio_tekucih_pomoci_po_godini": {**BY_YEAR_NUM,
                                              "description": "Udio tekućih pomoći u tekućim prihodima po godini."},
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
            "objasnjenje": {"type": ["object", "null"], "required": ["tekst", "izvor", "model", "provjera"],
                            "description": "Kratko objašnjenje ocjene. AI tekst (Gemma 4 na Kaggleu) objavljuje se samo ako je "
                                           "napisan iz istog paketa činjenica (pack_sha256) i ako prolazi provjeru brojki; "
                                           "inače predložak iz činjenica.", "properties": {
                "tekst": {"type": "string"},
                "izvor": {"type": "string", "enum": ["ai", "predlozak"]},
                "model": {"type": ["string", "null"], "description": "Model koji je napisao AI tekst, npr. Gemma 4 31B; null za predložak."},
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
        "required": ["clanice", "vrsta", "skupina", "stanovnici", "godina", "ocjene", "bodovi", "zadnja", "usteda",
                     "izravnanje"],
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
            "usteda": {
                "type": ["object", "null"],
                "description": "Potencijal uštede na općoj upravi (funkcija 01 bez 017 i 018) za zadnju godinu "
                               "(PLAN §4.3, odluka 17). Očekivani trošak je medijan troška uprave po stanovniku "
                               "usporedne skupine spojene jedinice puta broj stanovnika. Strukturni jaz je gornja "
                               "granica; realističan raspon je 0 do realno_do (najviše 10 % zbroja i najviše jaz).",
                "required": ["godina", "uprava_zbroj", "medijan_pc", "ocekivano", "strukturni_jaz", "realno_do",
                             "iznad_10000"],
                "properties": {
                    "godina": {"type": "integer"},
                    "uprava_zbroj": {**NUM, "description": "Zbroj troška opće uprave članica, € (uprava_pc spojene × stanovnici)."},
                    "medijan_pc": {**NUM, "description": "Medijan troška uprave po stanovniku u skupini, €."},
                    "ocekivano": {**NUM, "description": "medijan_pc × stanovnici, €."},
                    "strukturni_jaz": {**NUM, "minimum": 0, "description": "max(0, uprava_zbroj − ocekivano), €; gornja granica."},
                    "realno_do": {**NUM, "minimum": 0, "description": "min(0,10 × uprava_zbroj, strukturni_jaz), €."},
                    "iznad_10000": {"type": "boolean",
                                    "description": "Spojena jedinica ima više od 10.000 stanovnika: dodatna ušteda se ne očekuje."},
                },
            },
            "izravnanje": {"$ref": "#/components/schemas/Izravnanje"},
        },
    },
    "Izravnanje": {
        "type": ["object", "null"],
        "description": "Fiskalno izravnanje po zakonskoj formuli (Zakon o financiranju JLP(R)S, čl. 8. i 9.; "
                       "pipeline/izravnanje.py, docs/research/07): puni godišnji iznos za članice i za spojenu jedinicu, "
                       "uz kapacitete i referentne vrijednosti iz MF-ove tablice za danu godinu. Formula na toj tablici "
                       "reproducira MF-ove pune iznose za svih 576 jedinica. Isplata je udio u stavci državnog proračuna, "
                       "pa ovo nije iznos koji jedinica prima. null kad tablica nije preuzeta.",
        "required": ["godina", "puni_po_clanici", "puni_clanice", "puni_spojena", "promjena", "oznake"],
        "properties": {
            "godina": {"type": "integer", "description": "Godina na koju se tablica MF-a odnosi."},
            "puni_po_clanici": {"type": "array", "items": {"type": "number", "minimum": 0},
                                "description": "Puni iznos svake članice, €, istim redom kao clanice."},
            "puni_clanice": {"type": "number", "minimum": 0, "description": "Zbroj punih iznosa članica, €."},
            "puni_spojena": {"type": "number", "minimum": 0, "description": "Puni iznos spojene jedinice, €."},
            "promjena": {"type": "number", "description": "puni_spojena − puni_clanice, €. S tablicom za 2027. nikad nije pozitivna, "
                                                         "jer je referentna vrijednost za gradove niža od one za općine; zakon to ne jamči."},
            "promjena_udio": NUM,
            "kapacitet_pc": {"type": "number", "description": "Porezni kapacitet spojene jedinice po stanovniku, €."},
            "referentna_pc": {"type": "number", "description": "Referentna vrijednost za vrstu spojene jedinice, €."},
            "oznake": {"type": "array", "items": {"type": "string"},
                       "description": "Pretpostavke izračuna, npr. kapacitet_preracunat_na_stope_spojene, bez_prava_na_izravnanje."},
        },
    },
    "Metodologija": {
        "type": "object",
        "description": "Metodologija kako je kod primjenjuje (pipeline/metodologija.py): pomoćne veličine, pokazatelji s "
                       "formulom, ponderom i pragovima, granice ocjena, scenariji pondera, pravila, zastavice, usporedne "
                       "skupine, AI prompt i opis provjere, simulator i ograničenja.",
        "required": ["godina", "prozor", "velicine", "pokazatelji", "ocjene", "scenariji", "pravila", "zastavice", "ai",
                     "simulator", "ogranicenja"],
        "properties": {
            "godina": {"type": "integer"},
            "pokazatelji": {"type": "array", "items": {"type": "object", "required": ["oznaka", "formula", "ponder", "pragovi"]}},
            "ai": {"type": "object", "required": ["opis", "sustav", "pravila", "primjer", "prompt_sha256"]},
        },
    },
    "Izvor": {
        "type": "object",
        "description": "Vidljiva provjera brojki (PLAN §5, pipeline/provenance.py): za zadnju godinu formula svakog "
                       "pokazatelja I1-I5, pomoćne veličine po godinama i svi ulazni iznosi s mjestom u datotekama "
                       "Ministarstva financija (PR-RAS: radna knjiga u ZIP-u, list i redak; Bilanca: list i redak i "
                       "stupac). Iz samih ulaza dobivaju se objavljeni pokazatelji (tests/test_provenance.py).",
        "required": ["godina", "prozor", "pokazatelji", "velicine", "izvori", "konta", "ulazi"],
        "properties": {
            "godina": {"type": "integer"},
            "prozor": {"type": "object", "required": ["godine", "ponderi"], "properties": {
                "godine": {"type": "array", "items": {"type": "integer"}},
                "ponderi": {"type": "array", "items": {"type": "integer"}}}},
            "pokazatelji": {"type": "object", "propertyNames": {"enum": ["I1", "I2", "I3", "I4", "I5"]},
                            "additionalProperties": {"type": "object", "required": ["naziv", "formula", "vrijednost", "velicine"],
                                                     "properties": {"naziv": {"type": "string"}, "formula": {"type": "string"},
                                                                    "vrijednost": NUM, "bodovi": NUM,
                                                                    "velicine": {"type": "array", "items": {"type": "string"}}}}},
            "velicine": {"type": "object", "additionalProperties": {
                "type": "object", "required": ["formula", "godine"],
                "properties": {"formula": {"type": "string"}, "godine": {"type": "object", "additionalProperties": NUM}}}},
            "izvori": {"type": "object", "additionalProperties": {"type": "object", "properties": {
                "datoteka": STR, "list": STR}}},
            "konta": {"type": "object", "additionalProperties": {"type": "object", "required": ["izvor", "za"], "properties": {
                "naziv": STR, "izvor": {"enum": ["PR-RAS", "Bilanca"]},
                "za": {"type": "array", "items": {"type": "string"}, "description": "Veličine i pokazatelji koji koriste konto."}}}},
            "ulazi": {"type": "array", "items": {"type": "object", "required": ["konto", "godina", "iznos", "redak"], "properties": {
                "konto": {"type": "string"}, "godina": {"type": "integer"}, "iznos": {"type": "number"},
                "redak": {"type": ["integer", "null"], "description": "Redak u Excelu."},
                "stupac": {"type": ["string", "null"], "description": "Stupac u Excelu (Bilanca)."}}},
                      "description": "Ulazni iznosi u eurima; konta s iznosom 0 nisu navedena."},
            "napomena": {"type": "string"},
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
    "ReformaJedinica": {
        "type": "object",
        "description": "Jedinica nakon reforme: spojena skupina (2 ili više članica) ili jedinica koja se nije spajala. "
                       "Rezultat spojene skupine računa se istom funkcijom kao u simulatoru spajanja (pipeline/merge.py), "
                       "bez gornje granice broja članica.",
        "required": ["clanice", "naziv", "vrsta", "zup_id", "stanovnici", "skupina", "ocjene_prije", "ocjena",
                     "ocjena_rijec", "bodovi", "rang", "n_skupine", "usteda", "izravnanje"],
        "properties": {
            "clanice": {"type": "array", "minItems": 1, "items": {"type": "string", "pattern": "^[0-9]{5}$"},
                        "description": "Šifre DGU članica, poredane; jedna šifra za jedinicu koja se nije spajala."},
            "naziv": {"type": "string", "description": "Za skupinu kratki nazivi članica (bez \"Grad\"/\"Općina\") po broju "
                                                       "stanovnika silazno, npr. \"Pag + Povljana\"; inače puni naziv."},
            "vrsta": {"enum": ["grad", "opcina"], "description": "Grad ako je barem jedna članica grad."},
            "zup_id": {"type": "integer", "minimum": 1, "maximum": 20},
            "stanovnici": {"type": "integer", "minimum": 1, "description": "Popis 2021., zbroj članica."},
            "skupina": {"type": "string", "description": "Usporedna skupina po vrsti i ukupnom broju stanovnika."},
            "ocjene_prije": {"type": "object", "description": "Ocjena svake članice u zadnjoj godini (ključ je šifra).",
                             "propertyNames": {"pattern": "^[0-9]{5}$"},
                             "additionalProperties": {"type": ["integer", "null"], "minimum": 1, "maximum": 5}},
            "ocjena": {"type": ["integer", "null"], "minimum": 1, "maximum": 5,
                       "description": "Ocjena poslije reforme u zadnjoj godini; za jedinicu bez spajanja njezina vlastita."},
            "ocjena_rijec": STR,
            "bodovi": NUM,
            "rang": {**INT, "description": "Rang u usporednoj skupini postojećih jedinica (za skupinu bez njezinih članica)."},
            "n_skupine": INT,
            "usteda": {"$ref": "#/components/schemas/Spajanje/properties/usteda",
                       "description": "Ušteda na općoj upravi kao u simulatoru; null za jedinicu koja se nije spajala."},
            "izravnanje": {"$ref": "#/components/schemas/Izravnanje",
                           "description": "Fiskalno izravnanje kao u simulatoru; null za jedinicu koja se nije spajala."},
        },
    },
    "Reforma": {
        "type": "object",
        "description": "Karta reforme za jedan prag stanovnika (PLAN §5, odluka 17): scenarij, ne prijedlog granica. "
                       "Unutar svake županije, bez županija i Grada Zagreba, jedinica ili skupina s najmanje stanovnika "
                       "ispod praga spaja se sa susjedom (kopno ili veza preko mora) koji ima najmanje stanovnika; kod "
                       "izjednačenja odlučuje najniža šifra. Ponavlja se dok sve skupine ne dosegnu prag ili skupina "
                       "ispod praga nema više susjeda u županiji.",
        "required": ["prag", "godina", "n_prije", "n_poslije", "stanovnika_u_spojenima", "n_spojenih_skupina",
                     "n_ispod_praga", "usteda_realno_do_zbroj", "strukturni_jaz_zbroj", "jedinice"],
        "properties": {
            "prag": {"type": "integer", "enum": [2500, 5000, 10000], "description": "Prag stanovnika (Popis 2021.)."},
            "godina": {"type": "integer", "description": "Godina ocjena i uštede."},
            "napomena": {"type": "string"},
            "n_prije": {"type": "integer", "description": "Broj općina i gradova prije reforme, bez Grada Zagreba."},
            "n_poslije": {"type": "integer", "description": "Broj jedinica poslije reforme (duljina popisa jedinice)."},
            "stanovnika_u_spojenima": {"type": "integer", "description": "Stanovnici u skupinama s 2 ili više članica."},
            "n_spojenih_skupina": {"type": "integer"},
            "n_ispod_praga": {"type": "integer",
                              "description": "Jedinice koje su ostale ispod praga jer im je cijela povezana cjelina "
                                             "županije ispod praga."},
            "usteda_realno_do_zbroj": {"type": "number", "minimum": 0,
                                       "description": "Zbroj realno_do svih spojenih skupina, €: gornji kraj "
                                                      "realističnog raspona uštede (donji je 0)."},
            "strukturni_jaz_zbroj": {"type": "number", "minimum": 0,
                                     "description": "Zbroj strukturnih jazova spojenih skupina, €: gornja granica."},
            "izravnanje_promjena_zbroj": {"type": "number",
                                          "description": "Zbroj promjena punog iznosa fiskalnog izravnanja spojenih skupina, €."},
            "jedinice": {"type": "array", "items": {"$ref": "#/components/schemas/ReformaJedinica"}},
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
            "/jedinice/{slug}/izvor.json": {
                "parameters": [{"name": "slug", "in": "path", "required": True, "schema": {"type": "string"},
                                "description": "Slug jedinice iz jedinice.json."}],
                **_get("Odakle su brojke",
                       "Formula pokazatelja I1-I5, pomoćne veličine i ulazni iznosi s listom i retkom u datotekama MF-a.",
                       "Izvor"),
            },
            "/skupine.json": _get("Medijani usporednih skupina", "Medijani po skupini i godini.", "Skupine"),
            "/dcat.jsonld": _get("Katalog DCAT-AP", "Katalog skupova podataka projekta u DCAT-AP (JSON-LD), za "
                                 "preuzimanje u portal otvorenih podataka.", media="application/ld+json"),
            "/metodologija.json": _get("Metodologija", "Formule, pragovi, ponderi, pravila, AI prompt i provjera, "
                                       "kako ih kod primjenjuje.", "Metodologija"),
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
            "/reforma/prag-{prag}.json": {
                "parameters": [{"name": "prag", "in": "path", "required": True,
                                "schema": {"type": "string", "enum": ["2500", "5000", "10000"]},
                                "description": "Prag stanovnika: 2500, 5000 ili 10000."}],
                **_get("Karta reforme za jedan prag",
                       "Scenarij spajanja svih općina i gradova (bez Grada Zagreba) pohlepnim pravilom do praga "
                       "stanovnika: sve jedinice poslije reforme s ocjenama članica prije, ocjenom poslije i "
                       "uštedom na upravi. Scenarij, ne prijedlog granica.", "Reforma"),
            },
            "/geo/jls.topo.json": _get("Granice (TopoJSON)",
                                       "Slojevi jls (556 općina i gradova, svojstva sifra, naziv, slug, oib, zup_id) "
                                       "i zupanije (21). Izvor: DZS INSPIRE WFS, Otvorena dozvola; pojednostavljeno "
                                       "mapshaperom.", schema={"type": "object"}),
        },
        "components": {"schemas": SCHEMAS},
    }
