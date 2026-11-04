"""Karta reforme (PLAN §5, decision 17): a greedy merger scenario for three population thresholds.

Inside each county, without the counties themselves and without Grad Zagreb, the rule repeats:
take the unit, or the group already merged, with the fewest inhabitants below the threshold and
merge it with its neighbour (unit or group) that has the fewest inhabitants. Ties go to the lowest
DGU code; a group is represented by the lowest code of its members. Neighbours are land borders
and sea links (data.adj from geo/susjedi.json), only inside the county and only eligible units.
It stops when every group is at the threshold or above, or when a group below it has no
neighbour left in the county (then it is skipped and the others go on).

The rule works with inhabitants only. Each final group of 2 or more units is then computed once
with merge.merge(max_members=None): the same sums, methodology and savings block as the merger
simulator. It is a scenario, not a proposal for new borders.

    .venv/Scripts/python -m pipeline.reforma   # rewrite data/build/reforma from a finished build
"""
import json
import sys

import pandas as pd

from . import config, merge

PRAGOVI = (2500, 5000, 10000)
NAPOMENA = ("Scenarij, ne prijedlog granica. Unutar županije najmanja jedinica ispod praga spaja se s "
            "najmanjim susjedom dok sve ne dosegnu prag (pohlepno pravilo); rezultat spojene jedinice "
            "računa se istom funkcijom kao u simulatoru spajanja.")
OWN_COLS = ["oib", "year", "ocjena", "ocjena_rijec", "bodovi", "rang", "n_skupine"]


def _counties(data):
    """{zup_id: {code: set of eligible neighbour codes in the same county}}."""
    by_county = {}
    for o, u in data.units.items():
        if data.eligible(o):
            by_county.setdefault(int(u["zup_id"]), set()).add(u["sifra"])
    out = {}
    for zup, codes in by_county.items():
        nb = {s: {n for n in data.adj.get(s, ()) if n in codes and n != s} for s in codes}
        for s in codes:                                  # symmetric, whatever susjedi.json says
            for n in nb[s]:
                nb[n].add(s)
        out[zup] = nb
    return out


def greedy(data, prag):
    """Groups after the greedy rule: sorted tuples of DGU codes, every eligible unit in exactly
    one group (single units as 1-tuples), sorted by their first code."""
    out = []
    for zup, adj in sorted(_counties(data).items()):
        members = {s: {s} for s in adj}                  # representative (lowest code) -> codes
        pop = {s: int(data.units[data.oib_of[s]]["stanovnici_2021"]) for s in adj}
        nb = {s: set(ns) for s, ns in adj.items()}       # representative -> neighbouring representatives
        while True:
            below = [(pop[g], g) for g in members if pop[g] < prag and nb[g]]
            if not below:
                break
            g = min(below)[1]
            h = min((pop[n], n) for n in nb[g])[1]
            keep, gone = min(g, h), max(g, h)
            members[keep] |= members.pop(gone)
            pop[keep] += pop.pop(gone)
            nb_gone = nb.pop(gone)
            for n in nb_gone - {keep}:
                nb[n].discard(gone)
                nb[n].add(keep)
            nb[keep] = (nb[keep] | nb_gone) - {keep, gone}
        out += [tuple(sorted(m)) for m in members.values()]
    return sorted(out)


def _short(naziv):
    for prefix in ("Grad ", "Općina "):
        if naziv.startswith(prefix):
            return naziv[len(prefix):]
    return naziv


def _own_results(res, year):
    """{oib: row} of the published results for one year (results.parquet)."""
    last = res.loc[res["year"] == year, OWN_COLS]
    return {r["oib"]: r for r in last.to_dict("records")}


def _int(v):
    return None if merge._missing(v) else int(v)


def _float(v):
    return None if merge._missing(v) else float(v)


