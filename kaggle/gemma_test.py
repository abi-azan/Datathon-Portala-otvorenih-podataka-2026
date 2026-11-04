"""Gemma 4 on a Kaggle GPU: AI explanations with a number check (Fiskalna karta JLS).

Generated from kaggle/gemma_runner.py by `python -m pipeline.explain --kaggle-test N` (test,
kaggle/gemma_test.py) or `--kaggle-batch` (all units, kaggle/gemma_batch.py). Do not edit
the generated scripts by hand.

- Models: every attached Gemma 4 QAT Q4_0 GGUF (Kaggle model data sources, Apache-2.0), smallest
  first. A model larger than one T4 is split by layers across both T4s.
- Runtime: llama.cpp (MIT), built from source for the T4 (CUDA arch 75), served by llama-server.
- Every text is checked: each number must appear in the unit's fact pack. A failed text is
  generated again with feedback, at most 2 times, and then the template is used.
- The output is written after every unit, so a stopped run can be resumed with --skip.
Output: /kaggle/working/gemma_test_output.json
"""
import base64
import glob
import gzip
import json
import os
import subprocess
import sys
import time
import urllib.request

# ---- number check: pipeline/verify.py, embedded verbatim ----
"""Number check for AI texts (PLAN §5): every number in the text must appear in the fact pack.

The check is deliberately strict. A rounded number ("28 %" where the facts say "27,6 %"), a
computed one (a difference of two facts) or one written the English way ("41.7") fails, and
the text is generated again or replaced by the template. Numbers written as words are not
checked. The context (population, income) has its own rules: context_issues.

This file has no imports outside the standard library, because the Kaggle notebook embeds
it verbatim.
"""
import re
from decimal import Decimal, InvalidOperation

# Any run of digits joined by "." or "," (or a non-breaking space inside thousands) is one token,
# so "41.7" or "31.12.2025" cannot hide behind their first part. A plain space is not a
# thousands separator: "za 4 125 €" stays two numbers. A trailing ordinal dot ("2025.") is not
# part of the token.
NUMBER = re.compile(r"(?<![\d,.])-?\d+(?:[.,  ]\d+)*")
# The only accepted spellings: Croatian thousands groups and a decimal comma.
CROATIAN = re.compile(r"-?(?:\d{1,3}(?:[.  ]\d{3})+|\d+)(?:,\d+)?")


def normalise(token):
    """Decimal value of a Croatian-format number, or None for any other spelling."""
    if not CROATIAN.fullmatch(token):
        return None
    t = re.sub(r"[.  ]", "", token).replace(",", ".")
    try:
        return Decimal(t).normalize()
    except InvalidOperation:
        return None


def numbers(text):
    """All numbers in a text: (normalised Decimal or None if malformed, token)."""
    out = []
    for m in NUMBER.finditer(text):
        token = m.group(0).strip()
        v = normalise(token)
        out.append((abs(v) if v is not None else None, token))   # the sign is carried by words ("manjak")
    return out


def allowed(pack):
    vals = set()
    for f in pack["facts"]:
        for part in (f["label"], f["value"]):
            vals |= {v for v, _ in numbers(part) if v is not None}
    return vals


# Grades: after every "ocjen*" word, the first standalone digit 1-5 in the same sentence is
# a claimed grade and must be this year's or last year's. The scale wording "od 1 ... do 5"
# is removed first, and ordinals ("1. mjesto"), decimals and amounts ("1.767.926 €") are not grades.
# The search runs to the end of the sentence with no fixed length: a window of 120 characters
# once cut "3,8" after its "3", which was then read as a grade (11 correct texts rejected, 4.11.).
SCALE = re.compile(r"\bod\s+1\b[^.;]{0,40}?\bdo\s+5\b", re.IGNORECASE)
GRADE_WORD = re.compile(r"\bocjen\w*", re.IGNORECASE)
GRADE_DIGIT = re.compile(r"(?<![\d,.])([1-5])(?!\d)(?![,.]\d)(?!\.\s*[a-zčćđšž])")
SENTENCE_END = re.compile(r"[.!?;]\s+(?=[A-ZČĆĐŠŽ])")


