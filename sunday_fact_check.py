#!/usr/bin/env python3
"""Monday fact-check of Sunday's AI league messages.

Reads each archived Sunday race update, extracts the factual claims it made
(win counts, weekly winners, ties, clinches), verifies every claim against the
database, and emails Brent one report covering EVERY league — the accurate ones
as well as the wrong ones.

Design:
  - The LLM ONLY parses free text into structured claims. It never decides what
    is true. All verification is plain SQL against weekly_winners / season
    tables, so the checker cannot hallucinate a verdict.
  - Runs MONDAY, after the weekly winners job has written the week's rows, so
    claims are checked against the final outcome. This catches both claims that
    were wrong when written and claims invalidated by late Sunday scores.
  - Reports BOTH directions: fabrications (claimed, not supported) and
    omissions (true and material, never mentioned).
  - The email sends every week, pass or fail. Silence then means the checker
    itself broke, rather than "all good".

Usage:
    python sunday_fact_check.py              # check the most recent Sunday
    python sunday_fact_check.py --week 1857  # check a specific week
    python sunday_fact_check.py --dry-run    # print the report, send nothing
"""
import os
import sys
import json
import logging
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from league_data_adapter import get_db_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

REPORT_EMAILS = ['brentcurtis182@gmail.com']

DEFAULT_WINS_REGULAR = 4
DEFAULT_WINS_DIVISION = 3


# ---------------------------------------------------------------------------
# Claim extraction (the ONLY LLM step — parsing, never adjudicating)
# ---------------------------------------------------------------------------

EXTRACT_SYSTEM = """You extract factual claims from a sports-league message. You do NOT judge whether they are true.

Return ONLY a JSON array. Each element is one claim, with:
  {"type": "<type>", "player": "<name or null>", "players": [<names>], "number": <int or null>, "quote": "<the exact phrase from the message>"}

Claim types:
  "win_count"   - states which win of the season this is for a player
                  ("their 2nd win", "first win of the season"). number = the ordinal (1 for first).
  "weekly_win"  - states a player won the week outright. number = null.
  "shared_win"  - states two or more players tied/shared the week's win. players = all named. number = null.
  "clinch"      - states a player clinched/won the SEASON. number = season number if stated, else null.
  "promotion"   - states a player was promoted to a higher division.
  "relegation"  - states a player was relegated to a lower division.

Rules:
- Extract only ASSERTIONS about what HAS happened. Ignore hypotheticals
  ("could win", "if they post", "needs a 3 to take the lead", "is on track").
- Ignore pure standings/score statements ("leads at 17", "total of 15").
- "first win" => type win_count with number 1.
- If the message asserts nothing factual, return [].
- Use the player names exactly as they appear in the message."""


def extract_claims(message_text):
    """Parse a sent message into structured claims. Returns [] on any failure."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": EXTRACT_SYSTEM},
                {"role": "user", "content": message_text},
            ],
            max_tokens=800,
            temperature=0,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        claims = json.loads(raw.strip())
        return claims if isinstance(claims, list) else []
    except Exception as e:
        logging.error(f"Claim extraction failed: {e}")
        return []


# ---------------------------------------------------------------------------
# Ground truth (pure SQL — this is what decides right/wrong)
# ---------------------------------------------------------------------------

def get_league_truth(cursor, league_id, week):
    """Everything needed to adjudicate claims for one league-week."""
    cursor.execute("""
        SELECT name, COALESCE(division_mode, FALSE), season_wins
        FROM leagues WHERE id = %s
    """, (league_id,))
    row = cursor.fetchone()
    if not row:
        return None
    league_name, division_mode, season_wins = row

    wins_needed = season_wins or (DEFAULT_WINS_DIVISION if division_mode else DEFAULT_WINS_REGULAR)

    # Winners actually recorded for this week
    cursor.execute("""
        SELECT player_name, division, score
        FROM weekly_winners
        WHERE league_id = %s AND week_wordle_number = %s
        ORDER BY player_name
    """, (league_id, week))
    winners = [{'name': r[0], 'division': r[1], 'score': r[2]} for r in cursor.fetchall()]

    # Season boundaries — resolve them EXACTLY as the app does, never by reading
    # league_seasons directly. `seasons` is the source of truth and get_current_season
    # re-syncs from it; reading the raw table gives stale start weeks (PAL showed 1626
    # when the real boundary was 1850) and would manufacture false "wrong count" alarms.
    season_starts = {}
    if division_mode:
        from division_manager import get_division_season_info
        for div in (1, 2):
            info = get_division_season_info(league_id, div)
            season_starts[div] = {
                'season': info['current_season'],
                'start': info['season_start_week'] or 0,
            }
    else:
        from season_management import get_current_season
        season_num, start_week = get_current_season(league_id)
        season_starts[None] = {'season': season_num, 'start': start_week or 0}

    # Season win totals as of (and including) this week
    win_totals = {}
    for div, info in season_starts.items():
        if div is None:
            cursor.execute("""
                SELECT player_name, COUNT(*) FROM weekly_winners
                WHERE league_id = %s AND week_wordle_number >= %s
                  AND week_wordle_number <= %s
                GROUP BY player_name
            """, (league_id, info['start'], week))
        else:
            cursor.execute("""
                SELECT player_name, COUNT(*) FROM weekly_winners
                WHERE league_id = %s AND division = %s
                  AND week_wordle_number >= %s AND week_wordle_number <= %s
                GROUP BY player_name
            """, (league_id, div, info['start'], week))
        for name, cnt in cursor.fetchall():
            win_totals[(div, name)] = cnt

    return {
        'league_name': league_name,
        'division_mode': division_mode,
        'wins_needed': wins_needed,
        'winners': winners,
        'season_starts': season_starts,
        'win_totals': win_totals,
    }


def _divisions_for(truth, player):
    """Divisions this player has a recorded win in (None key when not div mode)."""
    return [div for (div, name) in truth['win_totals'] if name == player]


def _lookup_wins(truth, player):
    """(count, division) for a player's season wins through this week."""
    for (div, name), cnt in truth['win_totals'].items():
        if name == player:
            return cnt, div
    return 0, None


