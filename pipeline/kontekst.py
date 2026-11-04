"""Context blocks of the unit profile: population and economy, fiscal equalization, local tax rates.

publish.py adds three keys to every jedinice/<slug>.json. Nothing here enters the score, the
fact packs (facts.py) or the AI texts. Methodology texts: metodologija.py
("stanovnistvo_gospodarstvo", "izravnanje_jedinice").

stanovnistvo_gospodarstvo (DZS PxWeb, pipeline/pxweb.py; Porezna uprava, pipeline/porezna.py)
  - promjena_stanovnistva: population estimate (SP31_2, 31.12.) last year / first year - 1.
    The estimates are used only for this trend; every per-capita figure, here and in the
    score, stays on Popis 2021 (stanovnici_2021).
  - prirodni_prirast, neto_migracija: (živorođeni - umrli), (doseljeni - odseljeni) per 1,000
    inhabitants of Popis 2021, in the last year all four tables have.
  - nocenja_po_stanovniku: tourist nights in commercial accommodation (BS_TU19) / Popis 2021.
  - dozvole_na_1000: buildings with a building permit issued (PX14) per 1,000 inhabitants.
  - neto_dohodak_pc: residents' net income (vrsta_dohotka "ukupno") / Popis 2021, and
    udio_mirovina: the pensioners' share of it.
  DZS status symbols follow pxweb.value(): "-" counts as 0, "z" stays empty and is never 0.
  Each value comes with the median of its peer group (methodology.peer_group, the same groups
  as the score). Grad Zagreb has no peer group, so no median; counties are compared with counties.
  The block also carries the population series and the exact PxWeb query the browser sends to
  ask DZS for it live (CORS: *), with the unit's code from dzs_kodovi.json.

izravnanje (MF equalization table, pipeline/izravnanje.py)
  Capacity per inhabitant against the reference value of the unit's type, and the estimated
  yearly payout: the unit's share of all full amounts (izravnanje.udjeli, čl. 9. st. 4.-5.)
  x the budget line (izravnanje.isplata, čl. 9. st. 7.), as merge.payout does for the
  simulator. The table is for 2027 and its budget line is not set yet, so the 2026 one is used.

  For a unit whose lower rate is below the maximum, uz_najvise_stope estimates what its own budget
  would collect more a year at the highest rates (decision S1, docs/research/11 §2.5; highest_rates).

porezne_stope (Porezna uprava): the unit's local tax rates per year, as published.
"""
import json

import pandas as pd

from . import config, izravnanje, porezna, pxweb

PRORACUN_GODINA = 2026          # the year of izravnanje.ISPLATA_2026, the last budget line with an amount
PER_1000 = 1000.0
DEMOGRAFIJA = ["zivorodeni", "umrli", "doseljeni", "odseljeni"]
KLJUCEVI = ["promjena_stanovnistva", "prirodni_prirast", "neto_migracija", "nocenja_po_stanovniku",
            "dozvole_na_1000", "neto_dohodak_pc", "udio_mirovina"]


def _latest(dzs, pokazatelj):
    return int(dzs.loc[dzs.pokazatelj == pokazatelj, "godina"].max())


def _cells(dzs, pokazatelj, godina):
    """(value under the symbol rule, symbol) per OIB for one indicator and year."""
    x = dzs[(dzs.pokazatelj == pokazatelj) & (dzs.godina == godina)].set_index("oib")
    return x.vrijednost, x.oznaka


def _symbol(*symbols):
    """Symbol of a value computed from several cells: "z" when any input is hidden, "-" when
    every input is "-", else none."""
    s = [x if isinstance(x, str) else None for x in symbols]
    if pxweb.TAJNO in s:
        return pxweb.TAJNO
    if s and all(x == pxweb.NEMA for x in s):
        return pxweb.NEMA
    return None


