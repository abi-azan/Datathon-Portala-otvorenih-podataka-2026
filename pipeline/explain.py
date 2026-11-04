"""AI explanation of a unit's grade (PLAN §5): prompt, retries, template fallback.

    .venv/Scripts/python -m pipeline.explain --kaggle-test 20   # writes the Kaggle test script
    .venv/Scripts/python -m pipeline.explain --kaggle-test 20 --fresh   # 20 units not tested before
    .venv/Scripts/python -m pipeline.explain --check out.json   # re-verifies a downloaded Kaggle output
    .venv/Scripts/python -m pipeline.explain --kaggle-batch     # all 576 units, plus data/ai/manifest-2025.json
    .venv/Scripts/python -m pipeline.explain --kaggle-batch --skip out.json   # resume: leave out finished units
    .venv/Scripts/python -m pipeline.explain --import-batch out.json [out2.json]  # -> data/ai/objasnjenja-2025.json

Python computes the facts (pipeline/facts.py). The model writes 3-5 sentences around them,
and pipeline/verify.py rejects any text with a number that is not in the facts. A rejected
text is generated again with feedback, at most twice, and then the template is used.
The provider is a single function call(messages) -> str, so Gemma on Kaggle, a local
llama.cpp server or another API can be swapped without touching the prompt or the check.
"""
import argparse
import base64
import gzip
import hashlib
import inspect
import json
import random
import sys
from pathlib import Path

import pandas as pd

from . import config, facts, verify

MAX_RETRIES = 2

AI_DIR = config.ROOT / "data" / "ai"      # committed: manifest and imported texts
BATCH_KERNEL = "albertmari/fiskalna-karta-jls-gemma-batch"
BATCH_MODEL_SOURCE = "google/gemma-4/gguf/gemma-4-31b-it-qat-q4_0-gguf/2"
BATCH_OUTPUT = "gemma_batch_output.json"

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


