"""Merger simulator (PLAN §4; rules decided 4.11., PLAN §11 decision 16).

merge(data, oibs) returns the profile of 2-4 neighbouring units joined into one:
flows and stocks are summed per year, and the grade, flags and context are computed
again with methodology.evaluate_unit, so the simulator and the map use one methodology.

Rules:
1. Only units of the same county that form one connected group over land borders or
   sea links (pipeline/geo.py). Units across a county border are not offered.
2. No counties and no Grad Zagreb (another level of government; Zagreb is city and county).
3. The merged unit is a city if at least one member is a city. Its peer group follows from
   that type and the summed population (methodology.peer_group), and its rank is taken in
   that group without its own members.
4. Rule 1 (a loan reported as entirely overdue but repaid on schedule) is applied to each
   member before summing. The merged row carries the excluded amount, so a sum cannot
   create or hide overdue debt that no member has (methodology.RULE1_EXCLUDED).

A year is kept only when every member reports it. A value missing for every member stays
missing; otherwise missing counts as 0 (pandas sum with min_count=1).

Savings on general administration (PLAN §4.3; formula decided 4.11., docs/research/08 §7.1):
only function 01 without 017 and 018, for the last year, and only the economy of scale within
the merged unit's type. Each member is valued at the median cost per inhabitant of its own size
class in the merged type (a municipality joining a city is measured against cities of its
size), the merged unit at the median of its own peer group. The difference, never below 0, is
the scale effect; the realistic range is 0 to the smaller of the scale effect and 10 % of the
actual cost (research/01 §4.2). How far members spend above their own peers is shown apart, as
a gap that exists without merging. Above about 10,000 inhabitants no further savings are
expected (meta-analysis, research/01 §4.1).

Incentive for an actual merger (Odluka NN 88/2022, t. IX., in force in 2026; research/08 §3.2):
the largest member is taken to annex the others. An annexed member in development group I-V
brings 2 x its fiscal equalization of the year before, for five years, and up to 995,421 € for
capital projects; its overdue liabilities and loans as at 30.6.2022 are settled. Equalization
paid is estimated as the member's share of all full amounts in the MF table times the last
budget line with an amount (izravnanje.ISPLATA_2026).

Fiscal equalization (PLAN §4 t. 4, decision 17, docs/research/07): the full amount under the
statutory formula for the members and for the merged unit (izravnanje.za_spajanje), with the
capacities and reference values of the MF table. It is shown because the formula reproduces
MF's full amounts for all 576 units. The block is null when the table is not downloaded.

Demographic trend (decision P4, 4.11.; data/build/dzs.parquet from pipeline/pxweb.py): the members'
population estimates are summed per year and the change is taken from the first year to the last
(2021 -> 2024); natural change (live births - deaths) and net migration (in - out) are summed for
the last year. Rates per 1,000 inhabitants use Popis 2021 (the group's stanovnici) as the base; the
pages divide the two published numbers, which keeps the 13,353 precomputed groups small. Shares are
rounded to 3 decimals (0.1 %, the precision shown). Nothing of it enters the score: grades and
per-capita measures keep using Popis 2021. A DZS cell "-" (the phenomenon does not exist) counts
as 0, any other empty cell ("z", hidden) is None and makes the sum None (dzs_value).
The block is None when dzs.parquet has not been built.

precompute() writes every allowed group of 2-4 units, one JSON file per county, for the
static site (decision 4.11.: computed ahead in Python, no TypeScript copy of the method).

    .venv/Scripts/python -m pipeline.merge --precompute   # rewrite data/build/simulator only
"""
import argparse
import inspect
import json
import math
import re
import sys
from types import SimpleNamespace

import pandas as pd

from . import config, facts, izravnanje, methodology

MAX_MEMBERS = 4

SAVINGS_SHARE = 0.10            # realistic upper end: about 10 % of the summed administration cost
NO_SAVINGS_ABOVE = 10_000       # inhabitants; beyond this size no further economies of scale

