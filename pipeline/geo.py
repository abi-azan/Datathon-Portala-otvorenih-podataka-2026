"""Boundaries, neighbours and web geometry for the 556 towns and municipalities.

Source: the DZS INSPIRE WFS layer su-vector:AreaStatisticalUnit (portal entry "Kućanstva -
ukupno na razini gradova/općina iz Popisa stanovništva 2021. INSPIRE"). It is the same OGC
API family as the population layer. The feature id ends with the 5-digit unit code, and
areaValue is the official area in m².

Neighbours are Queen contiguity on the full-resolution polygons: two units are neighbours
when their borders touch, even in a single point. The polygons share exact borders, so no
snapping tolerance is needed (0.5 m and 5 m tolerances give the same pairs).

Five units have no land neighbour, and several islands only touch each other. The merger
simulator and Karta reforme work inside one county, so each county's land components are
joined by sea links: the closest pair of units between two components, shortest first,
until the county is one connected graph (Kruskal over components). These are the bridges
and ferry crossings, e.g. Vir-Privlaka 0.4 km and Mljet-Dubrovnik 5.7 km.

Outputs in data/build/geo/:
  jls.topo.json  layers jls (556 units) and zupanije (21), simplified with mapshaper
  susjedi.json   per unit code: land neighbours with shared border in km, sea links in km
"""
import hashlib
import json
import shutil
import subprocess
from itertools import combinations

import geopandas as gpd
import pandas as pd
import shapely
from libpysal.weights import Queen

from . import config, sources

METRIC_CRS = 3765          # HTRS96/TM, the Croatian projected CRS (metres)
DISTANCE_SIMPLIFY_M = 10   # simplify before measuring sea gaps; km-level answers need no more
SIMPLIFY_WEB = "0.04"      # mapshaper: keep 4% of removable points (written without % for cmd.exe)
MAPSHAPER = "mapshaper@0.6.102"

# The mainland is the land component of Grad Zagreb plus the Dubrovnik exclave south of the
# Neum corridor, which has no land link to the rest of Croatia (Konavle is in it).
MAINLAND_SEEDS = ("01333", "01988")


def fetch_boundaries(offline=False):
    path = config.RAW / "dzs" / "granice_wfs.json"
    if not (offline and path.exists()):
        path = sources.fetch("dzs_wfs_granice", config.WFS_BOUNDARIES, path,
                             meta={"publisher": "Državni zavod za statistiku (servis DGU/NIPP)",
                                   "license": "Otvorena dozvola"})
    return path


def load_boundaries(path):
    """GeoDataFrame sifra, povrsina_km2, geometry (EPSG:4326), one row per unit."""
    g = gpd.read_file(path)
    g["sifra"] = g["id"].str.rsplit("_", n=1).str[-1].str.zfill(5)
    g["povrsina_km2"] = g["areaValue"].map(lambda a: a["value"] / 1e6)
    g = g[["sifra", "povrsina_km2", "geometry"]].sort_values("sifra").reset_index(drop=True)
    if g.sifra.duplicated().any():
        raise ValueError(f"duplicate unit codes in WFS: {g[g.sifra.duplicated()].sifra.tolist()}")
    if not g.is_valid.all():
        g["geometry"] = shapely.make_valid(g.geometry.values)
    return g


def land_neighbours(gm):
    """{sifra: {neighbour: shared border in km}} from Queen contiguity (metric CRS)."""
    w = Queen.from_dataframe(gm, ids=gm.sifra.tolist(), use_index=False, silence_warnings=True)
    geom = dict(zip(gm.sifra, gm.geometry))
    nb = {s: {} for s in gm.sifra}
    for a, ns in w.neighbors.items():
        for b in ns:
            if b in nb[a]:
                continue
            km = round(geom[a].boundary.intersection(geom[b].boundary).length / 1000, 2)
            nb[a][b] = nb[b][a] = km
    return nb


def components(codes, nb):
    """Connected components of the land graph restricted to codes."""
    codes, seen, out = set(codes), set(), []
    for start in sorted(codes):
        if start in seen:
            continue
        comp, stack = set(), [start]
        while stack:
            c = stack.pop()
            if c in comp:
                continue
            comp.add(c)
            stack += [n for n in nb[c] if n in codes and n not in comp]
        seen |= comp
        out.append(comp)
    return out


