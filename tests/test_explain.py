"""Batch tooling for the AI explanations (pipeline/explain.py): fingerprints, resume, script,
import and its re-check, plus the regression for the number check's false alarm (4.11.)."""
import hashlib
import importlib.util
import json

import pytest

from pipeline import config, explain, verify


PACK = {"oib": "1", "year": 2025, "naziv": {"nom": "Općina Primjerovo"}, "ocjena": 4,
        "facts": [{"label": "Ocjena", "value": "4 (stabilno)"}]}


def batch_output(path, results, paketi, prompt=None):
    """A batch output as the runner writes it, with the fingerprints of the packs it was given."""
    out = {"meta": {"vrsta": "batch", "prompt_sha256": prompt or explain.prompt_sha256(), "paketi": paketi},
           "models": {"m-31b.gguf": {"results": results}}}
    path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return path


def test_pack_fingerprint_ignores_key_order_but_not_values():
    reordered = {k: PACK[k] for k in reversed(list(PACK))}
    assert explain.pack_sha256(reordered) == explain.pack_sha256(PACK)
    changed = {**PACK, "facts": [{"label": "Ocjena", "value": "3 (stabilno)"}]}
    assert explain.pack_sha256(changed) != explain.pack_sha256(PACK)
    assert len(explain.prompt_sha256()) == 64


def test_resume_skips_units_with_a_text_for_their_current_pack(tmp_path):
    """A unit is done only if its text was written from the pack it has now: after an MF release
    the units whose pack changed are exactly the ones that need a new text. Errors run again."""
    current = {"1": "a" * 64, "2": "b" * 64, "3": "c" * 64, "4": "d" * 64}
    p = batch_output(tmp_path / "out.json", [
        {"oib": "1", "text": "Tekst.", "source": "ai"},
        {"oib": "2", "text": "Tekst.", "source": "neprovjereno"},
        {"oib": "3", "error": "TimeoutError()"},
        {"oib": "4", "text": "Tekst.", "source": "ai"},                  # its pack changed since
    ], {**current, "4": "0" * 64})
    assert explain.done_oibs([p], current) == {"1", "2"}


def test_resume_refuses_an_output_without_fingerprints_or_with_another_prompt(tmp_path):
    p = tmp_path / "old.json"
    p.write_text(json.dumps({"models": {"m.gguf": {"results": [{"oib": "1", "text": "T.", "source": "ai"}]}}}),
                 encoding="utf-8")
    with pytest.raises(SystemExit, match="meta.paketi"):
        explain.done_oibs([p], {"1": "a" * 64})
    q = batch_output(tmp_path / "q.json", [{"oib": "1", "text": "T.", "source": "ai"}], {"1": "a" * 64}, prompt="f" * 64)
    with pytest.raises(SystemExit, match="prompt"):
        explain.done_oibs([q], {"1": "a" * 64})


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
            "facts": [{"label": "Ocjena financijske održivosti proračuna", "value": "4 (stabilno) na ljestvici od 1 do 5"},
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


def load_script(dest):
    spec = importlib.util.spec_from_file_location(dest.stem, dest)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)                 # main() is guarded, so nothing runs
    return mod


def test_resumed_batch_reruns_units_whose_pack_changed(tmp_path, monkeypatch):
    """Resume (--skip) after unit 1's pack changed: unit 1 runs again with its new pack, unit 2
    (text for its current pack) is left out, unit 3 (no text yet) runs. The script's output will
    carry the fingerprint of every pack it is given."""
    a, b, c = ({**PACK, "oib": o} for o in "123")
    monkeypatch.setattr(explain, "AI_DIR", tmp_path)
    monkeypatch.setattr(explain, "load_packs", lambda year=None: ([a, b, c], None))
    first = explain.write_kaggle_batch(dest=tmp_path / "s1.py")
    out = batch_output(tmp_path / "out1.json", [{"oib": o, "text": "T.", "source": "ai"} for o in "12"],
                       load_script(first).RUN_META["paketi"])
    a2 = {**a, "facts": [{"label": "Ocjena", "value": "3 (umjereno stabilno)"}]}      # unit 1 changed after its text
    monkeypatch.setattr(explain, "load_packs", lambda year=None: ([a2, b, c], None))
    mod = load_script(explain.write_kaggle_batch(skip=[out], dest=tmp_path / "s2.py"))
    assert [p["oib"] for p in mod.PACKS] == ["1", "3"]
    assert mod.RUN_META["paketi"] == {"1": explain.pack_sha256(a2), "3": explain.pack_sha256(c)}
    assert mod.RUN_META["verify_sha256"] == explain.verify_sha256()