def _season_moved(truth, week):
    """True if a season boundary now starts AFTER the week we're checking.

    Seasons roll over in the Monday job, i.e. after Sunday's message was written.
    When that happens the message's counts were computed against the OLD boundary
    and can't be fairly compared to the new one — flagging them would be a false
    positive, so those claims are reported unverifiable instead of wrong.
    """
    return any(info['start'] > week for info in truth['season_starts'].values())


def verify_claim(claim, truth, week=None):
    """Adjudicate one claim. Returns (verdict, detail).

    verdict is 'ok' | 'wrong' | 'unverifiable'
    """
    ctype = claim.get('type')
    player = claim.get('player')
    players = claim.get('players') or ([player] if player else [])
    number = claim.get('number')
    winner_names = [w['name'] for w in truth['winners']]

    # Season rolled over after the message was sent — counts aren't comparable.
    if week is not None and ctype in ('win_count', 'clinch') and _season_moved(truth, week):
        return 'unverifiable', ('a season boundary now starts after this week, so the message was '
                                'written against the previous season — counts not comparable')

    if ctype == 'win_count':
        if not player:
            return 'unverifiable', 'no player named'
        actual, div = _lookup_wins(truth, player)
        won_this_week = player in winner_names

        # An "Nth win" claim asserts a win happened THIS week. If the player has no
        # winner row for the week, the ordinal is about a win that never occurred —
        # regardless of their season total. (Kat, PAL week 1857.)
        if not won_this_week:
            if number is not None and number == actual:
                return 'ok', f"{player} has {actual} win(s) this season (did not win this week, but the count is right)"
            return 'wrong', (f"message credited {player} with win #{number}, but {player} has NO winner row "
                             f"for this week (season total: {actual}; winners: {', '.join(winner_names) or 'none'})")

        if number is None:
            return 'unverifiable', f'{player} has {actual} win(s); message gave no number'
        if number == actual:
            return 'ok', f"{player}: win #{number} confirmed ({actual} this season)"
        return 'wrong', f"message said {player}'s win #{number}, DB says {actual}"

    if ctype == 'weekly_win':
        if not player:
            return 'unverifiable', 'no player named'
        if player not in winner_names:
            return 'wrong', f"{player} is not a recorded winner for this week (recorded: {', '.join(winner_names) or 'none'})"
        if len(winner_names) > 1:
            others = [n for n in winner_names if n != player]
            # Only a problem when the co-winner is in the SAME division
            same_div = [w for w in truth['winners'] if w['name'] in others
                        and w['division'] == next((x['division'] for x in truth['winners'] if x['name'] == player), None)]
            if same_div:
                return 'wrong', f"{player} did not win outright — shared with {', '.join(w['name'] for w in same_div)}"
        return 'ok', f"{player} won the week (confirmed)"

    if ctype == 'shared_win':
        if len(players) < 2:
            return 'unverifiable', 'fewer than 2 players named'
        missing = [p for p in players if p not in winner_names]
        if missing:
            return 'wrong', f"claimed shared win, but {', '.join(missing)} has NO winner row this week (recorded: {', '.join(winner_names) or 'none'})"
        return 'ok', f"shared win confirmed for {', '.join(players)}"

    if ctype == 'clinch':
        if not player:
            return 'unverifiable', 'no player named'
        actual, div = _lookup_wins(truth, player)
        if actual < truth['wins_needed']:
            return 'wrong', f"claimed {player} clinched the season, but they have {actual} win(s) — {truth['wins_needed']} needed"
        return 'ok', f"{player} clinch confirmed ({actual}/{truth['wins_needed']} wins)"

    if ctype in ('promotion', 'relegation'):
        if not player:
            return 'unverifiable', 'no player named'
        if not truth['division_mode']:
            return 'wrong', f"claimed {ctype} for {player}, but this league is not in division mode"
        return 'unverifiable', f'{ctype} for {player} — not auto-verified'

    return 'unverifiable', f'unknown claim type: {ctype}'


