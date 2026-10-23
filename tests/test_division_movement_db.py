"""Real promotion/relegation code against the STAGING database, fully rolled back.

Builds a made-up Division II season on staging's 3-division test league inside
ONE transaction, runs the actual season-end functions, checks who moved, runs
the Monday audit over the result, then rolls everything back. Nothing is ever
committed.

Covers what the DB-free tests can't:
  - Division II's own promote/relegate counts reach the real code
  - the season's final week counts all seven days (eb82e28aca)
  - the 3-player floor holds relegation back
  - the independent audit agrees with the real moves
  - turning divisions on / switching 2<->3 resets every count to 1

Skipped unless WPL_STAGING_DB_URL is set to staging's public Postgres URL:
    WPL_STAGING_DB_URL=... pytest tests/test_division_movement_db.py
It refuses to run against a database without the staging test league, so it
can never touch prod data.
"""
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

STAGING_URL = os.environ.get('WPL_STAGING_DB_URL')
pytestmark = pytest.mark.skipif(not STAGING_URL, reason='WPL_STAGING_DB_URL not set')

LEAGUE = 27              # staging alchemer-wordle-starz, 3 divisions
LEAGUE_SLUG = 'alchemer-wordle-starz'
WORDLE_ZERO = date(2021, 6, 19)


@pytest.fixture
def sandbox(monkeypatch):
    """One shared connection for every module; commit/close are no-ops and the
    whole test is rolled back at the end."""
    os.environ['DATABASE_URL'] = STAGING_URL
    import psycopg2
    import league_data_adapter as lda
    import division_manager as dm
    import division_audit as da

    real = psycopg2.connect(STAGING_URL)
    # The season-end code forwards winners via twilio_webhook_app; importing
    # that boots the whole app (and its startup ALTERs block on this
    # transaction). A stub makes the forward a no-op.
    import types
    monkeypatch.setitem(sys.modules, 'twilio_webhook_app', types.SimpleNamespace(
        forward_season_winner_to_staging=lambda *a, **k: None,
        forward_weekly_winner_to_staging=lambda *a, **k: None))

    class Shared:
        def commit(self): pass
        def rollback(self): pass
        def close(self): pass
        def cursor(self): return real.cursor()

    shared = Shared()
    for mod in (lda, dm, da):
        monkeypatch.setattr(mod, 'get_db_connection', lambda *a, **k: shared)
    cur = real.cursor()
    cur.execute("SELECT slug, COALESCE(division_count, 2) FROM leagues WHERE id = %s", (LEAGUE,))
    row = cur.fetchone()
    if not row or row[0] != LEAGUE_SLUG:
        real.close()
        pytest.skip('not the staging database')
    try:
        yield cur, lda, dm, da
    finally:
        real.rollback()
        real.close()


def _build_division_ii_season(cur, lda, promoted, relegated, d2_promoted, d2_relegated):
    """Three-week Division II season ending last week, 6 players, scores chosen
    so the result depends on the whole final week. Returns (W, names)."""
    this_week = lda.calculate_wordle_number(lda.get_week_start_date())
    W = this_week - 7
    S = W - 14
    cur.execute("UPDATE leagues SET division_count = 3, promoted_count = %s, relegated_count = %s, "
                "div2_promoted_count = %s, div2_relegated_count = %s, "
                "division_confirmed_at = %s WHERE id = %s",
                (promoted, relegated, d2_promoted, d2_relegated, datetime(2026, 1, 1), LEAGUE))
    cur.execute("SELECT id FROM players WHERE league_id = %s AND active ORDER BY name", (LEAGUE,))
    ids = [r[0] for r in cur.fetchall()]
    div2 = ids[:6]
    names = ['Champ', 'Fullweek', 'Mondayonly', 'Middle', 'Steady', 'Worst']
    for i, pid in enumerate(ids):
        d = 2 if pid in div2 else (1 if i % 2 else 3)
        cur.execute("UPDATE players SET division = %s, division_immunity = FALSE, division_joined_week = %s, "
                    "created_at = %s WHERE id = %s", (d, S, datetime(2026, 1, 7, 20), pid))
    for pid, nm in zip(div2, names):
        cur.execute("UPDATE players SET name = %s WHERE id = %s", (nm, pid))
    # Only Division II posts this season, so Divisions I and III have no
    # eligible weekly winner and nothing else in the league interferes.
    cur.execute("DELETE FROM scores WHERE player_id = ANY(%s) AND wordle_number >= %s", (ids, S))
    cur.execute("DELETE FROM weekly_winners WHERE league_id = %s AND week_wordle_number >= %s", (LEAGUE, S))
    cur.execute("DELETE FROM division_movements WHERE league_id = %s", (LEAGUE,))
    cur.execute("UPDATE division_seasons SET current_season = 1, season_start_week = %s WHERE league_id = %s", (S, LEAGUE))
    cur.execute("DELETE FROM division_season_boundaries WHERE league_id = %s", (LEAGUE,))
    for d in (1, 2, 3):
        cur.execute("INSERT INTO division_season_boundaries (league_id, division, season_number, start_week, end_week) "
                    "VALUES (%s, %s, 1, %s, NULL)", (LEAGUE, d, S))

    # Per-week scores (7 days). Everyone posts every day; no missed weeks.
    plan = {
        'Champ':      [[1] * 7, [1] * 7, [1] * 7],   # wins all three weeks outright (5)
        # Fullweek vs Mondayonly is decided by the final week's Tue-Sun only:
        # Monday-only math picks Mondayonly, the real (full-week) math Fullweek.
        'Fullweek':   [[4] * 7, [4] * 7, [6, 1, 1, 1, 1, 2, 2]],
        'Mondayonly': [[4] * 7, [4] * 7, [1, 3, 3, 3, 3, 3, 3]],
        'Middle':     [[5] * 7, [5] * 7, [5] * 7],
        'Steady':     [[5] * 7, [5] * 7, [4] * 7],
        'Worst':      [[6] * 7, [6] * 7, [6] * 7],
    }
    for pid, nm in zip(div2, names):
        for w, week_scores in enumerate(plan[nm]):
            for day, sc in enumerate(week_scores):
                n = S + 7 * w + day
                cur.execute("INSERT INTO scores (player_id, wordle_number, score, date) VALUES (%s, %s, %s, %s)",
                            (pid, n, sc, WORDLE_ZERO + timedelta(days=n)))
    champ_id = div2[0]
    for wk in (S, S + 7, W):
        cur.execute("INSERT INTO weekly_winners (league_id, player_id, week_wordle_number, player_name, score, division) "
                    "VALUES (%s, %s, %s, 'Champ', 5, 2)", (LEAGUE, champ_id, wk))
    return W


