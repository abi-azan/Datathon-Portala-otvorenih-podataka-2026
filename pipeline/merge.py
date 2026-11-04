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

Savings on general administration (PLAN §4.3, decision 17): only function 01 without
017 and 018, for the last year. The expected cost is the median cost per inhabitant of the
merged unit's peer group times its population. The structural gap (actual minus expected,
never below 0) is the upper bound; the realistic range is 0 to 10 % of the actual cost,
and never more than the gap (research/01 §4.2). Above about 10,000 inhabitants no further
savings are expected (meta-analysis, research/01 §4.1).

Fiscal equalization (PLAN §4 t. 4, decision 17, docs/research/07): the full amount under the
statutory formula for the members and for the merged unit (izravnanje.za_spajanje), with the
capacities and reference values of the MF table. It is shown because the formula reproduces
MF's full amounts for all 576 units. The block is null when the table is not downloaded.

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
             "uprava_pc", "neto_dug_pc", "rang", "n_skupine", "percentil"]


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
            "ref": {k: v["referentna"] for k, v in df.attrs["referentne_mf"].items()}}


class Data:
    """Inputs of the simulator: unit-year rows, the register, peer-group points, neighbours and,
    when available, the members' fiscal equalization inputs (load_equalization)."""

    def __init__(self, reg, wide, res, susjedi, fi=None):
        self.fi = fi
        self.units = {u["oib"]: u for u in reg.to_dict("records")}
        self.oib_of = {u["sifra"]: o for o, u in self.units.items()}
        cols = ["oib", "year"] + [k for k in KEYS if k in wide.columns]
        self.rows = {}
        for r in wide[cols].to_dict("records"):
            self.rows.setdefault(r.pop("oib"), {})[int(r.pop("year"))] = r
        # same medians as the profiles and skupine.json (facts.peer_medians)
        med = facts.peer_medians(res)["uprava_pc"]
        self.uprava_median = {(g, int(y)): v for (g, y), v in med.items() if not _missing(v)}
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


def _num(r, k):
    v = r.get(k)
    return 0.0 if _missing(v) else float(v)


def savings(data, row, skupina, pop, year):
    """Savings block on general administration (01 - 017 - 018) for one year of a merged unit.
    row: the merged unit-year row (sums over the members)."""
    actual = _num(row, "p_01") - _num(row, "p_017") - _num(row, "p_018")
    median = data.uprava_median.get((skupina, year))
    expected = median * pop if median is not None else None
    gap = max(0.0, actual - expected) if expected is not None else None
    realistic = min(SAVINGS_SHARE * max(actual, 0.0), gap) if gap is not None else None
    return {"godina": year, "uprava_zbroj": actual, "medijan_pc": median, "ocekivano": expected,
            "strukturni_jaz": gap, "realno_do": realistic, "iznad_10000": pop > NO_SAVINGS_ABOVE}


# what the simulator file keeps of izravnanje.za_spajanje
FI_KEYS = ["godina", "puni_po_clanici", "puni_clanice", "puni_spojena", "promjena", "promjena_udio",
           "kapacitet_pc", "referentna_pc", "oznake"]


def equalization(data, oibs, vrsta):
    """Full equalization of the members and of the merged unit, or None without the MF table."""
    if not data.fi or not all(o in data.fi["clanice"] for o in oibs):
        return None
    out = izravnanje.za_spajanje([data.fi["clanice"][o] for o in oibs], vrsta == "grad", referentne=data.fi["ref"])
    out["godina"] = data.fi["godina"]
    return {k: out[k] for k in FI_KEYS}


def merge(data, oibs, max_members=MAX_MEMBERS):
    """Profile of the merged unit: type, peer group, population, a result per year and the
    savings block for the last year. max_members=None: no size limit (Karta reforme)."""
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
    return {"clanice": sorted(m["sifra"] for m in members), "vrsta": vrsta, "skupina": skupina,
            "stanovnici": pop, "zup_id": int(members[0]["zup_id"]), "godine": godine,
            "usteda": savings(data, rows[last], skupina, pop, last) if last is not None else None,
            "izravnanje": equalization(data, oibs, vrsta)}


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
                     "izravnanje": result.get("izravnanje")})


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
