"""metodologija.json: the methodology as the code applies it, for the "Metodologija i podaci" page.

Every threshold, weight, rule and the AI prompt are read from the modules that use them
(methodology.py, provenance.py, explain.py, verify.py, merge.py), so the page cannot drift
from the computation. publish.py writes it to api/v1/metodologija.json.
"""
import json

import pandas as pd

from . import config, dzs_xlsx, explain, facts, izravnanje, kontekst, merge, methodology, provenance, pxweb

REPO = "https://github.com/abi-azan/Datathon-Portala-otvorenih-podataka-2026"


def _pc(share):
    """0.3 -> "30 %" (Croatian spacing, as on the rest of the site)."""
    return f"{share * 100:.0f} %"


def _int(n):
    """10000 -> "10.000"."""
    return f"{n:,}".replace(",", ".")


def _years(ys):
    """[2021, 2022, 2023, 2024] -> "2021.–2024."; [2025] -> "2025."."""
    ys = sorted(int(y) for y in ys)
    if not ys:
        return ""
    if ys == list(range(ys[0], ys[-1] + 1)) and len(ys) > 1:
        return f"{ys[0]}.–{ys[-1]}."
    return ", ".join(f"{y}." for y in ys)


def _dzs_sources():
    """Sentence on where each population year comes from (PxWeb or the DZS workbook), read from
    data/build/dzs.parquet; empty when it is not built or PxWeb has every year."""
    if not pxweb.OUT.exists():
        return ""
    by_year = kontekst.year_sources(pd.read_parquet(pxweb.OUT))
    xl = [y for y, s in by_year.items() if s == dzs_xlsx.IZVOR_XLSX]
    px = [y for y, s in by_year.items() if s != dzs_xlsx.IZVOR_XLSX]
    if not xl:
        return ""
    return (f" Godine koje PxWeb još nema ({_years(xl)}) uzimaju se iz publikacije DZS-a „{dzs_xlsx.TITLE}” "
            f"(XLSX, listovi Tab-2. i Tab-3.); {_years(px)} su s PxWeba. Čim DZS objavi tu godinu i na PxWebu, "
            "vrijedi PxWeb. Publikacija se koristi samo ako se za zajedničke godine podudara s PxWebom u svakoj "
            "ćeliji i ako za svaku jedinicu vrijedi: promjena broja stanovnika = živorođeni − umrli + doseljeni − "
            "odseljeni.")


def _population_economy():
    """Card "Stanovništvo i gospodarstvo" (pipeline/kontekst.py); the symbol rule is read from pxweb."""
    nema = ("broji se kao 0, i u medijanu" if pxweb.NEMA_JE_NULA else "ostaje prazno")
    return ("Kretanje broja stanovnika od 2021. računa se iz procjena "
            "Državnog zavoda za statistiku (stanje 31.12.); preglednik niz pri otvaranju stranice traži i izravno "
            "s API-ja DZS-a." + _dzs_sources() + " Prirodni prirast (živorođeni − umrli), neto migracija (doseljeni − odseljeni) i "
            "građevinske dozvole (broj zgrada) iskazuju se na 1.000 stanovnika, a noćenja turista u komercijalnom "
            "smještaju i neto dohodak stanovnika (Porezna uprava, po prebivalištu) po stanovniku. Nazivnik je "
            "uvijek Popis 2021., kao u ocjeni. Udio mirovina je neto dohodak umirovljenika u ukupnom neto dohotku. "
            f"Oznaka DZS-a \"{pxweb.NEMA}\" znači da pojave nema (nema smještaja, nema dozvola) i {nema}; oznaka "
            f"\"{pxweb.TAJNO}\" znači da je podatak tajan, pa ostaje prazan i ne ulazi u medijan. Uz svaku brojku je "
            "medijan usporedne skupine iz ocjene; županije se uspoređuju sa županijama, a Grad Zagreb nema skupinu.")


def _dec(x):
    """2.0 -> "2", 1.6 -> "1,6"."""
    return f"{x:g}".replace(".", ",")