# NN 88/2022 t. IX.: incentive for an actual merger, only for annexed units in development groups I-V
INCENTIVE_GROUPS = range(1, 6)
INCENTIVE_FACTOR = 2            # x the annexed unit's fiscal equalization, every year
INCENTIVE_YEARS = 5
INCENTIVE_CAPITAL = 995_421.0   # 7.5 mil. kn at 7.53450 kn/€, for capital projects

# Demographic series of dzs.parquet (pipeline/pxweb.py) used for the trend; never for the score.
DZS_PARQUET = config.BUILD / "dzs.parquet"
POPULATION = "stanovnici_procjena"
DEMO_KEYS = (POPULATION, "zivorodeni", "umrli", "doseljeni", "odseljeni")
NO_EVENT = "-"                  # DZS symbol: the phenomenon does not exist
_LOAD = object()                # Data(demo=...) default: read DZS_PARQUET when it exists

# Every p_/b_ value the methodology reads: the literals in methodology.py plus the capital
# grants it builds with f-strings. Summing only these keeps precompute fast.
KEYS = sorted(set(re.findall(r'"([pb]_[A-Za-z0-9_]+)"', inspect.getsource(methodology)))
              | {f"p_{c}" for c in config.CAPITAL_GRANTS})

# What the simulator file keeps for the last year; earlier years keep grade and points only.
LAST_KEYS = ["bodovi", "bodovi_bez_ogranicenja", "ogranicenje_do", "ocjena", "ocjena_rijec",
             "stabilnost", "raspon_ocjena", "zastavice", "oznake", "kvaliteta",
             "I1", "I2", "I3", "I4", "I5", "S1", "S2", "S3", "S4", "S5",
             "PO", "OS", "ND", "SD", "ZO", "DO", "DO_iskazano", "kredit_iskazan_dospio",
             "udio_tekucih_pomoci", "udio_pomoci", "investicijska_stopa", "tekuci_prihodi_pc",
             "uprava_pc", "neto_dug_pc", "z5_manjak_udio", "z5_zadovoljava", "rang", "n_skupine", "percentil"]


def _missing(v):
    return v is None or (isinstance(v, float) and math.isnan(v))


def load_equalization(units_csv=config.BUILD / "units.csv"):
    """{"godina", "ref", "clanice": {oib: member}} from the MF equalization table
    (izravnanje.XLSX), or None when it has not been downloaded."""
    if not izravnanje.XLSX.exists():
        return None
    df = izravnanje.ucitaj(units_csv=units_csv)
    godine = df.attrs["godine"]
    members = {r["oib"]: izravnanje.clanica(r, godine) for r in df.to_dict("records")
               if isinstance(r["oib"], str) and r["vrsta"] in ("opcina", "grad")}
    return {"godina": int(df.attrs["godina"]), "clanice": members,
            "ref": {k: v["referentna"] for k, v in df.attrs["referentne_mf"].items()},
            "puni_ukupno": float(df["P4"].sum())}


def dzs_value(vrijednost, oznaka):
    """One DZS cell as a number: the value; 0 for "-" (the phenomenon does not exist); None for any
    other empty cell ("z" hidden, ".." not available), so that a sum containing it is None as well."""
    if not _missing(vrijednost):
        return float(vrijednost)
    return 0.0 if oznaka == NO_EVENT else None


def load_demography(path=DZS_PARQUET):
    """{"godine", "od", "do", "celije": {(oib, pokazatelj, godina): (number or None, symbol or None)}}
    for DEMO_KEYS, or None when dzs.parquet has not been built (then demography() is None too)."""
    if not path.exists():
        return None
    df = pd.read_parquet(path, columns=["oib", "godina", "pokazatelj", "vrijednost", "oznaka"])
    df = df[df["pokazatelj"].isin(DEMO_KEYS) & df["oib"].notna()]
    years = sorted(int(y) for y in df.loc[df["pokazatelj"] == POPULATION, "godina"].unique())
    if len(years) < 2:
        return None
    cells = {}
    for r in df.to_dict("records"):
        mark = r["oznaka"] if isinstance(r["oznaka"], str) else None
        cells[(r["oib"], r["pokazatelj"], int(r["godina"]))] = (dzs_value(r["vrijednost"], mark), mark)
    return {"godine": years, "od": years[0], "do": years[-1], "celije": cells}


