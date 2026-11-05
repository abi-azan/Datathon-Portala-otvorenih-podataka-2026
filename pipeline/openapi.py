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
DZS_IZVOR = {"enum": ["pxweb", "xlsx"]}
IZVOR_PO_GODINI = {"type": "object", "propertyNames": {"pattern": "^[0-9]{4}$"}, "additionalProperties": DZS_IZVOR,
                   "description": "Izvor demografskih brojki po godini: \"pxweb\" (DZS PxWeb API, glavni izvor) ili "
                                  "\"xlsx\" (publikacija DZS-a \"Gradovi i općine u statistici\", samo za godine koje "
                                  "PxWeb još nema; pipeline/dzs_xlsx.py)."}

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
            "z5_manjak_udio": {**NUM, "minimum": 0,
                               "description": "Kriterij od 10 % (Z5, zaključak Vlade 16.4.2026.): manjak prihoda nad rashodima "
                                              "((3 + 4) − (6 + 7), najmanje 0) kao udio u prihodima bez EU izvora "
                                              "(6 + 7 − 638 − 6324). Rashodi iz EU izvora uzimaju se jednaki EU prihodima. "
                                              "Naš izračun, ne MF-ov; ne ulazi u ocjenu."},
            "z5_zadovoljava": {"type": ["boolean", "null"], "description": "z5_manjak_udio <= 0,10."},
            "oznake": {"type": "array", "items": {"type": "string"}},
            "kvaliteta": {"type": "array", "items": {"type": "string"}},
        },
    },
    "Cinjenica": {"type": "object", "required": ["label", "value"],
                  "properties": {"label": {"type": "string"}, "value": {"type": "string"},
                                 "kontekst": {"type": "boolean",
                                              "description": "true za kontekst (kretanje stanovništva, neto dohodak) "
                                                             "koji ne ulazi u ocjenu; izostaje kod ostalih činjenica."}}},
    "Jedinica": {
        "type": "object",
        "description": "Pregled jedinice: šifre, struktura, sve godine, paket činjenica i objašnjenje.",
        "required": ["oib", "sifra", "slug", "naziv", "vrsta", "zupanija", "skupina", "stanovnici_2021", "godine",
                     "susjedi", "stanovnistvo_gospodarstvo", "izravnanje", "porezne_stope"],
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
            "revizija": {"type": ["object", "null"],
                         "description": "Zadnja financijska revizija Državnog ureda za reviziju (izvješća objavljena od 2019., "
                                        "pipeline/dur.py). null: na popisima DUR-a 2019.-2026. nije pronađena financijska "
                                        "revizija jedinice. Polja nema kad sloj revizija nije izgrađen.",
                         "required": ["objavljeno", "revidirana_godina", "misljenje", "url"],
                         "properties": {
                             "objavljeno": {"type": "integer", "description": "Godina objave izvješća."},
                             "revidirana_godina": INT,
                             "misljenje": {"enum": ["bezuvjetno", "uvjetno", "nepovoljno", "suzdržano", None]},
                             "url": {"type": "string", "format": "uri"}}},
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
                                "description": "Neslaganja sa činjenicama: najslabiji pokazatelj, jake strane, ograničenje "
                                               "ocjene. Činjenice s \"kontekst\": true (stanovništvo, dohodak) ne ulaze u "
                                               "ocjenu."}}}}},
            "stanovnistvo_gospodarstvo": {"$ref": "#/components/schemas/StanovnistvoGospodarstvo"},
            "izravnanje": {"$ref": "#/components/schemas/IzravnanjeJedinice"},
            "porezne_stope": {
                "type": ["object", "null"],
                "description": "Lokalne porezne stope prema odlukama jedinica (Porezna uprava), po godini. null za županije, "
                               "koje te stope ne određuju.",
                "additionalProperties": {"$ref": "#/components/schemas/PorezneStope"}},
        },
    },
    "KontekstPokazatelj": {
        "type": "object",
        "required": ["godina", "vrijednost", "oznaka", "broj", "medijan", "n_medijan"],
        "properties": {
            "godina": {"type": "integer"},
            "od_godine": {"type": "integer", "description": "Samo za promjenu stanovništva: prva godina niza."},
            "vrijednost": {**NUM, "description": "null kad podatka nema ili je povjerljiv (oznaka z)."},
            "oznaka": {"enum": ["-", "z", None],
                       "description": "Simbol DZS-a: \"-\" pojava ne postoji (broji se kao 0), \"z\" tajnost (vrijednost je null)."},
            "broj": {**NUM, "description": "Iznos prije dijeljenja: razlika stanovnika, broj rođenih minus umrlih, "
                                           "doseljenih minus odseljenih, noćenja, zgrada s dozvolom, neto dohodak ili mirovine (€)."},
            "medijan": {**NUM, "description": "Medijan usporedne skupine; null za Grad Zagreb, koji skupinu nema."},
            "n_medijan": {"type": "integer", "minimum": 0, "description": "Broj jedinica skupine s vrijednošću."},
            "izvor": {**DZS_IZVOR, "description": "Samo za promjenu stanovništva, prirodni prirast i neto migraciju: izvor "
                                                  "brojki zadnje godine (izvor_po_godini)."},
        },
    },
    "StanovnistvoGospodarstvo": {
        "type": "object",
        "description": "Stanovništvo i gospodarstvo (pipeline/kontekst.py; DZS PxWeb, za godine koje PxWeb još nema "
                       "publikacija DZS-a \"Gradovi i općine u statistici\", i Porezna uprava). Ne ulazi u ocjenu. "
                       "Procjene stanovništva služe samo za kretanje; iznosi po stanovniku računaju se s Popisom 2021.",
        "required": ["skupina", "pokazatelji", "procjene", "izvor_po_godini", "uzivo", "izvori"],
        "properties": {
            "skupina": {**STR, "description": "Usporedna skupina medijana; null za Grad Zagreb."},
            "pokazatelji": {
                "type": "object",
                "required": ["promjena_stanovnistva", "prirodni_prirast", "neto_migracija", "nocenja_po_stanovniku",
                             "dozvole_na_1000", "neto_dohodak_pc", "udio_mirovina"],
                "description": "promjena_stanovnistva: procjena zadnje godine / procjena 2021. − 1 (SP31_2); prirodni_prirast i "
                               "neto_migracija: (živorođeni − umrli) i (doseljeni − odseljeni) na 1.000 stanovnika (SV131, "
                               "SV331, SM31), u zadnjoj godini; godine koje PxWeb još nema iz publikacije DZS-a (listovi "
                               "Tab-2. i Tab-3.); nocenja_po_stanovniku: noćenja u komercijalnom smještaju (BS_TU19); "
                               "dozvole_na_1000: zgrade s izdanom građevinskom dozvolom (PX14); neto_dohodak_pc: neto dohodak "
                               "stanovnika (Porezna uprava); udio_mirovina: udio mirovina u njemu.",
                "additionalProperties": {"$ref": "#/components/schemas/KontekstPokazatelj"}},
            "procjene": {"type": "object", "description": "Procjena stanovništva 31.12. po godini, od 2021. (SP31_2; "
                                                         "godine koje PxWeb još nema iz publikacije, vidi izvor_po_godini).",
                         "additionalProperties": NUM},
            "izvor_po_godini": IZVOR_PO_GODINI,
            "uzivo": {"type": ["object", "null"],
                      "description": "Upit koji preglednik šalje DZS-u za niz procjena (POST na url, tijelo je upit, "
                                     "Content-Type text/plain; odgovor json-stat2).",
                      "required": ["tablica", "kod", "naziv", "url", "upit"],
                      "properties": {"tablica": {"type": "string"}, "kod": {"type": "string"},
                                     "naziv": {**STR, "description": "Naziv koji DZS daje kodu (metapodaci tablice); "
                                                                     "preglednik odbacuje odgovor s drugim nazivom."},
                                     "url": {"type": "string", "pattern": "^https://web\\.dzs\\.hr/"},
                                     "upit": {"type": "object", "required": ["query", "response"]}}},
            "izvori": {"type": "array", "items": {
                "type": "object", "required": ["izdavatelj", "naziv", "url", "azurirano"],
                "properties": {"izdavatelj": {"type": "string"}, "naziv": STR, "tablica": STR,
                               "url": {"type": "string", "pattern": "^https://"},
                               "azurirano": {**STR, "description": "Datum ažuriranja prema izdavatelju (PxWeb ili Last-Modified)."},
                               "preuzeto": STR,
                               "godine": {"type": "array", "items": {"type": "integer"},
                                          "description": "Samo za publikaciju DZS-a: godine koje dolaze iz nje."}}}},
        },
    },
    "IzravnanjeJedinice": {
        "type": ["object", "null"],
        "description": "Fiskalno izravnanje jedinice (Zakon o financiranju JLP(R)S, čl. 8. i 9.; pipeline/kontekst.py) iz "
                       "tablice Ministarstva financija za godinu godina. Isplata = puni iznos / zbroj punih iznosa svih "
                       "jedinica × iznos u državnom proračunu (za proracun_godina; za godinu tablice još nije utvrđen).",
        "required": ["godina", "proracun_godina", "iznos_proracuna", "vrsta_reference", "kapacitet_pc", "referentna_pc",
                     "puni_iznos", "udio", "isplata", "stopa", "uz_najvise_stope"],
        "properties": {
            "godina": {"type": "integer", "description": "Godina tablice MF-a."},
            "proracun_godina": {"type": "integer"},
            "iznos_proracuna": {"type": "number", "description": "Iznos za izravnanje u državnom proračunu, €."},
            "vrsta_reference": {"enum": ["opcina", "grad", "zupanija"],
                                "description": "Čija referentna vrijednost vrijedi; Grad Zagreb se mjeri s gradovima."},
            "kapacitet_pc": {"type": "number", "description": "Kapacitet poreznih prihoda po stanovniku, € (uz najvišu dopuštenu stopu)."},
            "referentna_pc": {"type": "number", "description": "Referentna vrijednost po stanovniku, €."},
            "puni_iznos": {"type": "number", "minimum": 0, "description": "Puni iznos po formuli, €; nije iznos koji jedinica prima."},
            "udio": {"type": "number", "minimum": 0, "maximum": 1},
            "isplata": {"type": "number", "minimum": 0, "description": "Procjena godišnje isplate, €."},
            "stopa": {"type": ["object", "null"], "required": ["godina", "niza", "niza_max", "ispod_maksimuma"],
                      "description": "Niža stopa poreza na dohodak i najviša koju jedinica smije odrediti; null za županije.",
                      "properties": {"godina": {"type": "integer"}, "niza": NUM, "visa": NUM, "niza_max": NUM,
                                     "visa_max": {**NUM, "description": "niza_max + 10 postotnih bodova (čl. 19.a st. 2. "
                                                                       "Zakona o porezu na dohodak)."},
                                     "ispod_maksimuma": {"type": ["boolean", "null"]}}},
            "uz_najvise_stope": {
                "type": ["object", "null"],
                "description": "Procjena koliko bi proračun jedinice godišnje imao više uz najviše dopuštene stope poreza na "
                               "dohodak (docs/research/11 §2.5). Samo za jedinice kojima je niža stopa ispod najviše; inače "
                               "null. Ne ulazi u ocjenu. Porez stanovnika (Porezna uprava) samo na plaće, mirovine, obrt i "
                               "drugi dohodak, koji plaćaju lokalnu stopu; dio višeg razreda iz broja obveznika iznad granice "
                               "(Pareto, α 2); udio jedinice: konto 611 / porez stanovnika iste godine.",
                "required": ["godina_stopa", "godina_poreza", "procjena", "od", "do", "niza", "visa", "niza_max", "visa_max"],
                "properties": {
                    "godina_stopa": {"type": "integer"}, "godina_poreza": {"type": "integer"},
                    "procjena": {"type": "number", "minimum": 0, "description": "€ godišnje, proračun jedinice."},
                    "od": {"type": "number", "minimum": 0,
                           "description": "Donja granica: najmanja procjena (bez višeg razreda; Pareto α 3, 2, 1,6) umanjena za 15 %."},
                    "do": {"type": "number", "minimum": 0, "description": "Gornja granica: najveća od tih procjena."},
                    "niza": {"type": "number"}, "visa": {"type": "number"},
                    "niza_max": {"type": "number"}, "visa_max": {"type": "number"},
                    "porez_lokalne_vrste": {"type": "number", "description": "Porez stanovnika na plaće, mirovine, obrt i drugi dohodak, €."},
                    "udio_u_proracunu": {"type": "number", "description": "Konto 611 jedinice / porez stanovnika."},
                    "udio_visi_razred": {"type": "number", "description": "Udio obveznika iznad granice višeg razreda (zadnja godina tablice razreda)."},
                }},
        },
    },
    "PorezneStope": {
        "type": "object",
        "properties": {
            "niza": NUM, "visa": NUM,
            "niza_max": {**NUM, "description": "Najviša niža stopa koju jedinica smije odrediti (tablica izravnanja MF-a)."},
            "ispod_maksimuma": {"type": ["boolean", "null"]},
            "potrosnja_min": NUM, "potrosnja_max": NUM,
            "nekretnine_min": {**NUM, "description": "Porez na nekretnine, €/m²; min i max kad odluka daje raspon."},
            "nekretnine_max": NUM,
            "nekretnine_naplata": {**STR, "description": "Tko naplaćuje porez na nekretnine: JLS ili PU (Porezna uprava)."},
        },
    },
    "Skupine": {
        "type": "object",
        "description": "Medijani po usporednoj skupini i godini: bodovi, I1-I5, bodovi S1-S5, trošak uprave, udio pomoći.",
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
                               "description": "Datum zadnje izmjene kako ga navodi izdavatelj: datum ažuriranja tablice u "
                                              "PxWeb-u DZS-a, HTTP Last-Modified datoteke ili datum revizije u metapodacima. Otvorena dozvola traži da se "
                                              "navede. Prazno za izvore koji se stalno mijenjaju (katalog portala, OSM): "
                                              "vrijedi stanje pri preuzimanju."},
            "pristup": {"type": "string", "enum": ["API (CKAN)", "API (OGC WFS)", "API (PxWeb)", "datoteka (XLSX/ZIP)",
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
                     "izravnanje", "poticaj", "demografija"],
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
                    "z5_manjak_udio": {"$ref": "#/components/schemas/Godina/properties/z5_manjak_udio"},
                    "z5_zadovoljava": {"$ref": "#/components/schemas/Godina/properties/z5_zadovoljava"},
                },
            },
            "usteda": {
                "type": ["object", "null"],
                "description": "Potencijal uštede na općoj upravi (funkcija 01 bez 017 i 018) za zadnju godinu, samo "
                               "od veličine unutar vrste spojene jedinice (odluka 4.11., docs/research/08 §7.1). Svaka "
                               "članica vrednuje se medijanom svog razreda veličine u vrsti spojene jedinice, a spojena "
                               "medijanom svoje skupine; razlika je razmjer. Realističan raspon je 0 do realno_do "
                               "(najviše razmjer i najviše 10 % zbroja). Koliko članice troše iznad svojih skupina "
                               "prikazuje se odvojeno (jaz_bez_spajanja): to nije ušteda od spajanja.",
                "required": ["godina", "uprava_zbroj", "medijan_pc", "ocekivano", "ocekivano_clanice", "razmjer",
                             "realno_do", "jaz_bez_spajanja", "iznad_10000"],
                "properties": {
                    "godina": {"type": "integer"},
                    "uprava_zbroj": {**NUM, "description": "Zbroj troška opće uprave članica, € (uprava_pc spojene × stanovnici)."},
                    "medijan_pc": {**NUM, "description": "Medijan troška uprave po stanovniku u skupini, €."},
                    "ocekivano": {**NUM, "description": "medijan_pc × stanovnici, €."},
                    "ocekivano_clanice": {**NUM, "minimum": 0,
                                          "description": "Σ medijan(vrsta spojene, razred veličine članice) × stanovnici članice, €."},
                    "razmjer": {**NUM, "minimum": 0, "description": "max(0, ocekivano_clanice − ocekivano), €: učinak veličine."},
                    "realno_do": {**NUM, "minimum": 0, "description": "min(0,10 × uprava_zbroj, razmjer), €."},
                    "jaz_bez_spajanja": {**NUM, "minimum": 0,
                                         "description": "Σ max(0, trošak članice − medijan njezine skupine × njezini "
                                                        "stanovnici), €: postoji i bez spajanja."},
                    "iznad_10000": {"type": "boolean",
                                    "description": "Spojena jedinica ima više od 10.000 stanovnika: dodatna ušteda se ne očekuje."},
                },
            },
            "izravnanje": {"$ref": "#/components/schemas/Izravnanje"},
            "poticaj": {
                "type": ["object", "null"],
                "description": "Poticaj za stvarno spajanje po Odluci NN 88/2022, t. IX. (na snazi i u 2026.). "
                               "Pretpostavka: najveća članica pripaja ostale. Za svaku pripojenu članicu iz I.–V. "
                               "skupine razvijenosti jedinica koja pripaja pet godina dobiva godišnje 2 × njezino "
                               "fiskalno izravnanje iz godine prije spajanja i do 995.421 € za kapitalne projekte; "
                               "podmiruju se i njezine dospjele obveze i krediti sa stanjem 30. lipnja 2022. To je "
                               "prijenos iz državnog proračuna, ne ušteda.",
                "required": ["pripaja", "s_pravom", "izravnanje_isplata", "godisnje", "ukupno", "kapitalni_do",
                             "omjer_isplate"],
                "properties": {
                    "pripaja": {"type": "string", "pattern": "^[0-9]{5}$", "description": "Šifra članice koja pripaja."},
                    "s_pravom": {"type": "array", "items": {"type": "string", "pattern": "^[0-9]{5}$"},
                                 "description": "Pripojene članice u I.–V. skupini razvijenosti."},
                    "izravnanje_isplata": {**NUM, "minimum": 0,
                                           "description": "Procjena godišnje isplate izravnanja pripojenih članica s pravom, "
                                                          "€: puni iznos × omjer_isplate."},
                    "godisnje": {**NUM, "minimum": 0, "description": "2 × izravnanje_isplata, €."},
                    "ukupno": {**NUM, "minimum": 0, "description": "5 × godisnje, €."},
                    "kapitalni_do": {"type": "number", "minimum": 0, "description": "Najviše za kapitalne projekte, €."},
                    "omjer_isplate": {**NUM, "description": "Stavka proračuna za 2026. / zbroj punih iznosa u tablici MF-a."},
                },
            },
            "demografija": {
                "type": ["object", "null"],
                "description": "Kretanje stanovništva (pipeline/merge.py demography, odluka P4): procjene stanovništva DZS-a "
                               "članica zbrojene po godini, prirodna promjena i migracijski saldo za zadnju godinu. Ne ulazi "
                               "u ocjenu: ocjena i iznosi po stanovniku koriste Popis 2021. Simbol DZS-a \"-\" (pojave "
                               "nema) broji se kao 0; drugi prazni podatak (npr. \"z\", tajno) daje null, pa je null i "
                               "zbroj. Stopa na 1.000 stanovnika je prirodna (ili migracije) / stanovnici (Popis 2021.) "
                               "× 1000. null kad dzs.parquet nije izgrađen.",
                "required": ["od", "do", "stanovnici", "promjena", "prirodna", "migracije", "clanice"],
                "properties": {
                    "od": {"type": "integer", "description": "Prva godina niza (2021.)."},
                    "do": {"type": "integer", "description": "Zadnja godina niza; godina prirodne promjene i migracija."},
                    "stanovnici": {"type": "array", "minItems": 2, "items": {"type": ["integer", "null"], "minimum": 0},
                                   "description": "Zbroj procjena stanovništva članica na dan 31.12., za svaku godinu od "
                                                  "od do do (izvor po godini: demografija_izvor_po_godini datoteke)."},
                    "promjena": {**NUM, "description": "stanovnici[zadnja] / stanovnici[prva] − 1, udio, na 3 decimale."},
                    "prirodna": {**INT, "description": "Živorođeni − umrli u godini do, zbroj članica."},
                    "migracije": {**INT, "description": "Doseljeni − odseljeni u godini do, zbroj članica (unutarnje i "
                                                        "vanjske migracije)."},
                    "clanice": {"type": "array", "items": NUM,
                                "description": "Promjena stanovništva svake članice od od do do, udio, istim redom kao "
                                               "clanice."},
                    "oznake": {"type": "array", "items": {"type": "string", "pattern": "^[0-9]{5}:[a-z_]+:[0-9]{4}:.+$"},
                               "description": "Simboli DZS-a u korištenim ćelijama, \"sifra:pokazatelj:godina:simbol\" "
                                              "(npr. \"04235:zivorodeni:2024:-\"); izostaje kad ih nema."},
                },
            },
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
            "iznos_proracuna": {"type": "number", "description": "Iznos za izravnanje u državnom proračunu, €; za godinu "
                                                                 "tablice još nije utvrđen, pa se uzima zadnji poznati (2026.)."},
            "omjer_prije": {"type": "number", "description": "iznos_proracuna / zbroj punih iznosa svih jedinica u tablici."},
            "omjer_poslije": {**NUM, "description": "Isto, sa zbrojem punih iznosa nakon spajanja (u Karti reforme: nakon "
                                                    "svih spajanja scenarija)."},
            "isplata_po_clanici": {"type": "array", "items": {"type": "number", "minimum": 0},
                                   "description": "Procjena godišnje isplate svake članice prije spajanja, €: puni iznos × omjer_prije."},
            "isplata_clanice": {"type": "number", "minimum": 0, "description": "Zbroj isplata članica prije spajanja, €."},
            "isplata_spojena": {"type": "number", "minimum": 0, "description": "puni_spojena × omjer_poslije, €."},
            "isplata_promjena": {"type": "number",
                                 "description": "isplata_spojena − isplata_clanice, €. Iznos u proračunu je fiksan, pa "
                                                "toliko (s obrnutim predznakom) dobivaju ostale jedinice; država ne štedi."},
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
                     "simulator", "ogranicenja", "stanovnistvo_gospodarstvo", "izravnanje_jedinice"],
        "properties": {
            "godina": {"type": "integer"},
            "pokazatelji": {"type": "array", "items": {"type": "object", "required": ["oznaka", "formula", "ponder", "pragovi"]}},
            "ai": {"type": "object", "required": ["opis", "sustav", "pravila", "primjer", "prompt_sha256"]},
            "kriterij_10": {"type": "string", "description": "Opis kriterija od 10 % (Z5) i kako se računa."},
            "stanovnistvo_gospodarstvo": {"type": "string",
                                          "description": "Kartica Stanovništvo i gospodarstvo u pregledu jedinice: pokazatelji, "
                                                         "izvori, simboli DZS-a i medijani. Ne ulazi u ocjenu."},
            "izravnanje_jedinice": {"type": "string",
                                    "description": "Kartica Fiskalno izravnanje u pregledu jedinice: kapacitet, referentna "
                                                   "vrijednost, isplata i stopa poreza na dohodak."},
            "simulator": {"type": "object", "required": ["usteda", "poticaj", "izravnanje", "reforma"]},
        },
    },
    "Izvor": {
        "type": "object",
        "description": "Vidljiva provjera brojki (PLAN §5, pipeline/provenance.py): za zadnju godinu formula svakog "
                       "pokazatelja I1-I5, pomoćne veličine po godinama i svi ulazni iznosi s mjestom u datotekama "
                       "Ministarstva financija (PR-RAS: radna knjiga u ZIP-u, list i redak; Bilanca: list i redak i "
                       "stupac; fiskalno izravnanje: tablica odluke MF-a za tu godinu, list, redak i stupac udjela, uz "
                       "iznos u proračunu). Iz samih ulaza dobivaju se objavljeni pokazatelji (tests/test_provenance.py).",
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
                "properties": {"formula": {"type": "string"}, "godine": {"type": "object", "additionalProperties": NUM},
                               "izvor": {"type": "object", "additionalProperties": {
                                   "enum": ["odluka", "konto_6353", "porez_na_dohodak"]},
                                   "description": "Samo FI: odakle je iznos u godini. odluka = udio iz odluke MF-a × iznos "
                                                  "u proračunu (najviše 6331 + 6352 + 6353); konto_6353 = nema odluke, "
                                                  "konto 6353 kako je knjižen; porez_na_dohodak = do 2020. izravnanje je "
                                                  "bilo udio u porezu na dohodak (611), pa se ne dodaje."}}}},
            "izvori": {"type": "object", "additionalProperties": {"type": "object", "properties": {
                "datoteka": STR, "list": STR}}},
            "konta": {"type": "object", "additionalProperties": {"type": "object", "required": ["izvor", "za"], "properties": {
                "naziv": STR, "izvor": {"enum": ["PR-RAS", "Bilanca", "Odluka MF-a"]},
                "za": {"type": "array", "items": {"type": "string"}, "description": "Veličine i pokazatelji koji koriste konto."}}}},
            "ulazi": {"type": "array", "items": {"type": "object", "required": ["konto", "godina", "iznos", "redak"], "properties": {
                "konto": {"type": "string"}, "godina": {"type": "integer"}, "iznos": {"type": "number"},
                "redak": {"type": ["integer", "null"], "description": "Redak u Excelu."},
                "stupac": {"type": ["string", "null"], "description": "Stupac u Excelu (Bilanca, Odluka MF-a)."},
                "datoteka": {"type": "string", "description": "Odluka MF-a: tablica udjela za tu godinu (XLSX s mfin.gov.hr)."},
                "list": {"type": "string", "description": "Odluka MF-a: list tablice (Udjeli ili Izračun)."},
                "udio": {"type": "number", "description": "Odluka MF-a: udio jedinice u sredstvima izravnanja."},
                "proracun": {"type": "number", "description": "Odluka MF-a: iznos u državnom proračunu za tu godinu, €."}}},
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
            "demografija_izvor_po_godini": {**IZVOR_PO_GODINI, "type": ["object", "null"]},
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
                     "ocjena_rijec", "bodovi", "rang", "n_skupine", "usteda", "izravnanje", "poticaj", "demografija"],
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
            "poticaj": {"$ref": "#/components/schemas/Spajanje/properties/poticaj",
                        "description": "Poticaj po NN 88/2022 kao u simulatoru; null za jedinicu koja se nije spajala."},
            "demografija": {"$ref": "#/components/schemas/Spajanje/properties/demografija",
                            "description": "Kretanje stanovništva kao u simulatoru, i za jedinicu koja se nije spajala."},
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
                     "n_ispod_praga", "usteda_realno_do_zbroj", "razmjer_zbroj", "jaz_bez_spajanja_zbroj",
                     "poticaj_godisnje_zbroj", "demografija", "jedinice"],
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
            "razmjer_zbroj": {"type": "number", "minimum": 0,
                              "description": "Zbroj učinka veličine (razmjer) spojenih skupina, €, prije granice od 10 %."},
            "jaz_bez_spajanja_zbroj": {"type": "number", "minimum": 0,
                                       "description": "Zbroj jazova članica prema vlastitim skupinama, €: postoji i bez spajanja."},
            "poticaj_godisnje_zbroj": {"type": "number", "minimum": 0,
                                       "description": "Zbroj godišnjeg poticaja po NN 88/2022 svih spojenih skupina, €."},
            "izravnanje_promjena_zbroj": {"type": "number",
                                          "description": "Zbroj promjena punog iznosa fiskalnog izravnanja spojenih skupina, €."},
            "izravnanje_omjer_prije": {"type": "number", "description": "Isplata / zbroj punih iznosa prije reforme."},
            "izravnanje_omjer_poslije": {"type": "number", "description": "Isto nakon svih spajanja scenarija."},
            "izravnanje_isplata_spojene_promjena": {"type": "number",
                                                    "description": "Promjena godišnje isplate izravnanja spojenih skupina, €."},
            "izravnanje_isplata_ostale_promjena": {"type": "number",
                                                   "description": "Promjena isplate jedinica koje se nisu spajale, €: "
                                                                  "uvijek suprotna prethodnoj, jer je iznos u proračunu fiksan."},
            "demografija": {
                "type": ["object", "null"],
                "description": "Promjena stanovništva (procjene DZS-a, zbroj) od od do do za sve spojene skupine zajedno "
                               "i za jedinice koje se nisu spajale. Ne ulazi u ocjenu. null bez dzs.parquet.",
                "required": ["od", "do", "spojene", "ostale"],
                "properties": {
                    "od": {"type": "integer"}, "do": {"type": "integer"},
                    "izvor_po_godini": IZVOR_PO_GODINI,
                    "spojene": {"type": ["object", "null"], "required": ["stanovnici_od", "stanovnici_do", "promjena"],
                          "properties": {"stanovnici_od": {"type": "integer"}, "stanovnici_do": {"type": "integer"},
                                         "promjena": NUM},
                                "description": "Spojene skupine (2 ili više članica)."},
                    "ostale": {"type": ["object", "null"], "required": ["stanovnici_od", "stanovnici_do", "promjena"],
                          "properties": {"stanovnici_od": {"type": "integer"}, "stanovnici_do": {"type": "integer"},
                                         "promjena": NUM},
                               "description": "Jedinice koje se nisu spajale."},
                },
            },
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
            "summary": "Ocjena financijske održivosti proračuna 576 općina, gradova i županija, kao statične datoteke.",
            "description": (
                "Statični API bez ključa i bez poslužitelja (GitHub Pages, CORS otvoren). Svi podaci izračunati su iz "
                "otvorenih podataka Ministarstva financija (PR-RAS, Bilanca, fiskalno izravnanje), DZS-a (Popis 2021., "
                "INSPIRE WFS, PxWeb API), Porezne uprave i Portala otvorenih podataka (CKAN API). Popis svih skupova s licencama je skupovi.json. "
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
                **_get("Pregled jedinice", "Sve godine, paket činjenica, objašnjenje i susjedi jedne jedinice, uz kontekst "
                       "koji ne ulazi u ocjenu: stanovništvo i gospodarstvo, fiskalno izravnanje i lokalne porezne stope.",
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