def _equalization_unit():
    """Card "Fiskalno izravnanje" (pipeline/kontekst.py), amounts read from pipeline/izravnanje.py."""
    return ("Po čl. 8. i 9. Zakona o financiranju JLP(R)S jedinica ima pravo na izravnanje kad joj "
            "je kapacitet poreznih prihoda po stanovniku ispod referentne vrijednosti za njezinu vrstu (općine, gradovi, "
            "županije; Grad Zagreb mjeri se s gradovima). Kapacitet i referentne vrijednosti su iz tablice Ministarstva "
            f"financija za {config.MF_FI_YEAR}. Prikazuje se procjena godišnje isplate: udio jedinice u zbroju punih iznosa "
            "svih jedinica puta iznos u državnom proračunu "
            f"({_int(round(izravnanje.ISPLATA_2026))} € za {kontekst.PRORACUN_GODINA}.; za {config.MF_FI_YEAR}. još nije "
            "utvrđen, pa se uzima isti), kao u simulatoru spajanja. Kapacitet se računa uz najvišu dopuštenu stopu poreza "
            "na dohodak, pa porez koji jedinica s nižom stopom sama ne naplati izravnanje ne nadoknađuje; stope su iz "
            "odluka jedinica koje objavljuje Porezna uprava. Za jedinice s nižom stopom procjenjuje se koliko bi proračun "
            "godišnje imao više uz najviše stope: porez stanovnika samo na plaće, mirovine, obrt i drugi dohodak (kapital, "
            "najam i prodaja nekretnina te paušalisti plaćaju fiksnu stopu), podijeljen na niži i viši razred prema broju "
            f"obveznika iznad granice (Pareto, α {_dec(kontekst.PARETO_ALFA)}), puta razlika do najviše stope, puta udio "
            "jedinice u porezu (konto 611 / porez stanovnika iste godine). Raspon: od najmanje procjene uz druge "
            f"pretpostavke o višem razredu umanjene za {_pc(1 - kontekst.PONASANJE)} (ljudi uz višu stopu prijave nešto "
            "manje dohotka) do najveće. Procjena ne ulazi u ocjenu, kartu ni usporedbu sa skupinom.")