class Data:
    """Inputs of the simulator: unit-year rows, the register, peer-group points, neighbours and,
    when available, the members' fiscal equalization inputs (load_equalization) and the DZS
    demographic series (load_demography; read from the build unless demo is given, None = none)."""

    def __init__(self, reg, wide, res, susjedi, fi=None, demo=_LOAD):
        self.fi = fi
        self.demo = load_demography() if demo is _LOAD else demo
        self.units = {u["oib"]: u for u in reg.to_dict("records")}
        self.oib_of = {u["sifra"]: o for o, u in self.units.items()}
        cols = ["oib", "year"] + [k for k in KEYS if k in wide.columns]
        self.rows = {}
        for r in wide[cols].to_dict("records"):
            self.rows.setdefault(r.pop("oib"), {})[int(r.pop("year"))] = r
        # same medians as the profiles and skupine.json (facts.peer_medians)
        med = facts.peer_medians(res)["uprava_pc"]
        self.uprava_median = {(g, int(y)): v for (g, y), v in med.items() if not _missing(v)}
        # each member's own cost per inhabitant, for the gap that exists without merging
        self.uprava_pc = {(r["oib"], int(r["year"])): r["uprava_pc"]
                          for r in res[["oib", "year", "uprava_pc"]].to_dict("records") if not _missing(r["uprava_pc"])}
        self.points = {}
        for r in res[["skupina", "year", "oib", "bodovi"]].to_dict("records"):
            if not _missing(r["bodovi"]):
                self.points.setdefault((r["skupina"], int(r["year"])), []).append((r["oib"], r["bodovi"]))
        self.adj = {}
        for s, links in susjedi.items():
            if s in self.oib_of:
                self.adj[s] = {n for kind in ("kopno", "more") for n in links.get(kind, {}) if n in self.oib_of}

    @classmethod
    def load(cls):
        """From a finished build (data/build)."""
        reg = pd.read_csv(config.BUILD / "units.csv", dtype={"oib": str, "rkp": str, "sifra": str})
        wide = pd.read_parquet(config.BUILD / "wide.parquet")
        res = pd.read_parquet(config.BUILD / "results.parquet")
        susjedi = json.loads((config.BUILD / "geo" / "susjedi.json").read_text(encoding="utf-8"))
        return cls(reg, wide, res, susjedi, fi=load_equalization())

    def eligible(self, oib):
        u = self.units[oib]
        return u["vrsta"] != "zupanija" and not bool(u["zagreb"])


def check(data, oibs, max_members=MAX_MEMBERS):
    """Raise ValueError when the group breaks a rule; the message is shown to the user.
    max_members=None: no upper limit (Karta reforme); the other rules still hold."""
    if len(set(oibs)) != len(oibs) or len(oibs) < 2 or (max_members is not None and len(oibs) > max_members):
        raise ValueError(f"Spajaju se 2 do {max_members} različite jedinice." if max_members
                         else "Spajaju se barem 2 različite jedinice.")
    for o in oibs:
        if o not in data.units:
            raise ValueError(f"Nepoznata jedinica: {o}")
        if not data.eligible(o):
            raise ValueError(f"{data.units[o]['naziv']}: županije i Grad Zagreb ne spajaju se u simulatoru.")
    if len({data.units[o]["zup_id"] for o in oibs}) > 1:
        raise ValueError("Spajaju se samo jedinice iste županije.")
    codes = {data.units[o]["sifra"] for o in oibs}
    seen, todo = set(), [next(iter(codes))]
    while todo:
        s = todo.pop()
        if s not in seen:
            seen.add(s)
            todo += [n for n in data.adj.get(s, ()) if n in codes]
    if seen != codes:
        raise ValueError("Jedinice moraju činiti jednu cjelinu: svaka graniči s barem jednom drugom "
                         "ili je s njom povezana vezom preko mora.")