def claimed_grades(text):
    t = SCALE.sub(" ", text)
    out = []
    for m in GRADE_WORD.finditer(t):
        rest = t[m.end():]
        end = SENTENCE_END.search(rest)
        d = GRADE_DIGIT.search(rest[:end.start() + 1] if end else rest)
        if d:
            out.append(d.group(1))
    return out


# Content claims the prompt asks for with fixed phrases, so they can be checked (Gemma test v4):
# the weakest component, the strengths, and a capped grade, which only rule 2 can cause.
WEAKEST = re.compile(r"spušta sastavnica\s+[„\"“]([^”\"“]+)[”\"“]", re.IGNORECASE)
STRENGTHS = re.compile(r"jake strane jedinice su:\s*([^.;]+)", re.IGNORECASE)
CAPPED = re.compile(r"\bograničen\w*", re.IGNORECASE)


def content_issues(text, pack):
    facts = {f["label"]: f["value"] for f in pack["facts"]}
    issues = []
    for name in WEAKEST.findall(text):
        if name.strip().lower() != facts.get("Najslabija sastavnica", "").lower():
            issues.append(f"najslabija sastavnica „{name.strip()}”")
    strong = facts.get("Jake strane", "").lower()
    for listed in STRENGTHS.findall(text):
        for part in re.split(r",| i | te ", listed):
            part = part.strip().lower()
            if part and part not in strong:
                issues.append(f"jaka strana „{part}”")
    if CAPPED.search(text) and "Pravilo" not in facts:
        issues.append("ograničenje ocjene bez pravila")
    return issues + context_issues(text, pack)


# Context (facts.context_facts: population change, net income per inhabitant; items marked
# "kontekst": true) never enters the score. A sentence about it needs its item in the pack, uses only
# the context numbers, with their sign and their side of the median, and does not tie them to the
# grade. The texts written before context existed mention none of these words (576 of 576, 4.11.).
POPULATION = re.compile(r"\b(?:stanovništv\w*|broj\w*\s+stanovnika|iseljav\w*|doseljav\w*|migracij\w*|"
                        r"demograf\w*|depopulacij\w*)", re.IGNORECASE)
INCOME = re.compile(r"\b(?:dohod\w*|dohot\w*)", re.IGNORECASE)
CONTEXT_WORD = re.compile(r"\bkontekst\w*", re.IGNORECASE)
UP = r"poveća\w*|porast\w*|porasl\w*|narast\w*|narasl\w*|rast\w*"
DOWN = r"smanj\w*|pad\w*|pao|pala|palo|opao|opala|opalo|opada\w*"
TREND = re.compile(rf"\b(?:{UP}|{DOWN})\b", re.IGNORECASE)
# a direction word bound to the number after the next "za": "smanjio se za 8,3 %",
# "porastao je od 2021. do 2025. za 6,2 %"
DIRECTION = re.compile(rf"\b(?:({UP})|({DOWN}))(?:\s+\S+){{0,6}}?\s+za\s+[+−-]?(\d+(?:[.,]\d+)*)", re.IGNORECASE)
SIDE = re.compile(r"\b(iznad|ispod)\s+medijan", re.IGNORECASE)
# a link between the context and the grade or its components; negated phrases ("ne ulazi u ocjenu",
# "ne objašnjava je", "nisu dio ocjene", "ne utječe na ocjenu") are taken out first
NEGATED = re.compile(r"\b(?:ne|nisu|nije|niti)\s+(?:\w+\s+){0,3}?(?:ocjen\w*|(?:utje|utječ|objašnjav|uzrok|doprinos|"
                     r"pridonos|odraž|povezan)\w*(?:\s+(?:na|u|s|sa|za)\s+(?:\w+\s+)?ocjen\w*)?)", re.IGNORECASE)
CAUSAL = re.compile(r"\b(?:ocjen\w*|sastavnic\w*|zbog|uslijed|uzrok\w*|posljedic\w*|utje\w*|utječ\w*|doprinos\w*|"
                    r"pridonos\w*|objašnjav\w*|stoga|zato|rezultir\w*|odraž\w*|povezan\w*)", re.IGNORECASE)


