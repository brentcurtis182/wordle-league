"""
Fix: league_seasons.season_start_week drifted away from the seasons table.

league_seasons is a cache; the seasons table (start_week per season_number) is
the source of truth. The cache was never updated as seasons rolled over, so on
prod it still held each league's FIRST EVER week. League 1 read 1514 (August
2025, its first week) while Season 10 actually began at week 1864.

Anything counting "wins this season" does WHERE week_wordle_number >=
season_start_week, so the stale value silently returned ALL-TIME wins. That is
how a player with 1 win in the current season was reported as having 24.

season_management.get_current_season() re-syncs this cache, but effectively
nothing calls it, so the drift persisted.

This copies the true season_number/start_week from seasons into league_seasons.
It only touches rows that already exist in league_seasons AND disagree with a
non-NULL seasons.start_week, so it is safe to re-run and a no-op once clean.

Usage:
    DATABASE_URL="<public_url>" python migrations/sync_league_seasons_start_week.py           # preview
    DATABASE_URL="<public_url>" python migrations/sync_league_seasons_start_week.py --apply   # write
"""

import os
import sys
import psycopg2


def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url, connect_timeout=10)
    return psycopg2.connect(
        host=os.environ.get('PGHOST'),
        database=os.environ.get('PGDATABASE'),
        user=os.environ.get('PGUSER'),
        password=os.environ.get('PGPASSWORD'),
        port=os.environ.get('PGPORT', 5432),
        connect_timeout=10
    )


def main():
    apply_changes = '--apply' in sys.argv

    conn = get_db_connection()
    cursor = conn.cursor()

    # Latest season per league from the source of truth, paired with the cache.
    cursor.execute("""
        SELECT ls.league_id,
               COALESCE(l.display_name, l.name, '') AS league_name,
               ls.current_season, ls.season_start_week,
               s.season_number, s.start_week
        FROM league_seasons ls
        LEFT JOIN leagues l ON l.id = ls.league_id
        LEFT JOIN LATERAL (
            SELECT season_number, start_week
            FROM seasons
            WHERE league_id = ls.league_id
            ORDER BY season_number DESC
            LIMIT 1
        ) s ON TRUE
        ORDER BY ls.league_id
    """)
    rows = cursor.fetchall()

    stale = []
    for league_id, name, cur_season, cur_start, true_season, true_start in rows:
        if true_start is None:
            continue  # no authoritative record — leave the cache alone
        if cur_start == true_start and cur_season == true_season:
            continue
        stale.append((league_id, name, cur_season, cur_start, true_season, true_start))

    print(f"Leagues with a league_seasons row: {len(rows)}")
    print(f"Leagues needing a sync:            {len(stale)}\n")

    if not stale:
        print("Nothing to do — cache already matches the seasons table.")
        cursor.close()
        conn.close()
        return

    print(f"{'league':<7} {'name':<24} {'cached':<18} {'true':<18} weeks off")
    print("-" * 82)
    for league_id, name, cur_season, cur_start, true_season, true_start in stale:
        cached = f"s{cur_season}/wk{cur_start}"
        truth = f"s{true_season}/wk{true_start}"
        drift = (true_start - cur_start) if cur_start is not None else '-'
        print(f"{league_id:<7} {(name or '')[:23]:<24} {cached:<18} {truth:<18} {drift}")

    if not apply_changes:
        print("\nPREVIEW ONLY — no changes written. Re-run with --apply to commit.")
        cursor.close()
        conn.close()
        return

    for league_id, name, cur_season, cur_start, true_season, true_start in stale:
        cursor.execute("""
            UPDATE league_seasons
            SET current_season = %s,
                season_start_week = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE league_id = %s
        """, (true_season, true_start, league_id))

    conn.commit()
    print(f"\nUpdated {len(stale)} row(s).")

    # Verify: re-read and confirm nothing disagrees anymore.
    cursor.execute("""
        SELECT ls.league_id, ls.current_season, ls.season_start_week, s.season_number, s.start_week
        FROM league_seasons ls
        LEFT JOIN LATERAL (
            SELECT season_number, start_week
            FROM seasons
            WHERE league_id = ls.league_id
            ORDER BY season_number DESC
            LIMIT 1
        ) s ON TRUE
        ORDER BY ls.league_id
    """)
    remaining = [r for r in cursor.fetchall()
                 if r[4] is not None and (r[2] != r[4] or r[1] != r[3])]
    if remaining:
        print(f"WARNING: {len(remaining)} row(s) still disagree: {remaining}")
    else:
        print("Verified: every league with a seasons record now matches it.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