def find_omissions(claims, truth):
    """Material facts the message should have stated but didn't."""
    omissions = []
    mentioned = set()
    for c in claims:
        if c.get('player'):
            mentioned.add(c['player'])
        for p in (c.get('players') or []):
            mentioned.add(p)

    for w in truth['winners']:
        if w['name'] not in mentioned:
            label = f" (Division {w['division']})" if w['division'] else ""
            omissions.append(f"{w['name']} won the week{label} with {w['score']} — never mentioned in the message")

    claimed_clinch = {c.get('player') for c in claims if c.get('type') == 'clinch'}
    for (div, name), cnt in truth['win_totals'].items():
        if cnt >= truth['wins_needed'] and name not in claimed_clinch and name in [w['name'] for w in truth['winners']]:
            label = f" (Division {div})" if div else ""
            omissions.append(f"{name}{label} reached {cnt} wins — season threshold is {truth['wins_needed']}, no clinch mentioned")

    return omissions


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def check_week(week=None, dry_run=False):
    conn = get_db_connection()
    cursor = conn.cursor()

    if week is None:
        cursor.execute("""
            SELECT MAX(week_wordle_number) FROM sent_ai_messages
            WHERE message_type = 'sunday_race'
        """)
        row = cursor.fetchone()
        week = row[0] if row else None

    if week is None:
        logging.warning("No archived Sunday messages found — nothing to check.")
        _send_report("No Sunday messages archived", [], week, 0, dry_run)
        cursor.close(); conn.close()
        return

    cursor.execute("""
        SELECT league_id, scenario_text, raw_ai_text, sent_text, sent_at
        FROM sent_ai_messages
        WHERE message_type = 'sunday_race' AND week_wordle_number = %s
        ORDER BY league_id
    """, (week,))
    messages = cursor.fetchall()
    logging.info(f"Fact-checking {len(messages)} message(s) for week {week}")

    reports = []
    for league_id, scenario_text, raw_ai_text, sent_text, sent_at in messages:
        truth = get_league_truth(cursor, league_id, week)
        if not truth:
            continue

        claims = extract_claims(sent_text)
        results = [(c, *verify_claim(c, truth, week)) for c in claims]
        omissions = find_omissions(claims, truth)

        reports.append({
            'league_id': league_id,
            'league_name': truth['league_name'],
            'sent_text': sent_text,
            'scenario_text': scenario_text,
            'guard_intervened': bool(raw_ai_text) and raw_ai_text != sent_text,
            'results': results,
            'omissions': omissions,
            'wrong': [r for r in results if r[1] == 'wrong'],
        })

    cursor.close()
    conn.close()
    _send_report(None, reports, week, len(messages), dry_run)


