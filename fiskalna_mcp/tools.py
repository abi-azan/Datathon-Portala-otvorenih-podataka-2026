"""The tool logic, independent of MCP: every function reads the static API and returns a dict.

Rules: numbers come only from API files (no new figures are computed, apart from picking and
renaming fields); every answer carries links to the page and to the source file; a bad
request gives {"greska": "..."} instead of an exception. Fields that an older API lacks are
returned as None or left out.
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from typing import Any

from .api import Api, ApiError

INDICATORS = ("I1", "I2", "I3", "I4", "I5")
# fallback names, used only when metodologija.json is missing (same text as in the API)
INDICATOR_NAMES = {"I1": "Operativni saldo", "I2": "Slobodni saldo", "I3": "Godine otplate duga",
                   "I4": "Servis duga", "I5": "Dospjele obveze"}
INDICATOR_ALIASES = {
    "I1": ["operativni saldo", "operativni visak", "operativni manjak"],
    "I2": ["slobodni saldo", "slobodni saldo nakon otplate glavnice"],
    "I3": ["godine otplate duga", "godine otplate neto duga", "otplata duga"],
    "I4": ["servis duga"],
    "I5": ["dospjele obveze", "dospjele neplacene obveze", "neplacene obveze"],
}
QUANTITY_ALIASES = {
    "KP": ["kapitalne pomoci"],
    "PO": ["tekuci prihodi", "prihodi poslovanja"],
    "OS": ["operativni saldo iznos"],
    "glavnica": ["glavnica", "otplata glavnice"],
    "ND": ["neto dug"],
    "SD": ["iznos servisa duga"],
    "ZO": ["zakonska osnovica"],
    "FI": ["fiskalno izravnanje", "izravnanje"],
    "DO": ["iznos dospjelih obveza"],
}
# quantities a quantity is built from (formulas in izvor.json: PO = 6 − KP, OS = PO − 3, ...)
QUANTITY_DEPS = {"PO": ["KP"], "OS": ["PO"], "ZO": ["FI"], "SD": ["glavnica"]}
REFORM_THRESHOLDS = (2500, 5000, 10000)
MAX_MERGE = 4
MAX_COMPARE = 5
RESULT_LIMIT = 10


# ---------------------------------------------------------------- text helpers

def norm(s: str) -> str:
    """Lower case, no diacritics (đ → d), words separated by single spaces."""
    s = str(s).lower().replace("đ", "d")
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def _base_name(naziv: str) -> str:
    n = norm(naziv)
    for prefix in ("grad ", "opcina "):
        if n.startswith(prefix):
            return n[len(prefix):]
    if n.endswith(" zupanija"):
        return n[: -len(" zupanija")]
    return n


def _err(msg: str, **extra) -> dict[str, Any]:
    return {"greska": msg, **extra}


def _split_list(value) -> list[str]:
    """A list of units given as a list, or as one string separated by commas or semicolons."""
    if value is None:
        return []
    if isinstance(value, str):
        value = re.split(r"[,;]", value)
    return [str(v).strip() for v in value if str(v).strip()]


class Fiskalna:
    def __init__(self, api: Api):
        self.api = api

    # ------------------------------------------------------------ API files

    def _units(self) -> dict:
        data = self.api.get("jedinice.json")
        if not data or "jedinice" not in data:
            raise ApiError("jedinice.json nije dostupan.")
        return data

    def _unit_list(self) -> list[dict]:
        return self._units()["jedinice"]

    def _last_year(self) -> int:
        return int(self._units().get("zadnja_godina") or max(
            int(y) for u in self._unit_list() for y in (u.get("ocjena") or {})))

    def _by_sifra(self) -> dict[str, dict]:
        return {u["sifra"]: u for u in self._unit_list()}

    def _profile(self, slug: str) -> dict | None:
        return self.api.get(f"jedinice/{slug}.json")

    def _methodology(self) -> dict:
        return self.api.get("metodologija.json") or {}

    def _indicator_meta(self) -> dict[str, dict]:
        meta = {k: {"naziv": n} for k, n in INDICATOR_NAMES.items()}
        for p in self._methodology().get("pokazatelji") or []:
            if p.get("oznaka") in meta:
                meta[p["oznaka"]] = {"naziv": p.get("naziv"), "ponder_posto": p.get("ponder"),
                                     "formula": p.get("formula")}
        return meta

    def _flag_texts(self) -> dict[str, str]:
        return {z["oznaka"]: z["tekst"] for z in self._methodology().get("zastavice") or [] if "oznaka" in z}

    def _group_medians(self, skupina: str | None, year: int) -> dict | None:
        groups = self.api.get("skupine.json") or {}
        return (groups.get(skupina) or {}).get(str(year))

    # ------------------------------------------------------------ links

    def _links(self, u: dict) -> dict[str, str]:
        slug = u["slug"]
        return {"stranica": f"{self.api.site}#/jedinica/{slug}",
                "podaci": self.api.url(f"jedinice/{slug}.json"),
                "izvor": self.api.url(f"jedinice/{slug}/izvor.json")}

    # ------------------------------------------------------------ resolving units

    def _brief(self, u: dict, year: int | None = None) -> dict[str, Any]:
        year = year or self._last_year()
        return {"slug": u["slug"], "naziv": u["naziv"], "vrsta": u.get("vrsta"), "zupanija": u.get("zupanija"),
                "sifra_dgu": u.get("sifra"), "godina": year,
                "ocjena": (u.get("ocjena") or {}).get(str(year)),
                "bodovi": (u.get("bodovi") or {}).get(str(year)),
                "stranica": f"{self.api.site}#/jedinica/{u['slug']}"}

    def _search(self, naziv: str, zupanija: str | None = None) -> list[dict]:
        q = norm(naziv)
        qs = {q, q.replace("dj", "d")}
        units = self._unit_list()
        if zupanija:
            z = norm(zupanija)
            z = z[: -len(" zupanija")] if z.endswith(" zupanija") else z
            units = [u for u in units if z and (z in norm(u.get("zupanija", "")) or z == str(u.get("zup_id")))]
        scored = []
        for u in units:
            base, full, slug = _base_name(u["naziv"]), norm(u["naziv"]), norm(u["slug"])
            best = None
            for x in qs:
                if not x:
                    continue
                if x in (base, full, slug):
                    s = 0
                elif base.startswith(x) or full.startswith(x):
                    s = 1
                elif any(w.startswith(x) for w in base.split()):
                    s = 2
                elif x in full:
                    s = 3
                else:
                    continue
                best = s if best is None else min(best, s)
            if best is not None:
                scored.append((best, len(base), u["naziv"], u))
        if not scored and q:                                   # typo: closest names
            bases = {_base_name(u["naziv"]): u for u in units}
            for i, b in enumerate(difflib.get_close_matches(q, list(bases), n=RESULT_LIMIT, cutoff=0.75)):
                scored.append((4 + i, 0, b, bases[b]))
        scored.sort(key=lambda t: t[:3])
        return [t[3] for t in scored]

    def _resolve(self, jedinica: str, zupanija: str | None = None) -> tuple[dict | None, dict | None]:
        """(unit, None) or (None, error dict). Accepts slug, name, DGU code (5 digits, Z01-Z20) or OIB."""
        key = str(jedinica or "").strip()
        if not key:
            return None, _err("Jedinica nije zadana.")
        units = self._unit_list()
        if re.fullmatch(r"\d{5}|[zZ]\d{2}", key):
            for u in units:
                if u.get("sifra", "").upper() == key.upper():
                    return u, None
            return None, _err(f"Nema jedinice sa šifrom DGU {key}.")
        if re.fullmatch(r"\d{11}", key):
            for u in units:
                if u.get("oib") == key:
                    return u, None
            return None, _err(f"Nema jedinice s OIB-om {key}.")
        for u in units:
            if u["slug"] == key.lower():
                return u, None
        found = self._search(key, zupanija)
        q = {norm(key), norm(key).replace("dj", "d")}
        exact = [u for u in found if q & {_base_name(u["naziv"]), norm(u["naziv"])}]
        if len(exact) == 1:
            return exact[0], None
        if len(exact) > 1:
            return None, _err(f"Naziv \"{key}\" nosi više jedinica. Zadajte slug ili šifru, ili dodajte županiju.",
                              kandidati=[self._brief(u) for u in exact])
        if len(found) == 1:
            return found[0], None
        return None, _err(f"Nisam našao jedinicu \"{key}\".",
                          prijedlozi=[self._brief(u) for u in found[:5]])

    # ------------------------------------------------------------ tools

    def pronadi_jedinicu(self, naziv: str, zupanija: str | None = None) -> dict[str, Any]:
        year = self._last_year()
        found = self._search(naziv, zupanija)
        out = {"upit": naziv, "zupanija": zupanija, "godina": year, "broj": len(found),
               "jedinice": [self._brief(u, year) for u in found[:RESULT_LIMIT]],
               "izvor": self.api.url("jedinice.json")}
        if not found:
            out["poruka"] = "Nema jedinice tog naziva." + (" Provjeri i naziv županije." if zupanija else "")
        elif len(found) > RESULT_LIMIT:
            out["poruka"] = f"Prikazano prvih {RESULT_LIMIT}; suzite upit ili dodajte županiju."
        return out

    def pregled_jedinice(self, jedinica: str, godina: int | None = None) -> dict[str, Any]:
        u, err = self._resolve(jedinica)
        if err:
            return err
        p = self._profile(u["slug"])
        if p is None:
            return _err(f"{u['naziv']}: profil nije dostupan u API-ju.", poveznice=self._links(u))
        years = sorted(int(y) for y in (p.get("godine") or {}))
        if not years:
            return _err(f"{u['naziv']} nema ocijenjenih godina.", poveznice=self._links(u))
        year = int(godina) if godina else (self._last_year() if self._last_year() in years else years[-1])
        g = (p.get("godine") or {}).get(str(year))
        if g is None:
            return _err(f"{u['naziv']}: nema ocjene za {year}. Dostupne godine: {years}.",
                        poveznice=self._links(u))
        meta = self._indicator_meta()
        med = self._group_medians(p.get("skupina"), year) or {}
        flags = self._flag_texts()
        out: dict[str, Any] = {
            "jedinica": {"slug": u["slug"], "naziv": p.get("naziv", u["naziv"]), "vrsta": p.get("vrsta"),
                         "zupanija": p.get("zupanija"), "sifra_dgu": p.get("sifra"), "oib": p.get("oib"),
                         "stanovnici_popis_2021": p.get("stanovnici_2021"), "otok": p.get("otok")},
            "godina": year,
            "ocjena": g.get("ocjena"),
            "ocjena_rijec": g.get("ocjena_rijec"),
            "ljestvica": "1 (vrlo nestabilno) do 5 (vrlo stabilno)",
            "bodovi": g.get("bodovi"),
            "bodovi_bez_ogranicenja": g.get("bodovi_bez_ogranicenja"),
            "ogranicenje_do": g.get("ogranicenje_do"),
            "stabilnost": g.get("stabilnost"),
            "ocjene_scenarija": g.get("ocjene_scenarija"),
            "sastavnice": [
                {"oznaka": k, "naziv": meta[k].get("naziv"), "ponder_posto": meta[k].get("ponder_posto"),
                 "vrijednost": g.get(k), "bodovi": g.get(f"S{k[1]}"), "medijan_skupine": med.get(k)}
                for k in INDICATORS],
            "usporedna_skupina": {"naziv": p.get("skupina"), "rang": _int(g.get("rang")), "od": g.get("n_skupine"),
                                  "percentil": g.get("percentil"), "medijan_bodova": med.get("bodovi")},
            "zastavice": [{"oznaka": z, "tekst": flags.get(z)} for z in g.get("zastavice") or []],
            "oznake_kvalitete": (g.get("kvaliteta") or []) + (g.get("oznake") or []),
            "ocjene_po_godinama": {y: (p["godine"][y] or {}).get("ocjena") for y in sorted(p["godine"])},
        }
        if g.get("ogranicenje_do"):
            rule = next((r["tekst"] for r in self._methodology().get("pravila") or []
                         if r.get("oznaka") == "pravilo 2"), None)
            out["napomena_ogranicenja"] = rule
        sg = p.get("stanovnistvo_gospodarstvo") or {}
        pok = sg.get("pokazatelji") or {}
        out["kontekst"] = {
            "napomena": "Kontekst ne ulazi u ocjenu.",
            "stanovnistvo": {"popis_2021": p.get("stanovnici_2021"), "procjene_dzs": sg.get("procjene"),
                             "promjena": pok.get("promjena_stanovnistva"),
                             "prirodni_prirast_na_1000": pok.get("prirodni_prirast"),
                             "neto_migracija_na_1000": pok.get("neto_migracija")} if p.get("stanovnici_2021") or sg else None,
            "neto_dohodak_po_stanovniku": pok.get("neto_dohodak_pc"),
            "ostali_pokazatelji": {k: v for k, v in pok.items() if k not in
                                   ("promjena_stanovnistva", "prirodni_prirast", "neto_migracija", "neto_dohodak_pc")} or None,
            "izravnanje": p.get("izravnanje"),
            "revizija_dur": p.get("revizija"),
            "indeks_razvijenosti_2024": p.get("indeks_razvijenosti_2024"),
            "razvojna_skupina": p.get("razvojna_skupina"),
        }
        ob = p.get("objasnjenje")
        fact_year = (p.get("cinjenice") or {}).get("year")
        if ob:
            ai = ob.get("izvor") == "ai"
            check = ob.get("provjera") or {}
            label = (f"AI tekst ({ob.get('model') or 'model'}), {check.get('n_brojki')} brojki provjereno"
                     if ai and check.get("ok") else "AI tekst" if ai else "predložak (bez AI-ja)")
            out["objasnjenje"] = {"tekst": ob.get("tekst"), "oznaka": label, "izvor": ob.get("izvor"),
                                  "godina": fact_year, "provjera": check or None}
            if fact_year and int(fact_year) != year:
                out["objasnjenje"]["napomena"] = f"Objašnjenje je napisano za {fact_year}., ne za {year}."
        else:
            out["objasnjenje"] = None
        out["poveznice"] = {**self._links(u), "metodologija": f"{self.api.site}#/metodologija"}
        return out

    def usporedi(self, jedinice, godina: int | None = None) -> dict[str, Any]:
        names = list(dict.fromkeys(_split_list(jedinice)))
        if not 2 <= len(names) <= MAX_COMPARE:
            return _err(f"Za usporedbu zadajte 2 do {MAX_COMPARE} različitih jedinica (zadano: {len(names)}).")
        units = []
        for n in names:
            u, err = self._resolve(n)
            if err:
                return {**err, "jedinica": n}
            if u["slug"] in {x["slug"] for x in units}:
                return _err(f"Jedinica {u['naziv']} je zadana dvaput.")
            units.append(u)
        year = int(godina) if godina else self._last_year()
        rows, medians = [], {}
        for u in units:
            p = self._profile(u["slug"]) or {}
            g = (p.get("godine") or {}).get(str(year))
            row = {"slug": u["slug"], "naziv": u["naziv"], "vrsta": u.get("vrsta"), "zupanija": u.get("zupanija"),
                   "stanovnici_popis_2021": u.get("stanovnici"), "usporedna_skupina": u.get("skupina"),
                   "stranica": self._links(u)["stranica"], "izvor": self._links(u)["izvor"]}
            if g is None:
                row["poruka"] = f"Nema ocjene za {year}."
            else:
                row.update({"ocjena": g.get("ocjena"), "ocjena_rijec": g.get("ocjena_rijec"), "bodovi": g.get("bodovi"),
                            "rang": _int(g.get("rang")), "od": g.get("n_skupine"),
                            "sastavnice": {k: {"vrijednost": g.get(k), "bodovi": g.get(f"S{k[1]}")} for k in INDICATORS},
                            "zastavice": g.get("zastavice") or []})
            rows.append(row)
            sk = u.get("skupina")
            if sk and sk not in medians:
                m = self._group_medians(sk, year)
                medians[sk] = {k: m.get(k) for k in ("bodovi", *INDICATORS)} if m else None
        meta = self._indicator_meta()
        return {"godina": year, "jedinice": rows, "medijani_skupina": medians,
                "sastavnice": {k: meta[k].get("naziv") for k in INDICATORS},
                "napomena": "Rang i medijan vrijede unutar usporedne skupine (vrsta i veličina jedinice).",
                "izvor": self.api.url("skupine.json")}

    # ------------------------------------------------------------ merger simulator

    def scenarij_spajanja(self, jedinice) -> dict[str, Any]:
        names = list(dict.fromkeys(_split_list(jedinice)))
        units = []
        for n in names:
            u, err = self._resolve(n)
            if err:
                return {**err, "jedinica": n}
            if u["sifra"] in {x["sifra"] for x in units}:
                return _err(f"Jedinica {u['naziv']} je zadana dvaput.")
            units.append(u)
        if not 2 <= len(units) <= MAX_MERGE:
            return _err(f"Spajaju se 2 do {MAX_MERGE} različite jedinice (zadano: {len(units)}).")
        for u in units:
            if u.get("vrsta") == "zupanija":
                return _err(f"{u['naziv']} je županija: u simulatoru se spajaju samo općine i gradovi.")
            if u["slug"] == "grad-zagreb" or u.get("skupina") == "Grad Zagreb":
                return _err("Grad Zagreb se ne spaja u simulatoru: on je ujedno grad i županija.")
        counties = {u.get("zup_id") for u in units}
        if len(counties) > 1:
            return _err("Spajaju se samo jedinice iste županije: "
                        + ", ".join(f"{u['naziv']} ({u.get('zupanija')})" for u in units) + ".")
        zup = units[0]["zup_id"]
        sim = self.api.get(f"simulator/zup-{int(zup):02d}.json")
        if sim is None:
            return _err("Simulator spajanja nije dostupan u ovom API-ju.")
        key = "-".join(sorted(u["sifra"] for u in units))
        r = (sim.get("skupine") or {}).get(key)
        if r is None:
            why = self._disconnected(units)
            return _err(why or "Ova kombinacija nije u unaprijed izračunatom skupu simulatora "
                        "(npr. jer neka članica nema podatke za istu godinu).",
                        jedinice=[self._brief(u) for u in units])
        year = r.get("godina")
        by = {u["sifra"]: u for u in units}
        fi = r.get("izravnanje") or {}
        members = []
        for i, s in enumerate(r.get("clanice") or []):
            u = by.get(s) or self._by_sifra().get(s, {"sifra": s, "naziv": s, "slug": ""})
            members.append({"sifra_dgu": s, "naziv": u.get("naziv"), "slug": u.get("slug"), "vrsta": u.get("vrsta"),
                            "stanovnici_popis_2021": u.get("stanovnici"), "usporedna_skupina": u.get("skupina"),
                            "ocjena": (u.get("ocjena") or {}).get(str(year)),
                            "bodovi": (u.get("bodovi") or {}).get(str(year)),
                            "izravnanje_isplata": _at(fi.get("isplata_po_clanici"), i),
                            "promjena_stanovnistva": _at((r.get("demografija") or {}).get("clanice"), i)})
        z = r.get("zadnja") or {}
        us = r.get("usteda")
        po = r.get("poticaj")
        return {
            "godina": year,
            "zupanija": sim.get("zupanija"),
            "prije": members,
            "poslije": {"vrsta": r.get("vrsta"), "usporedna_skupina": r.get("skupina"),
                        "stanovnici_popis_2021": r.get("stanovnici"), "ocjena": z.get("ocjena"),
                        "ocjena_rijec": z.get("ocjena_rijec"), "bodovi": z.get("bodovi"),
                        "bodovi_bez_ogranicenja": z.get("bodovi_bez_ogranicenja"),
                        "rang": z.get("rang"), "od": z.get("n_skupine"),
                        "napomena_ranga": "Rang u skupini bez samih članica.",
                        "sastavnice": {k: {"vrijednost": z.get(k), "bodovi": z.get(f"S{k[1]}")} for k in INDICATORS},
                        "zastavice": z.get("zastavice") or [], "oznake_kvalitete": z.get("kvaliteta") or [],
                        "ocjene_po_godinama": r.get("ocjene")},
            "usteda_na_upravi": None if us is None else {
                "godina": us.get("godina"),
                "raspon_eur_godisnje": [0, us.get("realno_do")],
                "ucinak_velicine_eur": us.get("razmjer"),
                "trosak_uprave_zbroj_eur": us.get("uprava_zbroj"),
                "jaz_bez_spajanja_eur": us.get("jaz_bez_spajanja"),
                "iznad_10000_stanovnika": us.get("iznad_10000"),
                "napomena": "Ušteda samo na općoj upravi i samo od veličine; jaz bez spajanja nije ušteda od spajanja.",
            },
            "izravnanje": None if not fi else {
                "godina": fi.get("godina"),
                "isplata_clanice_eur": fi.get("isplata_clanice"),
                "isplata_spojena_eur": fi.get("isplata_spojena"),
                "promjena_isplate_eur": fi.get("isplata_promjena"),
                "puni_iznos_clanice_eur": fi.get("puni_clanice"),
                "puni_iznos_spojena_eur": fi.get("puni_spojena"),
                "oznake": fi.get("oznake"),
            },
            "poticaj": None if po is None else {
                **po, "napomena": "Poticaj po Odluci NN 88/2022 je prijenos iz državnog proračuna, ne ušteda."},
            "demografija": r.get("demografija"),
            "demografija_izvor_po_godini": sim.get("demografija_izvor_po_godini"),
            "napomena": "Scenarij, ne prijedlog: ne uključuje troškove prijelaza ni promjenu poreznih stopa.",
            "poveznice": {"simulator": f"{self.api.site}#/simulator?j={','.join(r.get('clanice') or [])}",
                          "podaci": self.api.url(f"simulator/zup-{int(zup):02d}.json"),
                          "kljuc": key},
        }

    def _disconnected(self, units: list[dict]) -> str | None:
        """Why the units do not form one area (land border or sea link), from the profiles' neighbours."""
        slugs = {u["slug"]: u for u in units}
        adj = {}
        for s in slugs:
            p = self._profile(s)
            if p is None or p.get("susjedi") is None:
                return None
            adj[s] = {n["slug"] for n in p["susjedi"]} & set(slugs)
        seen, todo = set(), [next(iter(slugs))]
        while todo:
            s = todo.pop()
            if s not in seen:
                seen.add(s)
                todo += list(adj.get(s, ()))
        if seen == set(slugs):
            return None
        apart = [slugs[s]["naziv"] for s in slugs if s not in seen]
        return ("Jedinice ne čine jednu cjelinu: svaka mora graničiti s barem jednom drugom ili biti s njom "
                f"povezana vezom preko mora. Odvojeno od ostalih: {', '.join(apart)}.")

    # ------------------------------------------------------------ reform map

    def karta_reforme(self, prag: int, jedinica: str | None = None) -> dict[str, Any]:
        try:
            prag = int(prag)
        except (TypeError, ValueError):
            return _err(f"Prag mora biti broj: {', '.join(map(str, REFORM_THRESHOLDS))}.")
        if prag not in REFORM_THRESHOLDS:
            return _err(f"Karta reforme postoji za pragove {', '.join(map(str, REFORM_THRESHOLDS))} stanovnika.")
        f = self.api.get(f"reforma/prag-{prag}.json")
        if f is None:
            return _err("Karta reforme nije dostupna u ovom API-ju.")
        out = {k: v for k, v in f.items() if k != "jedinice"}
        out["poveznice"] = {"karta": f"{self.api.site}#/reforma?prag={prag}",
                            "podaci": self.api.url(f"reforma/prag-{prag}.json")}
        if jedinica:
            u, err = self._resolve(jedinica)
            if err:
                out["jedinica"] = err
                return out
            g = next((x for x in f.get("jedinice") or [] if u["sifra"] in (x.get("clanice") or [])), None)
            if g is None:
                out["jedinica"] = {"naziv": u["naziv"],
                                   "poruka": "Jedinica ne sudjeluje u Karti reforme (županije i Grad Zagreb ne spajaju se)."}
                return out
            by = self._by_sifra()
            key = "-".join(g.get("clanice") or [])
            before = g.get("ocjene_prije") or {}
            out["jedinica"] = {
                "naziv": u["naziv"],
                "spaja_se": len(g.get("clanice") or []) > 1,
                "skupina": {**{k: v for k, v in g.items() if k != "ocjene_prije"},
                            "clanice": [{"sifra_dgu": s, "naziv": by.get(s, {}).get("naziv"),
                                         "slug": by.get(s, {}).get("slug"), "ocjena_prije": before.get(s)}
                                        for s in g.get("clanice") or []]},
                "karta": f"{self.api.site}#/reforma?prag={prag}&s={key}",
            }
        return out

    # ------------------------------------------------------------ provenance

    def izvor_brojke(self, jedinica: str, pokazatelj: str = "I5") -> dict[str, Any]:
        u, err = self._resolve(jedinica)
        if err:
            return err
        iz = self.api.get(f"jedinice/{u['slug']}/izvor.json")
        if iz is None:
            return _err(f"{u['naziv']}: izvor brojki nije dostupan u ovom API-ju.", poveznice=self._links(u))
        code = _indicator_code(pokazatelj, iz)
        if code is None:
            return _err(f"Nepoznat pokazatelj \"{pokazatelj}\". Zadajte I1-I5 (ili naziv, npr. \"dospjele obveze\"), "
                        "veličinu (KP, PO, OS, glavnica, ND, SD, ZO, FI, DO) ili \"bodovi\".")
        vel = iz.get("velicine") or {}
        pok = iz.get("pokazatelji") or {}
        out: dict[str, Any] = {"jedinica": u["naziv"], "slug": u["slug"], "godina": iz.get("godina"),
                               "prozor": iz.get("prozor")}
        if code == "bodovi":
            meta = self._indicator_meta()
            out["bodovi"] = {"formula": "Σ ponder × bodovi sastavnice (S1-S5) / 100; pravilo 2 ograničava na 39,9",
                             "sastavnice": {k: {**(pok.get(k) or {}), "ponder_posto": meta[k].get("ponder_posto")}
                                            for k in INDICATORS}}
            out["poveznice"] = self._links(u)
            out["napomena"] = iz.get("napomena")
            return out
        if code in INDICATORS:
            out["pokazatelj"] = {"oznaka": code, **(pok.get(code) or {})}
            quantities = list((pok.get(code) or {}).get("velicine") or [])
        else:
            out["velicina"] = code
            quantities = [code]
        tags = set(_expand(quantities)) | ({code} if code in INDICATORS else set())
        out["velicine"] = {q: vel[q] for q in _expand(quantities) if q in vel}
        konta = {k: v for k, v in (iz.get("konta") or {}).items() if tags & set(v.get("za") or [])}
        src = iz.get("izvori") or {}
        ulazi = []
        for x in iz.get("ulazi") or []:
            k = konta.get(x.get("konto"))
            if k is None:
                continue
            s = src.get(k.get("izvor")) or {}
            ulazi.append({**x, "izvor": k.get("izvor"), "datoteka": x.get("datoteka") or s.get("datoteka"),
                          "list": x.get("list") or s.get("list")})
        out["konta"] = konta
        out["ulazi"] = ulazi
        out["izvori"] = src
        out["napomena"] = iz.get("napomena")
        out["poveznice"] = {**self._links(u), "izvori_podataka": self.api.url("izvori.json")}
        return out

    def metodologija(self) -> str:
        return self.api.text("metodologija.json") or '{"greska": "metodologija.json nije dostupan."}'