def test_rerun_of_only_the_unverified_units(tmp_path, monkeypatch):
    """--neprovjereni: only units whose stored text is not a shown AI text (rejected, written from an
    older pack, or missing); --oib adds single units. The manifest still covers every unit."""
    a, b, c, d = ({**PACK, "oib": o} for o in "1234")
    monkeypatch.setattr(explain, "AI_DIR", tmp_path)
    monkeypatch.setattr(explain, "load_packs", lambda year=None: ([a, b, c, d], None))
    (tmp_path / f"objasnjenja-{config.LAST_YEAR}.json").write_text(json.dumps({"tekstovi": {
        "1": {"izvor": "ai", "pack_sha256": explain.pack_sha256(a)},
        "2": {"izvor": "neprovjereno", "pack_sha256": explain.pack_sha256(b)},
        "3": {"izvor": "ai", "pack_sha256": "0" * 64}}}), encoding="utf-8")      # 3: pack changed; 4: no text
    mod = load_script(explain.write_kaggle_batch(dest=tmp_path / "s.py", unverified=True))
    assert [p["oib"] for p in mod.PACKS] == ["2", "3", "4"] and set(mod.RUN_META["paketi"]) == {"2", "3", "4"}
    assert len(json.loads((tmp_path / f"manifest-{config.LAST_YEAR}.json").read_text(encoding="utf-8"))["paketi"]) == 4
    mod = load_script(explain.write_kaggle_batch(dest=tmp_path / "s.py", only={"1"}))
    assert [p["oib"] for p in mod.PACKS] == ["1"]
    with pytest.raises(SystemExit, match="nepoznati"):
        explain.write_kaggle_batch(dest=tmp_path / "s.py", only={"9"})


def test_feedback_says_to_drop_a_strength_or_context_sentence_the_list_does_not_have():
    """Batch v2 (5.11.): all 15 rejected units repeated the same text three times after the general
    feedback. Without the pack the message stays general; with it, it says what to drop or keep."""
    no_extras = {"facts": [{"label": "Najslabiji pokazatelj", "value": "slobodni saldo"}]}
    strengths = {"facts": no_extras["facts"] + [{"label": "Jake strane", "value": "servis duga"}]}
    ctx = {"facts": no_extras["facts"] + [{"label": "Kontekst: broj stanovnika", "value": "x", "kontekst": True}]}
    ctx_issue, strong_issue = ["kontekst bez stavke u činjenicama"], ["jaka strana „operativni saldo”"]
    assert "izostavi" not in explain.feedback([], ctx_issue)
    assert "„Kontekst koji ne ulazi u ocjenu: …” potpuno izostavi" in explain.feedback([], ctx_issue, no_extras)
    assert "potpuno izostavi" not in explain.feedback([], ctx_issue, ctx)
    assert "„Jake strane jedinice su: …” potpuno izostavi" in explain.feedback([], strong_issue, no_extras)
    assert "Jake strane su samo: servis duga." in explain.feedback([], strong_issue, strengths)
    assert "potpuno izostavi" not in explain.feedback(["97"], [], no_extras)


GOOD = {"oib": "1", "year": 2025, "naziv": {"nom": "Općina Primjerovo"}, "ocjene": [4], "ocjena": 4,
        "facts": [{"label": "Ocjena financijske održivosti proračuna", "value": "4 (stabilno) na ljestvici od 1 do 5"},
                  {"label": "Ukupni bodovi", "value": "72,5 boda od 100"}]}
OK_TEXT = "Općina Primjerovo ima ocjenu 4 (stabilno) i 72,5 boda od 100."
BAD_TEXT = OK_TEXT.replace("72,5", "75,2")


