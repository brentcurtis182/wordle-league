#!/usr/bin/env python3
"""Monday audit of division movements and immunity.

Runs after the Monday reset job has recorded last week's winners and handled
any season ends. For every confirmed division league it re-derives, from raw
scores, what SHOULD have happened and compares it with what the database says
DID happen:

  - weekly winners per division for the week that just ended
  - whether each division's season ended exactly when someone hit the target,
    and whether the right champion(s) were recorded
  - who should have been promoted and relegated (winner first, then fewest
    missed weeks, then lowest season total, then most weekly wins, and a random
    draw only on a genuine tie of all three) and whether the draw was genuine
  - every player's immunity: each immune player must have a reason, and anyone
    who should be immune must be
  - division sizes after the moves

Independence matters. This file deliberately does NOT call the functions in
division_manager that make these decisions. A checker that reuses the code it
is checking always agrees with it - that is how the final-week bug (only the
last Monday of a season counted) went unnoticed. It shares only calendar
helpers and the database.

The Monday job saves a 'pre_monday' snapshot (save_pre_move_snapshot) before
anyone moves, so "who was in the division and who was immune" is read, not
guessed. Without one the audit reconstructs it and says so.

The email sends every week, issues or not, so silence means the audit broke.

Usage:
    python division_audit.py              # audit the week that just ended
    python division_audit.py --week 1934  # audit a specific week (its Monday wordle)
    python division_audit.py --dry-run    # print instead of emailing
"""
import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta, timezone, date

import pytz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from league_data_adapter import get_db_connection, calculate_wordle_number, get_week_start_date

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

REPORT_EMAILS = ['brentcurtis182@gmail.com']
PACIFIC = pytz.timezone('America/Los_Angeles')
WORDLE_ZERO = date(2021, 6, 19)
ROMAN = {1: 'I', 2: 'II', 3: 'III'}
SIZE_FLOOR = 3          # a division below this many active players gets flagged
SNAPSHOT_TYPE = 'pre_monday'


def wordle_to_date(n):
    return WORDLE_ZERO + timedelta(days=n)


def pacific_date(ts):
    """players.created_at / division_movements.created_at are naive UTC."""
    if ts is None:
        return None
    return pytz.utc.localize(ts).astimezone(PACIFIC).date()


def week_on_grid(n, anchor):
    return n - ((n - anchor) % 7)


# ---------------------------------------------------------------------------
# Snapshot hook (called by the Monday job BEFORE any season transition)
# ---------------------------------------------------------------------------

def save_pre_move_snapshot(league_id, week):
    """Record every player's division/immunity and each division's season
    before the Monday job moves anyone. `week` is the Monday wordle of the week
    that just ended. Never overwrites a snapshot already taken for the same
    week, so a re-run after the moves cannot replace the real 'before'.
    Fail-safe: logs and returns on any error, never blocks the reset."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT snapshot_data FROM division_snapshots
            WHERE league_id = %s AND snapshot_type = %s
        """, (league_id, SNAPSHOT_TYPE))
        row = cur.fetchone()
        if row and row[0] and row[0].get('week') == week:
            return
        cur.execute("""
            SELECT id, name, active, division, division_immunity, division_joined_week
            FROM players WHERE league_id = %s
        """, (league_id,))
        players = [{'id': r[0], 'name': r[1], 'active': r[2], 'division': r[3],
                    'immune': bool(r[4]), 'joined_week': r[5]} for r in cur.fetchall()]
        cur.execute("""
            SELECT division, current_season, season_start_week
            FROM division_seasons WHERE league_id = %s
        """, (league_id,))
        seasons = {str(r[0]): {'season': r[1], 'start': r[2]} for r in cur.fetchall()}
        data = {'week': week, 'players': players, 'seasons': seasons,
                'taken_at': datetime.now(timezone.utc).isoformat()}
        cur.execute("""
            INSERT INTO division_snapshots (league_id, snapshot_type, snapshot_data)
            VALUES (%s, %s, %s)
            ON CONFLICT (league_id, snapshot_type) DO UPDATE
            SET snapshot_data = EXCLUDED.snapshot_data, created_at = CURRENT_TIMESTAMP
        """, (league_id, SNAPSHOT_TYPE, json.dumps(data)))
        conn.commit()
    except Exception as e:
        logging.warning(f"pre-move snapshot failed for league {league_id}: {e}")
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# Independent math
# ---------------------------------------------------------------------------