def sentences(text):
    out, start = [], 0
    for m in SENTENCE_END.finditer(text):
        out.append(text[start:m.end()])
        start = m.end()
    return out + [text[start:]]


def signed_values(text):
    """{(abs value, +1 | -1, token)} a text claims: an explicit sign (+6,2 %, −8,3 %, -8,3 %) or a
    direction word bound to the number (smanjio se za 8,3 %)."""
    out = set()
    for m in NUMBER.finditer(text):
        token = m.group(0).strip()
        before = text[m.start() - 1] if m.start() else ""
        sign = -1 if token.startswith("-") else {"+": 1, "−": -1}.get(before)
        v = normalise(token)
        if sign and v is not None:
            out.add((abs(v), sign, token if token.startswith("-") else before + token))
    for m in DIRECTION.finditer(text):
        v = normalise(m.group(3))
        if v is not None:
            out.add((abs(v), 1 if m.group(1) else -1, m.group(0)))
    return out


def context_issues(text, pack):
    ctx = [f for f in pack["facts"] if f.get("kontekst")]
    labels = " ".join(f["label"].lower() for f in ctx)
    ctx_text = " ".join(f["value"] for f in ctx)
    issues = []
    about = []
    for s in sentences(text):
        pop = POPULATION.search(s) and (TREND.search(s) or "%" in s)
        inc = INCOME.search(s)
        if not (pop or inc or CONTEXT_WORD.search(s)):
            continue
        about.append(s)
        if pop and "stanovnik" not in labels:
            issues.append("kretanje stanovništva bez stavke u činjenicama")
        if inc and "dohod" not in labels:
            issues.append("dohodak bez stavke u činjenicama")
        if not ctx and not (pop or inc):
            issues.append("kontekst bez stavke u činjenicama")
    if not about or not ctx:
        return issues
    # numbers: only from the context items (and the unit line, e.g. its population); a number that
    # is nowhere in the pack is already in "nepoznate"
    in_pack = allowed(pack)
    ok_vals = allowed({"facts": ctx + [f for f in pack["facts"] if f["label"] == "Jedinica"]})
    pack_signs = {(v, s) for v, s, _ in signed_values(ctx_text)}
    signed = {v for v, _ in pack_signs}
    for s in about:
        for v, tok in numbers(s):
            if v in in_pack and v not in ok_vals:
                issues.append(f"brojka „{tok}” u rečenici o kontekstu nije iz stavki konteksta")
        for v, sign, tok in sorted(signed_values(s), key=lambda x: (x[0], x[1])):
            if v in signed and (v, sign) not in pack_signs:
                issues.append(f"smjer promjene „{tok}” ne slaže se s činjenicama")
        for side in SIDE.findall(s):
            if f"{side.lower()} medijana" not in ctx_text:
                issues.append(f"„{side} medijana” ne slaže se s činjenicama")
        if CAUSAL.search(NEGATED.sub(" ", s)):
            issues.append("kontekst povezan s ocjenom ili sastavnicama")
    return issues


def verify(text, pack):
    """{"ok", "n_brojki", "nepoznate", "sadrzaj"}. ok only if there is at least one number, every
    number is in the pack and written the Croatian way, every grade mentioned is the unit's grade
    (this year or last year), the weakest component, the strengths and any capped grade agree
    with the pack, and any sentence on the context keeps to the context items (context_issues)."""
    ok_vals = allowed(pack)
    found = numbers(text)
    unknown = [tok for v, tok in found if v is None or v not in ok_vals]
    grades = {str(g) for g in pack.get("ocjene", [])}
    if grades:
        unknown += [f"ocjena {g}" for g in claimed_grades(text) if g not in grades]
    issues = content_issues(text, pack)
    return {"ok": bool(found) and not unknown and not issues, "n_brojki": len(found), "nepoznate": unknown,
            "sadrzaj": issues}

# ---- end of pipeline/verify.py ----

