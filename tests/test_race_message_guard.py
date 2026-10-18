"""Unit tests for the Sunday race message fact-check guard.

Pure tests — no clock, DB, or OpenAI. They feed the deterministic scenario text
(what the code builds) plus a candidate AI message and assert the guard's verdict.
"""
from race_message_guard import (
    find_violations, allowed_win_counts, stakes_allowed, build_fallback_message,
    strip_unsupported_sentences,
    eliminated_names,
)


# --- the real bugs that triggered this work (must be CAUGHT) ---

def test_pal_inflation_caught():
    # PAL: scenario says Fuzwuz 2nd / Vox 1st; AI inflated to 3rd/2nd
    scenario = ("RACE OVER! Fuzwuz and Vox are tied at 13 and will share the weekly win! "
                "This makes it Fuzwuz's 2nd win and Vox's 1st win this season.")
    msg = "🎉 RACE OVER! Fuzwuz and Vox tie at 13! Fuzwuz marks their 3rd win, Vox their 2nd! 🏆"
    assert find_violations(msg, scenario)  # non-empty -> caught


def test_tiny_words_inflation_caught():
    # League 19: Rally's 1st win, AI said 2nd
    scenario = "RACE OVER! Rally wins the week with 18! This is their 1st win this season."
    msg = "🎉 RACE OVER! Rally triumphs with 18! Rally marks their 2nd win this season! 🌟"
    assert find_violations(msg, scenario)


def test_invented_promotion_caught():
    # Pickle Party Div II: no stakes in scenario, AI invented promotion
    scenario = ("Division II: RACE OVER! Brent and Dani are tied at 17 and will share the weekly "
                "win! (Season wins: Brent now has 1, Dani now has 1)")
    msg = ("Division II: RACE OVER! Brent and Dani tie at 17! Both now have 1 win. "
           "With another win, either could secure promotion to Division I! 🚀")
    assert find_violations(msg, scenario)


# --- legit messages that must PASS untouched (no false positives) ---

def test_correct_counts_pass():
    scenario = ("RACE OVER! Fuzwuz and Vox are tied at 13 and will share the weekly win! "
                "This makes it Fuzwuz's 2nd win and Vox's 1st win this season.")
    msg = "🎉 RACE OVER! Fuzwuz & Vox tie at 13! Fuzwuz's 2nd win, Vox's 1st! 🏆"
    assert find_violations(msg, scenario) == []


def test_legit_promotion_passes():
    scenario = ("Division I: Jess could clinch Division I Season 9 with a win! SEASON STAKES: "
                "Jess has 2 wins (one away).")
    msg = "Division I: SEASON STAKES! Jess could clinch Season 9 with a win — their promotion run is on! 🔥"
    assert find_violations(msg, scenario) == []


def test_legit_clinch_passes():
    scenario = ("RACE OVER! Brent wins the week with 17! SEASON CLINCH: Brent clinches Season 8 "
                "with their 4th win!")
    msg = "🏆 RACE OVER! Brent takes the week with 17 and CLINCHES Season 8 with their 4th win! 🎊"
    assert find_violations(msg, scenario) == []


def test_word_ordinal_inflation_caught():
    scenario = "RACE OVER! Rally wins the week with 18! This is their 1st win this season."
    msg = "RACE OVER! Rally wins with 18 — their second win this season! 🌟"
    assert find_violations(msg, scenario)


def test_lower_ordinal_not_flagged():
    # mentioning a number at/below the supported max is fine (contextual)
    scenario = ("RACE OVER! Fuzwuz and Vox are tied at 13 and will share the weekly win! "
                "This makes it Fuzwuz's 2nd win and Vox's 1st win this season.")
    msg = "RACE OVER! Fuzwuz & Vox share it — Vox grabs their 1st win! 🎉"
    assert find_violations(msg, scenario) == []


def test_no_scenario_still_catches_invented_counts():
    # Regression: league 11, week 1885. The single-eligible-player path built no
    # scenario text, so the guard used to fail open and shipped "This is their
    # 3rd win this season" on what was the player's 1st win.
    sent = "🎉 Brent wins with a solid 15! 🏆 RACE OVER. This is their 3rd win this season! 🎊"
    assert find_violations(sent, None)
    assert find_violations(sent, "")


def test_no_scenario_still_catches_invented_stakes():
    assert find_violations("Brent wins and clinches the season! 🏆", None)


