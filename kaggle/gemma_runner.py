"""Gemma 4 on a Kaggle GPU: AI explanations with a number check (Fiskalna karta JLS).

Generated from kaggle/gemma_runner.py by `python -m pipeline.explain --kaggle-test N` (test,
kaggle/gemma_test.py) or `--kaggle-batch` (all units, kaggle/gemma_batch.py). Do not edit
the generated scripts by hand.

- Models: every attached Gemma 4 QAT Q4_0 GGUF (Kaggle model data sources, Apache-2.0), smallest
  first. A model larger than one T4 is split by layers across both T4s.
- Runtime: llama.cpp (MIT), built from source for the T4 (CUDA arch 75), served by llama-server.
- Every text is checked: each number must appear in the unit's fact pack. A failed text is
  generated again with feedback, at most __MAX_RETRIES__ times, and then the template is used.
- The output is written after every unit, so a stopped run can be resumed with --skip.
Output: /kaggle/working/__OUT_NAME__
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
# __VERIFY__
# ---- end of pipeline/verify.py ----

# ---- prompt: pipeline/explain.py SYSTEM, RULES, messages(), feedback(), embedded verbatim ----
# __PROMPT__
# ---- end of prompt ----

# Fact packs as gzip + base64 JSON: Kaggle refuses a script of 1 MB or more, and all 576
# packs are about 1 MB as plain JSON.
PACKS = json.loads(gzip.decompress(base64.b64decode("__PACKS_GZ__")).decode("utf-8"))
RUN_META = json.loads("__RUN_META__")     # what the script was generated from (batch: prompt hash, model)
MAX_RETRIES = __MAX_RETRIES__
HF_MODELS = __HF_MODELS__                 # [[repo, file], ...] downloaded from Hugging Face in the session
HF_DIR = "/tmp/hf-models"                 # not /kaggle/working: the 20 GB output would keep the file
SRC = "/tmp/llama.cpp"
SERVER = f"{SRC}/build/bin/llama-server"
OUT = "/kaggle/working/__OUT_NAME__"
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