# ---- prompt: pipeline/explain.py SYSTEM, RULES, messages(), feedback(), embedded verbatim ----
SYSTEM = 'Ti si urednik javnog portala o financijama općina, gradova i županija. Pišeš kratka, točna i neutralna objašnjenja za građane na hrvatskom standardnom jeziku.'
RULES = 'Pravila:\n1. Napiši 3 do 5 rečenica, najviše 100 riječi, u jednom odlomku. Bez naslova, natuknica i oznaka (markdown).\n2. Koristi samo činjenice s popisa. Svaku brojku prepiši točno kako je napisana, zajedno s riječju ili znakom uz nju (boda, %, €). Ne zaokružuj i ne računaj nove brojke ni razlike.\n3. Redoslijed: ocjena i bodovi; najslabija sastavnica s usporedbom s medijanom skupine; jake strane; upozorenja; pravilo i napomena o podacima; kontekst. Dio za koji na popisu nema stavke izostavi.\n4. Najslabiju sastavnicu uvedi točno ovim riječima: \'Ocjenu najviše spušta sastavnica „…”.\' Jake strane uvedi riječima: \'Jake strane jedinice su: …\' Ne proglašavaj ništa drugo jakom ili slabom stranom.\n5. Upozorenja ne mijenjaju ocjenu: nikad ne piši da je ocjena zbog njih ograničena. O ograničenju ocjene piši samo ako na popisu postoji stavka "Pravilo".\n6. Ne dodaj rečenice o izvoru, obradi ili razdoblju podataka. Ton je neutralan i opisan; bez riječi "loše", "dobro", "uspjeh" i "neuspjeh", bez savjeta, nagađanja o uzrocima, političara i stranaka.\n7. Naziv jedinice piši samo u nominativu, kao subjekt rečenice ("{nom} ima ocjenu …"). Ne sklanjaj ga. U ostalim rečenicama piši "jedinica" ili naziv izostavi.\n8. Stavke "Kontekst" ne ulaze u ocjenu. Ako ih ima, dodaj na kraj još jednu rečenicu koja počinje riječima \'Za kontekst, što ne ulazi u ocjenu:\' i prepisuje njihove vrijednosti. Ne povezuj ih s ocjenom ni sa sastavnicama i ne navodi uzroke.'
EXAMPLE = 'PRIMJER za izmišljenu jedinicu (samo za stil; njegove brojke ne koristi):\nOpćina Primjerovo za 2025. godinu ima ocjenu 2 (pod pritiskom) i 31,4 boda od 100, dok je medijan usporedne skupine 78,8 boda. Ocjenu najviše spušta sastavnica „dospjele neplaćene obveze”: na kraju godine iznose 512.300 €, odnosno 41,2 % rashoda poslovanja, uz medijan skupine od 2,0 %. Jake strane jedinice su: servis duga. Upozorenje: novca na računu ima manje nego za mjesec dana rashoda poslovanja. Ocjena je ograničena na najviše 2 jer dospjele obveze dosežu 30 % rashoda poslovanja. Za kontekst, što ne ulazi u ocjenu: broj stanovnika od 2021. do 2025. smanjio se za 9,4 %, što je ispod medijana skupine (−2,1 %).'


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

# ---- end of prompt ----

# Fact packs as gzip + base64 JSON: Kaggle refuses a script of 1 MB or more, and all 576
# packs are about 1 MB as plain JSON.
PACKS = json.loads(gzip.decompress(base64.b64decode("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")).decode("utf-8"))
RUN_META = json.loads("{}")     # what the script was generated from (batch: prompt hash, model)
MAX_RETRIES = 2
HF_MODELS = []                 # [[repo, file], ...] downloaded from Hugging Face in the session
HF_DIR = "/tmp/hf-models"                 # not /kaggle/working: the 20 GB output would keep the file
SRC = "/tmp/llama.cpp"
SERVER = f"{SRC}/build/bin/llama-server"
OUT = "/kaggle/working/gemma_test_output.json"
LOG = "/kaggle/working/llama_server.log"
PORT = 8080


def sh(cmd, check=True):
    print("$", cmd, flush=True)
    t = time.time()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    tail = (r.stdout + r.stderr)[-3000:]
    print(tail, flush=True)
    print(f"  ({time.time() - t:.0f} s, exit {r.returncode})", flush=True)
    if r.returncode and check:
        raise SystemExit(f"failed: {cmd}")
    return r.stdout if not r.returncode else None


BIN_OUT = "/kaggle/working/llama-bin"     # saved with the notebook output, reused by later runs