def test_import_takes_fingerprints_from_the_output_never_from_the_manifest(tmp_path, monkeypatch):
    """A later --kaggle-batch rewrites the manifest with today's packs; if the import read it, an old
    text would get today's fingerprint and be shown although its pack changed."""
    b = {**GOOD, "oib": "2"}
    monkeypatch.setattr(explain, "AI_DIR", tmp_path)
    monkeypatch.setattr(explain, "load_packs", lambda year=None: ([GOOD, b], None))
    explain.write_manifest([GOOD, b])                                         # today's fingerprints
    out = batch_output(tmp_path / "out.json", [{"oib": o, "text": OK_TEXT, "source": "ai"} for o in "12"],
                       {"1": "0" * 64, "2": explain.pack_sha256(b)})          # unit 1 was written from an older pack
    res = explain.import_batch([out], dest=tmp_path / "o.json")
    assert res["tekstovi"]["1"]["pack_sha256"] == "0" * 64 and res["tekstovi"]["1"]["izvor"] == "neprovjereno"
    assert res["tekstovi"]["2"]["izvor"] == "ai" and res["meta"]["ai"] == 1
    from pipeline import publish
    assert publish.explanation(GOOD, res["tekstovi"]["1"])["izvor"] == "predlozak"
    legacy = tmp_path / "legacy.json"                                         # no meta.paketi and no sidecar
    legacy.write_text(json.dumps({"meta": {"prompt_sha256": explain.prompt_sha256()},
                                  "models": {"m.gguf": {"results": [{"oib": "1", "text": OK_TEXT, "source": "ai"}]}}}),
                      encoding="utf-8")
    with pytest.raises(SystemExit, match="meta.paketi"):
        explain.import_batch([legacy], dest=tmp_path / "o2.json")


def test_a_legacy_output_is_read_through_its_frozen_sidecar(tmp_path, monkeypatch):
    monkeypatch.setattr(explain, "load_packs", lambda year=None: ([GOOD], None))
    legacy = tmp_path / "legacy.json"
    legacy.write_text(json.dumps({"meta": {"prompt_sha256": explain.prompt_sha256()},
                                  "models": {"m.gguf": {"results": [{"oib": "1", "text": OK_TEXT, "source": "ai"}]}}}),
                      encoding="utf-8")
    side = explain.sidecar_path(legacy)
    assert side.name == "legacy.paketi.json"
    side_doc = {"izlaz_sha256": hashlib.sha256(legacy.read_bytes()).hexdigest(), "commit": "c" * 40,
                "prompt_sha256": explain.prompt_sha256(), "verify_sha256": "v" * 64,
                "paketi": {"1": explain.pack_sha256(GOOD)}}
    side.write_text(json.dumps(side_doc), encoding="utf-8")
    res = explain.import_batch([legacy], dest=tmp_path / "o.json")
    assert res["tekstovi"]["1"]["izvor"] == "ai" and res["meta"]["commit_skripte"] == "c" * 40
    assert res["meta"]["pokretanja"][0]["otisci_paketa"] == side.name
    assert res["meta"]["verify_sha256_kaggle"] == ["v" * 64]
    side.write_text(json.dumps({**side_doc, "izlaz_sha256": "0" * 64}), encoding="utf-8")   # another output's sidecar
    with pytest.raises(SystemExit, match="ne pripada"):
        explain.import_batch([legacy], dest=tmp_path / "o.json")


