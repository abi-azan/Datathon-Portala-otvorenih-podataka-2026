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
