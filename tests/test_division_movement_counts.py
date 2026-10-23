"""Per-division movement counts, the 3-division size floor, and the audit's math.

DB-free. Pins:
  - which count each division uses (Division II has its own pair only in
    3-division mode; NULL means the league pair; 2-division leagues ignore it)
  - what the public Rules tab and the dashboard panel show for each case
  - the Monday audit's independent season math, including the final-week bug:
    a season's last week must count all seven days, not just its Monday
The real promotion/relegation code against a database is covered by
test_division_movement_db.py.
"""
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from league_data_adapter import division_movement_counts, MIN_DIVISION_SIZE_AFTER_MOVES  # noqa: E402
from html_generator_v2 import generate_rules_html  # noqa: E402
import dashboard  # noqa: E402
from division_audit import season_stats, pick  # noqa: E402


# --- which count applies where ---------------------------------------------

def test_two_divisions_use_the_league_pair():
    assert division_movement_counts(2, 1, 1) == {1: {'relegation': 1}, 2: {'promotion': 1}}
    assert division_movement_counts(2, 3, 2) == {1: {'relegation': 2}, 2: {'promotion': 3}}


def test_two_divisions_ignore_the_division_ii_pair():
    # In two divisions, Division II is the bottom: it only promotes, and that
    # is the league pair's job. A stale Division II setting from an earlier
    # 3-division spell must not leak in.
    assert division_movement_counts(2, 1, 1, 3, 3) == {1: {'relegation': 1}, 2: {'promotion': 1}}


def test_three_divisions_default_to_the_league_pair():
    assert division_movement_counts(3, 2, 1) == {
        1: {'relegation': 1},
        2: {'promotion': 2, 'relegation': 1},
        3: {'promotion': 2},
    }


def test_three_divisions_division_ii_has_its_own_pair():
    assert division_movement_counts(3, 1, 1, 3, 2) == {
        1: {'relegation': 1},
        2: {'promotion': 3, 'relegation': 2},
        3: {'promotion': 1},
    }
    # Either half can be set alone; the other follows the league pair.
    assert division_movement_counts(3, 1, 2, None, 3)[2] == {'promotion': 1, 'relegation': 3}
    assert division_movement_counts(3, 1, 2, 3, None)[2] == {'promotion': 3, 'relegation': 2}


def test_top_never_promotes_and_bottom_never_relegates():
    for dc in (2, 3):
        counts = division_movement_counts(dc, 2, 2, 3, 3)
        assert 'promotion' not in counts[1]
        assert 'relegation' not in counts[dc]


def test_floor_is_three():
    assert MIN_DIVISION_SIZE_AFTER_MOVES == 3


# --- public Rules tab -----------------------------------------------------------

def _rules(division_count, promoted, relegated, d2p=None, d2r=None):
    data = {
        'division_mode': True, 'division_confirmed_at': datetime(2026, 1, 1),
        'division_count': division_count, 'min_weekly_scores': 5,
        'promoted_count': promoted, 'relegated_count': relegated,
        'movement_counts': division_movement_counts(division_count, promoted, relegated, d2p, d2r),
        'ai_settings': {},
    }
    return re.sub(r'<[^>]+>', '', generate_rules_html(data))


def test_rules_two_divisions_single_sentence_no_floor():
    text = _rules(2, 2, 1)
    assert 'top 2 players in a division move up' in text
    assert 'bottom 1 player drop' in text
    assert 'set to promote 2 and relegate 1 each season' in text
    assert 'fewer than 3 players' not in text  # the floor is a 3-division rule


def test_rules_three_divisions_same_everywhere_keeps_one_sentence():
    text = _rules(3, 1, 1)
    assert 'set to promote 1 and relegate 1 each season' in text
    assert 'Division II: promote' not in text
    assert 'fewer than 3 players' in text


def test_rules_three_divisions_lists_each_division_once_they_differ():
    text = _rules(3, 2, 2, 3, None)
    assert 'Division I: relegate 2' in text
    assert 'Division II: promote 3 and relegate 2' in text
    assert 'Division III: promote 2' in text
    assert 'How many depends on the division' in text
    assert 'set to promote 2 and relegate 2 each season' not in text


# --- dashboard panel ----------------------------------------------------------------