def season_stats(scores, season_start, season_end, joined_week, created_at, min_scores):
    """(missed_weeks, season_total) over [season_start, season_end's Sunday].

    Rules, written out rather than imported:
      - Counting starts at the week the player joined this division (stamped
        on confirm, promotion, relegation or add), never before season start.
        That first week counts in full.
      - The week a player was added is not a missed week, unless they were
        added on a Monday or Tuesday (Pacific): they had the full week.
      - A week with fewer than min_scores non-X scores is a missed week.
      - Season total = sum of the best min_scores non-X scores of every week,
        partial weeks included.
    """
    if joined_week and joined_week > season_start:
        floor = week_on_grid(joined_week, season_start)
    else:
        floor = season_start
    grace = None
    if created_at is not None:
        added = pacific_date(created_at)
        if added.weekday() > 1:
            grace = week_on_grid(calculate_wordle_number(added), season_start)
    missed = total = 0
    w = floor
    while w <= season_end:
        valid = sorted(s for n, s in scores if w <= n < w + 7 and s < 7)
        if len(valid) < min_scores and not (grace is not None and w <= grace):
            missed += 1
        total += sum(valid[:min_scores])
        w += 7
    return missed, total


def pick(ranked, spots):
    """ranked: list of (key, name), best-to-move first. Returns
    (certain_names, tie_names, tie_spots): players certain to move, plus a
    tied group of which exactly tie_spots move by random draw."""
    certain, i = [], 0
    while spots > 0 and i < len(ranked):
        key = ranked[i][0]
        group = [n for k, n in ranked if k == key]
        if len(group) <= spots:
            certain += group
            spots -= len(group)
            i += len(group)
        else:
            return certain, group, spots
    return certain, [], 0


# ---------------------------------------------------------------------------
# Per-league audit
# ---------------------------------------------------------------------------