def cached_build():
    """A llama-server built by an earlier run, attached as a kernel source."""
    hits = glob.glob("/kaggle/input/**/llama-bin/llama-server", recursive=True)
    if not hits:
        return None
    src = os.path.dirname(hits[0])
    sh(f"mkdir -p {SRC}/build && cp -r {src} {SRC}/build/bin && chmod +x {SERVER}")
    commit = open(os.path.join(src, "COMMIT")).read().strip() if os.path.exists(os.path.join(src, "COMMIT")) else "?"
    print("using cached llama-server from", src, commit, flush=True)
    return commit


def save_build(commit):
    sh(f"mkdir -p {BIN_OUT} && cp {SRC}/build/bin/llama-server {BIN_OUT}/ && "
       f"cp {SRC}/build/bin/*.so* {BIN_OUT}/ 2>/dev/null; echo {commit} > {BIN_OUT}/COMMIT; ls -la {BIN_OUT}")


def build_llama_cpp():
    os.environ["PATH"] = "/usr/local/cuda/bin:" + os.environ["PATH"]
    sh("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv")
    cached = cached_build()
    if cached:
        return cached
    sh("nvcc --version | tail -2; cmake --version | head -1")
    sh(f"git clone --depth 1 https://github.com/ggml-org/llama.cpp {SRC}")
    commit = sh(f"git -C {SRC} rev-parse HEAD").strip()
    # CUDA 13 on Kaggle: CMake may not find the libcuda stub, so point it at every stub
    # directory; if CUDA::cuda_driver is still missing, build without VMM (no libcuda link).
    stubs = sorted({os.path.dirname(p) for p in glob.glob("/usr/local/cuda*/**/stubs/libcuda.so", recursive=True)})
    print("libcuda stubs:", stubs, flush=True)
    base = (f"cmake -S {SRC} -B {SRC}/build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=75 "
            f"-DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release")
    if stubs:
        base += f" -DCMAKE_LIBRARY_PATH={';'.join(stubs)}"
    if sh(base, check=False) is None:
        sh(f"rm -rf {SRC}/build")
        sh(base + " -DGGML_CUDA_NO_VMM=ON")
    sh(f"cmake --build {SRC}/build --config Release -j {os.cpu_count()} --target llama-server")
    save_build(commit)
    return commit


def download_hf_models():
    """GGUF files that are not on Kaggle Models (e.g. Unsloth quants), fetched over HTTPS."""
    os.makedirs(HF_DIR, exist_ok=True)
    for repo, name in HF_MODELS:
        dest = os.path.join(HF_DIR, name)
        if not os.path.exists(dest):
            sh(f"curl -L --fail --retry 3 -sS -o {dest} https://huggingface.co/{repo}/resolve/main/{name} && ls -la {dest}")


def find_models():
    """Every attached or downloaded GGUF model except the vision projector and MTP drafter,
    smallest first."""
    files = glob.glob("/kaggle/input/**/*.gguf", recursive=True) + glob.glob(f"{HF_DIR}/*.gguf")
    files = [f for f in files if "mmproj" not in f and "mtp-" not in os.path.basename(f)]
    files.sort(key=os.path.getsize)
    print("GGUF files:", files, flush=True)
    if not files:
        raise SystemExit("no GGUF model attached")
    return files


def stop_server(proc):
    """Stop llama-server; kill it when it ignores SIGTERM (a 31B model stuck in CUDA can), so
    the port is free for the next start."""
    proc.terminate()
    try:
        proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=30)


def start_server(model):
    log = open(LOG, "a")                      # append: a restart keeps the crashed server's log
    log.write(f"\n===== {time.strftime('%H:%M:%S')} start {os.path.basename(model)}\n")
    log.flush()
    proc = subprocess.Popen([SERVER, "-m", model, "-ngl", "99", "-c", "8192", "--jinja",
                             "--split-mode", "layer", "--port", str(PORT), "-np", "1"],
                            stdout=log, stderr=subprocess.STDOUT)
    for _ in range(600):                      # up to 20 min: the 31B file is 17.7 GB
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=5) as r:
                if r.status == 200:
                    return proc
        except Exception:
            pass
        if proc.poll() is not None:
            break
        time.sleep(2)
    print(open(LOG).read()[-5000:])
    raise SystemExit("llama-server did not start")