def merged_rows(data, oibs):
    """{year: row} of the merged unit, with rule 1 applied per member."""
    series = [data.rows.get(o, {}) for o in oibs]
    years = set.intersection(*(set(s) for s in series)) if series else set()
    out = {}
    for y in sorted(years):
        row = {}
        for k in KEYS:
            vals = [s[y].get(k) for s in series]
            vals = [v for v in vals if not _missing(v)]
            row[k] = sum(vals) if vals else float("nan")
        row[methodology.RULE1_EXCLUDED] = sum(methodology.rule1_excluded(s[y], s.get(y - 1)) for s in series)
        out[y] = row
    return out


def _rank(data, skupina, year, points, members):
    """Rank, group size and percentile of the merged unit among the group without its members
    (same definitions as build.py: rank method 'min', percentile as pandas rank(pct=True))."""
    others = [b for o, b in data.points.get((skupina, year), []) if o not in members]
    n = len(others) + 1
    if _missing(points):
        return None, n, None
    better = sum(b > points for b in others)
    below = sum(b < points for b in others)
    ties = sum(b == points for b in others) + 1
    return better + 1, n, (below + (ties + 1) / 2) / n * 100


def savings(data, oibs, uprava_pc, vrsta, skupina, pop, year):
    """Savings block on general administration (01 - 017 - 018) for one year of a merged unit
    (module docstring). uprava_pc: the merged unit's cost per inhabitant as
    methodology.evaluate_unit computes it (one definition for the profile, the context and the savings)."""
    actual = None if _missing(uprava_pc) else uprava_pc * pop
    median = data.uprava_median.get((skupina, year))
    expected = median * pop if median is not None else None
    members_expected, gap_alone = 0.0, 0.0
    for o in oibs:
        u, n = data.units[o], int(data.units[o]["stanovnici_2021"])
        same_type = methodology.peer_group(SimpleNamespace(vrsta=vrsta, zagreb=False, stanovnici_2021=n))
        m_type = data.uprava_median.get((same_type, year))
        members_expected = None if None in (members_expected, m_type) else members_expected + m_type * n
        m_own, own_pc = data.uprava_median.get((u["skupina"], year)), data.uprava_pc.get((o, year))
        gap_alone = None if None in (gap_alone, m_own, own_pc) else gap_alone + max(0.0, (own_pc - m_own) * n)
    scale = max(0.0, members_expected - expected) if None not in (members_expected, expected) else None
    realistic = min(SAVINGS_SHARE * max(actual, 0.0), scale) if None not in (actual, scale) else None
    return {"godina": year, "uprava_zbroj": actual, "medijan_pc": median, "ocekivano": expected,
            "ocekivano_clanice": members_expected, "razmjer": scale, "realno_do": realistic,
            "jaz_bez_spajanja": gap_alone, "iznad_10000": pop > NO_SAVINGS_ABOVE}


def incentive(data, oibs, fi):
    """Incentive for an actual merger under NN 88/2022 t. IX. (module docstring). oibs in the
    order of the equalization block fi (sorted by code); fi is None without the MF table."""
    units = [data.units[o] for o in oibs]
    annexing = min(units, key=lambda u: (-int(u["stanovnici_2021"]), u["sifra"]))
    eligible = [i for i, u in enumerate(units)
                if u is not annexing and not _missing(u["razvojna_skupina"])
                and int(u["razvojna_skupina"]) in INCENTIVE_GROUPS]
    # the annexed member's equalization of the year before the merger: its payout (payout())
    ratio = fi["omjer_prije"] if fi else None
    paid = sum(fi["isplata_po_clanici"][i] for i in eligible) if fi else None
    yearly = None if paid is None else INCENTIVE_FACTOR * paid
    return {"pripaja": annexing["sifra"], "s_pravom": [units[i]["sifra"] for i in eligible],
            "izravnanje_isplata": paid, "godisnje": yearly,
            "ukupno": None if yearly is None else yearly * INCENTIVE_YEARS,
            "kapitalni_do": INCENTIVE_CAPITAL if eligible else 0.0, "omjer_isplate": ratio}