def indicators(units, dzs, doh):
    """One row per unit (index oib) with value, year, symbol and count of every indicator.
    Columns <key>, <key>_godina, <key>_oznaka, <key>_broj, plus promjena_od (first year)."""
    d = pxweb.with_symbols(dzs)
    oib = units.oib.tolist()
    pop = units.set_index("oib").stanovnici_2021.astype(float)
    out = pd.DataFrame(index=pd.Index(oib, name="oib"))

    # population change from the estimates (only the trend)
    est = d[d.pokazatelj == "stanovnici_procjena"]
    y0, y1 = int(est.godina.min()), int(est.godina.max())
    a, a_s = _cells(d, "stanovnici_procjena", y0)
    b, b_s = _cells(d, "stanovnici_procjena", y1)
    out["promjena_stanovnistva"] = b.reindex(oib) / a.reindex(oib) - 1
    out["promjena_stanovnistva_broj"] = b.reindex(oib) - a.reindex(oib)
    out["promjena_stanovnistva_godina"], out["promjena_od"] = y1, y0
    out["promjena_stanovnistva_oznaka"] = [_symbol(x, y) for x, y in zip(a_s.reindex(oib), b_s.reindex(oib))]

    # natural change and net migration per 1,000 (Popis 2021), last year with all four tables
    yd = min(_latest(d, p) for p in DEMOGRAFIJA)
    c = {p: _cells(d, p, yd) for p in DEMOGRAFIJA}
    for key, plus, minus in (("prirodni_prirast", "zivorodeni", "umrli"), ("neto_migracija", "doseljeni", "odseljeni")):
        n = c[plus][0].reindex(oib) - c[minus][0].reindex(oib)
        out[key + "_broj"] = n
        out[key] = n / pop.reindex(oib) * PER_1000
        out[key + "_godina"] = yd
        out[key + "_oznaka"] = [_symbol(x, y) for x, y in zip(c[plus][1].reindex(oib), c[minus][1].reindex(oib))]

    for key, pok, scale in (("nocenja_po_stanovniku", "nocenja", 1.0), ("dozvole_na_1000", "dozvole_zgrade", PER_1000)):
        y = _latest(d, pok)
        v, s = _cells(d, pok, y)
        out[key + "_broj"] = v.reindex(oib)
        out[key] = v.reindex(oib) / pop.reindex(oib) * scale
        out[key + "_godina"] = y
        out[key + "_oznaka"] = [x if isinstance(x, str) and x in (pxweb.NEMA, pxweb.TAJNO) else None
                                for x in s.reindex(oib)]

    # residents' net income (Porezna uprava), Popis 2021 as the base
    yi = int(doh.godina.max())
    di = doh[doh.godina == yi]
    total = di[di.vrsta_dohotka == porezna.UKUPNO].set_index("oib").neto.reindex(oib)
    pens = di[di.vrsta_dohotka == "umirovljenici"].set_index("oib").neto.reindex(oib)
    out["neto_dohodak_pc"] = total / pop.reindex(oib)
    out["neto_dohodak_pc_broj"] = total
    out["udio_mirovina"] = pens / total
    out["udio_mirovina_broj"] = pens
    out["neto_dohodak_pc_godina"] = out["udio_mirovina_godina"] = yi
    out["neto_dohodak_pc_oznaka"] = out["udio_mirovina_oznaka"] = None
    return out


def medians(units, ind):
    """Peer-group median and count of every indicator; Grad Zagreb's own group gets none.
    "-" cells are already 0 (pxweb.with_symbols); empty and "z" cells are left out."""
    g = units.set_index("oib").skupina.reindex(ind.index)
    zg = units.set_index("oib").zagreb.reindex(ind.index).astype(bool)
    rows = ind[~zg.to_numpy()].groupby(g[~zg.to_numpy()])
    return rows[KLJUCEVI].median(), rows[KLJUCEVI].count()