def chat(msgs):
    body = {"messages": msgs, "temperature": 0.3, "top_p": 0.9, "max_tokens": 450,
            "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/v1/chat/completions",
                                 data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    t = time.time()
    with urllib.request.urlopen(req, timeout=300) as r:
        out = json.loads(r.read())
    text = out["choices"][0]["message"].get("content") or ""
    for tag in ("<think>", "<|channel>"):          # in case a thinking block slips through
        if tag in text:
            text = text.split("</think>")[-1].split("<channel|>")[-1]
    return text.strip(), round(time.time() - t, 1), out.get("usage", {})


def run_job(pack):
    """Same loop as pipeline/explain.generate, but keeps the last model text instead of the
    template, so the test shows what the model wrote."""
    msgs = messages(pack)
    attempts = []
    for _ in range(1 + MAX_RETRIES):
        text, secs, usage = chat(msgs)
        check = verify(text, pack)
        attempts.append({"text": text, "check": check, "seconds": secs, "usage": usage})
        if check["ok"]:
            break
        msgs = msgs + [{"role": "assistant", "content": text},
                       {"role": "user", "content": feedback(check["nepoznate"], check.get("sadrzaj", []))}]
    return {"oib": pack["oib"], "naziv": pack["naziv"]["nom"], "text": attempts[-1]["text"],
            "source": "ai" if attempts[-1]["check"]["ok"] else "neprovjereno",
            "check": attempts[-1]["check"], "attempts": attempts}


def main():
    t0 = time.time()
    commit = build_llama_cpp()
    gpu = sh("nvidia-smi --query-gpu=name --format=csv,noheader").strip()
    out = {"partial": True, "meta": {"llama_cpp_commit": commit, "gpu": gpu, "max_retries": MAX_RETRIES,
                                     "hf_models": HF_MODELS, **RUN_META}, "models": {}}
    t_dl = time.time()
    download_hf_models()
    out["meta"]["hf_download_seconds"] = round(time.time() - t_dl)
    for model in find_models():
        name = os.path.basename(model)
        t1 = time.time()
        try:
            proc = start_server(model)
        except SystemExit as e:                # e.g. out of GPU memory: keep the other models
            out["models"][name] = {"error": str(e), "log": open(LOG).read()[-3000:], "results": []}
            json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
            continue
        out["models"][name] = {"load_seconds": round(time.time() - t1), "results": [],
                               "gpu_memory": sh("nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader")}
        results = []
        for i, pack in enumerate(PACKS, 1):
            try:
                r = run_job(pack)
            except Exception as e:             # a hung or crashed server: restart it once, try again
                print(f"[{name} {i}/{len(PACKS)}] {pack['naziv']['nom']}: {e!r}, restarting server", flush=True)
                try:
                    stop_server(proc)
                    proc = start_server(model)
                    r = run_job(pack)
                except BaseException as e2:    # SystemExit from start_server too: keep the output
                    r = {"oib": pack["oib"], "naziv": pack["naziv"]["nom"], "error": repr(e2)}
                    results.append(r)
                    out["models"][name]["results"] = results
                    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
                    if proc.poll() is not None:
                        raise SystemExit(f"llama-server is down after {i - 1} units")
                    continue
            results.append(r)
            print(f"[{name} {i}/{len(PACKS)}] {r['naziv']}: {r['source']}, {len(r['attempts'])} pokušaja, "
                  f"{r['check']['n_brojki']} brojki, nepoznate {r['check']['nepoznate']}", flush=True)
            out["models"][name]["results"] = results
            json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
        stop_server(proc)
        out["models"][name]["seconds"] = round(time.time() - t1)
        ok = sum(r.get("source") == "ai" for r in results)
        print(f"{name}: {ok}/{len(results)} tekstova prošlo provjeru u {out['models'][name]['seconds']} s", flush=True)
    out["partial"] = False
    out["meta"]["seconds_total"] = round(time.time() - t0)
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("Gotovo:", out["meta"])


if __name__ == "__main__":
    main()