def test_no_scenario_plain_message_passes():
    # Without a win count or stakes language there is nothing to contradict.
    assert find_violations("🏆 Brent has it locked at 15! Nice work! 🎉", None) == []


def test_this_season_not_flagged_as_stakes():
    # "this season" must NOT trip the clinch/season detector
    scenario = "RACE OVER! Rally wins the week with 18! This is their 1st win this season."
    msg = "RACE OVER! Rally wins with 18 — their 1st win this season! Nice work! 🎉"
    assert find_violations(msg, scenario) == []


# --- helper-level checks ---

def test_allowed_win_counts_extraction():
    s = "This makes it Fuzwuz's 2nd win and Vox's 1st win this season."
    assert allowed_win_counts(s) == {1, 2}
    assert allowed_win_counts("Brent now has 1, Dani now has 1") == {1}


def test_stakes_detection():
    assert stakes_allowed("SEASON STAKES: ...") is True
    assert stakes_allowed("...Promotion: Jess...") is True
    assert stakes_allowed("RACE OVER! plain weekly win.") is False


def test_fallback_message_is_factual():
    scenario = "RACE OVER! Rally wins the week with 18! This is their 1st win this season."
    out = build_fallback_message(scenario)
    assert "Rally" in out and "1st win" in out
    assert find_violations(out, scenario) == []  # the template must pass its own check


# --- stripping, used when there is no scenario text to rebuild from ---

def test_strip_removes_only_the_invented_sentence():
    sent = "🎉 Brent wins with a solid 15! 🏆 No contenders left. This is their 3rd win this season! 🎊"
    out = strip_unsupported_sentences(sent, None)
    assert "Brent wins with a solid 15" in out
    assert "No contenders left" in out
    assert "3rd win" not in out
    assert find_violations(out, None) == []


def test_strip_keeps_supported_counts():
    scenario = "RACE OVER! Rally wins the week with 18! This is their 2nd win this season."
    sent = "RACE OVER! Rally wins with 18! Their 2nd win this season! 🎉"
    assert strip_unsupported_sentences(sent, scenario) == sent


def test_strip_returns_empty_when_nothing_survives():
    assert strip_unsupported_sentences("Their 4th win clinches the season!", None) == ""


# --- eliminated players must not be described as merely needing more games ---
#
# League 1, week 1947. The scenario had already worked out that Joanna was out
# (4 of 5 games, best-4 of 18, leader on 16 — even a 1 lands her on 19), but the
# names were dropped before the AI saw them, so it grouped her by game count
# with two players who had not played at all.

_ELIM_SCENARIO = (
    "Tony leads at 16. Nanna (at 17) needs a solid 3 to win or a 4 to tie "
    "(replacing a 5). No one else can catch up — Brent, Gene and Joanna "
    "are out of contention"
)


def test_eliminated_names_parsed_from_scenario():
    assert eliminated_names(_ELIM_SCENARIO) == {"Brent", "Gene", "Joanna"}


def test_eliminated_names_handles_single_player():
    s = "No one else can catch up — Gene is out of contention"
    assert eliminated_names(s) == {"Gene"}


def test_flags_eliminated_player_described_as_needing_games():
    msg = ("Tony leads with 16, but hasn't posted yet. Brent and Gene are out of "
           "contention. Joanna, Evan, and Malia need more games.")
    issues = find_violations(msg, _ELIM_SCENARIO)
    assert any("Joanna" in i and "out of contention" in i for i in issues)


def test_oxford_comma_does_not_hide_the_contradiction():
    with_oxford = "Joanna, Evan, and Malia need more games."
    without = "Joanna, Evan and Malia need more games."
    assert find_violations(with_oxford, _ELIM_SCENARIO)
    assert find_violations(without, _ELIM_SCENARIO)


def test_does_not_flag_players_who_genuinely_need_games():
    # Evan and Malia have no games at all and are not in the scenario's out list.
    msg = "Tony leads with 16. Evan and Malia need more games."
    assert find_violations(msg, _ELIM_SCENARIO) == []


def test_correct_grouping_passes_clean():
    msg = ("Tony leads with 16. Brent, Gene and Joanna are out of contention. "
           "Evan and Malia need more games.")
    assert find_violations(msg, _ELIM_SCENARIO) == []


def test_silent_when_scenario_names_nobody():
    # No "out of contention" line means nothing to contradict — stay quiet.
    assert find_violations("Joanna needs more games.", "Tony leads at 16.") == []