def audit_league(cur, league, week):
    lid, name, div_count, p_count, r_count, min_scores, target, confirmed_at, d2_p, d2_r = league
    this_week = week + 7
    run_start = datetime.combine(wordle_to_date(this_week), datetime.min.time())  # naive UTC
    run_end = run_start + timedelta(days=7)
    issues, notes, sections = [], [], []

    def label(d):
        return f"Division {ROMAN.get(d, d)}"

    cur.execute("""
        SELECT id, name, active, created_at, division, division_immunity, division_joined_week
        FROM players WHERE league_id = %s
    """, (lid,))
    players = {r[0]: {'id': r[0], 'name': r[1], 'active': r[2], 'created_at': r[3],
                      'division': r[4], 'immune': bool(r[5]), 'joined_week': r[6]}
               for r in cur.fetchall()}
    by_name = {p['name']: p for p in players.values()}

    cur.execute("SELECT division, current_season, season_start_week FROM division_seasons WHERE league_id = %s", (lid,))
    seasons_now = {r[0]: {'season': r[1], 'start': r[2]} for r in cur.fetchall()}
    cur.execute("SELECT division, season_number, start_week, end_week FROM division_season_boundaries WHERE league_id = %s", (lid,))
    bounds = {(r[0], r[1]): (r[2], r[3]) for r in cur.fetchall()}
    cur.execute("""
        SELECT player_name, movement_type, season_number, division, randomized, tied_with, created_at
        FROM division_movements WHERE league_id = %s ORDER BY created_at
    """, (lid,))
    movements = [{'name': r[0], 'type': r[1], 'season': r[2], 'from': r[3], 'random': bool(r[4]),
                  'tied_with': r[5], 'at': r[6],
                  'to': r[3] - 1 if r[1] == 'promotion' else r[3] + 1} for r in cur.fetchall()]
    run_moves = [m for m in movements if m['at'] and run_start <= m['at'] < run_end]
    cur.execute("""
        SELECT sw.division, sw.season_number, p.name, sw.completed_date
        FROM season_winners sw JOIN players p ON p.id = sw.player_id
        WHERE sw.league_id = %s AND sw.division IS NOT NULL
    """, (lid,))
    champs = {}
    for d, sn, pname, _ in cur.fetchall():
        champs.setdefault((d, sn), set()).add(pname)
    cur.execute("""
        SELECT player_name, week_wordle_number, division FROM weekly_winners
        WHERE league_id = %s AND division IS NOT NULL
    """, (lid,))
    ww = cur.fetchall()

    # -- the "before" picture ------------------------------------------------
    cur.execute("SELECT snapshot_data FROM division_snapshots WHERE league_id = %s AND snapshot_type = %s",
                (lid, SNAPSHOT_TYPE))
    srow = cur.fetchone()
    snap = srow[0] if srow and srow[0] and srow[0].get('week') == week else None
    if snap:
        before = {p['id']: p for p in snap['players']}
        seasons_before = {int(k): v for k, v in snap['seasons'].items()}
    else:
        notes.append("No pre-move snapshot for this week, so who was in each division and who was "
                     "immune before the moves is reconstructed from the movement log.")
        before = {pid: {'id': pid, 'name': p['name'], 'active': p['active'], 'division': p['division'],
                        'immune': p['immune'], 'joined_week': p['joined_week']}
                  for pid, p in players.items()}
        for m in run_moves:
            p = by_name.get(m['name'])
            if p:
                before[p['id']]['division'] = m['from']
                before[p['id']]['immune'] = False  # moved players were not immune (else they couldn't move)
                before[p['id']]['joined_week'] = None
        seasons_before = {}
        for d, s in seasons_now.items():
            ended = (d, s['season'] - 1) in bounds and bounds[(d, s['season'] - 1)][1] is not None \
                and s['start'] == this_week
            seasons_before[d] = {'season': s['season'] - 1, 'start': bounds[(d, s['season'] - 1)][0]} \
                if ended else s
        # Immunity cleared this morning cannot be seen; re-derive it for the
        # unmoved players of any division that turned over.
        moved_ids = {by_name[m['name']]['id'] for m in run_moves if m['name'] in by_name}
        for pid, b in before.items():
            d = b['division']
            if pid in moved_ids or d not in seasons_before or not b['active']:
                continue
            if seasons_before[d]['season'] != seasons_now.get(d, {}).get('season'):
                jw = b['joined_week']
                b['immune'] = bool(jw and jw > seasons_before[d]['start'])

    # Raw scores for everyone, once.
    cur.execute("""
        SELECT s.player_id, s.wordle_number, s.score FROM scores s
        JOIN players p ON p.id = s.player_id WHERE p.league_id = %s
    """, (lid,))
    scores = {}
    for pid, n, s in cur.fetchall():
        scores.setdefault(pid, []).append((n, s))

    # -- 1. weekly winners for the week that just ended -------------------------
    wk_lines = []
    relaid = confirmed_at and pacific_date(confirmed_at) > wordle_to_date(week + 6)
    if relaid:
        wk_lines.append(('info', f"Divisions were (re)confirmed on {pacific_date(confirmed_at):%b %d}, after this week ended, "
                                 "so last week's winners were decided under the old layout. Not checked."))
    for d in range(1, div_count + 1):
        if relaid:
            break
        totals = {}
        for pid, b in before.items():
            if not b['active'] or b['division'] != d:
                continue
            valid = sorted(s for n, s in scores.get(pid, []) if week <= n < week + 7 and s < 7)
            if len(valid) >= min_scores:
                totals[b['name']] = sum(valid[:min_scores])
        expected = set()
        if totals:
            best = min(totals.values())
            expected = {n for n, t in totals.items() if t == best}
        recorded = {n for n, wn, dv in ww if wn == week and dv == d}
        shown = ', '.join(sorted(expected)) or 'nobody eligible'
        if expected != recorded:
            issues.append(f"{label(d)} week winner: expected {shown}"
                          f"{' (' + str(min(totals.values())) + ')' if totals else ''}, "
                          f"recorded {', '.join(sorted(recorded)) or 'none'}.")
            wk_lines.append(('bad', f"{label(d)}: expected {shown}, recorded {', '.join(sorted(recorded)) or 'none'}"))
        else:
            wk_lines.append(('ok', f"{label(d)}: {shown}" + (f" ({min(totals.values())})" if totals else '')))
    sections.append(('Weekly winners, week ' + str(week), wk_lines))

    # -- 2. season ends, promotions, relegations -------------------------------
    move_lines = []
    explained_moves = set()
    for d in range(1, div_count + 1):
        sb, sn = seasons_before.get(d), seasons_now.get(d)
        if not sb or not sn:
            issues.append(f"{label(d)} has no season record.")
            continue
        ended = sb['season'] != sn['season']
        S = sb['start']
        if not ended:
            wins = {}
            for n, wn, dv in ww:
                if dv == d and wn >= S:
                    wins[n] = wins.get(n, 0) + 1
            top = max(wins.values()) if wins else 0
            leaders = sorted(n for n, c in wins.items() if c == top) if top else []
            if top >= target:
                issues.append(f"{label(d)} Season {sb['season']} should have ended: "
                              f"{', '.join(leaders)} reached {top} of {target} wins.")
                move_lines.append(('bad', f"{label(d)} Season {sb['season']}: should have ended ({', '.join(leaders)} on {top})"))
            else:
                move_lines.append(('ok', f"{label(d)} Season {sb['season']}: still running"
                                   + (f", leader {', '.join(leaders)} on {top} of {target}" if top else ", no wins yet")))
            continue

        ended_season = sb['season']
        E = bounds.get((d, ended_season), (S, None))[1]
        if E is None:
            issues.append(f"{label(d)} moved to Season {sn['season']} but Season {ended_season} has no end week.")
            continue
        wins = {}
        for n, wn, dv in ww:
            if dv == d and S <= wn <= E:
                wins[n] = wins.get(n, 0) + 1
        top = max(wins.values()) if wins else 0
        exp_champs = {n for n, c in wins.items() if c == top} if top >= target else set()
        got_champs = champs.get((d, ended_season), set())
        if not exp_champs:
            issues.append(f"{label(d)} Season {ended_season} ended but nobody reached {target} wins (top was {top}).")
        if exp_champs != got_champs:
            issues.append(f"{label(d)} Season {ended_season} champion: expected {', '.join(sorted(exp_champs)) or 'none'}, "
                          f"recorded {', '.join(sorted(got_champs)) or 'none'}.")
        if sn['start'] != E + 7:
            issues.append(f"{label(d)} Season {sn['season']} starts at {sn['start']}, expected {E + 7} (week after Season {ended_season}).")
        move_lines.append(('ok' if exp_champs == got_champs and exp_champs else 'bad',
                           f"{label(d)} Season {ended_season} ENDED: champion {', '.join(sorted(got_champs)) or '?'} "
                           f"({top} wins). Season {sn['season']} starts week {sn['start']}."))

        roster = [b for b in before.values() if b['active'] and b['division'] == d]
        win_counts = wins

        def stats_for(b):
            p = players[b['id']]
            return season_stats(scores.get(b['id'], []), S, E, b['joined_week'], p['created_at'], min_scores)

        detail = []
        # Spec, restated: the league pair covers every boundary, except that a
        # 3-division league's Division II has its own pair (NULL = league pair).
        mid = div_count >= 3 and d == 2
        promo_n = (d2_p or p_count) if mid else p_count
        releg_n = (d2_r or r_count) if mid else r_count
        promoted_out = 0
        for direction, count, to_div in (('promotion', promo_n, d - 1), ('relegation', releg_n, d + 1)):
            if not (1 <= to_div <= div_count):
                continue
            pool = []
            promoted_now = {m['name'] for m in run_moves if m['type'] == 'promotion' and m['from'] == d}
            for b in roster:
                if b['name'] in got_champs:
                    continue
                if direction == 'relegation' and b['name'] in promoted_now:
                    continue  # already went up this run
                if b['immune']:
                    detail.append(f"{b['name']}: immune, not eligible for {direction}")
                    continue
                missed, total = stats_for(b)
                w = win_counts.get(b['name'], 0)
                key = (missed, total, -w) if direction == 'promotion' else (-missed, -total, w)
                pool.append((key, b['name'], missed, total, w))
            pool.sort()
            if direction == 'promotion':
                spots = max(count - len(got_champs), 0)
                auto = sorted(got_champs)
            else:
                spots, auto = count, []
            floor_note = ''
            if div_count >= 3:
                # 3-division floor: moves never leave the division below
                # SIZE_FLOOR. Size at that moment = the roster, plus anyone
                # relegated in from the division above earlier in the same
                # run, minus whoever this division already promoted out.
                arrived = sum(1 for m in run_moves if m['type'] == 'relegation' and m['from'] == d - 1)
                size_now = len(roster) + arrived - promoted_out
                room = max(size_now - len(auto) - SIZE_FLOOR, 0)
                if room < spots:
                    floor_note = f" (held to {room} by the {SIZE_FLOOR}-player floor)"
                    spots = room
            certain, tie, tie_spots = pick([(k, n) for k, n, *_ in pool], spots)
            actual = [m for m in run_moves if m['type'] == direction and m['from'] == d]
            actual_names = {m['name'] for m in actual}
            for m in actual:
                explained_moves.add((m['name'], m['type'], m['from']))
            expected_fixed = set(auto) | set(certain)
            ok = expected_fixed <= actual_names
            drawn = actual_names - expected_fixed
            if tie:
                ok = ok and drawn <= set(tie) and len(drawn) == tie_spots
                for m in actual:
                    if m['name'] in drawn and not m['random']:
                        issues.append(f"{m['name']}'s {direction} was a tie-break draw but isn't marked as random.")
            else:
                ok = ok and not drawn
            for m in actual:
                if m['random'] and m['name'] not in tie:
                    issues.append(f"{m['name']}'s {direction} is marked random, but there was no genuine tie for that spot.")
            if direction == 'promotion':
                promoted_out = len(actual_names)
            exp_text = (', '.join(auto + certain) or 'nobody') + floor_note
            if tie:
                exp_text += f" + {tie_spots} drawn from tied {', '.join(tie)}"
            arrow = f"{label(d)} → {label(to_div)}"
            if not ok:
                issues.append(f"{arrow} {direction}: expected {exp_text}; actually moved {', '.join(sorted(actual_names)) or 'nobody'}.")
            move_lines.append(('ok' if ok else 'bad',
                               f"{arrow} {direction} ({count} spot{'s' if count != 1 else ''}): "
                               f"moved {', '.join(sorted(actual_names)) or 'nobody'}"
                               + (floor_note if ok else f" — expected {exp_text}")))
            for m in actual:
                p = by_name.get(m['name'])
                if p and p['division'] != to_div:
                    issues.append(f"{m['name']} was logged as {direction} to {label(to_div)} but is in "
                                  f"{label(p['division']) if p['division'] else 'no division'}.")
            for k, n, missed, total, w in pool:
                tag = 'moved' if n in actual_names else ''
                detail.append(f"{direction} rank: {n} — missed {missed}, total {total}, weekly wins {w}"
                              + (f"  ← {tag}" if tag else ''))
        if detail:
            sections.append((f"{label(d)} Season {ended_season} numbers (weeks {S}–{E + 6})",
                             [('info', line) for line in detail]))
    for m in run_moves:
        if (m['name'], m['type'], m['from']) not in explained_moves:
            issues.append(f"{m['name']} had a {m['type']} from {label(m['from'])} this week, but that division's season didn't end.")
    sections.insert(1, ('Seasons and movements', move_lines))

    # -- 3. immunity ------------------------------------------------------------
    imm_lines = []
    # division_confirmed_at is naive UTC, like created_at: the Pacific-aware
    # value confirm_division_mode writes is converted by the UTC session.
    confirm_week = calculate_wordle_number(get_week_start_date(pacific_date(confirmed_at))) if confirmed_at else None
    for p in sorted(players.values(), key=lambda x: (x['division'] or 9, x['name'])):
        if not p['active']:
            if p['immune']:
                notes.append(f"{p['name']} is inactive but still carries immunity; it would come back with them if re-added.")
            continue
        d = p['division']
        if d is None or not (1 <= d <= div_count):
            issues.append(f"{p['name']} is active but in {'no division' if d is None else 'Division ' + str(d)} "
                          f"(league runs {div_count}).")
            continue
        cs = seasons_now.get(d, {}).get('start')
        if cs is None:
            continue
        # How did they arrive in this division? The latest of: a logged move
        # into it, being added after confirm, or the confirm itself.
        into = [m for m in movements if m['name'] == p['name'] and m['to'] == d]
        last_move = into[-1] if into else None
        created_day = calculate_wordle_number(pacific_date(p['created_at'])) if p['created_at'] else None
        added_after_confirm = bool(p['created_at'] and confirmed_at and p['created_at'] > confirmed_at
                                   and (not last_move or p['created_at'] > last_move['at']))
        if last_move and (not added_after_confirm):
            move_week = calculate_wordle_number(get_week_start_date(pacific_date(last_move['at'])))
            if last_move['type'] == 'promotion':
                expected = cs < move_week
                why = f"promoted from {label(last_move['from'])} (week {move_week})"
            else:
                expected = cs <= move_week
                why = f"relegated from {label(last_move['from'])} (week {move_week})"
            if not expected:
                why += f"; {label(d)} started a new season at week {cs}, so it should have ended"
        elif added_after_confirm:
            created_week = week_on_grid(created_day, confirm_week) if confirm_week else None
            mon_tue = pacific_date(p['created_at']).weekday() <= 1
            if created_week == confirm_week and mon_tue:
                expected, why = False, "added Mon/Tue of the first division week (races in full)"
            else:
                expected = created_day >= cs
                why = f"added mid-season on {pacific_date(p['created_at'])}"
                if not expected:
                    why += f"; {label(d)} started a new season at week {cs}, so it should have ended"
        else:
            created_week = calculate_wordle_number(get_week_start_date(pacific_date(p['created_at']))) \
                if p['created_at'] else None
            in_confirm_week = created_week is not None and created_week == confirm_week
            if in_confirm_week and pacific_date(p['created_at']).weekday() > 1:
                expected = cs <= confirm_week
                why = "added Wed+ of the first division week"
            else:
                expected, why = False, "in this division since divisions were set up"
        actual = p['immune']
        jw = p['joined_week']
        if actual and jw is not None and jw < cs and not expected:
            why += f" (joined week {jw} is before {label(d)}'s current season start {cs}: stale)"
        if actual == expected:
            if actual:
                imm_lines.append(('ok', f"{p['name']} ({label(d)}): immune — {why}"))
        elif actual:
            issues.append(f"{p['name']} ({label(d)}) is immune but shouldn't be: {why}.")
            imm_lines.append(('bad', f"{p['name']} ({label(d)}): immune, should NOT be — {why}"))
        else:
            issues.append(f"{p['name']} ({label(d)}) should be immune but isn't: {why}.")
            imm_lines.append(('bad', f"{p['name']} ({label(d)}): NOT immune, should be — {why}"))
    if not imm_lines:
        imm_lines.append(('ok', 'Nobody is immune, and nobody should be.'))
    sections.append(('Immunity', imm_lines))

    # -- 4. sizes -----------------------------------------------------------------
    size_lines = []
    for d in range(1, div_count + 1):
        n = sum(1 for p in players.values() if p['active'] and p['division'] == d)
        small = n < SIZE_FLOOR
        if small and div_count >= 3:
            issues.append(f"{label(d)} is down to {n} active player{'s' if n != 1 else ''}.")
        elif small:
            # The floor is a 3-division rule; in two divisions it's just worth knowing.
            notes.append(f"{label(d)} has {n} active player{'s' if n != 1 else ''}.")
        size_lines.append(('bad' if small and div_count >= 3 else 'ok', f"{label(d)}: {n} players"))
    sections.append(('Division sizes', size_lines))

    return {'league_id': lid, 'league_name': name, 'divisions': div_count,
            'issues': issues, 'notes': notes, 'sections': sections,
            'moved': len(run_moves), 'snapshot': bool(snap)}


