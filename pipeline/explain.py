"""AI explanation of a unit's grade (PLAN §5): prompt, retries, template fallback.

    .venv/Scripts/python -m pipeline.explain --kaggle-test 20   # writes the Kaggle test script
    .venv/Scripts/python -m pipeline.explain --kaggle-test 20 --fresh   # 20 units not tested before
    .venv/Scripts/python -m pipeline.explain --check out.json   # re-verifies a downloaded Kaggle output

Python computes the facts (pipeline/facts.py). The model writes 3-5 sentences around them,
and pipeline/verify.py rejects any text with a number that is not in the facts. A rejected
text is generated again with feedback, at most twice, and then the template is used.
The provider is a single function call(messages) -> str, so Gemma on Kaggle, a local
llama.cpp server or another API can be swapped without touching the prompt or the check.
"""
import argparse
import inspect
import json
import random
import sys
from pathlib import Path

import pandas as pd

from . import config, facts, verify

MAX_RETRIES = 2

SYSTEM = ("Ti si urednik javnog portala o financijama općina, gradova i županija. Pišeš kratka, točna "
          "i neutralna objašnjenja za građane na hrvatskom standardnom jeziku.")

RULES = """Pravila:
1. Napiši 3 do 5 rečenica, najviše 100 riječi, u jednom odlomku. Bez naslova, natuknica i oznaka (markdown).
2. Koristi samo činjenice s popisa. Svaku brojku prepiši točno kako je napisana, zajedno s riječju ili znakom uz nju (boda, %, €). Ne zaokružuj i ne računaj nove brojke ni razlike.
3. Redoslijed: ocjena i bodovi; najslabija sastavnica s usporedbom s medijanom skupine; jake strane; upozorenja; pravilo i napomena o podacima. Dio za koji na popisu nema stavke izostavi.
4. Najslabiju sastavnicu uvedi točno ovim riječima: 'Ocjenu najviše spušta sastavnica „…”.' Jake strane uvedi riječima: 'Jake strane jedinice su: …' Ne proglašavaj ništa drugo jakom ili slabom stranom.
5. Upozorenja ne mijenjaju ocjenu: nikad ne piši da je ocjena zbog njih ograničena. O ograničenju ocjene piši samo ako na popisu postoji stavka "Pravilo".
6. Ne dodaj rečenice o izvoru, obradi ili razdoblju podataka. Ton je neutralan i opisan; bez riječi "loše", "dobro", "uspjeh" i "neuspjeh", bez savjeta, nagađanja o uzrocima, političara i stranaka.
7. Naziv jedinice piši samo u nominativu, kao subjekt rečenice ("{nom} ima ocjenu …"). Ne sklanjaj ga. U ostalim rečenicama piši "jedinica" ili naziv izostavi."""

EXAMPLE = ("PRIMJER za izmišljenu jedinicu (samo za stil; njegove brojke ne koristi):\n"
           "Općina Primjerovo za 2025. godinu ima ocjenu 2 (pod pritiskom) i 31,4 boda od 100, dok je medijan "
           "usporedne skupine 78,8 boda. Ocjenu najviše spušta sastavnica „dospjele neplaćene obveze”: na kraju "
           "godine iznose 512.300 €, odnosno 41,2 % rashoda poslovanja, uz medijan skupine od 2,0 %. Jake strane "
           "jedinice su: servis duga. Upozorenje: novca na računu ima manje nego za mjesec dana rashoda poslovanja. "
           "Ocjena je ograničena na najviše 2 jer dospjele obveze dosežu 30 % rashoda poslovanja.")


def messages(pack):
    n = pack["naziv"]
    lines = "\n".join(f"- {f['label']}: {f['value']}" for f in pack["facts"])
    user = (f"Jedinica: {n['nom']}. Napiši objašnjenje njezine ocjene financijske stabilnosti za {pack['year']}. godinu.\n\n"
            + RULES.format(**n) + f"\n\n{EXAMPLE}\n\nČINJENICE:\n{lines}")
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def feedback(unknown, issues=()):
    parts = []
    if unknown:
        parts.append("Tekst sadrži brojke kojih nema u činjenicama: " + ", ".join(unknown)
                     + ". Koristi samo brojke s popisa, prepisane točno.")
    if issues:
        parts.append("Tekst se ne slaže s činjenicama: " + "; ".join(issues)
                     + ". Najslabiju sastavnicu, jake strane i ograničenje ocjene navedi samo kako piše na popisu.")
    return " ".join(parts) + " Napiši tekst ponovno."


def template(pack):
    """Fallback text with no model: built only from the facts."""
    f = {x["label"]: x["value"] for x in pack["facts"]}
    grade = next(v for k, v in f.items() if k.startswith("Ocjena financijske"))
    parts = [f"{pack['naziv']['nom']} za {pack['year']}. godinu ima ocjenu {grade.split(' na ljestvici')[0]}."]
    if "Najslabija sastavnica" in f:
        parts.append(f"Najslabija sastavnica: {f['Najslabija sastavnica']}.")
    if "Jake strane" in f:
        parts.append(f"Jake strane: {f['Jake strane']}.")
    if "Pravilo" in f:
        parts.append(f"{f['Pravilo'][0].upper()}{f['Pravilo'][1:]}.")
    if f.get("Upozorenja", "nema upozorenja") != "nema upozorenja":
        parts.append(f"Upozorenja: {f['Upozorenja']}.")
    return " ".join(parts)


