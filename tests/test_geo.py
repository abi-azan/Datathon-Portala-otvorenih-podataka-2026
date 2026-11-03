import geopandas as gpd
from shapely.geometry import box

from pipeline import geo


def squares():
    # metres in EPSG:3765; A-B share a side, B-D touch in one corner, C is 1.5 km east of D,
    # E lies in another county right next to C
    rows = [("A", box(0, 0, 1000, 1000)), ("B", box(1000, 0, 2000, 1000)),
            ("D", box(2000, 1000, 3000, 2000)), ("C", box(4500, 1000, 5500, 2000)),
            ("E", box(5600, 1000, 6600, 2000))]
    return gpd.GeoDataFrame({"sifra": [r[0] for r in rows]}, geometry=[r[1] for r in rows], crs=3765)


def test_queen_counts_corner_contact_with_zero_border():
    nb = geo.land_neighbours(squares())
    assert nb["A"] == {"B": 1.0}
    assert nb["B"] == {"A": 1.0, "D": 0.0}
    assert nb["C"] == {} and nb["E"] == {}


def test_sea_links_join_components_inside_a_county_only():
    g = squares()
    nb = geo.land_neighbours(g)
    county = {"A": 1, "B": 1, "D": 1, "C": 1, "E": 2}
    assert geo.sea_links(g, county, nb) == [("C", "D", 1.5)]


def test_sea_links_take_the_shortest_gap_first():
    g = squares()
    nb = geo.land_neighbours(g)
    county = {"A": 1, "B": 1, "D": 1, "C": 1, "E": 1}
    links = geo.sea_links(g, county, nb)
    assert links == [("C", "E", 0.1), ("C", "D", 1.5)]      # E joins C first, then C's group joins D


def test_components():
    nb = {"A": {"B": 1}, "B": {"A": 1}, "C": {}}
    assert sorted(map(sorted, geo.components(["A", "B", "C"], nb))) == [["A", "B"], ["C"]]
