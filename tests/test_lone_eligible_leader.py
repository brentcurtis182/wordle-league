"""Unit tests for the week where only ONE player has qualified yet.

Pure tests — no clock, DB, or OpenAI. They build standings dicts by hand and
assert on the deterministic scenario text / qualifier set.

Regression origin (Alchemer Wordle Starz / league 44, week 1927, 2026-10-04):
Brent was the only player with 5+ valid scores (best-5 = 20). Andreas sat on 4
scores totalling 17 and had not posted — a 3 ties, a 2 wins. The Sunday update
announced "RACE OVER! Brent wins the week with 20!".

Cause: the one-eligible-player shortcut filtered challengers with
`current_total + 6 <= leader_total` — whether their WORST possible score still
beats the leader. That is a guaranteed-win test, not a can-they-still-win test,
so every live challenger was dropped, `potential_qualifiers` came back empty,
and the builder took the "truly locked" path without ever consulting
`compute_player_scenario` (which had the correct math all along). The AI relayed
the scenario faithfully, so the fact-check guard could not have caught it — the
guard validates the message AGAINST this text.

The shortcut existed in both paths; the division copy had no check at all and
returned "LOCKED" unconditionally. Both now share `find_potential_qualifiers`.
"""
from sunday_race_update import build_division_scenario, find_potential_qualifiers

MIN_SCORES = 5
WINS_NEEDED = 3


def _eligible(name, total, posted_today, scores):
    return {
        'name': name,
        'eligible': True,
        'best_5_total': total,
        'days_posted': len(scores),
        'posted_today': posted_today,
        'scores': scores,
    }


def _one_short(name, posted_today, scores):
    """A player with 4 of 5 games — not yet eligible, can qualify by posting."""
    return {
        'name': name,
        'eligible': False,
        'best_5_total': None,
        'days_posted': len(scores),
        'posted_today': posted_today,
        'scores': scores,
    }


# League 44, week 1927, exactly as it stood when the message was generated.
BRENT = _eligible('Brent', 20, True,
                  {1928: 3, 1929: 7, 1930: 3, 1931: 5, 1932: 5, 1933: 4})
ANDREAS = _one_short('Andreas', False, {1928: 3, 1929: 6, 1930: 4, 1931: 4})   # 17
LIZZIE = _one_short('Lizzie', False, {1928: 3, 1929: 6, 1930: 5, 1931: 5})     # 19
AJ = _one_short('AJ', False, {1928: 5, 1929: 7, 1930: 7, 1931: 5})             # 2 valid


def _scenario(standings, weekly_wins=None, div_num=1):
    # build_division_scenario mutates weekly_wins in place — hand it a fresh dict.
    return build_division_scenario(
        standings, div_num, dict(weekly_wins or {}), 1,
        min_scores=MIN_SCORES, wins_for_season=WINS_NEEDED,
    )


# --- root cause: the qualifier filter ---

def test_challenger_who_can_still_tie_is_a_qualifier():
    """Andreas at 17 needs a 3 to reach 20. 17+6 > 20 but 17+1 <= 20."""
    out = find_potential_qualifiers([BRENT, ANDREAS], 20, MIN_SCORES)
    assert [p['name'] for p in out] == ['Andreas']


def test_challenger_who_needs_a_perfect_score_is_still_a_qualifier():
    """Lizzie at 19 can only tie, and only with a 1 — unlikely, but not over."""
    out = find_potential_qualifiers([BRENT, LIZZIE], 20, MIN_SCORES)
    assert [p['name'] for p in out] == ['Lizzie']


def test_mathematically_eliminated_challenger_is_not_a_qualifier():
    """At 19 against a leader on 17, even a 1 finishes at 20. Done."""
    out = find_potential_qualifiers([BRENT, LIZZIE], 17, MIN_SCORES)
    assert out == []


def test_player_too_many_games_short_is_not_a_qualifier():
    """AJ has two 7s — only 2 valid scores, so today cannot get him to 5."""
    out = find_potential_qualifiers([BRENT, AJ], 20, MIN_SCORES)
    assert out == []


def test_eligible_players_are_never_qualifiers():
    """This filter is only about players who have not qualified yet."""
    out = find_potential_qualifiers([BRENT], 99, MIN_SCORES)
    assert out == []


# --- the bug, end to end ---

def test_lone_eligible_leader_is_not_locked_while_a_challenger_lives():
    out = _scenario([BRENT, ANDREAS, LIZZIE, AJ], {})
    assert 'RACE OVER' not in out
    assert 'LOCKED' not in out


def test_live_challenger_is_told_what_they_need():
    """Silence is not enough — the message has to state the actual scenario."""
    out = _scenario([BRENT, ANDREAS, LIZZIE, AJ], {})
    assert 'Brent leads at 20' in out
    assert 'Andreas' in out
    assert 'to win' in out and 'to tie' in out


def test_lone_eligible_leader_does_not_announce_season_clinch():
    """Clinch detection keys off the same decided-race flag."""
    out = _scenario([BRENT, ANDREAS, LIZZIE, AJ], {'Brent': WINS_NEEDED - 1})
    assert 'SEASON CLINCH' not in out
    assert 'SEASON STAKES' in out


# --- cases that must STILL be locked (guarding against over-correction) ---

def test_lone_eligible_leader_is_locked_when_no_one_can_reach_them():
    leader = _eligible('Brent', 15, True,
                       {1928: 3, 1929: 3, 1930: 3, 1931: 3, 1932: 3})
    out = _scenario([leader, LIZZIE, AJ], {})
    assert 'LOCKED' in out


def test_lone_eligible_leader_is_locked_when_everyone_else_is_far_short():
    leader = _eligible('Brent', 20, True,
                       {1928: 3, 1929: 7, 1930: 3, 1931: 5, 1932: 5, 1933: 4})
    out = _scenario([leader, AJ], {})
    assert 'LOCKED' in out
