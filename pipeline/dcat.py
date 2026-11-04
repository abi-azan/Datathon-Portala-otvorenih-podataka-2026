"""DCAT-AP catalogue of what the project publishes (PLAN §6 MUST 7): api/v1/dcat.jsonld.

A portal such as data.gov.hr (CKAN with the DCAT extension) or the European Data Portal can
harvest the project's outputs from this one file: each dataset with title, description,
licence, publisher, coverage, themes and its distributions (download URL, format, media type),
and dct:source pointing at the public-sector datasets it is built from (data/reference/skupovi.csv).
Controlled vocabularies are the EU ones that DCAT-AP prescribes (licence, file type, data theme,
country, frequency, language).
"""
SITE = "https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/"
API = SITE + "api/v1/"
REPO = "https://github.com/abi-azan/Datathon-Portala-otvorenih-podataka-2026"
EU = "http://publications.europa.eu/resource/authority/"

CONTEXT = {
    "dcat": "http://www.w3.org/ns/dcat#",
    "dct": "http://purl.org/dc/terms/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "vcard": "http://www.w3.org/2006/vcard/ns#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}
FORMATS = {  # EU file type, IANA media type
    "csv": ("CSV", "text/csv"),
    "json": ("JSON", "application/json"),
}


def _hr(text):
    return {"@value": text, "@language": "hr"}


def _ref(uri):
    return {"@id": uri}


def _dist(path, title, kind="json", download=True):
    """One distribution. A path with a placeholder ({slug}, {id}) is one file per unit or county:
    it is not a URI, so the access URL is the OpenAPI description and the pattern goes in the text."""
    ft, media = FORMATS[kind]
    templated = "{" in path
    ident = API + "dcat.jsonld#" + path.replace("/", "-").replace("{", "").replace("}", "") if templated         else API + path + "#distribucija"
    d = {"@id": ident, "@type": "dcat:Distribution", "dct:title": _hr(title),
         "dcat:accessURL": _ref(API + ("openapi.json" if templated else path)), "dct:format": _ref(EU + "file-type/" + ft),
         "dcat:mediaType": _ref("https://www.iana.org/assignments/media-types/" + media),
         "dct:license": _ref(EU + "licence/CC_BY_4_0")}
    if templated:
        d["dct:description"] = _hr(f"Jedna datoteka po jedinici ili županiji: {API}{path}; putanje i sheme su u openapi.json.")
    elif download:
        d["dcat:downloadURL"] = _ref(API + path)
    return d


# rows of skupovi.csv that are tools rather than data the outputs are derived from
NOT_SOURCES = {"gemma_4", "osm_openfreemap"}


def catalogue(generated, sources, year_from, year_to, exists=lambda path: True):
    """generated: ISO time of the publish run; sources: rows of skupovi.csv that are used;
    exists(path): whether a published file is there (a distribution that was not published is left
    out, and a dataset without distributions too)."""
    publisher = {"@type": "foaf:Agent", "foaf:name": _hr("Tim Fiskalna karta JLS (Datathon Portala otvorenih podataka 2026)"),
                 "foaf:homepage": _ref(REPO)}
    contact = {"@type": "vcard:Kind", "vcard:fn": "Fiskalna karta JLS", "vcard:hasURL": _ref(REPO + "/issues")}
    src = [_ref(r.get("portal_url") or r["url"]) for r in sources if r["kljuc"] not in NOT_SOURCES]
    common = {
        "dct:publisher": publisher, "dcat:contactPoint": contact,
        "dct:license": _ref(EU + "licence/CC_BY_4_0"),
        "dct:language": _ref(EU + "language/HRV"), "dct:spatial": _ref(EU + "country/HRV"),
        "dcat:theme": [_ref(EU + "data-theme/ECON"), _ref(EU + "data-theme/GOVE")],
        "dct:accrualPeriodicity": _ref(EU + "frequency/WEEKLY"),
        "dct:modified": {"@value": generated, "@type": "xsd:dateTime"},
        "dcat:landingPage": _ref(SITE), "dct:source": src,
        "dct:temporal": {"@type": "dct:PeriodOfTime",
                         "dcat:startDate": {"@value": f"{year_from}-01-01", "@type": "xsd:date"},
                         "dcat:endDate": {"@value": f"{year_to}-12-31", "@type": "xsd:date"}},
        "dct:conformsTo": _ref(API + "openapi.json"),
    }
    datasets = [
        ("ocjene", "Ocjena financijske stabilnosti općina, gradova i županija",
         f"Ocjena 1-5 i bodovi 0-100 za svih 576 JLP(R)S po godini {year_from}.-{year_to}., pokazatelji I1-I5, "
         "zastavice, rang u usporednoj skupini i pregled svake jedinice s objašnjenjem.",
         ["financijska stabilnost", "proračun", "općine", "gradovi", "županije", "lokalna samouprava"],
         [_dist("rezultati.csv", "Svi rezultati, jedan red po jedinici i godini", "csv"),
          _dist("jedinice.json", "Indeks jedinica s ocjenama i bodovima po godini"),
          _dist("skupine.json", "Medijani usporednih skupina"),
          _dist("jedinice/{slug}.json", "Pregled jedne jedinice (slug iz jedinice.json)", download=False)]),
        ("sifrarnik", "Šifrarnik JLP(R)S",
         "Veza OIB, RKP, šifre DGU/DZS, naziva, vrste i županije za 576 jedinica lokalne i područne (regionalne) samouprave.",
         ["šifrarnik", "OIB", "RKP", "jedinice lokalne samouprave"],
         [_dist("sifrarnik.csv", "Šifrarnik", "csv")]),
        ("izvor-brojki", "Izvor svake brojke ocjene",
         "Za svaku jedinicu formula pokazatelja I1-I5, pomoćne veličine i ulazni iznosi s radnom knjigom, listom i "
         "retkom u datotekama Ministarstva financija.",
         ["provenijencija", "provjera brojki", "PR-RAS", "Bilanca"],
         [_dist("jedinice/{slug}/izvor.json", "Izvor brojki jedne jedinice", download=False)]),
        ("simulator-spajanja", "Simulator spajanja jedinica",
         "Svaka povezana skupina od 2 do 4 susjedne općine i grada iste županije (13.353 skupine): ocjena spojene "
         "jedinice, potencijal uštede na općoj upravi i promjena fiskalnog izravnanja po zakonskoj formuli. Scenarij.",
         ["spajanje", "teritorijalni ustroj", "fiskalno izravnanje", "simulator"],
         [_dist("simulator/zup-{id}.json", "Skupine jedne županije (dvoznamenkasti zup_id)", download=False)]),
        ("karta-reforme", "Karta reforme",
         "Scenarij spajanja do praga od 2.500, 5.000 i 10.000 stanovnika pohlepnim pravilom unutar županije, s ocjenama, "
         "uštedom i izravnanjem spojenih jedinica. Scenarij, ne prijedlog granica.",
         ["reforma", "spajanje", "teritorijalni ustroj"],
         [_dist(f"reforma/prag-{p}.json", f"Prag {p} stanovnika") for p in (2500, 5000, 10000)]),
        ("metodologija", "Metodologija ocjene",
         "Formule, pragovi, ponderi, pravila, zastavice i AI prompt kako ih kod primjenjuje.",
         ["metodologija"], [_dist("metodologija.json", "Metodologija")]),
    ]
    return {
        "@context": CONTEXT,
        "@id": API + "dcat.jsonld",
        "@type": "dcat:Catalog",
        "dct:title": _hr("Fiskalna karta JLS: otvoreni podaci"),
        "dct:description": _hr("Ocjene financijske stabilnosti, šifrarnik, simulator spajanja i Karta reforme za "
                               "576 jedinica lokalne i područne (regionalne) samouprave u Hrvatskoj, izračunati iz "
                               "otvorenih podataka javnog sektora."),
        "dct:publisher": publisher,
        "dct:license": _ref(EU + "licence/CC_BY_4_0"),
        "dct:language": _ref(EU + "language/HRV"),
        "dct:modified": {"@value": generated, "@type": "xsd:dateTime"},
        "foaf:homepage": _ref(SITE),
        "dcat:dataset": [
            {"@id": API + "dcat.jsonld#" + key, "@type": "dcat:Dataset", "dct:identifier": key,
             "dct:title": _hr(title), "dct:description": _hr(desc), "dcat:keyword": [_hr(k) for k in kw],
             "dcat:distribution": kept, **common}
            for key, title, desc, kw, dists in datasets
            for kept in [[d for d in dists if "dcat:downloadURL" not in d
                          or exists(d["dcat:downloadURL"]["@id"][len(API):])]]
            if kept
        ],
    }