def live_query(kodovi, oib, table="SP31_2"):
    """The POST the browser sends to DZS for the unit's population series: the query template of
    dzs_kodovi.json with the unit's code and every year (so a new year shows up live). None when
    the unit has no code in the table."""
    meta = kodovi["meta"]["tablice"].get(table)
    code = kodovi["jedinice"].get(oib, {}).get(table)
    if not meta or code is None:
        return None
    body = json.loads(json.dumps(meta["upit"]))
    for q in body["query"]:
        if q["selection"].get("values") == ["{kod}"]:
            q["selection"] = {"filter": "item", "values": [code]}
        elif q["code"] == pxweb.YEAR_VAR:
            q["selection"] = {"filter": "all", "values": ["*"]}
    return {"tablica": table, "kod": code, "url": meta["url"], "upit": body}


def sources(kodovi, log):
    """The sources of the block, for the card's footnote: DZS tables with their PxWeb update
    date, and the Porezna uprava workbook with its Last-Modified date."""
    out = []
    for table, m in kodovi["meta"]["tablice"].items():
        out.append({"izdavatelj": pxweb.PUBLISHER, "naziv": m.get("naslov"), "tablica": table, "url": m["url"],
                    "azurirano": (m.get("dzs_azurirano") or "")[:10] or None, "preuzeto": m.get("preuzeto")})
    e = log.get("porezna_neto_dohodak")
    if e:
        from email.utils import parsedate_to_datetime
        out.append({"izdavatelj": "Porezna uprava", "naziv": "Neto dohodak stanovništva po općinama/gradovima prebivališta",
                    "tablica": None, "url": e["url"],
                    "azurirano": parsedate_to_datetime(e["last_modified"]).date().isoformat() if e.get("last_modified") else None,
                    "preuzeto": e.get("retrieved")})
    return out


def _num(x):
    return None if x is None or pd.isna(x) else float(x)


def population_economy(units, dzs, doh, kodovi, log):
    """{oib: stanovnistvo_gospodarstvo block} for all 576 units."""
    ind = indicators(units, dzs, doh)
    med, cnt = medians(units, ind)
    est = dzs[dzs.pokazatelj == "stanovnici_procjena"]
    series = {o: {str(int(y)): _num(v) for y, v in zip(g.godina, g.vrijednost)} for o, g in est.groupby("oib")}
    src = sources(kodovi, log)
    out = {}
    for u in units.itertuples():
        r = ind.loc[u.oib]
        peers = None if bool(u.zagreb) else u.skupina
        block = {}
        for k in KLJUCEVI:
            has_med = peers is not None and peers in med.index
            sym = r[k + "_oznaka"]
            block[k] = {"godina": int(r[k + "_godina"]), "vrijednost": _num(r[k]),
                        "oznaka": sym if isinstance(sym, str) else None,
                        "broj": _num(r[k + "_broj"]),
                        "medijan": _num(med.loc[peers, k]) if has_med else None,
                        "n_medijan": int(cnt.loc[peers, k]) if has_med else 0}
        block["promjena_stanovnistva"]["od_godine"] = int(r["promjena_od"])
        out[u.oib] = {"skupina": peers, "pokazatelji": block, "procjene": series.get(u.oib, {}),
                      "uzivo": live_query(kodovi, u.oib), "izvori": src}
    return out


# ---------------------------------------------------------------- tax at the highest rates (decision S1)
# docs/research/11 §2.2-2.6. What the unit's own budget would collect more in a year if its income tax
# rates were the highest the law allows. Only for units below the maximum; never in the score, on the
# map or against a peer median.
LOKALNE_VRSTE = ["zaposlenici", "umirovljenici", "obrt", "drugi_dohodak"]   # pay the unit's rates (§2.2);
#   kapital, imovina, povremeni_rad_imovina (renting and selling property) and paušalisti pay a fixed 12 %
VISA_IZNAD_NIZE = 0.10      # čl. 19.a st. 2. Zakona o porezu na dohodak: highest higher rate = highest lower + 10 pp
SREDNJA_OSNOVICA = 14_000.0  # mean taxable base per taxpayer in these units, € (2024; §2.3)
PARETO_ALFA = 2.0            # tail of the income distribution for the point estimate (§2.3)
PARETO_RASPON = (3.0, 2.0, 1.6)
UDIO_VISI_MAX = 0.4          # cap on the base share above the threshold
PONASANJE = 0.85             # low end: the smallest estimate less 15 % for behaviour (§2.5)