# what the simulator file keeps of izravnanje.za_spajanje, plus the payout estimate (payout())
FI_KEYS = ["godina", "puni_po_clanici", "puni_clanice", "puni_spojena", "promjena", "promjena_udio",
           "kapacitet_pc", "referentna_pc", "oznake",
           "iznos_proracuna", "omjer_prije", "omjer_poslije", "isplata_po_clanici", "isplata_clanice",
           "isplata_spojena", "isplata_promjena"]


def payout(full_members, full_merged, total, budget=izravnanje.ISPLATA_2026):
    """What is actually paid (čl. 9. st. 7.): share of the sum of all full amounts x the budget line.
    The line is fixed, so a merger that lowers the full amount raises everyone else's share: the
    merged unit's loss goes to the other units and the state budget does not change.
    full_members: the members' full amounts; total: the sum over all units before the merger.
    The line for the table's year is not set yet, so the last one with an amount (2026) is used."""
    before = budget / total
    after_total = total - sum(full_members) + full_merged
    after = budget / after_total if after_total > 0 else None
    paid_members = [p * before for p in full_members]
    paid_merged = full_merged * after if after is not None else 0.0
    return {"iznos_proracuna": budget, "omjer_prije": before, "omjer_poslije": after,
            "isplata_po_clanici": paid_members, "isplata_clanice": sum(paid_members),
            "isplata_spojena": paid_merged, "isplata_promjena": paid_merged - sum(paid_members)}


def equalization(data, oibs, vrsta):
    """Fiscal equalization of the members and of the merged unit, full amount and payout,
    or None without the MF table."""
    if not data.fi or not all(o in data.fi["clanice"] for o in oibs):
        return None
    out = izravnanje.za_spajanje([data.fi["clanice"][o] for o in oibs], vrsta == "grad", referentne=data.fi["ref"])
    out["godina"] = data.fi["godina"]
    out.update(payout(out["puni_po_clanici"], out["puni_spojena"], data.fi["puni_ukupno"]))
    return {k: out[k] for k in FI_KEYS}


def demography(data, oibs):
    """Demographic trend of a group of units (module docstring), or None without dzs.parquet.
    oibs in the order of clanice. The population series is kept for the group only; each member
    keeps just its change. oznake ("sifra:pokazatelj:godina:symbol") lists the DZS symbols of the
    cells used and is left out when there are none."""
    d = data.demo
    if not d:
        return None
    first, last = d["od"], d["do"]

    def cell(o, key, year):                          # (number or None, symbol or None)
        return d["celije"].get((o, key, year), (None, None))

    def total(key, year):
        vals = [cell(o, key, year)[0] for o in oibs]
        return None if any(v is None for v in vals) else sum(vals)

    def change(a, b):
        return None if a is None or b is None or a <= 0 else round(b / a - 1, 3)

    def diff(a, b):
        return None if a is None or b is None else int(round(a - b))

    series = [total(POPULATION, y) for y in d["godine"]]
    used = [(POPULATION, y) for y in d["godine"]] + [(k, last) for k in DEMO_KEYS[1:]]
    marks = sorted(f"{data.units[o]['sifra']}:{k}:{y}:{m}" for o in oibs for k, y in used if (m := cell(o, k, y)[1]))
    return {"od": first, "do": last,
            "stanovnici": [None if v is None else int(round(v)) for v in series],
            "promjena": change(series[0], series[-1]),
            "prirodna": diff(total("zivorodeni", last), total("umrli", last)),
            "migracije": diff(total("doseljeni", last), total("odseljeni", last)),
            "clanice": [change(cell(o, POPULATION, first)[0], cell(o, POPULATION, last)[0]) for o in oibs],
            **({"oznake": marks} if marks else {})}


