"""Batch tooling for the AI explanations (pipeline/explain.py): fingerprints, resume, script."""
import importlib.util
import json

from pipeline import explain


PACK = {"oib": "1", "year": 2025, "naziv": {"nom": "Općina Primjerovo"}, "ocjena": 4,
        "facts": [{"label": "Ocjena", "value": "4 (stabilno)"}]}


def test_pack_fingerprint_ignores_key_order_but_not_values():
    reordered = {k: PACK[k] for k in reversed(list(PACK))}
    assert explain.pack_sha256(reordered) == explain.pack_sha256(PACK)
    changed = {**PACK, "facts": [{"label": "Ocjena", "value": "3 (stabilno)"}]}
    assert explain.pack_sha256(changed) != explain.pack_sha256(PACK)
    assert len(explain.prompt_sha256()) == 64


def test_resume_skips_units_with_a_text_and_retries_errors(tmp_path):
    out = {"models": {"m.gguf": {"results": [
        {"oib": "1", "text": "Tekst.", "source": "ai"},
        {"oib": "2", "text": "Tekst.", "source": "neprovjereno"},
        {"oib": "3", "error": "TimeoutError()"},
    ]}}}
    p = tmp_path / "out.json"
    p.write_text(json.dumps(out), encoding="utf-8")
    assert explain.done_oibs([p]) == {"1", "2"}


def test_kaggle_script_carries_the_packs_and_metadata(tmp_path):
    dest = explain.write_kaggle_script([PACK], tmp_path / "s.py", out_name="x.json", run_meta={"vrsta": "batch"})
    spec = importlib.util.spec_from_file_location("s", dest)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)                 # main() is guarded, so nothing runs
    assert mod.PACKS == [PACK] and mod.RUN_META == {"vrsta": "batch"}
    assert mod.OUT.endswith("/x.json") and mod.MAX_RETRIES == explain.MAX_RETRIES
    assert dest.stat().st_size < 1_000_000       # Kaggle refuses a script of 1 MB or more


def test_publish_uses_the_ai_text_only_when_it_still_fits():
    from pipeline import publish
    pack = {"oib": "1", "year": 2025, "naziv": {"nom": "Općina Primjerovo"}, "ocjene": [4],
            "facts": [{"label": "Ocjena financijske stabilnosti", "value": "4 (stabilno) na ljestvici od 1 do 5"},
                      {"label": "Ukupni bodovi", "value": "72,5 boda od 100"}]}
    text = "Općina Primjerovo ima ocjenu 4 (stabilno) i 72,5 boda od 100."
    ai = {"tekst": text, "izvor": "ai", "pack_sha256": explain.pack_sha256(pack), "model": "Gemma 4 31B"}
    shown = publish.explanation(pack, ai)
    assert shown["izvor"] == "ai" and shown["model"] == "Gemma 4 31B" and shown["provjera"]["ok"]
    stale = publish.explanation(pack, {**ai, "pack_sha256": "0" * 64})
    unchecked = publish.explanation(pack, {**ai, "izvor": "neprovjereno"})
    wrong = publish.explanation(pack, {**ai, "tekst": text.replace("72,5", "75,2")})
    for e in (stale, unchecked, wrong, publish.explanation(pack, None)):
        assert e["izvor"] == "predlozak" and e["model"] is None


def test_resumed_batch_keeps_the_fingerprint_the_model_saw(tmp_path, monkeypatch):
    """A resume (--skip) must not stamp earlier texts with the fingerprint of a pack that changed
    after they were written; the output also carries the fingerprints of its own packs."""
    a = {**PACK, "oib": "1"}
    b = {**PACK, "oib": "2"}
    monkeypatch.setattr(explain, "AI_DIR", tmp_path)
    monkeypatch.setattr(explain, "load_packs", lambda year=None: ([a, b], None))
    explain.write_kaggle_batch(dest=tmp_path / "s1.py")
    first = json.loads((tmp_path / "manifest-2025.json").read_text(encoding="utf-8"))["paketi"]
    out = tmp_path / "out1.json"
    out.write_text(json.dumps({"models": {"m.gguf": {"results": [{"oib": "1", "text": "T.", "source": "ai"}]}}}),
                   encoding="utf-8")
    a2 = {**a, "facts": [{"label": "Ocjena", "value": "3 (umjereno)"}]}      # unit 1 changed after its text
    monkeypatch.setattr(explain, "load_packs", lambda year=None: ([a2, b], None))
    dest = explain.write_kaggle_batch(skip=[out], dest=tmp_path / "s2.py")
    second = json.loads((tmp_path / "manifest-2025.json").read_text(encoding="utf-8"))["paketi"]
    assert second["1"] == first["1"] != explain.pack_sha256(a2)               # what the model saw
    spec = importlib.util.spec_from_file_location("s2", dest)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert [p["oib"] for p in mod.PACKS] == ["2"] and mod.RUN_META["paketi"] == {"2": explain.pack_sha256(b)}