def _higher_share(p_above, granica, alfa):
    """Share of the taxable base above the bracket threshold: a Pareto tail with index alfa above it,
    p_above taxpayers past it (E[y − c | y > c] = c / (alfa − 1)), over the mean base."""
    if alfa is None:
        return 0.0
    return min(UDIO_VISI_MAX, p_above * granica / (alfa - 1) / SREDNJA_OSNOVICA)


def _at_highest(t_lok, t_drugi, niza, visa, niza_max, h):
    """Extra tax (all levels) at the highest rates: the higher bracket's part of the tax on wages,
    pensions and crafts is v·h / (n·(1 − h) + v·h); drugi dohodak is all in the lower bracket."""
    visa_max = niza_max + VISA_IZNAD_NIZE
    sal = t_lok - t_drugi
    sh = visa * h / (niza * (1 - h) + visa * h)
    t_low, t_high = sal * (1 - sh) + t_drugi, sal * sh
    return t_low * (niza_max / niza - 1) + t_high * (visa_max / visa - 1)


def highest_rates(doh, stope, razredi, p611):
    """{oib: estimate} for units whose lower rate is below the maximum in the last rate year.
    Rates of that year (2026), residents' tax of the last income year (2025, Porezna uprava) and the
    unit's own share of it, p_611 / tax of residents (PR-RAS of the same year). The point estimate uses
    PARETO_ALFA; the range is the smallest estimate over no higher bracket and PARETO_RASPON less 15 %,
    to the largest."""
    yr, yi = int(stope.godina.max()), int(doh.godina.max())
    rates = stope[(stope.godina == yr) & stope.ispod_maksimuma.fillna(False).astype(bool)].set_index("oib")
    tax = doh[doh.godina == yi].pivot_table(index="oib", columns="vrsta_dohotka", values="porez", aggfunc="sum")
    last = int(razredi.godina.max())
    rz = razredi[razredi.godina == last].set_index("oib")
    out = {}
    for o, r in rates.iterrows():
        if o not in tax.index or pd.isna(r.niza) or pd.isna(r.visa) or pd.isna(r.niza_max):
            continue
        t = tax.loc[o]
        t_lok = t.reindex(LOKALNE_VRSTE).sum(min_count=1)
        total, own = t.get(porezna.UKUPNO), p611.get(o)
        if pd.isna(t_lok) or not total or own is None or pd.isna(own):
            continue
        t_drugi = 0.0 if pd.isna(t.get("drugi_dohodak")) else float(t["drugi_dohodak"])
        b = rz.loc[o] if o in rz.index else None
        n_all = None if b is None else (b.ispod or 0) + (0 if pd.isna(b.iznad) else b.iznad)
        p_above = 0.0 if b is None or not n_all or pd.isna(b.iznad) else float(b.iznad) / n_all
        granica = float(b.granica) if b is not None else 0.0
        share = float(own) / float(total)
        est = {a: _at_highest(float(t_lok), t_drugi, r.niza, r.visa, r.niza_max, _higher_share(p_above, granica, a)) * share
               for a in (None, *PARETO_RASPON)}
        point = _at_highest(float(t_lok), t_drugi, r.niza, r.visa, r.niza_max,
                            _higher_share(p_above, granica, PARETO_ALFA)) * share
        out[o] = {"godina_stopa": yr, "godina_poreza": yi, "procjena": point,
                  "od": min(est.values()) * PONASANJE, "do": max(est.values()),
                  "niza": float(r.niza), "visa": float(r.visa), "niza_max": float(r.niza_max),
                  "visa_max": round(float(r.niza_max) + VISA_IZNAD_NIZE, 4),
                  "porez_lokalne_vrste": float(t_lok), "udio_u_proracunu": share, "udio_visi_razred": p_above}
    return out


