"""AI explanation of a unit's grade (PLAN §5): prompt, retries, template fallback.

    .venv/Scripts/python -m pipeline.explain --kaggle-test 20   # writes the Kaggle test script
    .venv/Scripts/python -m pipeline.explain --kaggle-test 20 --fresh   # 20 units not tested before
    .venv/Scripts/python -m pipeline.explain --kaggle-test 20 --kontekst 12   # at least 12 with context
    .venv/Scripts/python -m pipeline.explain --check out.json   # re-verifies a downloaded Kaggle output
    .venv/Scripts/python -m pipeline.explain --kaggle-batch     # all 576 units, plus data/ai/manifest-2025.json
    .venv/Scripts/python -m pipeline.explain --kaggle-batch --skip out.json   # resume: leave out units whose text fits their pack
    .venv/Scripts/python -m pipeline.explain --import-batch out.json [out2.json]  # -> data/ai/objasnjenja-2025.json

A batch output is matched to the packs its texts were written from by fingerprint (pack_sha256),
taken from the output itself (meta.paketi) or, for an output made before that field existed, from
its frozen sidecar kaggle/results/<name>.paketi.json (output_fingerprints). Never from
data/ai/manifest-<year>.json, which every --kaggle-batch rewrites with the current packs.

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
CONTEXT_OPENING = "Za kontekst, što ne ulazi u ocjenu:"    # rule 8, the example and the template

AI_DIR = config.ROOT / "data" / "ai"      # committed: manifest and imported texts
RESULTS_DIR = config.ROOT / "kaggle" / "results"   # committed: raw Kaggle outputs, byte for byte
SIDECAR = ".paketi.json"                  # <output>.paketi.json: frozen fingerprints of a legacy output
BATCH_KERNEL = "albertmari/fiskalna-karta-jls-gemma-batch"
BATCH_MODEL_SOURCE = "google/gemma-4/gguf/gemma-4-31b-it-qat-q4_0-gguf/2"
BATCH_OUTPUT = "gemma_batch_output.json"

SYSTEM = ("Ti si urednik javnog portala o financijama općina, gradova i županija. Pišeš kratka, točna "
          "i neutralna objašnjenja za građane na hrvatskom standardnom jeziku.")

RULES = """Pravila:
1. Napiši 3 do 5 rečenica, najviše 100 riječi, u jednom odlomku. Bez naslova, natuknica i oznaka (markdown).
2. Koristi samo činjenice s popisa. Svaku brojku prepiši točno kako je napisana, zajedno s riječju ili znakom uz nju (boda, %, €). Ne zaokružuj i ne računaj nove brojke ni razlike.
3. Redoslijed: ocjena i bodovi; najslabija sastavnica s usporedbom s medijanom skupine; jake strane; upozorenja; pravilo i napomena o podacima; kontekst. Dio za koji na popisu nema stavke izostavi.
4. Najslabiju sastavnicu uvedi točno ovim riječima: 'Ocjenu najviše spušta sastavnica „…”.' Jake strane uvedi riječima: 'Jake strane jedinice su: …' Ne proglašavaj ništa drugo jakom ili slabom stranom.
5. Upozorenja ne mijenjaju ocjenu: nikad ne piši da je ocjena zbog njih ograničena. O ograničenju ocjene piši samo ako na popisu postoji stavka "Pravilo".
6. Ne dodaj rečenice o izvoru, obradi ili razdoblju podataka. Ton je neutralan i opisan; bez riječi "loše", "dobro", "uspjeh" i "neuspjeh", bez savjeta, nagađanja o uzrocima, političara i stranaka.
7. Naziv jedinice piši samo u nominativu, kao subjekt rečenice ("{nom} ima ocjenu …"). Ne sklanjaj ga. U ostalim rečenicama piši "jedinica" ili naziv izostavi.
8. Stavke "Kontekst" ne ulaze u ocjenu. Ako ih ima, dodaj na kraj još jednu rečenicu koja počinje riječima 'Za kontekst, što ne ulazi u ocjenu:' i prepisuje njihove vrijednosti. Ne povezuj ih s ocjenom ni sa sastavnicama i ne navodi uzroke."""

EXAMPLE = ("PRIMJER za izmišljenu jedinicu (samo za stil; njegove brojke ne koristi):\n"
           "Općina Primjerovo za 2025. godinu ima ocjenu 2 (pod pritiskom) i 31,4 boda od 100, dok je medijan "
           "usporedne skupine 78,8 boda. Ocjenu najviše spušta sastavnica „dospjele neplaćene obveze”: na kraju "
           "godine iznose 512.300 €, odnosno 41,2 % rashoda poslovanja, uz medijan skupine od 2,0 %. Jake strane "
           "jedinice su: servis duga. Upozorenje: novca na računu ima manje nego za mjesec dana rashoda poslovanja. "
           "Ocjena je ograničena na najviše 2 jer dospjele obveze dosežu 30 % rashoda poslovanja. Za kontekst, što "
           "ne ulazi u ocjenu: broj stanovnika od 2021. do 2025. smanjio se za 9,4 %, što je ispod medijana "
           "skupine (−2,1 %).")


def pack_sha256(pack):
    """Fingerprint of a fact pack. A stored AI text is shown only while the pack it was
    written from is unchanged (publish.explanation)."""
    s = json.dumps(pack, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def prompt_sha256():
    """Fingerprint of the prompt text the model saw (SYSTEM, RULES and EXAMPLE)."""
    s = json.dumps([SYSTEM, RULES, EXAMPLE], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _sha256_lf(raw):
    """sha256 of file bytes with CRLF read as LF, so a Windows checkout (autocrlf) gives the same value."""
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def verify_sha256():
    """Fingerprint of the number check (pipeline/verify.py) as it is now."""
    return _sha256_lf((config.ROOT / "pipeline" / "verify.py").read_bytes())


def sidecar_path(path):
    """kaggle/results/<name>.json -> kaggle/results/<name>.paketi.json."""
    path = Path(path)
    return path.with_name(path.stem + SIDECAR)


def output_fingerprints(path, raw=None):
    """What a batch output's texts were written from: {"paketi": {oib: pack_sha256}, "prompt_sha256",
    "verify_sha256" (the check on Kaggle, if known), "commit" (of the script, if known), "izvor"}.

    From the output's own meta.paketi, written into the script together with the packs, or, for an
    output made before that field existed, from its sidecar <name>.paketi.json, which is frozen and
    names the output's sha256. Never from the manifest: every --kaggle-batch rewrites it with the
    current packs, which would stamp old texts with new fingerprints. An output with neither, or
    without the prompt fingerprint, is refused."""
    path = Path(path)
    raw = path.read_bytes() if raw is None else raw
    meta = json.loads(raw.decode("utf-8")).get("meta") or {}
    if meta.get("paketi"):
        fp = {"paketi": meta["paketi"], "prompt_sha256": meta.get("prompt_sha256"),
              "verify_sha256": meta.get("verify_sha256"), "commit": meta.get("commit"), "izvor": "meta.paketi"}
    else:
        side = sidecar_path(path)
        if not side.exists():
            raise SystemExit(f"{path}: izlaz nema meta.paketi ni datoteku {side.name}, pa se ne zna iz kojih su paketa "
                             "tekstovi napisani. Manifest se za to ne koristi, jer ga svaki --kaggle-batch prepisuje.")
        sc = json.loads(side.read_text(encoding="utf-8"))
        if sc.get("izlaz_sha256") != _sha256_lf(raw):
            raise SystemExit(f"{side.name} ne pripada izlazu {path}: sha256 izlaza se ne slaže")
        if meta.get("prompt_sha256") not in (None, sc.get("prompt_sha256")):
            raise SystemExit(f"{side.name}: prompt se razlikuje od onoga u izlazu {path}")
        fp = {"paketi": sc["paketi"], "prompt_sha256": sc.get("prompt_sha256"),
              "verify_sha256": sc.get("verify_sha256"), "commit": sc.get("commit"), "izvor": side.name}
    if not fp["prompt_sha256"]:
        raise SystemExit(f"{path}: nema otiska prompta (prompt_sha256)")
    return fp


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
                     + ". Najslabiju sastavnicu, jake strane, ograničenje ocjene i kontekst navedi samo kako piše na "
                     "popisu, a kontekst ne povezuj s ocjenom.")
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
    # "Kontekst: broj stanovnika" + "od 2021. do 2025. smanjio se za 8,3 %, …" -> one closing sentence
    ctx = [x for x in pack["facts"] if x.get("kontekst") and ": " in x["label"]]
    if ctx:
        parts.append(f"{CONTEXT_OPENING} "
                     + ", a ".join(f"{x['label'].split(': ', 1)[1]} {x['value']}" for x in ctx) + ".")
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
    for f in RESULTS_DIR.glob("*.json"):
        if f.name.endswith(SIDECAR):
            continue
        out = json.loads(f.read_text(encoding="utf-8"))
        models = out.get("models") or {"model": {"results": out.get("results", [])}}
        seen |= {r["oib"] for m in models.values() for r in m["results"]}
    return seen


def has_context(pack):
    """True when the pack has a context item (facts.context_facts, "kontekst": true)."""
    return any(f.get("kontekst") for f in pack["facts"])


def pick_test_units(packs, n, seed=7, fresh=False, min_context=0):
    """The fixed stories plus a sample spread over all grades. With fresh=True: no fixed
    stories and no unit from an earlier test, so a prompt tuned on the old sample is
    checked on units it has not seen. With min_context: at least that many units with a
    context item (has_context), picked first and spread over the grades; the rest as before."""
    if min_context:
        seen = tested_oibs() if fresh else set()
        chosen = [] if fresh else [p for p in packs if p["naziv"]["nom"] in TEST_FIXED][:n]
        rng = random.Random(seed)
        need = max(0, min_context - sum(map(has_context, chosen)))
        # first the missing context units, then the rest from every unit; both spread over the grades
        for only_context, target in ((True, min(n, len(chosen) + need)), (False, n)):
            pool = [p for p in packs if p not in chosen and p["oib"] not in seen and (has_context(p) or not only_context)]
            by_grade = {g: [p for p in pool if p["ocjena"] == g] for g in (1, 2, 3, 4, 5)}
            g = 1
            while len(chosen) < target and any(by_grade.values()):
                if by_grade[g]:
                    chosen.append(by_grade[g].pop(rng.randrange(len(by_grade[g]))))
                g = g % 5 + 1
        return chosen
    if fresh:
        seen = tested_oibs()
        chosen, rest = [], [p for p in packs if p["oib"] not in seen]
        if len(rest) < n:
            raise SystemExit(f"--fresh: traženo je {n} neisprobanih jedinica, a samo {len(rest)} od {len(packs)} nije ni u "
                             f"jednom izlazu u {RESULTS_DIR.relative_to(config.ROOT).as_posix()}/ (batch za 576 jedinica "
                             "pokriva sve). Pokreni test bez --fresh ili s manjim N.")
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


def write_kaggle_test(n, fresh=False, hf=(), min_context=0):
    """kaggle/gemma_test.py for a test on n units. hf: "repo:file" GGUF files the notebook
    downloads from Hugging Face. min_context: at least that many units with a context item."""
    packs = pick_test_units(load_packs()[0], n, seed=11 if fresh else 7, fresh=fresh, min_context=min_context)
    print(f"uzorak: {len(packs)} jedinica, od toga {sum(map(has_context, packs))} s kontekstom")
    write_kaggle_script(packs, config.ROOT / "kaggle" / "gemma_test.py",
                        hf_models=[x.split(":", 1) for x in hf])


def done_oibs(paths, current):
    """Units whose text in an earlier batch output (an AI text or the model's last unverified one)
    was written from the pack they have now. current: {oib: pack_sha256} of today's packs. A unit
    whose pack changed since (e.g. after a new MF release) needs a new text and runs again, as does
    a unit that hit an error (no text). The fingerprints come from output_fingerprints."""
    done, changed = set(), set()
    for p in paths:
        fp = output_fingerprints(p)
        if fp["prompt_sha256"] != prompt_sha256():
            raise SystemExit(f"{p}: prompt se promijenio od tog izlaza: pokreni cijeli batch ponovno, bez --skip")
        out = json.loads(Path(p).read_text(encoding="utf-8"))
        for m in (out.get("models") or {}).values():
            for r in m.get("results", []):
                if r.get("text"):
                    fits = fp["paketi"].get(r["oib"]) == current.get(r["oib"])
                    (done if fits else changed).add(r["oib"])
    changed -= done
    if changed:
        print(f"{len(changed)} jedinica ima tekst, ali se paket od tada promijenio: generiraju se ponovno "
              f"{sorted(changed)[:10]}")
    return done


def write_manifest(packs, year=config.LAST_YEAR):
    """data/ai/manifest-<year>.json: the fingerprint of every unit's current pack, of the prompt and
    of the check, written with the batch script. It records the run; the import does not read
    fingerprints from it, because the next --kaggle-batch rewrites it (output_fingerprints)."""
    AI_DIR.mkdir(parents=True, exist_ok=True)
    dest = AI_DIR / f"manifest-{year}.json"
    manifest = {"godina": year, "prompt_sha256": prompt_sha256(), "verify_sha256": verify_sha256(),
                "model_izvor": BATCH_MODEL_SOURCE, "biljeznica": BATCH_KERNEL,
                "paketi": {p["oib"]: pack_sha256(p) for p in sorted(packs, key=lambda p: p["oib"])}}
    dest.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{dest} ({len(manifest['paketi'])} paketa, prompt {manifest['prompt_sha256'][:12]})")
    return manifest


def write_kaggle_batch(skip=(), dest=None):
    """kaggle/gemma_batch.py: every unit's pack for LAST_YEAR, minus the units whose text in one of
    the outputs listed in skip still fits their pack. The manifest always covers all units."""
    packs = load_packs()[0]
    current = {p["oib"]: pack_sha256(p) for p in packs}
    done = done_oibs(skip, current)
    manifest = write_manifest(packs)
    todo = [p for p in packs if p["oib"] not in done]
    if skip:
        print(f"preskačem {len(done)} jedinica s tekstom za nepromijenjen paket, ostaje {len(todo)}")
    # the output carries the fingerprint of every pack it was given (and of the check), so an
    # import does not have to trust a manifest that a later run may have rewritten
    meta = {"vrsta": "batch", "godina": config.LAST_YEAR, "prompt_sha256": manifest["prompt_sha256"],
            "verify_sha256": manifest["verify_sha256"],
            "model_izvor": BATCH_MODEL_SOURCE, "biljeznica": BATCH_KERNEL, "paketa": len(todo),
            "paketi": {p["oib"]: current[p["oib"]] for p in todo}}
    return write_kaggle_script(todo, dest or config.ROOT / "kaggle" / "gemma_batch.py",
                               out_name=BATCH_OUTPUT, run_meta=meta)


def model_name(gguf):
    """Display name of a Gemma 4 GGUF file, e.g. gemma-4-31B_q4_0-it.gguf -> Gemma 4 31B."""
    g = gguf.lower()
    for key, name in (("26b", "Gemma 4 26B-A4B"), ("31b", "Gemma 4 31B"), ("12b", "Gemma 4 12B"), ("e4b", "Gemma 4 E4B")):
        if key in g:
            return name
    return gguf


def pick_attempt(r, pack):
    """(text, attempt number, passes) for one stored result, checked with today's verify.py: the
    earliest stored attempt that passes, else the final text."""
    attempts = r.get("attempts") or []
    for i, a in enumerate(attempts, 1):
        if a.get("text") and verify.verify(a["text"], pack)["ok"]:
            return a["text"], i, True
    last = len(attempts) if attempts and attempts[-1].get("text") == r["text"] else None
    return r["text"], last, verify.verify(r["text"], pack)["ok"]


def _one(values, what):
    """The single value all imported outputs agree on (None when none states it)."""
    values = {v for v in values if v is not None}
    if len(values) > 1:
        raise SystemExit(f"izlazi se razlikuju u {what}: {sorted(values)}; uvezi ih odvojeno")
    return next(iter(values), None)


def import_batch(paths, dest=None, year=config.LAST_YEAR):
    """data/ai/objasnjenja-<year>.json from downloaded batch outputs (the raw files stay as they are).

    pack_sha256 is the fingerprint of the pack the model saw, from the output itself or its frozen
    sidecar (output_fingerprints), never from the manifest. Every stored text is checked again with
    today's pipeline/verify.py against today's pack: the earliest stored attempt that passes becomes
    the AI text (izvor "ai"); otherwise the final text is kept as "neprovjereno". A text whose pack
    changed since cannot be checked against the pack it was written from, so it is "neprovjereno"
    (publish shows the template for it anyway). A unit in more than one output keeps its first AI
    text; a later output replaces only an unverified or outdated one. meta.verify_sha256 is the
    check used here; each run keeps the one used on Kaggle."""
    packs = {p["oib"]: p for p in load_packs(year)[0]}
    current = {o: pack_sha256(p) for o, p in packs.items()}
    texts, runs = {}, []

    def rank(t):
        return (t["pack_sha256"] == current[t["oib"]], t["izvor"] == "ai")

    for path in paths:
        raw = Path(path).read_bytes()
        out = json.loads(raw.decode("utf-8"))
        meta = out.get("meta", {})
        fp = output_fingerprints(path, raw)
        seen = fp["paketi"]
        runs.append({"datoteka": Path(path).name, "sha256": hashlib.sha256(raw).hexdigest(),
                     "djelomicno": bool(out.get("partial")), "llama_cpp_commit": meta.get("llama_cpp_commit"),
                     "gpu": (meta.get("gpu") or "").replace("\n", ", "), "sekundi": meta.get("seconds_total"),
                     "modeli": list(out.get("models", {})),
                     "otisci_paketa": fp["izvor"], "prompt_sha256": fp["prompt_sha256"],
                     "verify_sha256_kaggle": fp["verify_sha256"], "commit_skripte": fp["commit"],
                     "model_izvor": meta.get("model_izvor"), "biljeznica": meta.get("biljeznica")})
        missing = []
        for gguf, m in out.get("models", {}).items():
            for r in m.get("results", []):
                o = r["oib"]
                if not r.get("text") or o not in packs:
                    continue
                if o not in seen:
                    missing.append(o)
                    continue
                if seen[o] == current[o]:
                    text, attempt, ok = pick_attempt(r, packs[o])
                else:
                    text, attempt, ok = r["text"], None, False
                entry = {"oib": o, "tekst": text, "pack_sha256": seen[o], "pokusaja": len(r.get("attempts", [])),
                         "pokusaj": attempt, "izvor": "ai" if ok else "neprovjereno",
                         "izvor_kaggle": "ai" if r.get("source") == "ai" else "neprovjereno",
                         "model": model_name(gguf), "gguf": gguf}
                if o not in texts or rank(entry) > rank(texts[o]):
                    texts[o] = entry
        if missing:
            print(f"UPOZORENJE: {path}: {len(missing)} tekstova nema otisak paketa i nisu uvezeni: {missing[:10]}")
    prompt = _one((r["prompt_sha256"] for r in runs), "promptu")
    if prompt != prompt_sha256():
        print("UPOZORENJE: prompt se promijenio od batcha; stranica metodologije to navodi")
    stale = sorted(o for o, t in texts.items() if current[o] != t["pack_sha256"])
    if stale:
        print(f"UPOZORENJE: {len(stale)} paketa se promijenilo od batcha; ti tekstovi idu na predložak: {stale[:10]}")
    rescued = sorted(t["oib"] for t in texts.values() if t["izvor"] == "ai" and t["izvor_kaggle"] != "ai")
    if rescued:
        print(f"{len(rescued)} tekstova koje je provjera na Kaggleu odbila prolazi današnju provjeru: "
              + ", ".join(packs[o]["naziv"]["nom"] for o in rescued))
    ggufs = sorted({t["gguf"] for t in texts.values()})
    result = {
        "meta": {"godina": year, "modeli": [model_name(g) for g in ggufs], "gguf": ggufs,
                 "model_izvor": next((r["model_izvor"] for r in runs if r["model_izvor"]), None),
                 "biljeznica": next((r["biljeznica"] for r in runs if r["biljeznica"]), None),
                 "prompt_sha256": prompt, "verify_sha256": verify_sha256(),
                 "verify_sha256_kaggle": sorted({r["verify_sha256_kaggle"] for r in runs if r["verify_sha256_kaggle"]}),
                 # the commit the batch script was generated from, only when every run states the same one
                 "commit_skripte": runs[0]["commit_skripte"] if len({r["commit_skripte"] for r in runs}) == 1 else None,
                 "llama_cpp_commit": next((r["llama_cpp_commit"] for r in runs if r["llama_cpp_commit"]), None),
                 "pokretanja": runs, "uvezeno": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds"),
                 "jedinica": len(packs), "tekstova": len(texts),
                 "ai": sum(t["izvor"] == "ai" for t in texts.values())},
        "tekstovi": {o: {k: v for k, v in texts[o].items() if k != "oib"} for o in sorted(texts)},
    }
    dest = Path(dest) if dest else AI_DIR / f"objasnjenja-{year}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    m = result["meta"]
    print(f"{dest}: {m['tekstova']}/{m['jedinica']} tekstova, od toga {m['ai']} AI "
          f"(provjereno pri uvozu, verify {m['verify_sha256'][:12]})")
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
    sys.stderr.reconfigure(encoding="utf-8")       # SystemExit messages are Croatian too
    ap = argparse.ArgumentParser()
    ap.add_argument("--kaggle-test", type=int, metavar="N")
    ap.add_argument("--fresh", action="store_true", help="test units not used in any earlier test")
    ap.add_argument("--kontekst", type=int, default=0, metavar="K",
                    help="with --kaggle-test: at least K units whose pack has a context item")
    ap.add_argument("--hf", action="append", default=[], metavar="REPO:FILE",
                    help="GGUF on Hugging Face that the notebook downloads, e.g. "
                         "unsloth/gemma-4-31B-it-qat-GGUF:gemma-4-31B-it-qat-UD-Q4_K_XL.gguf")
    ap.add_argument("--check", metavar="OUTPUT_JSON")
    ap.add_argument("--kaggle-batch", action="store_true",
                    help="script for every unit (kaggle/gemma_batch.py) and data/ai/manifest-<year>.json")
    ap.add_argument("--skip", action="append", default=[], metavar="OUTPUT_JSON",
                    help="with --kaggle-batch: leave out units whose text in this output was written from "
                         "their current pack")
    ap.add_argument("--import-batch", nargs="+", metavar="OUTPUT_JSON",
                    help="downloaded batch outputs -> data/ai/objasnjenja-<year>.json")
    ap.add_argument("--out", metavar="JSON", help="with --import-batch: write here instead of data/ai/")
    a = ap.parse_args()
    if a.import_batch:
        import_batch(a.import_batch, dest=a.out)
    if a.kaggle_test:
        write_kaggle_test(a.kaggle_test, fresh=a.fresh, hf=a.hf, min_context=a.kontekst)
    if a.kaggle_batch:
        write_kaggle_batch(skip=a.skip)
    if a.check:
        check_output(a.check)


if __name__ == "__main__":
    main()