def generate(pack, call):
    """Run the model with retries; returns the text, its check and every attempt."""
    msgs = messages(pack)
    attempts = []
    for _ in range(1 + MAX_RETRIES):
        text = call(msgs).strip()
        check = verify.verify(text, pack)
        attempts.append({"text": text, "check": check})
        if check["ok"]:
            return {"text": text, "source": "ai", "check": check, "attempts": attempts}
        msgs = msgs + [{"role": "assistant", "content": text},
                       {"role": "user", "content": feedback(check["nepoznate"], check.get("sadrzaj", []))}]
    text = template(pack)
    return {"text": text, "source": "predlozak", "check": verify.verify(text, pack), "attempts": attempts}


def load_packs(year=config.LAST_YEAR):
    units = pd.read_csv(config.BUILD / "units.csv", dtype={"oib": str, "sifra": str})
    res = pd.read_parquet(config.BUILD / "results.parquet")
    return facts.build_all(units, res, year), units


# Units that test known stories: rule 1 (Sveta Marija), rule 2 (Povljana), court debt (Senj),
# stress (Primorski Dolac), investment gap (Kloštar Podravski), Zagreb, a big city, a county.
TEST_FIXED = ["Općina Sveta Marija", "Općina Povljana", "Grad Senj", "Općina Primorski Dolac",
              "Općina Kloštar Podravski", "Grad Zagreb", "Grad Split", "Istarska županija"]


def tested_oibs():
    """Units already used in earlier Kaggle tests (kaggle/results/*.json)."""
    seen = set()
    for f in (config.ROOT / "kaggle" / "results").glob("*.json"):
        out = json.loads(f.read_text(encoding="utf-8"))
        models = out.get("models") or {"model": {"results": out.get("results", [])}}
        seen |= {r["oib"] for m in models.values() for r in m["results"]}
    return seen


def pick_test_units(packs, n, seed=7, fresh=False):
    """The fixed stories plus a sample spread over all grades. With fresh=True: no fixed
    stories and no unit from an earlier test, so a prompt tuned on the old sample is
    checked on units it has not seen."""
    if fresh:
        seen = tested_oibs()
        chosen, rest = [], [p for p in packs if p["oib"] not in seen]
    else:
        chosen = [p for p in packs if p["naziv"]["nom"] in TEST_FIXED][:n]
        rest = [p for p in packs if p not in chosen]
    rng = random.Random(seed)
    by_grade = {g: [p for p in rest if p["ocjena"] == g] for g in (1, 2, 3, 4, 5)}
    g = 1
    while len(chosen) < min(n, len(packs)):
        if by_grade[g]:
            chosen.append(by_grade[g].pop(rng.randrange(len(by_grade[g]))))
        g = g % 5 + 1
    return chosen


def write_kaggle_test(n, fresh=False):
    """kaggle/gemma_test.py: the runner with the number check, the prompt code and the fact
    packs embedded, so the Kaggle notebook needs nothing but the attached model."""
    packs = pick_test_units(load_packs()[0], n, seed=11 if fresh else 7, fresh=fresh)
    here = config.ROOT / "kaggle"
    src = (here / "gemma_runner.py").read_text(encoding="utf-8")
    verify_src = (config.ROOT / "pipeline" / "verify.py").read_text(encoding="utf-8")
    prompt_src = (f"SYSTEM = {SYSTEM!r}\nRULES = {RULES!r}\nEXAMPLE = {EXAMPLE!r}\n\n\n"
                  + inspect.getsource(messages) + "\n\n" + inspect.getsource(feedback))
    out = (src.replace("# __VERIFY__", verify_src)
              .replace("# __PROMPT__", prompt_src)
              .replace('"__PACKS__"', json.dumps(json.dumps(packs, ensure_ascii=False, separators=(",", ":")),
                                                 ensure_ascii=False))
              .replace("__MAX_RETRIES__", str(MAX_RETRIES)))
    dest = here / "gemma_test.py"
    dest.write_text(out, encoding="utf-8")
    print(f"{dest} ({len(packs)} jedinica, {len(out) // 1024} KB)")


def check_output(path):
    """Re-verify a downloaded Kaggle output with the local packs and print a summary."""
    out = json.loads(Path(path).read_text(encoding="utf-8"))
    packs = {p["oib"]: p for p in load_packs()[0]}
    models = out.get("models") or {out.get("meta", {}).get("model_file", "model"): {"results": out["results"]}}
    for name, m in models.items():
        results = m["results"]
        first_ok = sum(r["attempts"][0]["check"]["ok"] for r in results)
        final_ok = 0
        print(f"===== {name} ({m.get('seconds', '?')} s)")
        for r in results:
            c = verify.verify(r["text"], packs[r["oib"]])
            final_ok += c["ok"] and r["source"] == "ai"
            print(f"[{'OK' if c['ok'] else '--'}] {r['naziv']} ({r['source']}, {len(r['attempts'])} pokušaja, "
                  f"{c['n_brojki']} brojki, nepoznate: {c['nepoznate']})\n    {r['text']}\n")
        n = len(results)
        print(f"{name}: prvi pokušaj prošao {first_ok}/{n}; AI tekst nakon ponavljanja {final_ok}/{n}\n")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--kaggle-test", type=int, metavar="N")
    ap.add_argument("--fresh", action="store_true", help="test units not used in any earlier test")
    ap.add_argument("--check", metavar="OUTPUT_JSON")
    a = ap.parse_args()
    if a.kaggle_test:
        write_kaggle_test(a.kaggle_test, fresh=a.fresh)
    if a.check:
        check_output(a.check)


if __name__ == "__main__":
    main()