def equalization(fi, stope, budget=izravnanje.ISPLATA_2026, higher=None):
    """{oib: izravnanje block} from the MF table (izravnanje.ucitaj): capacity, reference value,
    full amount and the payout share x budget line, plus the unit's income tax rate."""
    share = izravnanje.udjeli(fi["P4"].to_numpy())
    paid = izravnanje.isplata(share, budget)
    ref_grad = fi.attrs["referentne_mf"]["grad"]["referentna"]
    last = int(stope.godina.max())
    rates = stope[stope.godina == last].set_index("oib")
    out = {}
    for i, r in enumerate(fi.itertuples()):
        if not isinstance(r.oib, str):
            continue
        zagreb = r.vrsta == "zagreb"
        rate = None
        if r.oib in rates.index:
            s = rates.loc[r.oib]
            rate = {"godina": last, "niza": _num(s.niza), "visa": _num(s.visa), "niza_max": _num(s.niza_max),
                    "visa_max": None if pd.isna(s.niza_max) else round(float(s.niza_max) + VISA_IZNAD_NIZE, 4),
                    "ispod_maksimuma": None if pd.isna(s.ispod_maksimuma) else bool(s.ispod_maksimuma)}
        out[r.oib] = {
            "godina": int(fi.attrs["godina"]),
            "proracun_godina": PRORACUN_GODINA,
            "iznos_proracuna": budget,
            # čl. 8. st. 8.: Grad Zagreb is left out of the reference values and compared with towns
            "vrsta_reference": "grad" if zagreb else r.vrsta,
            "kapacitet_pc": float(r.P2),
            "referentna_pc": float(ref_grad if zagreb else r.P3),
            "puni_iznos": float(r.P4),
            "udio": float(share[i]),
            "isplata": float(paid[i]),
            "stopa": rate,
            "uz_najvise_stope": (higher or {}).get(r.oib),
        }
    return out


def tax_rates(stope):
    """{oib: {year: rates}}: lower and higher income tax rate, the highest lower rate allowed,
    consumption tax and property tax per m² (range when the decision gives one), who collects it."""
    cols = ["niza", "visa", "niza_max", "ispod_maksimuma", "potrosnja_min", "potrosnja_max",
            "nekretnine_min", "nekretnine_max", "nekretnine_naplata"]
    out = {}
    for r in stope.to_dict("records"):
        out.setdefault(r["oib"], {})[str(int(r["godina"]))] = {
            c: (None if r[c] is None or (not isinstance(r[c], str) and pd.isna(r[c])) else
                bool(r[c]) if c == "ispod_maksimuma" else r[c]) for c in cols}
    return out


def load(units):
    """Everything publish.py needs, from data/build and the MF table. Fails when a layer is missing:
    the profile must not be published without it."""
    dzs = pd.read_parquet(pxweb.OUT)
    doh = pd.read_parquet(porezna.OUT_DOHODAK)
    stope = pd.read_parquet(porezna.OUT_STOPE)
    kodovi = json.loads(pxweb.CODES_OUT.read_text(encoding="utf-8"))
    log = json.loads(config.SOURCES_LOG.read_text(encoding="utf-8")) if config.SOURCES_LOG.exists() else {}
    fi = izravnanje.ucitaj(units_csv=config.BUILD / "units.csv")
    razredi = pd.read_parquet(porezna.OUT_RAZREDI)
    wide = pd.read_parquet(config.BUILD / "wide.parquet")
    yi = int(doh.godina.max())
    p611 = wide[wide.year == yi].set_index("oib")["p_611"].to_dict()
    return {"stanovnistvo_gospodarstvo": population_economy(units, dzs, doh, kodovi, log),
            "izravnanje": equalization(fi, stope, higher=highest_rates(doh, stope, razredi, p611)),
            "porezne_stope": tax_rates(stope)}
