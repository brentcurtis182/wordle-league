"""Unit tests: relegation/promotion lines must always state WHY.

Pure tests — no clock, DB, or OpenAI.

Regression origin (Belly Up / league 7, week 1927, 2026-10-04): the Sunday
message said "Relegation: If the season ends today, Dave would be relegated to
Division II." with no reason. The league page's Season Total column showed Dave
on 63 — the best score in Division I — so the message read as a flat
contradiction and looked like a bug.

It was not. Dave had a missed week, and missed weeks rank above season total in
relegation_sort_key. The reason that matters is structural: Season Total is a
SUM across weeks, so a short week contributes fewer scores and a player who
misses games ends up with a LOWER (apparently better) total. Dave's 4-game week
contributed 15 where a full week contributed 16-18. Ranking missed weeks first
exists to undo exactly that, and the message has to say so or it is unreadable.

Two separate defects produced the bare claim:
  1. The deterministic text omitted the reason whenever MORE than one player was
     going down or coming up (and attached only the first player's otherwise).
  2. The AI paraphrased the line and dropped the parenthetical that was there.
     The guard cannot catch that — it only flags claims the AI ADDS, never facts
     it drops. Fixed by appending these lines verbatim instead of letting the
     model rewrite them.
"""
from sunday_race_update import _standing_reason, _names_with_reasons


# --- the reason string itself ---

def test_missed_week_is_named_not_just_the_total():
    assert _standing_reason(63, 1) == "63 total, 1 missed wk"


def test_multiple_missed_weeks_pluralise():
    assert _standing_reason(70, 2) == "70 total, 2 missed wks"


def test_clean_record_states_the_total():
    assert _standing_reason(69, 0) == "Season Total 69"


# --- every named player carries their own reason ---

def test_single_player_gets_a_reason():
    out = _names_with_reasons([('Dave', 63, 1, 1)])
    assert out == "Dave (63 total, 1 missed wk)"


def test_every_player_gets_a_reason_not_just_the_first():
    """The old code attached _why() to candidates[0] only, or omitted it
    entirely when relegated_count > 1."""
    out = _names_with_reasons([('Dave', 63, 1, 1), ('Sam', 70, 0, 0)])
    assert out == "Dave (63 total, 1 missed wk) and Sam (Season Total 70)"


def test_reason_is_never_empty_for_any_player():
    entries = [('A', 60, 0, 3), ('B', 61, 2, 0), ('C', 59, 1, 1)]
    out = _names_with_reasons(entries)
    for name in ('A', 'B', 'C'):
        assert f"{name} (" in out, f"{name} was named without a reason"
    assert out.count('(') == 3


def test_league_7_week_1927_line_reads_correctly():
    """The exact case that prompted this: the sentence must explain itself."""
    line = (f"Relegation: If the season ends today, "
            f"{_names_with_reasons([('Dave', 63, 1, 1)])} "
            f"would be relegated to Division II.")
    assert line == ("Relegation: If the season ends today, "
                    "Dave (63 total, 1 missed wk) would be relegated to Division II.")
    assert "missed wk" in line  # the bit that was missing
