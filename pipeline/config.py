"""Paths, source URLs and constants shared by the pipeline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"            # downloaded sources (gitignored)
BUILD = ROOT / "data" / "build"        # intermediate tables (gitignored)
REFERENCE = ROOT / "data" / "reference"  # small curated inputs, committed
SOURCES_LOG = RAW / "sources.json"     # provenance of every download

YEARS = list(range(2019, 2026))
LAST_YEAR = YEARS[-1]

MF_BASE = ("https://mfin.gov.hr/UserDocsImages//dokumenti/o-ministarstvu/lokalna-samouprava/"
           "financijski-izvjestaji-jlp-r-s//")
MF_PRRAS_ZIP = MF_BASE + "Lokalci%20FINALI%202019%202024%20EURO.zip"
MF_BILANCA = MF_BASE + "Bilanca_2019_do_2025_R22_EURO.xlsx"

# Fiscal equalization: MF table of shares per unit (capacity, reference value, full amount).
# List of all years: https://mfin.gov.hr/istaknute-teme/lokalna-samouprava/fiskalno-izravnanje/202
MF_FI_YEAR = 2027
MF_FI_XLSX = ("https://mfin.gov.hr/UserDocsImages//dokumenti/o-ministarstvu/lokalna-samouprava//"
              "Tablica%20udjela%20po%20JLP(R)S%20za%20fiskalno%20izravnanje%20u%202027.%20godini.xlsx")

CKAN = "https://data.gov.hr/ckan/api/3/action/"

# DZS INSPIRE WFS, Popis 2021 by town/municipality (pd:StatisticalDistribution)
WFS_POP = ("https://transformiraj.nipp.hr/ows/services/org.14.f834670c-e1ce-4714-ab8d-9d06317a0fb2_wfs"
           "?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=pd:StatisticalDistribution&COUNT=10"
           "&OUTPUTFORMAT=application/geo%2Bjson")

# DZS INSPIRE WFS, Popis 2021 statistical units = town/municipality polygons (su-vector:AreaStatisticalUnit)
WFS_BOUNDARIES = ("https://transformiraj.nipp.hr/ows/services/org.14.b8096c46-3962-421f-baf8-918a45735eed_wfs"
                  "?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=su-vector:AreaStatisticalUnit"
                  "&COUNT=1000&OUTPUTFORMAT=application/geo%2Bjson&SRSNAME=EPSG:4326")

POPULATION_RH_2021 = 3_871_833

# Capital grants and donations inside class 6. They fund projects, not running costs,
# so they are taken out of current revenue (KDZ "laufende Gebarung").
CAPITAL_GRANTS = ["6312", "6322", "6324", "6332", "6342", "6352", "6362", "6382", "6632"]

# PR-RAS / RAS-funkcijski rows used by the methodology
PRRAS_CODES = [
    "6", "61", "611", "613", "63", "633", "638", "6353", "64", "65", "66", "663", "7",
    *CAPITAL_GRANTS,
    "3", "31", "32", "34", "341", "342", "36", "367", "37", "38", "4", "5", "54", "8", "84",
    "01", "017", "018", "02", "03", "04", "05", "06", "07", "08", "09", "10", "R1",
    "Z006", "dio611",
]

# Bilanca: plain account columns, plus the "dio XX" overdue (D) / not yet due (N) splits
BILANCA_CODES = ["11", "23", "24", "25", "26", "9221", "9222"]
BILANCA_SPLITS = ["23", "24", "26"]
