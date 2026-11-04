"""metodologija.json: the methodology as the code applies it, for the "Metodologija i podaci" page.

Every threshold, weight, rule and the AI prompt are read from the modules that use them
(methodology.py, provenance.py, explain.py, verify.py, merge.py), so the page cannot drift
from the computation. publish.py writes it to api/v1/metodologija.json.
"""
import json

from . import config, explain, facts, merge, methodology, provenance

REPO = "https://github.com/abi-azan/Datathon-Portala-otvorenih-podataka-2026"


def _pc(share):
    """0.3 -> "30 %" (Croatian spacing, as on the rest of the site)."""
    return f"{share * 100:.0f} %"


def _int(n):
    """10000 -> "10.000"."""
    return f"{n:,}".replace(",", ".")


def doc(ai_texts_path=None, shown_ai=None, n_units=None):
    """ai_texts_path: the AI texts publish.py used; shown_ai: how many profiles it published with
    the AI text (a text whose pack changed since the batch is shown as the template)."""
    ai = None
    if ai_texts_path is not None and ai_texts_path.exists():
        meta = json.loads(ai_texts_path.read_text(encoding="utf-8"))["meta"]
        ai = {k: meta.get(k) for k in ("modeli", "gguf", "model_izvor", "llama_cpp_commit", "tekstova", "uvezeno",
                                       "prompt_sha256", "verify_sha256")}
        ai.update(uvezeno_ai=meta.get("ai"), prikazano_ai=shown_ai, jedinica=n_units or meta.get("jedinica"))
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
                    "(sha256) i ako provjera prolazi i pri objavi.",
            "model": (f"{', '.join(ai['modeli'])} ({', '.join(ai['gguf'] or [])}; Apache-2.0), llama.cpp (MIT) na Kaggle GPU-u"
                      if ai and ai.get("modeli") else
                      f"Gemma 4 ({explain.BATCH_MODEL_SOURCE}; Apache-2.0), llama.cpp (MIT) na Kaggle GPU-u"),
            "sustav": explain.SYSTEM, "pravila": explain.RULES, "primjer": explain.EXAMPLE,
            "prompt_sha256": explain.prompt_sha256(),
            "prompt_jednak_batchu": None if not ai else ai.get("prompt_sha256") == explain.prompt_sha256(),
            "kod": {"prompt": f"{REPO}/blob/main/pipeline/explain.py", "provjera": f"{REPO}/blob/main/pipeline/verify.py",
                    "cinjenice": f"{REPO}/blob/main/pipeline/facts.py", "biljeznica": f"{REPO}/blob/main/kaggle/gemma_runner.py"},
            "batch": ai,
        },
        "simulator": {
            "usteda": "Ušteda samo na općoj upravi (funkcija 01 bez 017 i 018). Očekivani trošak je medijan troška po "
                      "stanovniku usporedne skupine spojene jedinice puta broj stanovnika. Strukturni jaz je gornja granica; "
                      f"realističan raspon je 0 do {_pc(merge.SAVINGS_SHARE)} zbroja troška uprave, najviše do jaza. Iznad "
                      f"{_int(merge.NO_SAVINGS_ABOVE)} stanovnika dodatna ušteda se ne očekuje.",
            "izravnanje": "Fiskalno izravnanje po čl. 8. i 9. Zakona o financiranju JLP(R)S: puni iznos = max(0, (referentna "
                          "vrijednost − kapacitet) × stanovnici), s kapacitetima i referentnim vrijednostima iz tablice "
                          "Ministarstva financija. Formula na toj tablici daje iste pune iznose za svih 576 jedinica. Isplata "
                          "je udio u stavci državnog proračuna.",
            "reforma": "Unutar županije najmanja jedinica ispod praga spaja se s najmanjim susjedom dok sve "
                       "ne dosegnu prag (2.500, 5.000 ili 10.000 stanovnika). Scenarij, ne prijedlog granica.",
        },
        "revizija": "Na svjedodžbi je zadnje mišljenje financijske revizije Državnog ureda za reviziju (izvješća "
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
