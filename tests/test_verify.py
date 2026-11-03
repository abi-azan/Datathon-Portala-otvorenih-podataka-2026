from pipeline import explain, facts, verify

PACK = {"ocjene": [5, 4], "facts": [
    {"label": "Ocjena za 2025.", "value": "5 (vrlo stabilno) na ljestvici od 1 do 5"},
    {"label": "Bodovi", "value": "96,5 od 100; medijan skupine 78,8"},
    {"label": "Dospjele obveze", "value": "1.626 €, što je 0,2 % rashoda poslovanja"},
    {"label": "Razdoblje", "value": "prosjek zadnje 4 godine"},
]}


def test_numbers_are_read_the_croatian_way():
    got = [str(v) for v, _ in verify.numbers("od 2019.-2025. i 1.625,85 € te 27,6 % i 12. od 84; 1 234 i 4 125")]
    assert got == ["2019", "2025", "1625.85", "27.6", "12", "84", "1234", "4", "125"]


def test_copied_numbers_pass_and_rounded_or_invented_fail():
    assert verify.verify("Ocjena je 5 (vrlo stabilno), 96,5 boda; dospjelo je 1.626 €.", PACK)["ok"]
    r = verify.verify("Ocjena je 5, a bodova je 97.", PACK)
    assert not r["ok"] and r["nepoznate"] == ["97"]
    assert verify.verify("Dospjele obveze su 0,20 % rashoda.", PACK)["ok"]    # 0,20 is the same number as 0,2
    assert not verify.verify("Bez ijedne brojke.", PACK)["ok"]


def test_a_wrong_grade_fails_even_if_the_digit_is_elsewhere_in_the_facts():
    r = verify.verify("Jedinica ima ocjenu 4 za prosjek zadnje 4 godine.", PACK)
    assert r["ok"]                                   # 4 was last year's grade
    r = verify.verify("Jedinica ima ocjenu 1, na ljestvici od 1 do 5.", PACK)
    assert not r["ok"] and r["nepoznate"] == ["ocjena 1"]


def test_croatian_forms():
    assert facts.num(1625.85, 2) == "1.625,85" and facts.pct(0.276) == "27,6 %"
    assert [facts.plural(n, "jedinica", "jedinice", "jedinica") for n in (1, 2, 5, 12, 21, 193)] == \
        ["jedinica", "jedinice", "jedinica", "jedinica", "jedinica", "jedinice"]
    assert facts.cases("Međimurska županija", "zupanija")["gen"] == "Međimurske županije"
    assert facts.cases("Grad Zagreb", "grad")["lok"] == "Gradu Zagrebu"
    assert facts.cases("Općina Sveta Marija", "opcina")["gen"] == "Općine Sveta Marija"


def test_generate_retries_with_feedback_then_falls_back_to_the_template():
    pack = {**PACK, "naziv": {"nom": "Općina X", "gen": "Općine X", "lok": "Općini X"}, "year": 2025,
            "facts": PACK["facts"] + [{"label": "Ocjena financijske stabilnosti za 2025.", "value": "5 (vrlo stabilno) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno)"},
                                      {"label": "Jake strane", "value": "operativni saldo"}]}
    seen = []

    def bad(msgs):
        seen.append(msgs)
        return "Ocjena je 5, a bodova je 97."
    out = explain.generate(pack, bad)
    assert out["source"] == "predlozak" and len(out["attempts"]) == 1 + explain.MAX_RETRIES
    assert "97" in seen[-1][-1]["content"]           # the retry tells the model which number was wrong
    assert out["check"]["ok"]                        # the template itself passes the check


def test_english_decimals_and_dates_cannot_hide_behind_their_first_part():
    pack = {"ocjene": [4], "facts": [{"label": "x", "value": "41 % i 512 €"}]}
    r = verify.verify("Obveze iznose 41.7 % odnosno 512.30 €.", pack)
    assert not r["ok"] and r["nepoznate"] == ["41.7", "512.30"]
    assert not verify.verify("Stanje na dan 31.12.2025. iznosi 41 %.", pack)["ok"]


def test_grade_claims_are_found_beyond_filler_words_and_the_scale_is_not_a_claim():
    pack = {"ocjene": [4], "facts": [{"label": "Ocjena", "value": "4 (stabilno) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno); 2025."}]}
    r = verify.verify("Jedinica ima ocjenu financijske stabilnosti 1 (ozbiljan pritisak).", pack)
    assert not r["ok"] and r["nepoznate"] == ["ocjena 1"]
    assert verify.verify("Ocjene od 1 do 5 opisuju stabilnost; jedinica ima ocjenu 4.", pack)["ok"]
    assert verify.verify("Ocjena za 2025. godinu je 4 (stabilno) na ljestvici od 1 (ozbiljan pritisak) do 5 (vrlo stabilno).", pack)["ok"]


def test_the_gemma_v2_texts_still_pass():
    """Regression: the 20 texts from the Kaggle run (docs/research/06) passed the old check."""
    import json
    from pathlib import Path
    out = json.loads((Path(__file__).parent.parent / "kaggle" / "results" / "gemma_test_v2_e4b.json").read_text(encoding="utf-8"))
    from pipeline import config
    if not (config.BUILD / "results.parquet").exists():
        return
    packs = {p["oib"]: p for p in explain.load_packs()[0]}
    failed = [(r["naziv"], verify.verify(r["text"], packs[r["oib"]])["nepoznate"]) for r in out["results"]]
    failed = [f for f in failed if f[1]]
    assert not failed, failed


def test_an_amount_after_the_word_ocjena_is_not_a_grade():
    """Regression from the 12B run: 'Ocjenu najviše spuštaju … 1.767.926 €' is not grade 1."""
    pack = {"ocjene": [2], "facts": [{"label": "x", "value": "2 (pod pritiskom); 1.767.926 €; 80,9 %"}]}
    assert verify.verify("Ocjenu najviše spuštaju obveze od 1.767.926 €, odnosno 80,9 %, a ocjena je 2.", pack)["ok"]