def run_audit(week=None, dry_run=False):
    if week is None:
        week = calculate_wordle_number(get_week_start_date()) - 7
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, COALESCE(division_count, 2), COALESCE(promoted_count, 1),
               COALESCE(relegated_count, 1), COALESCE(min_weekly_scores, 5), season_wins,
               division_confirmed_at, div2_promoted_count, div2_relegated_count
        FROM leagues WHERE division_mode = TRUE AND division_confirmed_at IS NOT NULL
        ORDER BY id
    """)
    leagues = []
    for r in cur.fetchall():
        min_scores = r[5] if 3 <= (r[5] or 0) <= 7 else 5
        target = r[6] if r[6] is not None and 2 <= r[6] <= 6 else 3
        leagues.append((r[0], r[1], r[2], r[3], r[4], min_scores, target, r[7], r[8], r[9]))
    reports = []
    for lg in leagues:
        try:
            reports.append(audit_league(cur, lg, week))
        except Exception as e:
            logging.exception(f"audit failed for league {lg[0]}")
            conn.rollback()
            reports.append({'league_id': lg[0], 'league_name': lg[1], 'divisions': lg[2],
                            'issues': [f"The audit itself crashed on this league: {e}"],
                            'notes': [], 'sections': [], 'moved': 0, 'snapshot': False})
    cur.close()
    conn.close()
    send_report(reports, week, dry_run)
    return reports


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

def _esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;')


def render_html(reports, week):
    ok_c, bad_c, mute = '#2ecc71', '#e74c3c', '#9a9ab0'
    total = sum(len(r['issues']) for r in reports)
    moves = sum(r['moved'] for r in reports)
    h = ['<div style="font-family:system-ui,-apple-system,sans-serif;max-width:760px;margin:0 auto;padding:24px;background:#12121c;color:#e8e8f0;">']
    h.append('<h1 style="margin:0 0 4px;font-size:22px;">Division Movement Audit</h1>')
    h.append(f'<div style="color:{mute};font-size:13px;margin-bottom:20px;">Week {week} (ended {wordle_to_date(week + 6):%b %d}) '
             f'&middot; {len(reports)} division league(s) &middot; {moves} movement(s)</div>')
    h.append(f'<div style="background:{bad_c if total else ok_c};color:#0b0b12;font-weight:700;padding:12px 16px;'
             f'border-radius:8px;margin-bottom:24px;">{f"{total} issue(s) found" if total else "Everything checks out"}</div>')
    h.append('<table style="width:100%;border-collapse:collapse;margin-bottom:24px;font-size:13px;">')
    for r in reports:
        ok = not r['issues']
        c = ok_c if ok else bad_c
        h.append(f'<tr style="border-bottom:1px solid #26263a;"><td style="padding:7px 8px 7px 0;color:{c};font-weight:700;width:18px;">'
                 f'{"&#10003;" if ok else "&#10007;"}</td><td style="padding:7px 0;color:#e8e8f0;">{_esc(r["league_name"])} '
                 f'<span style="color:#6a6a80;">(league {r["league_id"]}, {r["divisions"]} divisions)</span></td>'
                 f'<td style="padding:7px 0;text-align:right;color:{c};">{"all correct" if ok else str(len(r["issues"])) + " issue(s)"}</td></tr>')
    h.append('</table>')
    colors = {'ok': ok_c, 'bad': bad_c, 'info': '#c8c8d8'}
    icons = {'ok': '&#10003;', 'bad': '&#10007;', 'info': '&middot;'}
    for r in reports:
        border = bad_c if r['issues'] else ok_c
        h.append(f'<div style="border-left:4px solid {border};background:#1b1b28;border-radius:6px;padding:16px;margin-bottom:16px;">')
        h.append(f'<div style="font-weight:700;font-size:16px;">{_esc(r["league_name"])} '
                 f'<span style="color:{mute};font-weight:400;">(league {r["league_id"]})</span></div>')
        if r['issues']:
            h.append(f'<div style="font-size:12px;color:{bad_c};text-transform:uppercase;letter-spacing:.06em;margin:10px 0 6px;">Issues</div>'
                     '<ul style="margin:0 0 12px;padding-left:18px;font-size:13px;line-height:1.7;">')
            h += [f'<li style="color:{bad_c};">{_esc(i)}</li>' for i in r['issues']]
            h.append('</ul>')
        for title, lines in r['sections']:
            h.append(f'<div style="font-size:12px;color:{mute};text-transform:uppercase;letter-spacing:.06em;margin:12px 0 6px;">{_esc(title)}</div>'
                     '<ul style="margin:0;padding-left:0;list-style:none;font-size:13px;line-height:1.7;">')
            h += [f'<li style="color:{colors[k]};"><strong>{icons[k]}</strong> {_esc(t)}</li>' for k, t in lines]
            h.append('</ul>')
        if r['notes']:
            h.append(f'<div style="font-size:12px;color:{mute};margin-top:12px;">' +
                     '<br>'.join(_esc(n) for n in r['notes']) + '</div>')
        h.append('</div>')
    h.append(f'<div style="color:#6a6a80;font-size:11px;margin-top:24px;">Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} '
             '&middot; every verdict re-derived from raw scores, independently of the code that moved players.</div></div>')
    # Arrows and dashes as character references, so no mail client can garble them.
    return ''.join(h).encode('ascii', 'xmlcharrefreplace').decode('ascii')


def send_report(reports, week, dry_run=False):
    total = sum(len(r['issues']) for r in reports)
    subject = (f"[WordPlayLeague] Division Audit — {total} issue(s), week {week}" if total
               else f"[WordPlayLeague] Division Audit — all correct, week {week}")
    if dry_run:
        print(f"\nSUBJECT: {subject}\n")
        for r in reports:
            print(f"=== {r['league_name']} (league {r['league_id']}, {r['divisions']} divisions)"
                  f"{'' if r['snapshot'] else ' [no snapshot]'}")
            for i in r['issues']:
                print(f"  ISSUE: {i}")
            for title, lines in r['sections']:
                print(f"  -- {title}")
                for k, t in lines:
                    print(f"     [{k}] {t}")
            for n in r['notes']:
                print(f"  note: {n}")
        print("\n(dry run — no email sent)")
        return
    try:
        from email_utils import _send_email_sync
        html = render_html(reports, week)
        for addr in REPORT_EMAILS:
            _send_email_sync(addr, subject, html)
            logging.info(f"Division audit emailed to {addr}")
    except Exception as e:
        logging.error(f"Failed to send division audit: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', type=int, default=None, help='Monday wordle of the week to audit')
    ap.add_argument('--dry-run', action='store_true', help='print instead of emailing')
    args = ap.parse_args()
    run_audit(week=args.week, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
