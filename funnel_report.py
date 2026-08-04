#!/usr/bin/env python3
"""Growth funnel metrics.

Answers one question: when someone arrives, how far do they get?

    signed up -> created a league -> connected a channel -> first score
              -> still posting after 14 days -> subscribed

Every stage is a plain SQL count, so the numbers are auditable and cheap. The
output is a dict, consumed by /api/funnel and rendered by the Jarvis dashboard.

`leagues` has no created_at, so user_leagues.created_at (when a manager claimed
the league) stands in for league creation. That is the moment that matters for
the funnel anyway.

Legacy leagues are reported separately throughout: they are free forever and
can never convert, so folding them into conversion rates would flatter every
number. As of Aug 2026 they are ~91% of all activity.

Usage:
    python funnel_report.py            # print a summary
    python funnel_report.py --json     # machine-readable
"""
import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from league_data_adapter import get_db_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Free forever — mirrors billing.LEGACY_LEAGUE_IDS
LEGACY_LEAGUE_IDS = (1, 3, 4, 7, 8, 19)


def _scalar(cur, sql, params=()):
    cur.execute(sql, params)
    row = cur.fetchone()
    return (row[0] if row and row[0] is not None else 0)


def build_funnel(days=30):
    """Compute the funnel. Returns a dict; never raises for missing data."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        since = datetime.now(timezone.utc) - timedelta(days=days)

        # ---- stage counts, windowed and all-time -------------------------
        signups = _scalar(cur, "SELECT COUNT(*) FROM users WHERE created_at >= %s", (since,))
        signups_all = _scalar(cur, "SELECT COUNT(*) FROM users")

        leagues_created = _scalar(cur, """
            SELECT COUNT(DISTINCT league_id) FROM user_leagues WHERE created_at >= %s
        """, (since,))
        leagues_all = _scalar(cur, "SELECT COUNT(*) FROM leagues")

        connected = _scalar(cur, """
            SELECT COUNT(*) FROM leagues
            WHERE twilio_conversation_sid IS NOT NULL
               OR slack_channel_id IS NOT NULL
               OR discord_channel_id IS NOT NULL
        """)

        with_scores = _scalar(cur, """
            SELECT COUNT(DISTINCT p.league_id)
            FROM players p JOIN scores s ON s.player_id = p.id
        """)

        active_14d = _scalar(cur, """
            SELECT COUNT(DISTINCT p.league_id)
            FROM players p JOIN scores s ON s.player_id = p.id
            WHERE s.date > CURRENT_DATE - 14
        """)

        # ---- money -------------------------------------------------------
        subs = {}
        cur.execute("SELECT status, COUNT(*) FROM subscriptions GROUP BY status")
        for status, n in cur.fetchall():
            subs[status] = n
        paying = subs.get('active', 0) + subs.get('trialing', 0)

        # ---- legacy vs billable activity ---------------------------------
        cur.execute("""
            SELECT COALESCE(SUM(CASE WHEN p.league_id IN %s THEN 1 ELSE 0 END), 0),
                   COALESCE(SUM(CASE WHEN p.league_id IN %s THEN 0 ELSE 1 END), 0)
            FROM players p JOIN scores s ON s.player_id = p.id
            WHERE s.date > CURRENT_DATE - 28
        """, (LEGACY_LEAGUE_IDS, LEGACY_LEAGUE_IDS))
        legacy_scores, billable_scores = cur.fetchone()

        # ---- per-signup detail, so zeros are explainable -----------------
        cur.execute("""
            SELECT u.id, u.email, u.created_at,
                   (SELECT COUNT(*) FROM user_leagues ul WHERE ul.user_id = u.id) AS leagues,
                   (SELECT COUNT(*) FROM subscriptions s WHERE s.user_id = u.id) AS subs
            FROM users u
            WHERE u.created_at >= %s
            ORDER BY u.created_at DESC
            LIMIT 25
        """, (since,))
        recent = [{
            'user_id': r[0],
            'email': r[1],
            'signed_up': r[2].isoformat() if r[2] else None,
            'leagues': r[3],
            'subscriptions': r[4],
        } for r in cur.fetchall()]

        # ---- channel split ------------------------------------------------
        cur.execute("""
            SELECT COALESCE(l.channel_type, 'sms'), COUNT(*)
            FROM leagues l GROUP BY 1 ORDER BY 2 DESC
        """)
        by_channel = {r[0]: r[1] for r in cur.fetchall()}

        return {
            'ok': True,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'window_days': days,
            'funnel': [
                {'stage': 'Signed up',        'window': signups,         'all_time': signups_all},
                {'stage': 'Created a league', 'window': leagues_created, 'all_time': leagues_all},
                {'stage': 'Connected',        'window': None,            'all_time': connected},
                {'stage': 'First score',      'window': None,            'all_time': with_scores},
                {'stage': 'Active (14d)',     'window': None,            'all_time': active_14d},
                {'stage': 'Paying / trialing','window': None,            'all_time': paying},
            ],
            'subscriptions': subs,
            'paying_or_trialing': paying,
            'activity_28d': {
                'legacy_free': legacy_scores,
                'billable': billable_scores,
            },
            'leagues_by_channel': by_channel,
            'recent_signups': recent,
        }
    except Exception as e:
        logging.error(f"Funnel build failed: {e}")
        return {'ok': False, 'error': str(e), 'generated_at': datetime.now(timezone.utc).isoformat()}
    finally:
        try:
            cur.close(); conn.close()
        except Exception:
            pass


def _print_summary(d):
    if not d.get('ok'):
        print("FAILED:", d.get('error')); return
    print(f"\nGrowth funnel — last {d['window_days']} days\n")
    print(f"  {'stage':22} {'window':>8} {'all time':>10}")
    for s in d['funnel']:
        w = '-' if s['window'] is None else s['window']
        print(f"  {s['stage']:22} {str(w):>8} {s['all_time']:>10}")
    print(f"\n  subscriptions: {d['subscriptions'] or 'none'}")
    a = d['activity_28d']
    print(f"  scores 28d   : {a['legacy_free']} legacy (free forever) / {a['billable']} billable")
    print(f"  leagues      : {d['leagues_by_channel']}")
    if d['recent_signups']:
        print(f"\n  recent signups ({len(d['recent_signups'])}):")
        for r in d['recent_signups']:
            print(f"    {r['email'][:34]:36} leagues={r['leagues']}  subs={r['subscriptions']}")
    else:
        print("\n  no signups in window")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--days', type=int, default=30)
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    data = build_funnel(days=args.days)
    print(json.dumps(data, indent=2)) if args.json else _print_summary(data)


if __name__ == '__main__':
    main()