# ---------------------------------------------------------------- small helpers

def _int(v):
    return int(v) if isinstance(v, (int, float)) and v == v else v


def _at(seq, i):
    return seq[i] if isinstance(seq, list) and i < len(seq) else None


def _expand(quantities: list[str]) -> list[str]:
    out, todo = [], list(quantities)
    while todo:
        q = todo.pop(0)
        if q not in out:
            out.append(q)
            todo += QUANTITY_DEPS.get(q, [])
    return out


def _indicator_code(pokazatelj: str | None, iz: dict) -> str | None:
    raw = str(pokazatelj or "I5").strip()
    up = raw.upper()
    if re.fullmatch(r"[IS][1-5]", up):
        return "I" + up[1]
    for q in (iz.get("velicine") or {}):
        if raw.lower() == q.lower():
            return q
    n = norm(raw)
    if n in ("bodovi", "ocjena", "ukupno"):
        return "bodovi"
    names = {k: [norm(v.get("naziv", ""))] for k, v in (iz.get("pokazatelji") or {}).items()}
    for k, aliases in INDICATOR_ALIASES.items():
        if any(n == a or (len(n) >= 4 and n in a) for a in aliases + names.get(k, [])):
            return k
    for k, aliases in QUANTITY_ALIASES.items():
        if any(n == a or (len(n) >= 4 and n in a) for a in aliases):
            return k
    return None