def sea_links(gm, county_of, nb):
    """[(a, b, km)] joining the land components of each county, shortest gap first."""
    geom = dict(zip(gm.sifra, gm.geometry.simplify(DISTANCE_SIMPLIFY_M)))
    links = []
    for county in sorted(set(county_of.values())):
        codes = [s for s, z in county_of.items() if z == county]
        comps = components(codes, nb)
        if len(comps) < 2:
            continue
        comp_of = {s: i for i, comp in enumerate(comps) for s in comp}
        gaps = sorted((geom[a].distance(geom[b]), a, b) for a, b in combinations(sorted(codes), 2)
                      if comp_of[a] != comp_of[b])
        parent = list(range(len(comps)))

        def root(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for d, a, b in gaps:
            ra, rb = root(comp_of[a]), root(comp_of[b])
            if ra != rb:
                parent[ra] = rb
                links.append((a, b, round(d / 1000, 1)))
    return links


def mainland(nb):
    """Codes reachable over land from the mainland seeds."""
    seen, stack = set(), list(MAINLAND_SEEDS)
    while stack:
        c = stack.pop()
        if c not in seen:
            seen.add(c)
            stack += list(nb[c])
    return seen


def write_topojson(g, units, out):
    """Simplify with mapshaper and write layers jls and zupanije into one TopoJSON.

    Skipped when the boundaries, the unit properties and the mapshaper settings are unchanged
    (stamp file next to the output), so offline builds do not need Node."""
    props = units[["sifra", "naziv", "slug", "oib", "zup_id"]]
    log = json.loads(config.SOURCES_LOG.read_text(encoding="utf-8")) if config.SOURCES_LOG.exists() else {}
    key = hashlib.sha256("|".join([
        log.get("dzs_wfs_granice", {}).get("sha256", ""), MAPSHAPER, SIMPLIFY_WEB,
        props.sort_values("sifra").to_csv(index=False)]).encode()).hexdigest()
    stamp = out.with_suffix(".stamp")
    if out.exists() and stamp.exists() and stamp.read_text() == key:
        print("  TopoJSON: bez promjene")
        return out
    npx = shutil.which("npx")
    if not npx:
        raise RuntimeError("npx (Node.js) is needed for mapshaper")
    full = out.parent / "_jls_full.geojson"
    g[["sifra", "geometry"]].merge(props, on="sifra").to_file(full, driver="GeoJSON")
    cmd = [npx, "-y", MAPSHAPER, "-i", str(full), "name=jls",
           "-simplify", SIMPLIFY_WEB, "keep-shapes", "-clean",
           "-dissolve", "zup_id", "+", "name=zupanije",
           "-o", "format=topojson", "quantization=1e5", "target=*", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    full.unlink(missing_ok=True)
    if r.returncode:
        raise RuntimeError(f"mapshaper failed ({r.returncode}): {r.stderr[-3000:]}")
    topo = json.loads(out.read_text(encoding="utf-8"))
    n = {k: len(v["geometries"]) for k, v in topo["objects"].items()}
    if n.get("jls") != len(g) or n.get("zupanije") != 21:
        raise ValueError(f"unexpected TopoJSON layers: {n}")
    stamp.write_text(key)
    return out


def build_geo(units, offline=False):
    """Compute geometry outputs. Returns one row per JLS: sifra, povrsina_km2, otok,
    n_susjeda, morske_veze, lon, lat."""
    g = load_boundaries(fetch_boundaries(offline))
    jls = units[units.vrsta != "zupanija"]
    missing = set(jls.sifra) ^ set(g.sifra)
    if missing:
        raise ValueError(f"unit codes not matched between WFS and the register: {sorted(missing)}")

    gm = g.to_crs(METRIC_CRS)
    nb = land_neighbours(gm)
    county_of = dict(zip(jls.sifra, jls.zup_id.astype(int)))
    links = sea_links(gm, county_of, nb)
    on_land = mainland(nb)

    sea = {s: {} for s in nb}
    for a, b, km in links:
        sea[a][b] = sea[b][a] = km
    out_dir = config.BUILD / "geo"
    out_dir.mkdir(parents=True, exist_ok=True)
    susjedi = {s: {"kopno": dict(sorted(nb[s].items())), "more": dict(sorted(sea[s].items()))} for s in sorted(nb)}
    (out_dir / "susjedi.json").write_text(json.dumps(susjedi, ensure_ascii=False, indent=0), encoding="utf-8")
    write_topojson(g, units, out_dir / "jls.topo.json")

    pt = gm.geometry.representative_point().to_crs(4326)
    return pd.DataFrame({
        "sifra": g.sifra,
        "povrsina_km2": g.povrsina_km2.round(3),
        "otok": ~g.sifra.isin(on_land),
        "n_susjeda": g.sifra.map(lambda s: len(nb[s])),
        "morske_veze": g.sifra.map(lambda s: len(sea[s])),
        "lon": pt.x.round(5).values,
        "lat": pt.y.round(5).values,
    })
