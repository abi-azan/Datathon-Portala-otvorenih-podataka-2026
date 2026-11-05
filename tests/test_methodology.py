import math

from pipeline import methodology as m


def unit_year(**kw):
    base = {"p_6": 1000.0, "p_3": 850.0, "p_7": 0.0, "p_63": 200.0, "p_6353": 50.0, "p_663": 0.0,
            "p_dio611": 0.0, "p_341": 0.0, "p_342": 5.0, "p_54": 20.0, "p_84": 0.0,
            "b_11": 100.0, "b_25": 0.0, "b_26": 120.0, "b_23_D": 4.0, "b_24_D": 0.0, "b_26_D": 0.0,
            "b_9221": 50.0, "b_9222": 0.0}
    base.update(kw)
    return base


def test_interp_clamps_and_interpolates():
    a = m.ANCHORS["I1"]
    assert m.interp(-0.5, a) == 0
    assert m.interp(0.05, a) == 50
    assert m.interp(0.125, a) == 75
    assert m.interp(0.9, a) == 100
    assert m.interp(math.inf, m.ANCHORS["I3"]) == 0
    assert m.interp(None, a) is None


def test_capital_grants_leave_current_revenue():
    a = m.aux(unit_year(p_6332=300.0))
    assert a["KP"] == 300.0
    assert a["PO"] == 700.0
    assert a["OS"] == -150.0


def test_net_debt_and_overdue():
    a = m.aux(unit_year())
    assert a["ND"] == 20.0          # 120 + 0 - 100
    assert a["DO"] == 4.0
    assert m.aux(unit_year(b_11=500.0))["ND"] == 0.0


def test_refinancing_is_neutralised():
    normal = m.aux(unit_year())
    refi = m.aux(unit_year(p_54=400.0, p_84=380.0))
    assert not normal["refinanciranje"] and normal["SD"] == 25.0
    assert refi["refinanciranje"] and refi["SD"] == 5.0 + 20.0


def test_legal_base_adds_back_equalisation():
    a = m.aux(unit_year(p_7=10.0))
    assert a["ZO"] == 1000 + 10 - 200 + 50


def test_window_weights_and_payback():
    rows = {2022: unit_year(p_3=900.0), 2023: unit_year(), 2024: unit_year(), 2025: unit_year(p_3=800.0)}
    res = m.evaluate_unit(rows, 1000)
    r = res[2025]
    # OS: 2025 200 (w4), 2024 150 (w3), 2023 150 (w2), 2022 100 (w1) -> 1650 / 10000
    assert abs(r["I1"] - 0.165) < 1e-9
    assert r["prozor_godina"] == 4
    assert abs(r["I3"] - 20.0 / 165.0) < 1e-9
    assert res[2022]["I4"] is None          # no prior-year legal base inside the data
    assert r["ocjena"] in (1, 2, 3, 4, 5)


def test_debt_without_operating_surplus_scores_zero_on_payback():
    rows = {2025: unit_year(p_3=1100.0)}
    r = m.evaluate_unit(rows, 1000)[2025]
    assert math.isinf(r["I3"]) and r["S3"] == 0


def test_grade_bands():
    assert m.grade(80)[0] == 5 and m.grade(79.9)[0] == 4
    assert m.grade(20)[0] == 2 and m.grade(19.9)[0] == 1
    assert m.grade(None) == (None, None)


def test_loan_reported_all_due_but_repaid_is_not_overdue():
    # Sveta Marija 2025: the whole loan sits in 26 D, but 70.785 € of principal was repaid
    prev = unit_year(b_26=990_996.0)
    r = unit_year(b_26=920_211.51, b_26_D=920_211.51, b_23_D=1_625.85, p_54=70_785.0)
    a = m.aux(r, prev)
    assert a["kredit_iskazan_dospio"]
    assert abs(a["DO"] - 1_625.85) < 1e-6
    assert abs(a["DO_iskazano"] - (920_211.51 + 1_625.85)) < 1e-6


def test_loan_all_due_without_repayment_stays_overdue():
    # Povljana: the debt is reported as overdue and is not being repaid
    a = m.aux(unit_year(b_26=2_600_000.0, b_26_D=2_600_000.0, p_54=0.0), unit_year(b_26=2_600_000.0))
    assert not a["kredit_iskazan_dospio"] and a["DO"] == 2_600_000.0 + 4.0


