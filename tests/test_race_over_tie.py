"""Unit tests for when the Sunday race is allowed to be declared OVER.

Pure tests — no clock, DB, or OpenAI. They build standings dicts by hand and
assert on the deterministic scenario text that gets fed to the AI.

Regression origin (PAL / league 3, week 1857, 2026-07-26): Kat and Vox were
both at 17 (best-4 of 7) on Sunday morning, with Vox still holding two unplayed
days. The update announced a shared win for both. Vox then posted a 3, finished
at 15, and won outright — Kat got nothing.

Cause: a tied leader who hadn't posted was classified 'can_improve' rather than
'can_catch_up', so `players_who_can_catch_up` came back empty, `race_is_decided`
flipped True, and the builder wrote "RACE OVER!" into the prompt. The AI relayed
it faithfully — this was NOT an AI narration bug, so the message fact-check
guard could not have caught it.

`compute_player_scenario` is shared by BOTH the division and non-division paths,
so the classification test below covers the non-division path too (which can't
be exercised directly — it's inline in send_sunday_race_update, behind the DB
and an OpenAI call).
"""
from sunday_race_update import build_division_scenario, compute_player_scenario


def _player(name, total, posted_today, scores, eligible=True):
    """One row of division standings."""
    return {
        'name': name,
        'eligible': eligible,
        'best_5_total': total,
        'posted_today': posted_today,
        'scores': scores,
    }


# PAL week 1857, as it stood when the Sunday message was generated.
# Kat had posted Mon-Sat; Vox had skipped Saturday and not yet posted Sunday.
# Both sit at 17 on a best-4 league.
KAT = _player('Kat', 17, True, {1857: 4, 1858: 5, 1859: 6, 1860: 4, 1861: 4, 1862: 6})
VOX = _player('Vox', 17, False, {1857: 5, 1858: 4, 1859: 6, 1860: 4, 1861: 4})

MIN_SCORES = 4          # PAL is best-4 of 7
WINS_NEEDED = 3         # division seasons need 3 wins


def _scenario(standings, weekly_wins=None, div_num=1):
    # build_division_scenario mutates weekly_wins in place — hand it a fresh dict.
    return build_division_scenario(
        standings, div_num, dict(weekly_wins or {}), 11,
        min_scores=MIN_SCORES, wins_for_season=WINS_NEEDED,
    )


# --- root cause (shared by both the division and non-division paths) ---

def test_tied_unposted_leader_is_classified_can_improve():
    """A tied leader who hasn't posted is 'can_improve', never 'can_catch_up'.

    This is why the race looked decided: the catch-up list stayed empty even
    though Vox could still overtake Kat.
    """
    text, status = compute_player_scenario(
        VOX, leader_total=17, leader_names=['Kat', 'Vox'], min_scores=MIN_SCORES,
    )
    assert status == 'can_improve'
    assert text  # must produce text, or the tie-break can't be surfaced


# --- the bug ---

def test_breakable_tie_is_not_declared_over():
    out = _scenario([KAT, VOX], {'Vox': 1})
    assert 'RACE OVER' not in out
    assert 'share the weekly win' not in out


def test_breakable_tie_explains_it_can_still_break():
    """Not enough to stay silent — the message must say the tie is still live."""
    out = _scenario([KAT, VOX], {'Vox': 1})
    assert 'tied at 17' in out
    assert 'Vox' in out and "hasn't posted" in out


def test_breakable_tie_does_not_announce_season_clinch():
    """Clinch detection keys off the same flag, so a breakable tie must yield
    conditional STAKES wording, never a definitive CLINCH."""
    out = _scenario([KAT, VOX], {'Kat': WINS_NEEDED - 1, 'Vox': 1})
    assert 'SEASON CLINCH' not in out
    assert 'SEASON STAKES' in out


# --- cases that must STILL be declared over (guarding against over-correction) ---

def test_genuine_shared_win_when_everyone_posted():
    vox_posted = dict(VOX, posted_today=True)
    out = _scenario([KAT, vox_posted], {'Vox': 1})
    assert 'RACE OVER' in out
    assert 'share the weekly win' in out


def test_lone_leader_who_hasnt_posted_still_ends_race():
    """A single leader's ability to improve is irrelevant — if nobody can catch
    them the race is over, even with the leader yet to post."""
    leader = _player('Kat', 14, False, {1857: 3, 1858: 3, 1859: 4, 1860: 4, 1861: 6})
    trailer = _player('Vox', 25, True, {1857: 6, 1858: 6, 1859: 6, 1860: 7, 1861: 6})
    out = _scenario([leader, trailer], {'Kat': 1})
    assert 'RACE OVER' in out


def test_clear_winner_keeps_correct_ordinal():
    """The pending win is still added exactly once for the outright winner."""
    leader = _player('Kat', 14, True, {1857: 3, 1858: 3, 1859: 4, 1860: 4, 1861: 6})
    trailer = _player('Vox', 25, True, {1857: 6, 1858: 6, 1859: 6, 1860: 7, 1861: 6})
    out = _scenario([leader, trailer], {'Kat': 1})
    assert 'This is their 2nd win this season' in out