def _render_html(reports, week, headline):
    total_wrong = sum(len(r['wrong']) + len(r['omissions']) for r in reports)
    total_claims = sum(len(r['results']) for r in reports)
    ok_color, bad_color = '#2ecc71', '#e74c3c'

    h = ['<div style="font-family:system-ui,-apple-system,sans-serif;max-width:760px;margin:0 auto;padding:24px;background:#12121c;color:#e8e8f0;">']
    h.append(f'<h1 style="margin:0 0 4px;font-size:22px;">Sunday Message Fact-Check</h1>')
    h.append(f'<div style="color:#9a9ab0;font-size:13px;margin-bottom:20px;">Week {week} &middot; {len(reports)} league message(s) &middot; {total_claims} claim(s) checked</div>')

    banner = bad_color if total_wrong else ok_color
    label = f'{total_wrong} issue(s) found' if total_wrong else 'All messages accurate'
    h.append(f'<div style="background:{banner};color:#0b0b12;font-weight:700;padding:12px 16px;border-radius:8px;margin-bottom:24px;">{label}</div>')

    if headline:
        h.append(f'<p style="color:#f39c12;">{headline}</p>')

    for r in reports:
        has_problem = bool(r['wrong'] or r['omissions'])
        border = bad_color if has_problem else ok_color
        status = 'ISSUES FOUND' if has_problem else 'ACCURATE'
        h.append(f'<div style="border-left:4px solid {border};background:#1b1b28;border-radius:6px;padding:16px;margin-bottom:16px;">')
        h.append(f'<div style="font-weight:700;font-size:16px;">{r["league_name"]} <span style="color:#9a9ab0;font-weight:400;">(league {r["league_id"]})</span></div>')
        h.append(f'<div style="color:{border};font-weight:700;font-size:12px;letter-spacing:.06em;margin:4px 0 12px;">{status}</div>')

        h.append('<div style="background:#0f0f18;border-radius:5px;padding:12px;font-size:13px;line-height:1.5;white-space:pre-wrap;color:#c8c8d8;margin-bottom:12px;">')
        h.append((r['sent_text'] or '').replace('<', '&lt;'))
        h.append('</div>')

        if r['results']:
            h.append('<div style="font-size:12px;color:#9a9ab0;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;">Claims</div><ul style="margin:0 0 12px;padding-left:18px;font-size:13px;line-height:1.7;">')
            for claim, verdict, detail in r['results']:
                icon = {'ok': '&#10003;', 'wrong': '&#10007;', 'unverifiable': '&#63;'}[verdict]
                color = {'ok': ok_color, 'wrong': bad_color, 'unverifiable': '#9a9ab0'}[verdict]
                quote = (claim.get('quote') or '').replace('<', '&lt;')
                h.append(f'<li style="color:{color};"><strong>{icon}</strong> &ldquo;{quote}&rdquo; &mdash; {detail}</li>')
            h.append('</ul>')
        else:
            h.append('<div style="font-size:13px;color:#9a9ab0;margin-bottom:12px;">No factual claims detected in this message.</div>')

        if r['omissions']:
            h.append('<div style="font-size:12px;color:#9a9ab0;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;">Omissions</div><ul style="margin:0 0 12px;padding-left:18px;font-size:13px;line-height:1.7;">')
            for o in r['omissions']:
                h.append(f'<li style="color:{bad_color};">{o}</li>')
            h.append('</ul>')

        if has_problem:
            h.append('<details style="margin-top:8px;"><summary style="cursor:pointer;color:#9a9ab0;font-size:12px;">Scenario text the AI was given (shows whether the bug is in the code or the AI)</summary>')
            h.append(f'<div style="background:#0f0f18;border-radius:5px;padding:12px;font-size:12px;white-space:pre-wrap;color:#a8a8bc;margin-top:8px;">{(r["scenario_text"] or "(none)").replace("<", "&lt;")}</div></details>')

        if r['guard_intervened']:
            h.append('<div style="margin-top:10px;font-size:12px;color:#f39c12;">Note: the fact-check guard re-rolled or replaced this message before sending.</div>')

        h.append('</div>')

    h.append(f'<div style="color:#6a6a80;font-size:11px;margin-top:24px;">Generated {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")} &middot; claims parsed by GPT-4o, every verdict decided by SQL against the league database.</div>')
    h.append('</div>')
    return ''.join(h)


def _send_report(headline, reports, week, message_count, dry_run):
    total_wrong = sum(len(r['wrong']) + len(r['omissions']) for r in reports)
    subject = (f"[WordPlayLeague] Sunday Fact-Check — {total_wrong} issue(s), week {week}"
               if total_wrong else
               f"[WordPlayLeague] Sunday Fact-Check — all clear, week {week}")

    html = _render_html(reports, week, headline)

    if dry_run:
        print(f"\nSUBJECT: {subject}\n")
        for r in reports:
            state = 'ISSUES' if (r['wrong'] or r['omissions']) else 'ACCURATE'
            print(f"--- {r['league_name']} (league {r['league_id']}): {state}")
            for claim, verdict, detail in r['results']:
                print(f"    [{verdict}] {detail}")
            for o in r['omissions']:
                print(f"    [omission] {o}")
        print(f"\n(dry run — no email sent)")
        return

    try:
        from email_utils import _send_email_sync
        for addr in REPORT_EMAILS:
            _send_email_sync(addr, subject, html)
            logging.info(f"Fact-check report emailed to {addr}")
    except Exception as e:
        logging.error(f"Failed to send fact-check report: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', type=int, default=None, help='week_wordle_number to check')
    ap.add_argument('--dry-run', action='store_true', help='print instead of emailing')
    args = ap.parse_args()
    check_week(week=args.week, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