def doc(ai_texts_path=None, shown_ai=None, n_units=None):
    """ai_texts_path: the AI texts publish.py used; shown_ai: how many profiles it published with
    the AI text (a text whose pack changed since the batch is shown as the template)."""
    ai = None
    if ai_texts_path is not None and ai_texts_path.exists():
        meta = json.loads(ai_texts_path.read_text(encoding="utf-8"))["meta"]
        # verify_sha256: the check run at import; verify_sha256_kaggle: the one run on Kaggle while generating
        ai = {k: meta.get(k) for k in ("modeli", "gguf", "model_izvor", "llama_cpp_commit", "tekstova", "uvezeno",
                                       "prompt_sha256", "verify_sha256", "verify_sha256_kaggle", "commit_skripte")}
        ai.update(uvezeno_ai=meta.get("ai"), prikazano_ai=shown_ai, jedinica=n_units or meta.get("jedinica"))
    # the runner as it was when the batch script was generated, when the import knows that commit
    runner_ref = (ai or {}).get("commit_skripte") or "main"
    w = methodology.WINDOW_WEIGHTS
    big = methodology.SIZE_CLASSES[-1][0]
    return {
        "godina": config.LAST_YEAR,
        "prozor": {"ponderi": w,
                   "opis": f"Pokazatelji I1-I4 su ponderirani prosjek zadnje {len(w)} godine (ponderi "
                           f"{', '.join(map(str, w[:-1]))} i {w[-1]}, od najnovije), a I5 je stanje na kraju zadnje godine."},
        "velicine": [{"oznaka": k, "formula": v} for k, v in provenance.QUANTITIES.items()],
        "pokazatelji": [{"oznaka": k, "naziv": n, "formula": f,
                         "ponder": methodology.SCENARIOS["osnovni"][k],
                         "pragovi": [{"vrijednost": x, "bodovi": b} for x, b in methodology.ANCHORS[k]]}
                        for k, (n, f, _) in provenance.INDICATORS.items()],
        "ocjene": [{"ocjena": g, "rijec": w, "od_bodova": max(cut, 0)} for cut, g, w in methodology.GRADES],
        "scenariji": methodology.SCENARIOS,
        "pravila": [
            {"oznaka": "pravilo 1",
             "tekst": f"Kredit iskazan kao cijeli dospio (barem {_pc(methodology.LOAN_ALL_DUE_SHARE)} stanja, stanje veće od "
                      f"{_int(methodology.LOAN_ALL_DUE_MIN)} €) ne ulazi u dospjele obveze kad se glavnica redovno otplaćuje "
                      f"(barem {_pc(methodology.LOAN_REPAID_SHARE)} stanja na početku godine) ili kad se kredit još povlači "
                      f"(stanje veće nego prethodne godine). Jedinica dobiva oznaku kvalitete podataka."},
            {"oznaka": "pravilo 2",
             "tekst": f"Dospjele obveze od barem {_pc(methodology.DO_CAP_SHARE)} rashoda poslovanja ograničavaju bodove na "
                      f"{str(methodology.DO_CAP_POINTS).replace('.', ',')}, pa je ocjena najviše "
                      f"{methodology.grade(methodology.DO_CAP_POINTS)[0]}."},
            {"oznaka": "refinanciranje",
             "tekst": f"Otplata glavnice veća od {_pc(methodology.REFINANCING_SHARE)} tekućih prihoda, plaćena novim kreditom "
                      "iste godine, broji se umanjena za novi kredit (54 − 84)."},
        ],
        "zastavice": [{"oznaka": k, "tekst": v} for k, v in facts.FLAGS.items()],
        "kriterij_10": "Kriterij od 10 % (Z5) uveo je zaključak Vlade od 16.4.2026. za pomoći iz državnog proračuna "
                       "koje se dodjeljuju na temelju poziva (ne za izravnanje, decentralizirane funkcije ni EU ugovore). "
                       "Manjak prihoda nad rashodima bez EU izvora smije biti najviše "
                       f"{_pc(methodology.Z5_SHARE)} prihoda bez EU izvora, prema zadnjem godišnjem izvještaju. "
                       "Računamo ga kao ((3 + 4) − (6 + 7)) / (6 + 7 − " + " − ".join(methodology.EU_REVENUE) + "). "
                       "PR-RAS ne razdvaja rashode po izvoru, pa se rashodi iz EU izvora uzimaju jednaki EU prihodima "
                       "iste godine; kod jedinica s velikim EU projektima rezultat je približan. Zaključak ne kaže je li riječ "
                       "o manjku same godine ili o ukupnom manjku s prenesenim rezultatom; uzimamo manjak godine, jer je "
                       "svrha zaključka fiskalni rezultat opće države, koji se mjeri po godinama. Izračun je naš, a ne "
                       "MF-ov, i ne ulazi u ocjenu.",
        "skupine": {"razredi": [label for _, _, label in methodology.SIZE_CLASSES],
                    "opis": f"Općine i gradovi uspoređuju se unutar vrste i razreda veličine; gradovi od {_int(big)} "
                            "stanovnika naviše čine skupinu velikih gradova, županije svoju skupinu, a Grad Zagreb nema "
                            "usporedne skupine. Rang se prikazuje samo unutar skupine."},
        "ai": {
            "opis": "Python izračuna sve brojke i složi paket činjenica (pipeline/facts.py). Model napiše 3-5 rečenica oko "
                    "njih. Provjera (pipeline/verify.py) odbija tekst u kojem je ijedna brojka koje nema u paketu, ocjena "
                    "koja nije stvarna, ili najslabija sastavnica, jake strane i ograničenje ocjene drukčiji od paketa. "
                    f"Odbijeni tekst piše se ponovno uz povratnu informaciju, najviše {explain.MAX_RETRIES} puta, a zatim "
                    "se koristi predložak. Na stranici se AI tekst prikazuje samo ako je napisan iz istog paketa "
                    "(sha256) i ako ga prihvaća trenutna verzija provjere, koja se ponovno pokreće pri uvozu i pri objavi. "
                    "Kada se kretanje stanovništva ili neto dohodak po stanovniku jedinice izrazito razlikuju od medijana "
                    "usporedne skupine, mogu se spomenuti u jednoj završnoj rečenici kao kontekst, koji ne ulazi u ocjenu "
                    "i ne objašnjava je.",
            "model": (f"{', '.join(ai['modeli'])} ({', '.join(ai['gguf'] or [])}; Apache-2.0), llama.cpp (MIT) na Kaggle GPU-u"
                      if ai and ai.get("modeli") else
                      f"Gemma 4 ({explain.BATCH_MODEL_SOURCE}; Apache-2.0), llama.cpp (MIT) na Kaggle GPU-u"),
            "sustav": explain.SYSTEM, "pravila": explain.RULES, "primjer": explain.EXAMPLE,
            "prompt_sha256": explain.prompt_sha256(),
            "prompt_jednak_batchu": None if not ai else ai.get("prompt_sha256") == explain.prompt_sha256(),
            # every published AI text passed this check at publication (publish.explanation runs it)
            "verify_sha256": explain.verify_sha256(),
            "provjera_jednaka_uvozu": None if not ai else ai.get("verify_sha256") == explain.verify_sha256(),
            "kod": {"prompt": f"{REPO}/blob/main/pipeline/explain.py", "provjera": f"{REPO}/blob/main/pipeline/verify.py",
                    "cinjenice": f"{REPO}/blob/main/pipeline/facts.py",
                    "biljeznica": f"{REPO}/blob/{runner_ref}/kaggle/gemma_runner.py"},
            "batch": ai,
        },
        "simulator": {
            "usteda": "Ušteda samo na općoj upravi (funkcija 01 bez 017 i 018) i samo od veličine. Svaka članica "
                      "vrednuje se medijanom troška po stanovniku jedinica svoje veličine iste vrste kao spojena jedinica "
                      "(općina koja ulazi u grad mjeri se s gradovima svoje veličine), a spojena jedinica medijanom svoje "
                      "skupine. Razlika je učinak veličine. Realističan raspon je 0 do manjeg od učinka veličine i "
                      f"{_pc(merge.SAVINGS_SHARE)} zbroja troška uprave. Koliko članice troše iznad sličnih jedinica "
                      "prikazuje se odvojeno: taj jaz postoji i bez spajanja i ne pripisuje se spajanju. Iznad "
                      f"{_int(merge.NO_SAVINGS_ABOVE)} stanovnika dodatna ušteda se ne očekuje.",
            "poticaj": "Poticaj za stvarno spajanje po Odluci NN 88/2022 (t. IX., na snazi i u 2026.). Pretpostavljamo da "
                       "najveća članica pripaja ostale. Pripojena jedinica iz razvojne skupine I.-V. donosi pet godina "
                       f"godišnje {merge.INCENTIVE_FACTOR} × svoje fiskalno izravnanje iz godine prije spajanja i do "
                       f"{_int(round(merge.INCENTIVE_CAPITAL))} € za kapitalne projekte; podmiruju se i njezine dospjele obveze "
                       "i krediti sa stanjem 30.6.2022. Isplatu izravnanja procjenjujemo kao udio u zbroju punih iznosa "
                       "tablice MF-a puta stavku proračuna za 2026. Poticaj je prijenos iz državnog proračuna, ne ušteda.",
            "izravnanje": "Fiskalno izravnanje po čl. 8. i 9. Zakona o financiranju JLP(R)S. Puni iznos (pravo) = max(0, "
                          "(referentna vrijednost − kapacitet) × stanovnici), s kapacitetima i referentnim vrijednostima iz "
                          "tablice Ministarstva financija; formula na toj tablici daje iste pune iznose za svih 576 jedinica. "
                          "Prikazuje se isplata: udio jedinice u zbroju svih punih iznosa puta iznos u državnom proračunu "
                          "(za 2026. 280,4 mil. €; za 2027. još nije utvrđen, pa se uzima isti). Iznos u proračunu je fiksan, "
                          "pa spajanje državi ne štedi: što spojena jedinica izgubi, dobivaju ostale jedinice.",
            "reforma": "Unutar županije najmanja jedinica ispod praga spaja se s najmanjim susjedom dok sve "
                       "ne dosegnu prag (2.500, 5.000 ili 10.000 stanovnika). Scenarij, ne prijedlog granica.",
            "demografija": "Kretanje stanovništva prikazuje se uz rezultat, ali ne ulazi u ocjenu: ocjena i iznosi po "
                           "stanovniku i dalje koriste Popis 2021. Za spojenu jedinicu zbraja se broj stanovnika članica "
                           "na kraju svake godine (31.12.) prema Državnom zavodu za statistiku, a promjena se računa od "
                           "2021. do zadnje godine; za svaku članicu prikazuje se njezina promjena. Prirodna promjena (živorođeni "
                           "manje umrli) i migracijski saldo (doseljeni manje odseljeni) zbrajaju se za zadnju godinu i "
                           "prikazuju i na 1.000 stanovnika prema Popisu 2021. Oznaka DZS-a \"-\" (pojave nema) broji "
                           "se kao 0, a skriveni podatak (\"z\") znači da zbroj nije poznat." + _dzs_sources(),
        },
        "stanovnistvo_gospodarstvo": _population_economy(),
        "izravnanje_jedinice": _equalization_unit(),
        "revizija": "U pregledu jedinice je zadnje mišljenje financijske revizije Državnog ureda za reviziju (izvješća "
                    "objavljena od 2019.), pročitano iz teksta izvješća, s revidiranom godinom i poveznicom. Mišljenje "
                    "ne ulazi u ocjenu.",
        "ogranicenja": [
            "Ocjenjuje se financijska održivost proračuna, a ne kvaliteta upravljanja ni razina usluga.",
            "Podaci su razina 22: proračun jedinice bez proračunskih korisnika i bez komunalnih društava, pa dug "
            "društava u vlasništvu jedinice nije uključen.",
            "Dospjele obveze jedinice iskazuju same; pravilo 1 ispravlja čestu grešku s kreditom, ali ne sve.",
            "Zakonska osnovica je približna (zakon koristi prosječni anuitet i jamstva, a ovdje se uzimaju stvarne isplate).",
            "Pragovi bodova preuzeti su iz austrijske (KDZ) i slovačke (INEKO) prakse i kalibrirani na hrvatskim podacima.",
            "Simulator i Karta reforme su scenariji: ne uključuju troškove prijelaza, promjenu stopa poreza ni nefinancijsku "
            "cijenu spajanja.",
        ],
    }
