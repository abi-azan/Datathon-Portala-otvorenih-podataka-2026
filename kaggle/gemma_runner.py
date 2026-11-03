"""Gemma 4 on a Kaggle GPU: AI explanations with a number check (Fiskalna karta JLS).

Generated from kaggle/gemma_runner.py by `python -m pipeline.explain --kaggle-test N`.
Do not edit kaggle/gemma_test.py by hand.

- Model: Gemma 4 E4B-it, QAT Q4_0 GGUF, attached as a Kaggle model data source (Apache-2.0).
- Runtime: llama.cpp (MIT), built from source for the T4 (CUDA arch 75), served by llama-server.
- Every text is checked: each number must appear in the unit's fact pack. A failed text is
  generated again with feedback, at most __MAX_RETRIES__ times, and then the template is used.
Output: /kaggle/working/gemma_test_output.json
"""
import glob
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

PACKS = json.loads("__PACKS__")
MAX_RETRIES = __MAX_RETRIES__
SRC = "/tmp/llama.cpp"
SERVER = f"{SRC}/build/bin/llama-server"
OUT = "/kaggle/working/gemma_test_output.json"
LOG = "/kaggle/working/llama_server.log"
PORT = 8080


def sh(cmd):
    print("$", cmd, flush=True)
    t = time.time()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    tail = (r.stdout + r.stderr)[-3000:]
    print(tail, flush=True)
    print(f"  ({time.time() - t:.0f} s, exit {r.returncode})", flush=True)
    if r.returncode:
        raise SystemExit(f"failed: {cmd}")
    return r.stdout


def build_llama_cpp():
    os.environ["PATH"] = "/usr/local/cuda/bin:" + os.environ["PATH"]
    sh("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv")
    sh("nvcc --version | tail -2; cmake --version | head -1")
    sh(f"git clone --depth 1 https://github.com/ggml-org/llama.cpp {SRC}")
    commit = sh(f"git -C {SRC} rev-parse HEAD").strip()
    sh(f"cmake -S {SRC} -B {SRC}/build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=75 "
       f"-DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release")
    sh(f"cmake --build {SRC}/build --config Release -j {os.cpu_count()} --target llama-server")
    return commit


def find_model():
    files = [f for f in glob.glob("/kaggle/input/**/*.gguf", recursive=True) if "mmproj" not in f]
    print("GGUF files:", files, flush=True)
    if not files:
        raise SystemExit("no GGUF model attached")
    return files[0]


def start_server(model):
    log = open(LOG, "w")
    proc = subprocess.Popen([SERVER, "-m", model, "-ngl", "99", "-c", "8192", "--jinja",
                             "--port", str(PORT), "-np", "1"], stdout=log, stderr=subprocess.STDOUT)
    for _ in range(300):
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
        msgs = msgs + [{"role": "assistant", "content": text}, {"role": "user", "content": feedback(check["nepoznate"])}]
    return {"oib": pack["oib"], "naziv": pack["naziv"]["nom"], "text": attempts[-1]["text"],
            "source": "ai" if attempts[-1]["check"]["ok"] else "neprovjereno",
            "check": attempts[-1]["check"], "attempts": attempts}


def main():
    t0 = time.time()
    commit = build_llama_cpp()
    model = find_model()
    proc = start_server(model)
    results = []
    for i, pack in enumerate(PACKS, 1):
        r = run_job(pack)
        results.append(r)
        print(f"[{i}/{len(PACKS)}] {r['naziv']}: {r['source']}, {len(r['attempts'])} pokušaja, "
              f"{r['check']['n_brojki']} brojki, nepoznate {r['check']['nepoznate']}", flush=True)
        json.dump({"partial": True, "results": results}, open(OUT, "w"), ensure_ascii=False, indent=1)
    proc.terminate()
    meta = {"llama_cpp_commit": commit, "model_file": os.path.basename(model),
            "gpu": sh("nvidia-smi --query-gpu=name --format=csv,noheader").strip(),
            "seconds_total": round(time.time() - t0), "max_retries": MAX_RETRIES}
    json.dump({"partial": False, "meta": meta, "results": results}, open(OUT, "w"), ensure_ascii=False, indent=1)
    ok = sum(r["source"] == "ai" for r in results)
    print(f"Gotovo: {ok}/{len(results)} tekstova prošlo provjeru; {meta}")


if __name__ == "__main__":
    main()