def test_loan_rule_edges():
    new_loan = m.aux(unit_year(b_26=500_000.0, b_26_D=500_000.0, p_54=0.0), unit_year(b_26=0.0))
    assert new_loan["kredit_iskazan_dospio"]
    small = m.aux(unit_year(b_26=9_000.0, b_26_D=9_000.0, p_54=5_000.0), unit_year(b_26=14_000.0))
    assert not small["kredit_iskazan_dospio"]
    partly_due = m.aux(unit_year(b_26=500_000.0, b_26_D=100_000.0, p_54=50_000.0), unit_year(b_26=550_000.0))
    assert not partly_due["kredit_iskazan_dospio"] and partly_due["DO"] == 100_004.0
    first_year = m.aux(unit_year(b_26=500_000.0, b_26_D=500_000.0, p_54=20_000.0), None)
    assert first_year["kredit_iskazan_dospio"]          # 20.000 >= 3% of 500.000


def test_loan_being_drawn_counts_as_regular():
    # decision 17: Sveta Marija 2023 drew the rest of its loan (241.522 -> 1.061.782 €) in a
    # grace period, so no principal was repaid, and still reported it all as overdue
    prev = unit_year(b_26=241_522.0)
    r = unit_year(b_26=1_061_782.0, b_26_D=1_061_782.0, p_54=0.0)
    a = m.aux(r, prev)
    assert a["kredit_iskazan_dospio"] and a["DO"] == 4.0
    flat = m.aux(unit_year(b_26=1_061_782.0, b_26_D=1_061_782.0, p_54=0.0), unit_year(b_26=1_061_782.0))
    assert not flat["kredit_iskazan_dospio"]            # same balance, no repayment: stays overdue
    first = m.aux(unit_year(b_26=1_061_782.0, b_26_D=1_061_782.0, p_54=0.0), None)
    assert not first["kredit_iskazan_dospio"]           # first year of the series is not a drawdown
    small = m.aux(unit_year(b_26=9_000.0, b_26_D=9_000.0, p_54=0.0), unit_year(b_26=1_000.0))
    assert not small["kredit_iskazan_dospio"]           # the size and share conditions still apply
    partly = m.aux(unit_year(b_26=500_000.0, b_26_D=400_000.0, p_54=0.0), unit_year(b_26=100_000.0))
    assert not partly["kredit_iskazan_dospio"]


def test_overdue_at_30_percent_caps_grade_at_2():
    ok = m.evaluate_unit({2025: unit_year()}, 1000)[2025]
    hit = m.evaluate_unit({2025: unit_year(b_23_D=300.0)}, 1000)[2025]   # 300 / 850 = 35%
    assert ok["ocjena"] >= 3 and not ok["ogranicenje_do"]
    assert hit["I5"] >= 0.30 and hit["ogranicenje_do"]
    assert hit["bodovi_bez_ogranicenja"] > 40 and hit["bodovi"] == m.DO_CAP_POINTS
    assert hit["ocjena"] == 2 and hit["ocjena_rijec"] == "nestabilno"
    assert max(hit["ocjene_scenarija"].values()) == 2      # the cap holds in every weight scenario
    worse = m.evaluate_unit({2025: unit_year(b_23_D=300.0, p_3=1300.0)}, 1000)[2025]
    assert not worse["ogranicenje_do"] and worse["bodovi"] == worse["bodovi_bez_ogranicenja"]


def test_flags():
    rows = {2024: unit_year(p_3=1100.0), 2025: unit_year(p_3=1100.0, b_9222=200.0, b_9221=0.0, b_11=10.0)}
    z = m.evaluate_unit(rows, 1000)[2025]["zastavice"]
    assert {"Z1", "Z3", "Z4"} <= set(z)


def test_criterion_10_without_eu_sources():
    """Z5 (Government conclusion 16.4.2026, research/08 §5): deficit (3 + 4) - (6 + 7) as a share of
    revenue without EU sources (638, 6324); a surplus counts as 0."""
    r = {"p_6": 1_000_000, "p_7": 0, "p_638": 200_000, "p_6324": 0, "p_3": 900_000, "p_4": 180_000}
    z = m.criterion_10(r)
    assert abs(z["z5_manjak_udio"] - 80_000 / 800_000) < 1e-12 and z["z5_zadovoljava"]   # exactly 10 %
    z = m.criterion_10({**r, "p_4": 181_000})
    assert not z["z5_zadovoljava"]
    z = m.criterion_10({**r, "p_4": 50_000})
    assert z["z5_manjak_udio"] == 0 and z["z5_zadovoljava"]
    assert m.criterion_10({"p_6": 0}) == {"z5_manjak_udio": None, "z5_zadovoljava": None}
    # it is context: no red flag, so the AI fact packs do not change
    assert "Z5" not in m.flags({2025: m.aux({**r, "p_4": 400_000})}, 2025, {**r, "p_4": 400_000})
