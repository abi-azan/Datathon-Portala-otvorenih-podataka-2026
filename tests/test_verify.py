import pytest

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
            "facts": PACK["facts"] + [{"label": "Ocjena financijske održivosti proračuna za 2025.", "value": "5 (vrlo stabilno) na ljestvici od 1 (vrlo nestabilno) do 5 (vrlo stabilno)"},
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
    pack = {"ocjene": [4], "facts": [{"label": "Ocjena", "value": "4 (stabilno) na ljestvici od 1 (vrlo nestabilno) do 5 (vrlo stabilno); 2025."}]}
    r = verify.verify("Jedinica ima ocjenu financijske stabilnosti 1 (vrlo nestabilno).", pack)
    assert not r["ok"] and r["nepoznate"] == ["ocjena 1"]
    assert verify.verify("Ocjene od 1 do 5 opisuju stabilnost; jedinica ima ocjenu 4.", pack)["ok"]
    assert verify.verify("Ocjena za 2025. godinu je 4 (stabilno) na ljestvici od 1 (vrlo nestabilno) do 5 (vrlo stabilno).", pack)["ok"]


def test_no_false_grade_claims_in_real_model_texts():
    """Regression on the Kaggle texts (docs/research/06): every grade the checker reads out of a
    real model text is a grade the text really states, so the grade check raises no false alarms
    (Gradec, 4.11.: "3" cut out of "3,8"). (The full check is not repeated: the fact packs have
    changed since those runs.)

    A grade counts as stated when it is the unit's grade in today's pack, or when the text writes it
    the canonical way, "N (word for N)". The second case is needed because a text keeps the grade of
    the build it was written from: v6 (3.11.) says Rešetari 4 and Petrinja 2, which were right then,
    but the equalization rule of 4.11. raised both. A digit cut out of an amount or a share is never
    followed by its grade word, so the check stays sharp."""
    import json
    import re
    from pathlib import Path
    from pipeline import config, facts
    if not (config.BUILD / "results.parquet").exists():
        return
    packs = {p["oib"]: p for p in explain.load_packs()[0]}
    results = Path(__file__).parent.parent / "kaggle" / "results"
    texts = []
    for f in results.glob("gemma_test_*.json"):
        out = json.loads(f.read_text(encoding="utf-8"))
        for m in (out.get("models") or {"": {"results": out.get("results", [])}}).values():
            texts += [(r["oib"], r["text"]) for r in m["results"] if r["source"] == "ai"]   # wrong texts may claim wrong grades
    assert len(texts) >= 60

    # the stored test texts were written with the grade words before 5.11. (PLAN §11, decision 18)
    legacy = {3: "umjereno", 2: "pod pritiskom", 1: "ozbiljan pritisak"}

    def stated(t):
        return {d for d, w in re.findall(r"(?<![\d,.])([1-5])\s*\(([^)]+)\)", t)
                if w.strip() in (facts.GRADE_WORDS[int(d)], legacy.get(int(d)))}

    bad = [(packs[o]["naziv"]["nom"], g) for o, t in texts for g in verify.claimed_grades(t)
           if int(g) not in packs[o]["ocjene"] and g not in stated(t)]
    assert not bad, bad
    # the canonical form does not let a fragment through
    fragment = "Općina Primjerovo ima ocjenu 5 (vrlo stabilno). Ocjenu najviše spušta servis duga, uz medijan 3"
    assert [g for g in verify.claimed_grades(fragment) if g not in stated(fragment)] == ["3"]


def test_an_amount_after_the_word_ocjena_is_not_a_grade():
    """Regression from the 12B run: 'Ocjenu najviše spuštaju … 1.767.926 €' is not grade 1."""
    pack = {"ocjene": [2], "facts": [{"label": "x", "value": "2 (nestabilno); 1.767.926 €; 80,9 %"}]}
    assert verify.verify("Ocjenu najviše spuštaju obveze od 1.767.926 €, odnosno 80,9 %, a ocjena je 2.", pack)["ok"]


def test_content_claims_must_match_the_pack():
    """Gemma v4: 'zbog prenesenog manjka ocjena je ograničena' (no rule), invented strengths."""
    pack = {"ocjene": [2], "facts": [
        {"label": "Ocjena", "value": "2 (nestabilno); 34,2 boda"},
        {"label": "Najslabiji pokazatelj", "value": "dospjele neplaćene obveze"},
        {"label": "Jake strane", "value": "operativni saldo, servis duga"},
        {"label": "Upozorenja", "value": "preneseni manjak"}]}
    good = ("Jedinica ima ocjenu 2 i 34,2 boda. Ocjenu najviše spušta sastavnica „dospjele neplaćene obveze”. "
            "Jake strane jedinice su: operativni saldo i servis duga.")
    assert verify.verify(good, pack)["ok"]
    r = verify.verify(good + " Zbog prenesenog manjka ocjena je ograničena.", pack)
    assert not r["ok"] and r["sadrzaj"] == ["ograničenje ocjene bez pravila"]
    r = verify.verify("Ocjena je 2. Ocjenu najviše spušta sastavnica „servis duga”.", pack)
    assert r["sadrzaj"] == ["najslabiji pokazatelj „servis duga”"]
    r = verify.verify("Ocjena je 2. Jake strane jedinice su: ovisnost o pomoćima.", pack)
    assert r["sadrzaj"] == ["jaka strana „ovisnost o pomoćima”"]
    with_rule = {**pack, "facts": pack["facts"] + [{"label": "Pravilo", "value": "ocjena je ograničena na najviše 2"}]}
    assert verify.verify("Ocjena je 2, ograničena na najviše 2.", with_rule)["ok"]


def test_the_weakest_indicator_needs_its_value():
    """Grad Zagreb and Općina Blato, 6.11.: 'Ocjenu najviše spušta pokazatelj „slobodni saldo”.' and
    not a word on how much. The text must carry a number of the unit's own part of that item."""
    pack = {"ocjene": [5], "naziv": {"nom": "Grad X"}, "year": 2025, "facts": [
        {"label": "Ocjena financijske održivosti proračuna za 2025.",
         "value": "5 (vrlo stabilno) na ljestvici od 1 (vrlo nestabilno) do 5 (vrlo stabilno)"},
        {"label": "Bodovi", "value": "80,1 boda od 100"},
        {"label": "Pokazatelj: slobodni saldo",
         "value": "nakon otplate glavnice kredita ostaje 5,7 % tekućih prihoda; medijan skupine: ostaje 9,2 % tekućih prihoda"},
        {"label": "Pokazatelj: godine otplate duga", "value": "jedinica nema neto duga (novac na računu pokriva kredite)"},
        {"label": "Najslabiji pokazatelj", "value": "slobodni saldo"}]}
    thin = "Grad X ima ocjenu 5 (vrlo stabilno) i 80,1 boda od 100. Ocjenu najviše spušta pokazatelj „slobodni saldo”."
    r = verify.verify(thin, pack)
    assert not r["ok"] and r["nepoznate"] == [] and r["sadrzaj"] == ["najslabiji pokazatelj „slobodni saldo” bez vrijednosti"]
    # the peer median alone is not the unit's value
    assert not verify.verify(thin[:-1] + ", uz medijan skupine od 9,2 % tekućih prihoda.", pack)["ok"]
    assert verify.verify(thin[:-1] + ": nakon otplate glavnice kredita ostaje 5,7 % tekućih prihoda.", pack)["ok"]
    # an indicator with no number of its own asks for nothing
    no_debt = {**pack, "facts": pack["facts"][:-1] + [{"label": "Najslabiji pokazatelj", "value": "godine otplate duga"}]}
    assert verify.verify("Grad X ima ocjenu 5. Ocjenu najviše spušta pokazatelj „godine otplate duga”.", no_debt)["ok"]
    # the retry quotes the item to copy, and the template states the value itself
    msg = explain.feedback([], r["sadrzaj"], pack)
    assert "„Pokazatelj: slobodni saldo”" in msg and "ostaje 5,7 % tekućih prihoda" in msg
    text = explain.template(pack)
    assert "„slobodni saldo”: nakon otplate glavnice kredita ostaje 5,7 % tekućih prihoda" in text
    assert verify.verify(text, pack)["ok"]


# --- context: population and income (facts.context_facts) ---------------------------------------

FISCAL = [{"label": "Jedinica", "value": "Općina Bogdanovci (Vukovarsko-srijemska županija), 1.893 stanovnika (Popis 2021.)"},
          {"label": "Ocjena financijske održivosti proračuna za 2025.", "value": "4 (stabilno) na ljestvici od 1 (vrlo nestabilno) do 5 (vrlo stabilno)"},
          {"label": "Bodovi", "value": "72,5 boda od 100; medijan skupine 78,8 boda"},
          {"label": "Najslabiji pokazatelj", "value": "dospjele neplaćene obveze"}]
CONTEXT = [{"label": "Kontekst", "value": "ne ulazi u ocjenu i ne objašnjava je", "kontekst": True},
           {"label": "Kontekst: broj stanovnika",
            "value": "od 2021. do 2024. smanjio se za 8,3 %, što je ispod medijana skupine (−2,9 %)", "kontekst": True},
           {"label": "Kontekst: neto dohodak po stanovniku",
            "value": "u 2025. iznosio je 6.592 €, što je ispod medijana skupine (9.164 €)", "kontekst": True}]
CTX_PACK = {"ocjene": [4], "facts": FISCAL + CONTEXT}
NO_CTX_PACK = {"ocjene": [4], "facts": FISCAL}
FIRST = "Općina Bogdanovci za 2025. godinu ima ocjenu 4 (stabilno) i 72,5 boda od 100, uz medijan skupine 78,8 boda."
CTX = ("Za kontekst, što ne ulazi u ocjenu: broj stanovnika od 2021. do 2024. smanjio se za 8,3 %, što je ispod "
       "medijana skupine (−2,9 %), a neto dohodak po stanovniku u 2025. iznosio je 6.592 €, što je ispod medijana "
       "skupine (9.164 €).")


def check(text, pack=CTX_PACK):
    r = verify.verify(text, pack)
    return r["nepoznate"] + r["sadrzaj"]


def test_a_copied_context_sentence_passes_in_every_spelling_of_its_sign():
    assert check(f"{FIRST} {CTX}") == []
    assert verify.claimed_grades(f"{FIRST} {CTX}") == ["4"]          # "ne ulazi u ocjenu" is not followed by a grade
    for variant in ("promijenio se za −8,3 %", "promijenio se za -8,3 %", "pao je za 8,3 %", "smanjio se za 8,3 %"):
        text = CTX.replace("smanjio se za 8,3 %", variant)
        assert check(f"{FIRST} {text}") == [], variant
    plus = {"ocjene": [4], "facts": FISCAL + [
        {"label": "Kontekst: broj stanovnika", "kontekst": True,
         "value": "od 2021. do 2024. povećao se za 6,2 %, što je iznad medijana skupine (+1,0 %)"}]}
    assert check(f"{FIRST} Za kontekst, što ne ulazi u ocjenu: broj stanovnika od 2021. do 2024. porastao je za "
                 "+6,2 %, iznad medijana skupine (+1,0 %).", plus) == []


def test_an_altered_context_number_fails():
    assert check(f"{FIRST} {CTX.replace('8,3 %', '8,4 %')}") == ["8,4"]
    assert check(f"{FIRST} {CTX.replace('6.592 €', '6.593 €')}") == ["6.593"]
    assert check(f"{FIRST} {CTX.replace('od 2021.', 'od 2020.')}") == ["2020"]


def test_a_flipped_sign_direction_or_side_of_the_median_fails():
    assert check(f"{FIRST} {CTX.replace('smanjio se za 8,3 %', 'povećao se za 8,3 %')}") == \
        ["smjer promjene „povećao se za 8,3” ne slaže se s činjenicama"]
    assert check(f"{FIRST} {CTX.replace('(−2,9 %)', '(+2,9 %)')}") == ["smjer promjene „+2,9” ne slaže se s činjenicama"]
    assert check(f"{FIRST} {CTX.replace('što je ispod medijana skupine (9.164', 'što je iznad medijana skupine (9.164')}") \
        == ["„iznad medijana” ne slaže se s činjenicama"]


def test_context_only_when_the_pack_has_it():
    r = verify.verify(f"{FIRST} {CTX}", NO_CTX_PACK)
    assert not r["ok"] and r["sadrzaj"] == ["kretanje stanovništva bez stavke u činjenicama",
                                            "dohodak bez stavke u činjenicama"]
    only_pop = {"ocjene": [4], "facts": FISCAL + CONTEXT[:2]}
    assert "dohodak bez stavke u činjenicama" in check(f"{FIRST} {CTX}", only_pop)
    assert check(f"{FIRST} Za kontekst, jedinica je mala.", NO_CTX_PACK) == ["kontekst bez stavke u činjenicama"]
    assert check(f"{FIRST} Broj stanovnika se smanjuje.", NO_CTX_PACK) == ["kretanje stanovništva bez stavke u činjenicama"]
    # the unit's census population (the first fact) is not the population trend
    assert check(f"{FIRST[:-1]}, a ima 1.893 stanovnika.", NO_CTX_PACK) == []


def test_context_tied_to_the_grade_or_mixed_with_fiscal_numbers_fails():
    cause = f"{FIRST} Zbog pada stanovništva od 8,3 % ocjena je niža."
    assert "kontekst povezan s ocjenom ili pokazateljima" in check(cause)
    for link in ("što utječe na ocjenu", "pa je ocjena niža", "što objašnjava slabiju sastavnicu"):
        assert "kontekst povezan s ocjenom ili pokazateljima" in check(f"{FIRST} {CTX[:-1]}, {link}."), link
    for negated in ("što ne ulazi u ocjenu i ne objašnjava je", "koji nisu dio ocjene", "što ne utječe na ocjenu"):
        assert check(f"{FIRST} {CTX.replace('što ne ulazi u ocjenu', negated)}") == [], negated
    mixed = f"Jedinica ima 72,5 boda, a broj stanovnika od 2021. do 2024. smanjio se za 8,3 %."
    assert check(mixed) == ["brojka „72,5” u rečenici o kontekstu nije iz stavki konteksta"]


def test_the_committed_texts_raise_no_context_issue():
    """Every accepted AI text keeps to the context rules against its own current pack: a unit with
    context items may mention them, a unit without them writes no context sentence. (Until the batch
    of 5.11. the texts predated context, so they were checked against CTX_PACK and NO_CTX_PACK; the
    texts now carry context for the units whose packs have it, so only their own pack is a fair test.)"""
    import json
    from pipeline import config
    path = config.ROOT / "data" / "ai" / "objasnjenja-2025.json"
    if not path.exists():
        pytest.skip("no imported texts")
    if not (config.BUILD / "results.parquet").exists():
        pytest.skip("no build")
    packs = {p["oib"]: p for p in explain.load_packs()[0]}
    texts = {o: t["tekst"] for o, t in json.loads(path.read_text(encoding="utf-8"))["tekstovi"].items()
             if t["izvor"] == "ai" and t["pack_sha256"] == explain.pack_sha256(packs[o])}
    assert len(texts) >= 500
    assert {o: i for o, t in texts.items() if (i := verify.context_issues(t, packs[o]))} == {}