def reforma(data, prag, res=None):
    """The scenario for one threshold: header plus every unit after the reform (merged groups
    and the units that stay alone). res: results table (results.parquet); read when omitted."""
    if res is None:
        res = pd.read_parquet(config.BUILD / "results.parquet", columns=OWN_COLS)
    year = config.LAST_YEAR
    own = _own_results(res, year)
    jedinice = []
    for g in greedy(data, prag):
        oibs = [data.oib_of[s] for s in g]
        units = [data.units[o] for o in oibs]
        prije = {u["sifra"]: _int(own[o]["ocjena"]) for o, u in zip(oibs, units)}
        if len(g) == 1:
            u, r = units[0], own[oibs[0]]
            jedinice.append({
                "clanice": list(g), "naziv": u["naziv"], "vrsta": u["vrsta"], "zup_id": int(u["zup_id"]),
                "stanovnici": int(u["stanovnici_2021"]), "skupina": u["skupina"], "ocjene_prije": prije,
                "ocjena": _int(r["ocjena"]), "ocjena_rijec": r["ocjena_rijec"], "bodovi": _float(r["bodovi"]),
                "rang": _int(r["rang"]), "n_skupine": _int(r["n_skupine"]), "usteda": None, "izravnanje": None})
            continue
        m = merge.merge(data, oibs, max_members=None)
        last = m["godine"].get(year, {})
        by_size = sorted(units, key=lambda u: (-int(u["stanovnici_2021"]), u["sifra"]))
        jedinice.append({
            "clanice": m["clanice"], "naziv": " + ".join(_short(u["naziv"]) for u in by_size),
            "vrsta": m["vrsta"], "zup_id": m["zup_id"], "stanovnici": m["stanovnici"], "skupina": m["skupina"],
            "ocjene_prije": prije, "ocjena": _int(last.get("ocjena")), "ocjena_rijec": last.get("ocjena_rijec"),
            "bodovi": _float(last.get("bodovi")), "rang": _int(last.get("rang")),
            "n_skupine": _int(last.get("n_skupine")), "usteda": m["usteda"], "izravnanje": m.get("izravnanje")})
    jedinice.sort(key=lambda j: (j["zup_id"], j["clanice"][0]))
    merged = [j for j in jedinice if len(j["clanice"]) > 1]
    blocks = [j["usteda"] for j in merged if j["usteda"]]
    return merge._compact({
        "prag": prag, "godina": year, "napomena": NAPOMENA,
        "n_prije": sum(len(j["clanice"]) for j in jedinice),
        "n_poslije": len(jedinice),
        "stanovnika_u_spojenima": sum(j["stanovnici"] for j in merged),
        "n_spojenih_skupina": len(merged),
        "n_ispod_praga": sum(j["stanovnici"] < prag for j in jedinice),
        "usteda_realno_do_zbroj": sum(b["realno_do"] or 0.0 for b in blocks),
        "strukturni_jaz_zbroj": sum(b["strukturni_jaz"] or 0.0 for b in blocks),
        "izravnanje_promjena_zbroj": sum(j["izravnanje"]["promjena"] for j in merged if j.get("izravnanje")),
        "jedinice": jedinice,
    })


def write_all(data, res, out_dir, pragovi=PRAGOVI):
    """Write prag-<N>.json for every threshold; return {prag: header without jedinice}."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("prag-*.json"):
        old.unlink()
    out = {}
    for prag in pragovi:
        doc = reforma(data, prag, res)
        (out_dir / f"prag-{prag}.json").write_text(
            json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        out[prag] = {k: v for k, v in doc.items() if k != "jedinice"}
    return out


def _hr(x, decimals=0):
    """Croatian number format: 12.345,6."""
    return f"{x:,.{decimals}f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def report(headers):
    for prag, h in headers.items():
        print(f"  prag {_hr(prag)}: {h['n_prije']} -> {h['n_poslije']} jedinica, {h['n_spojenih_skupina']} "
              f"spojenih skupina, {_hr(h['stanovnika_u_spojenima'])} stanovnika u spojenima, ušteda 0 do "
              f"{_hr(h['usteda_realno_do_zbroj'] / 1e6, 1)} mil. € (jaz {_hr(h['strukturni_jaz_zbroj'] / 1e6, 1)} "
              f"mil. €), ispod praga {h['n_ispod_praga']}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    res = pd.read_parquet(config.BUILD / "results.parquet", columns=OWN_COLS)
    out_dir = config.BUILD / "reforma"
    headers = write_all(merge.Data.load(), res, out_dir)
    print(f"Karta reforme -> {out_dir}")
    report(headers)


if __name__ == "__main__":
    main()