def test_import_checks_again_and_takes_the_earliest_attempt_that_passes_now(tmp_path, monkeypatch):
    """Texts rejected on Kaggle by an older check become AI texts when today's check passes them.
    meta.verify_sha256 is the check used at import."""
    b, c = {**GOOD, "oib": "2"}, {**GOOD, "oib": "3"}
    monkeypatch.setattr(explain, "load_packs", lambda year=None: ([GOOD, b, c], None))
    second = OK_TEXT.replace(" i 72,5", ", odnosno 72,5")                    # passes too, but comes later
    out = batch_output(tmp_path / "out.json", [
        {"oib": "1", "text": second, "source": "neprovjereno", "attempts": [
            {"text": BAD_TEXT}, {"text": OK_TEXT}, {"text": second}]},
        {"oib": "2", "text": BAD_TEXT, "source": "neprovjereno", "attempts": [{"text": BAD_TEXT}] * 3},
        {"oib": "3", "text": OK_TEXT, "source": "ai"},                        # no attempts stored
    ], {o: explain.pack_sha256(p) for o, p in (("1", GOOD), ("2", b), ("3", c))})
    res = explain.import_batch([out], dest=tmp_path / "o.json")
    t = res["tekstovi"]
    assert (t["1"]["tekst"], t["1"]["pokusaj"], t["1"]["izvor"], t["1"]["izvor_kaggle"]) == (OK_TEXT, 2, "ai", "neprovjereno")
    assert (t["2"]["tekst"], t["2"]["pokusaj"], t["2"]["izvor"]) == (BAD_TEXT, 3, "neprovjereno")
    assert t["3"]["izvor"] == "ai" and t["3"]["pokusaj"] is None and t["1"]["pokusaja"] == 3
    assert res["meta"]["verify_sha256"] == explain.verify_sha256() and res["meta"]["ai"] == 2


def test_the_committed_batch_output_has_a_frozen_sidecar_bound_to_it():
    """kaggle/results/gemma_batch_2025_31b_q4_0.json predates meta.paketi; its fingerprints are the
    manifest at commit 4c03c97, frozen next to it (the raw output itself stays byte for byte)."""
    out_path = explain.RESULTS_DIR / "gemma_batch_2025_31b_q4_0.json"
    fp = explain.output_fingerprints(out_path)
    out = json.loads(out_path.read_text(encoding="utf-8"))
    assert fp["izvor"] == "gemma_batch_2025_31b_q4_0.paketi.json" and fp["commit"].startswith("4c03c97")
    assert set(fp["paketi"]) == {r["oib"] for m in out["models"].values() for r in m["results"]}
    assert fp["prompt_sha256"] == out["meta"]["prompt_sha256"]


def test_fresh_test_fails_clearly_when_too_few_untested_units_remain(monkeypatch):
    packs = [{**PACK, "oib": o} for o in "123"]
    monkeypatch.setattr(explain, "tested_oibs", lambda: {"1", "2"})
    assert [p["oib"] for p in explain.pick_test_units(packs, 1, fresh=True)] == ["3"]
    with pytest.raises(SystemExit, match="--fresh"):
        explain.pick_test_units(packs, 2, fresh=True)


def test_sample_with_context_has_at_least_the_asked_number_and_keeps_the_fixed_stories():
    ctx = {"label": "Kontekst: broj stanovnika", "value": "od 2021. do 2025. smanjio se za 9,4 %", "kontekst": True}
    fixed = {**PACK, "oib": "povljana", "ocjena": 2, "naziv": {**PACK["naziv"], "nom": "Općina Povljana"}}
    packs = [fixed] + [{**PACK, "oib": str(i), "ocjena": i % 5 + 1, "naziv": {**PACK["naziv"], "nom": f"J{i}"},
                        "facts": PACK["facts"] + ([ctx] if i % 4 == 0 else [])} for i in range(40)]
    chosen = explain.pick_test_units(packs, 12, min_context=7)
    assert len(chosen) == 12 and len({p["oib"] for p in chosen}) == 12
    assert chosen[0]["oib"] == "povljana"
    assert sum(map(explain.has_context, chosen)) >= 7
    assert {p["ocjena"] for p in chosen} == {1, 2, 3, 4, 5}
    # deterministic, and the old sample (no min_context) is unchanged by the new option
    assert [p["oib"] for p in explain.pick_test_units(packs, 12, min_context=7)] == [p["oib"] for p in chosen]
    assert explain.pick_test_units(packs, 12) == explain.pick_test_units(packs, 12, min_context=0)


# Općina Gradec from the batch (kaggle/results/gemma_batch_2025_31b_q4_0.json): a correct text that the
# check rejected 3 times, because a window of 120 characters after "Ocjenu" ended inside "3,8".
GRADEC = "16296383026"
GRADEC_TEXT = (
    "Općina Gradec za 2025. godinu ima ocjenu 5 (vrlo stabilno) i 99 bodova od 100, dok je medijan usporedne "
    "skupine 87,8 boda. Ocjenu najviše spušta sastavnica „servis duga”: otplata kredita i kamata iznosi 2,2 % "
    "zakonske osnovice, uz medijan skupine 3,8 % zakonske osnovice. Jake strane jedinice su: operativni saldo, "
    "slobodni saldo nakon otplate glavnice, godine otplate neto duga, servis duga, dospjele neplaćene obveze.")
