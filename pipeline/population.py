"""Popis 2021 by town and municipality from the DZS INSPIRE WFS (an OGC API, CORS enabled).

Portal entry: "Raspodjela stanovništva prema dobnim skupinama i spolu na razini
gradova/općina iz Popisa stanovništva 2021. INSPIRE" (data.gov.hr). The key is the
5-digit code of the unit.
"""
import json
from collections import defaultdict

import pandas as pd

from . import config, sources


def fetch_population(offline=False):
    path = config.RAW / "dzs" / "popis2021_wfs.json"
    if not (offline and path.exists()):
        path = sources.fetch("dzs_wfs_popis2021", config.WFS_POP, path,
                             meta={"publisher": "Državni zavod za statistiku (servis DGU/NIPP)",
                                   "license": "Otvorena dozvola"})
    feats = json.loads(path.read_text(encoding="utf-8"))["features"]
    data = defaultdict(dict)
    for f in feats:
        for v in f["properties"]["value"]:
            sv = v["StatisticalValue"]
            dims = sv["dimensions"]["Dimensions"]
            code = dims["spatial"]["href"].split("_")[-1].zfill(5)
            th = dims.get("thematic")
            items = th if isinstance(th, list) else ([th] if th else [])
            key = "+".join(sorted(i["ClassificationItem"]["type"]["href"].rsplit("/", 1)[-1] for i in items)) or "ukupno"
            data[code][key] = sv["value"]
    df = pd.DataFrame([{"sifra": c, "stanovnici_2021": d.get("ukupno"), "st_0_14": d.get("0_14"),
                        "st_65_plus": d.get("65+")} for c, d in sorted(data.items())])
    if df.stanovnici_2021.sum() != config.POPULATION_RH_2021:
        raise ValueError(f"WFS population sums to {df.stanovnici_2021.sum()}, expected {config.POPULATION_RH_2021}")
    return df