def _panel(division_count, promoted, relegated, d2p=None, d2r=None):
    league = {'id': 1, 'division_locked': True, 'division_confirmed_at': datetime(2026, 1, 1),
              'promoted_count': promoted, 'relegated_count': relegated,
              'division_count': division_count, 'div2_promoted_count': d2p,
              'div2_relegated_count': d2r, 'channel_type': 'slack'}
    players = [{'id': i, 'name': f'P{i}', 'division': 1 + i % division_count,
                'division_immunity': False} for i in range(12)]
    return dashboard._render_division_players(league, players, True)


def _selected(html, el_id):
    m = re.search(rf'<select id="{el_id}".*?</select>', html, re.S)
    assert m, f'{el_id} missing'
    return int(re.search(r'<option value="(\d)" selected', m.group(0)).group(1))


def test_panel_two_divisions_has_only_the_league_pair():
    html = _panel(2, 2, 1)
    assert re.findall(r'<select id="(\w+)"', html) == ['promotedCount', 'relegatedCount']
    assert _selected(html, 'promotedCount') == 2
    assert _selected(html, 'relegatedCount') == 1


def test_panel_three_divisions_groups_by_division_with_division_ii_levers():
    html = _panel(3, 2, 1, 3, None)
    assert re.findall(r'<select id="(\w+)"', html) == [
        'relegatedCount', 'div2PromotedCount', 'div2RelegatedCount', 'promotedCount']
    assert _selected(html, 'relegatedCount') == 1      # Division I relegated
    assert _selected(html, 'div2PromotedCount') == 3   # its own value
    assert _selected(html, 'div2RelegatedCount') == 1  # NULL shows the league pair
    assert _selected(html, 'promotedCount') == 2       # Division III promoted
    for label in ('DIVISION I', 'DIVISION II', 'DIVISION III'):
        assert label in html


# --- the audit's independent math -------------------------------------------------

S = 1900  # a season-start Monday wordle
OLD = datetime(2026, 1, 7, 20, 0)  # created long before, a Wednesday


def _week(start, scores):
    return [(start + i, s) for i, s in enumerate(scores)]


def test_final_week_counts_all_seven_days():
    # Regression for the bug fixed in eb82e28aca: the season's end is stored as
    # its last MONDAY, and only that Monday used to count.
    scores = _week(S, [3, 3, 3, 3, 3, 3, 3]) + _week(S + 7, [6, 1, 1, 1, 1, 1, 1])
    missed, total = season_stats(scores, S, S + 7, None, OLD, 5)
    assert missed == 0
    assert total == 15 + 5  # best 5 of the final week are the 1s, not the Monday 6


def test_missed_week_and_partial_total():
    scores = _week(S, [3, 3, 3, 3, 3]) + _week(S + 7, [2, 2, 7, 7])  # two fails = X
    missed, total = season_stats(scores, S, S + 7, None, OLD, 5)
    assert missed == 1
    assert total == 15 + 4  # a short week still adds what it has


def test_counting_starts_at_the_join_week():
    scores = _week(S, [6, 6, 6, 6, 6]) + _week(S + 7, [2, 2, 2, 2, 2])
    missed, total = season_stats(scores, S, S + 7, S + 9, OLD, 5)
    assert (missed, total) == (0, 10)  # joined mid week 2: week 1 never counts


def test_added_wednesday_gets_first_week_grace_monday_does_not():
    wed = datetime(2026, 10, 22, 18, 0)  # Thursday UTC 18:00 = Thursday Pacific
    mon = datetime(2026, 10, 19, 18, 0)  # Monday Pacific
    week_start = 1948                     # Monday 2026-10-19
    scores = _week(week_start + 3, [3, 3, 3, 3])
    assert season_stats(scores, week_start, week_start, None, wed, 5)[0] == 0
    assert season_stats(scores, week_start, week_start, None, mon, 5)[0] == 1


def test_pick_fills_spots_and_flags_a_genuine_tie_only():
    ranked = [((0, 10, -1), 'A'), ((0, 12, 0), 'B'), ((0, 12, 0), 'C'), ((0, 15, 0), 'D')]
    assert pick(ranked, 1) == (['A'], [], 0)
    assert pick(ranked, 3) == (['A', 'B', 'C'], [], 0)
    assert pick(ranked, 2) == (['A'], ['B', 'C'], 1)   # one spot, two dead level
    assert pick(ranked, 0) == ([], [], 0)