GRADEC_PACK = {"oib": GRADEC, "year": 2025, "ocjena": 5, "ocjene": [5, 5], "facts": [
    {"label": "Jedinica", "value": "Općina Gradec (Zagrebačka županija), 3.189 stanovnika (Popis 2021.)"},
    {"label": "Ocjena financijske održivosti proračuna za 2025.",
     "value": "5 (vrlo stabilno) na ljestvici od 1 (vrlo nestabilno) do 5 (vrlo stabilno)"},
    {"label": "Usporedna skupina", "value": "općine 2.000-5.000 (193 jedinice)"},
    {"label": "Bodovi", "value": "99 bodova od 100; medijan skupine 87,8 boda"},
    {"label": "Mjesto u skupini", "value": "14. od 193"},
    {"label": "Ocjena za 2024.", "value": "5 (vrlo stabilno)"},
    {"label": "Pokazatelj: operativni saldo",
     "value": "operativni višak iznosi 30,4 % tekućih prihoda; medijan skupine: višak 20,0 % tekućih prihoda"},
    {"label": "Pokazatelj: slobodni saldo nakon otplate glavnice",
     "value": "nakon otplate glavnice kredita ostaje 29,3 % tekućih prihoda; medijan skupine: ostaje 16,9 % tekućih prihoda"},
    {"label": "Pokazatelj: godine otplate neto duga",
     "value": "jedinica nema neto duga (novac na računu pokriva kredite); većina jedinica u skupini nema neto duga"},
    {"label": "Pokazatelj: servis duga",
     "value": "otplata kredita i kamata iznosi 2,2 % zakonske osnovice; medijan skupine 3,8 % zakonske osnovice"},
    {"label": "Pokazatelj: dospjele neplaćene obveze",
     "value": "na kraju godine nema dospjelih neplaćenih obveza; medijan skupine 1,5 % rashoda poslovanja"},
    {"label": "Najslabiji pokazatelj", "value": "servis duga"},
    {"label": "Jake strane", "value": "operativni saldo, slobodni saldo nakon otplate glavnice, godine otplate neto "
                                      "duga, servis duga, dospjele neplaćene obveze"},
    {"label": "Upozorenja", "value": "nema upozorenja"}]}


def test_a_decimal_far_after_the_grade_word_is_not_cut_into_a_grade():
    out = json.loads((explain.RESULTS_DIR / "gemma_batch_2025_31b_q4_0.json").read_text(encoding="utf-8"))
    real = next(r for m in out["models"].values() for r in m["results"] if r["oib"] == GRADEC)
    assert real["text"] == GRADEC_TEXT and real["check"]["nepoznate"] == ["ocjena 3"]   # what Kaggle said
    start = GRADEC_TEXT.index("Ocjenu najviše") + len("Ocjenu")
    assert GRADEC_TEXT[start:start + 120].endswith(" 3,")                    # the old window ended inside "3,8"
    assert verify.claimed_grades(GRADEC_TEXT) == ["5"]
    assert verify.verify(GRADEC_TEXT, GRADEC_PACK) == {"ok": True, "n_brojki": 7, "nepoznate": [], "sadrzaj": []}
    # a wrong grade later in the same sentence, beyond the old window, is now found
    wrong = GRADEC_TEXT.replace("zakonske osnovice. Jake", "zakonske osnovice, a razred je 4. Jake")
    assert verify.claimed_grades(wrong) == ["5", "4"]
    assert verify.verify(wrong, GRADEC_PACK)["nepoznate"] == ["4", "ocjena 4"]


def test_verify_stays_standard_library_only():
    """The Kaggle script embeds pipeline/verify.py verbatim."""
    src = (config.ROOT / "pipeline" / "verify.py").read_text(encoding="utf-8")
    imports = {line.split()[1].split(".")[0] for line in src.splitlines() if line.startswith(("import ", "from "))}
    assert imports <= {"re", "decimal"}, imports