def pack_sha256(pack):
    """Fingerprint of a fact pack. A stored AI text is shown only while the pack it was
    written from is unchanged (publish.explanation)."""
    s = json.dumps(pack, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def prompt_sha256():
    """Fingerprint of the prompt text the model saw (SYSTEM, RULES and EXAMPLE)."""
    s = json.dumps([SYSTEM, RULES, EXAMPLE], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


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


def write_kaggle_script(packs, dest, out_name="gemma_test_output.json", hf_models=(), run_meta=None):
    """The runner (kaggle/gemma_runner.py) with the number check, the prompt code and the fact
    packs embedded, so the Kaggle notebook needs nothing but the attached model."""
    src = (config.ROOT / "kaggle" / "gemma_runner.py").read_text(encoding="utf-8")
    verify_src = (config.ROOT / "pipeline" / "verify.py").read_text(encoding="utf-8")
    prompt_src = (f"SYSTEM = {SYSTEM!r}\nRULES = {RULES!r}\nEXAMPLE = {EXAMPLE!r}\n\n\n"
                  + inspect.getsource(messages) + "\n\n" + inspect.getsource(feedback))

    def literal(obj):
        return json.dumps(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), ensure_ascii=False)

    packs_gz = base64.b64encode(gzip.compress(
        json.dumps(packs, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), 9, mtime=0)).decode("ascii")
    out = (src.replace("# __VERIFY__", verify_src)
              .replace("# __PROMPT__", prompt_src)
              .replace("__PACKS_GZ__", packs_gz)
              .replace('"__RUN_META__"', literal(run_meta or {}))
              .replace("__OUT_NAME__", out_name)
              .replace("__MAX_RETRIES__", str(MAX_RETRIES))
              .replace("__HF_MODELS__", json.dumps([list(m) for m in hf_models])))
    dest = Path(dest)
    dest.write_text(out, encoding="utf-8")
    print(f"{dest} ({len(packs)} jedinica, {len(out) // 1024} KB)")
    return dest


def write_kaggle_test(n, fresh=False, hf=()):
    """kaggle/gemma_test.py for a test on n units. hf: "repo:file" GGUF files the notebook
    downloads from Hugging Face."""
    packs = pick_test_units(load_packs()[0], n, seed=11 if fresh else 7, fresh=fresh)
    write_kaggle_script(packs, config.ROOT / "kaggle" / "gemma_test.py",
                        hf_models=[x.split(":", 1) for x in hf])


def done_oibs(paths):
    """Units that already have a text in earlier batch outputs (an AI text or the model's
    last unverified one). Units that hit an error have no text and run again."""
    done = set()
    for p in paths:
        out = json.loads(Path(p).read_text(encoding="utf-8"))
        for m in (out.get("models") or {}).values():
            done |= {r["oib"] for r in m.get("results", []) if r.get("text")}
    return done


def write_manifest(packs, year=config.LAST_YEAR):
    """data/ai/manifest-<year>.json: the fingerprint of every unit's pack and of the prompt,
    written with the batch script, so an imported text can be matched to what the model saw."""
    AI_DIR.mkdir(parents=True, exist_ok=True)
    verify_src = (config.ROOT / "pipeline" / "verify.py").read_bytes().replace(b"\r\n", b"\n")
    manifest = {"godina": year, "prompt_sha256": prompt_sha256(),
                "verify_sha256": hashlib.sha256(verify_src).hexdigest(),
                "model_izvor": BATCH_MODEL_SOURCE, "biljeznica": BATCH_KERNEL,
                "paketi": {p["oib"]: pack_sha256(p) for p in sorted(packs, key=lambda p: p["oib"])}}
    dest = AI_DIR / f"manifest-{year}.json"
    dest.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{dest} ({len(manifest['paketi'])} paketa, prompt {manifest['prompt_sha256'][:12]})")
    return manifest


def write_kaggle_batch(skip=(), dest=None):
    """kaggle/gemma_batch.py: every unit's pack for LAST_YEAR, minus the units already done in
    the outputs listed in skip. The manifest always covers all units."""
    packs = load_packs()[0]
    manifest = write_manifest(packs)
    done = done_oibs(skip)
    todo = [p for p in packs if p["oib"] not in done]
    if done:
        print(f"preskačem {len(packs) - len(todo)} gotovih jedinica, ostaje {len(todo)}")
    meta = {"vrsta": "batch", "godina": config.LAST_YEAR, "prompt_sha256": manifest["prompt_sha256"],
            "model_izvor": BATCH_MODEL_SOURCE, "biljeznica": BATCH_KERNEL, "paketa": len(todo)}
    return write_kaggle_script(todo, dest or config.ROOT / "kaggle" / "gemma_batch.py",
                               out_name=BATCH_OUTPUT, run_meta=meta)


def model_name(gguf):
    """Display name of a Gemma 4 GGUF file, e.g. gemma-4-31B_q4_0-it.gguf -> Gemma 4 31B."""
    g = gguf.lower()
    for key, name in (("26b", "Gemma 4 26B-A4B"), ("31b", "Gemma 4 31B"), ("12b", "Gemma 4 12B"), ("e4b", "Gemma 4 E4B")):
        if key in g:
            return name
    return gguf


def import_batch(paths, dest=None, year=config.LAST_YEAR):
    """data/ai/objasnjenja-<year>.json from downloaded batch outputs. pack_sha256 comes from the
    manifest written with the batch script, so it records the pack the model saw. A unit that
    appears more than once keeps its first AI text; a later output only replaces an
    unverified one. Warns when a current pack no longer matches the manifest."""
    manifest = json.loads((AI_DIR / f"manifest-{year}.json").read_text(encoding="utf-8"))
    current = {p["oib"]: pack_sha256(p) for p in load_packs(year)[0]}
    texts, runs = {}, []
    for path in paths:
        raw = Path(path).read_bytes()
        out = json.loads(raw.decode("utf-8"))
        meta = out.get("meta", {})
        if meta.get("prompt_sha256") not in (None, manifest["prompt_sha256"]):
            print(f"UPOZORENJE: {path}: prompt se razlikuje od manifesta")
        runs.append({"datoteka": Path(path).name, "sha256": hashlib.sha256(raw).hexdigest(),
                     "djelomicno": bool(out.get("partial")), "llama_cpp_commit": meta.get("llama_cpp_commit"),
                     "gpu": (meta.get("gpu") or "").replace("\n", ", "), "sekundi": meta.get("seconds_total"),
                     "modeli": list(out.get("models", {}))})
        for gguf, m in out.get("models", {}).items():
            for r in m.get("results", []):
                if not r.get("text") or r["oib"] not in manifest["paketi"]:
                    continue
                old = texts.get(r["oib"])
                if old and (old["izvor"] == "ai" or r.get("source") != "ai"):
                    continue
                texts[r["oib"]] = {"tekst": r["text"], "pack_sha256": manifest["paketi"][r["oib"]],
                                   "pokusaja": len(r.get("attempts", [])),
                                   "izvor": "ai" if r.get("source") == "ai" else "neprovjereno",
                                   "model": model_name(gguf), "gguf": gguf}
    stale = sorted(o for o, t in texts.items() if current.get(o) != t["pack_sha256"])
    if stale:
        print(f"UPOZORENJE: {len(stale)} paketa se razlikuje od manifesta; ti tekstovi idu na predložak: {stale[:10]}")
    ggufs = sorted({t["gguf"] for t in texts.values()})
    result = {
        "meta": {"godina": year, "modeli": [model_name(g) for g in ggufs], "gguf": ggufs,
                 "model_izvor": manifest["model_izvor"], "biljeznica": manifest["biljeznica"],
                 "prompt_sha256": manifest["prompt_sha256"], "verify_sha256": manifest["verify_sha256"],
                 "llama_cpp_commit": next((r["llama_cpp_commit"] for r in runs if r["llama_cpp_commit"]), None),
                 "pokretanja": runs, "uvezeno": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds"),
                 "jedinica": len(manifest["paketi"]), "tekstova": len(texts),
                 "ai": sum(t["izvor"] == "ai" for t in texts.values())},
        "tekstovi": {o: texts[o] for o in sorted(texts)},
    }
    dest = Path(dest) if dest else AI_DIR / f"objasnjenja-{year}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    m = result["meta"]
    print(f"{dest}: {m['tekstova']}/{m['jedinica']} tekstova, od toga {m['ai']} AI (provjereno na Kaggleu)")
    return result


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
    ap.add_argument("--hf", action="append", default=[], metavar="REPO:FILE",
                    help="GGUF on Hugging Face that the notebook downloads, e.g. "
                         "unsloth/gemma-4-31B-it-qat-GGUF:gemma-4-31B-it-qat-UD-Q4_K_XL.gguf")
    ap.add_argument("--check", metavar="OUTPUT_JSON")
    ap.add_argument("--kaggle-batch", action="store_true",
                    help="script for every unit (kaggle/gemma_batch.py) and data/ai/manifest-<year>.json")
    ap.add_argument("--skip", action="append", default=[], metavar="OUTPUT_JSON",
                    help="with --kaggle-batch: leave out units that already have a text in this output")
    ap.add_argument("--import-batch", nargs="+", metavar="OUTPUT_JSON",
                    help="downloaded batch outputs -> data/ai/objasnjenja-<year>.json")
    ap.add_argument("--out", metavar="JSON", help="with --import-batch: write here instead of data/ai/")
    a = ap.parse_args()
    if a.import_batch:
        import_batch(a.import_batch, dest=a.out)
    if a.kaggle_test:
        write_kaggle_test(a.kaggle_test, fresh=a.fresh, hf=a.hf)
    if a.kaggle_batch:
        write_kaggle_batch(skip=a.skip)
    if a.check:
        check_output(a.check)


if __name__ == "__main__":
    main()