def merge(data, oibs, max_members=MAX_MEMBERS):
    """Profile of the merged unit: type, peer group, population, a result per year and the
    savings, equalization, incentive and demography blocks. max_members=None: no size limit (Karta reforme)."""
    check(data, oibs, max_members)
    oibs = sorted(oibs, key=lambda o: data.units[o]["sifra"])   # same sums whatever the click order
    members = [data.units[o] for o in oibs]
    vrsta = "grad" if any(m["vrsta"] == "grad" for m in members) else "opcina"
    pop = int(sum(m["stanovnici_2021"] for m in members))
    skupina = methodology.peer_group(SimpleNamespace(vrsta=vrsta, zagreb=False, stanovnici_2021=pop))
    rows = merged_rows(data, oibs)
    godine = methodology.evaluate_unit(rows, pop)
    for y, r in godine.items():
        r["rang"], r["n_skupine"], r["percentil"] = _rank(data, skupina, y, r["bodovi"], set(oibs))
    last = max(godine) if godine else None
    fi = equalization(data, oibs, vrsta)
    return {"clanice": sorted(m["sifra"] for m in members), "vrsta": vrsta, "skupina": skupina,
            "stanovnici": pop, "zup_id": int(members[0]["zup_id"]), "godine": godine,
            "usteda": savings(data, oibs, godine[last]["uprava_pc"], vrsta, skupina, pop, last)
                      if last is not None else None,
            "izravnanje": fi, "poticaj": incentive(data, oibs, fi),
            "demografija": demography(data, oibs)}


def groups(data, max_members=MAX_MEMBERS):
    """Every connected group of 2..max_members eligible units inside one county, each once
    (sorted tuples of DGU codes). Enumerated by extending a group with neighbours that have a
    larger code than its first unit, so no group is produced twice."""
    adj = {s: {n for n in ns if data.eligible(data.oib_of[n])
               and data.units[data.oib_of[n]]["zup_id"] == data.units[data.oib_of[s]]["zup_id"]}
           for s, ns in data.adj.items() if data.eligible(data.oib_of[s])}
    out = []

    def extend(group, frontier, root):
        if len(group) >= 2:
            out.append(tuple(sorted(group)))
        if len(group) == max_members:
            return
        frontier = set(frontier)
        while frontier:
            w = frontier.pop()
            new = {x for x in adj[w] if x > root and x not in group and all(x not in adj[g] for g in group)}
            extend(group | {w}, frontier | new, root)

    for s in sorted(adj):
        extend({s}, {x for x in adj[s] if x > s}, s)
    return out


def _compact(v):
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        return round(v, 1) if abs(v) >= 100 else round(v, 4)
    if isinstance(v, (list, tuple)):
        return [_compact(x) for x in v]
    if isinstance(v, dict):
        return {k: _compact(x) for k, x in v.items()}
    return v


def summary(result):
    """What the static simulator file keeps for one group."""
    years = sorted(result["godine"])
    last = result["godine"][years[-1]] if years else {}
    return _compact({**{k: result[k] for k in ("clanice", "vrsta", "skupina", "stanovnici")},
                     "godina": years[-1] if years else None,
                     "ocjene": {str(y): result["godine"][y]["ocjena"] for y in years},
                     "bodovi": {str(y): result["godine"][y]["bodovi"] for y in years},
                     "zadnja": {k: last.get(k) for k in LAST_KEYS},
                     "usteda": result.get("usteda"),
                     "izravnanje": result.get("izravnanje"),
                     "poticaj": result.get("poticaj"),
                     "demografija": result.get("demografija")})


def precompute(data, out_dir):
    """Write simulator/zup-<id>.json for every county; return the number of groups."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("zup-*.json"):
        old.unlink()
    by_county = {}
    for g in groups(data):
        oibs = [data.oib_of[s] for s in g]
        res = merge(data, oibs)
        if res["godine"]:
            by_county.setdefault(res["zup_id"], {})["-".join(g)] = summary(res)
    names = {u["zup_id"]: u["zupanija"] for u in data.units.values()}
    for zup, skupine in by_county.items():
        doc = {"zup_id": int(zup), "zupanija": names[zup], "skupine": skupine}
        (out_dir / f"zup-{int(zup):02d}.json").write_text(
            json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return sum(len(s) for s in by_county.values())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--precompute", action="store_true",
                    help="rewrite data/build/simulator/ from a finished build, without running the build")
    if ap.parse_args().precompute:
        n = precompute(Data.load(), config.BUILD / "simulator")
        print(f"Simulator: {n} skupina -> {config.BUILD / 'simulator'}")


if __name__ == "__main__":
    main()