# --- context (population, income): template, prompt and the Kaggle script ------------------------

CTX_PACK = {"oib": "9", "year": 2025, "naziv": {"nom": "Općina Bogdanovci"}, "ocjena": 4, "ocjene": [4], "facts": [
    {"label": "Ocjena financijske održivosti proračuna za 2025.",
     "value": "4 (stabilno) na ljestvici od 1 (vrlo nestabilno) do 5 (vrlo stabilno)"},
    {"label": "Najslabiji pokazatelj", "value": "dospjele neplaćene obveze"},
    {"label": "Upozorenja", "value": "nema upozorenja"},
    {"label": "Kontekst", "value": "ne ulazi u ocjenu i ne objašnjava je", "kontekst": True},
    {"label": "Kontekst: broj stanovnika", "kontekst": True,
     "value": "od 2021. do 2024. smanjio se za 8,3 %, što je ispod medijana skupine (−2,9 %)"},
    {"label": "Kontekst: neto dohodak po stanovniku", "kontekst": True,
     "value": "u 2025. iznosio je 6.592 €, što je ispod medijana skupine (9.164 €)"}]}


def test_template_closes_with_one_context_sentence():
    text = explain.template(CTX_PACK)
    assert text == ("Općina Bogdanovci za 2025. godinu ima ocjenu 4 (stabilno). Ocjenu najviše spušta pokazatelj "
                    "„dospjele neplaćene obveze”. Kontekst koji ne ulazi u ocjenu: broj stanovnika od 2021. do 2024. smanjio "
                    "se za 8,3 %, što je ispod medijana skupine (−2,9 %), a neto dohodak po stanovniku u 2025. iznosio "
                    "je 6.592 €, što je ispod medijana skupine (9.164 €).")
    assert verify.verify(text, CTX_PACK)["ok"]
    only_income = {**CTX_PACK, "facts": [f for f in CTX_PACK["facts"] if "broj stanovnika" not in f["label"]]}
    assert explain.template(only_income).endswith(
        "Kontekst koji ne ulazi u ocjenu: neto dohodak po stanovniku u 2025. iznosio je 6.592 €, "
        "što je ispod medijana skupine (9.164 €).")
    fiscal = {**CTX_PACK, "facts": [f for f in CTX_PACK["facts"] if not f.get("kontekst")]}
    assert "kontekst" not in explain.template(fiscal)


def test_prompt_puts_context_last_and_the_example_passes_the_check():
    assert explain.CONTEXT_OPENING in explain.RULES and explain.EXAMPLE.count(explain.CONTEXT_OPENING) == 1
    last = explain.EXAMPLE[explain.EXAMPLE.index(explain.CONTEXT_OPENING):]
    assert verify.sentences(explain.EXAMPLE)[-1] == last                   # the closing sentence
    pack = {"ocjene": [2], "facts": [{"label": "Kontekst: broj stanovnika", "kontekst": True,
                                      "value": "od 2021. do 2025. smanjio se za 9,4 %, što je ispod medijana skupine (−2,1 %)"}]}
    assert verify.verify(last, pack)["ok"]
    assert "{" not in explain.RULES.replace("{nom}", "")          # RULES.format(**naziv) stays safe


def test_kaggle_script_checks_context_like_the_pipeline(tmp_path):
    mod = load_script(explain.write_kaggle_script([CTX_PACK], tmp_path / "c.py"))
    assert mod.RULES == explain.RULES and mod.EXAMPLE == explain.EXAMPLE
    good = explain.template(CTX_PACK)
    assert mod.verify(good, mod.PACKS[0]) == verify.verify(good, CTX_PACK) and mod.verify(good, mod.PACKS[0])["ok"]
    flipped = good.replace("smanjio se za 8,3 %", "povećao se za 8,3 %")
    assert mod.verify(flipped, mod.PACKS[0])["sadrzaj"] == ["smjer promjene „povećao se za 8,3” ne slaže se s činjenicama"]
    assert "kontekst" in mod.feedback([], ["x"])