def _run_season_end(cur, dm, da, W):
    da.save_pre_move_snapshot(LEAGUE, W)
    assert dm.check_division_season_transition(LEAGUE, 2)
    dm.check_division_relegation(LEAGUE, 2)
    cur.execute("SELECT name, division FROM players WHERE league_id = %s AND active", (LEAGUE,))
    return dict(cur.fetchall())


def _audit(cur, da, W):
    cur.execute("SELECT id, name, COALESCE(division_count, 2), promoted_count, relegated_count, "
                "COALESCE(min_weekly_scores, 5), COALESCE(season_wins, 3), division_confirmed_at, "
                "div2_promoted_count, div2_relegated_count FROM leagues WHERE id = %s", (LEAGUE,))
    r = cur.fetchone()
    min_scores = r[5] if 3 <= r[5] <= 7 else 5
    return da.audit_league(cur, (r[0], r[1], r[2], r[3], r[4], min_scores, r[6], r[7], r[8], r[9]), W)


def test_division_ii_counts_and_full_final_week(sandbox):
    cur, lda, dm, da = sandbox
    # League pair 1/1, Division II overridden to promote 2, relegate 1.
    W = _build_division_ii_season(cur, lda, 1, 1, 2, 1)
    div = _run_season_end(cur, dm, da, W)
    assert div['Champ'] == 1                      # champion always up
    assert div['Fullweek'] == 1                   # 2nd spot: decided by the WHOLE final week
    assert div['Mondayonly'] == 2                 # would have gone up under the old bug
    assert div['Worst'] == 3                      # Division II's relegation
    assert sum(1 for d in div.values() if d == 2) == 3
    report = _audit(cur, da, W)
    assert report['issues'] == [], report['issues']


def test_floor_holds_relegation_back(sandbox):
    cur, lda, dm, da = sandbox
    # Division II set to promote 3 and relegate 3 with only 6 players:
    # 3 go up, which leaves 3, so the floor allows nobody down.
    W = _build_division_ii_season(cur, lda, 1, 1, 3, 3)
    div = _run_season_end(cur, dm, da, W)
    assert sum(1 for d in div.values() if d == 2) == 3
    assert div['Worst'] == 2                      # held by the floor
    report = _audit(cur, da, W)
    assert report['issues'] == [], report['issues']
    moves = [t for title, lines in report['sections'] if title == 'Seasons and movements' for _, t in lines]
    assert any('held to 0 by the 3-player floor' in t for t in moves), moves


def test_switching_division_count_resets_counts_to_one(sandbox):
    cur, lda, dm, da = sandbox
    cur.execute("UPDATE leagues SET division_mode = TRUE, division_count = 3, promoted_count = 3, "
                "relegated_count = 2, div2_promoted_count = 2, div2_relegated_count = 3 WHERE id = %s", (LEAGUE,))
    result = dm.change_division_count(LEAGUE, 2)
    assert result['success'], result
    cur.execute("SELECT promoted_count, relegated_count, div2_promoted_count, div2_relegated_count "
                "FROM leagues WHERE id = %s", (LEAGUE,))
    assert cur.fetchone() == (1, 1, None, None)
