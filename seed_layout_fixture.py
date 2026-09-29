"""
Seed a STAGING league with long player names and a week of scores, so the
layout tests have something worth measuring.

Layout bugs only show up with awkward content: a 25-character name next to an
emoji grid is what pushed the grid off-screen on mobile. Real leagues rarely
have names that long, so the fixture has to be deliberate about it.

Idempotent — safe to run repeatedly, and safe to re-run after a staging resync
wipes it. Requires an explicit connection URL so it can never be pointed at prod
by accident.

    python seed_layout_fixture.py "<staging-db-url>" [league-slug]
"""
import sys
import datetime

import psycopg2

DEFAULT_SLUG = 'super-test'

# Exactly 25 characters each — the current maximum a name may be.
LONG_NAMES = [
    'Bobby BanCheesingtonlyBiG',
    'Alexandra Papadopoulos Jr',
]

# Real Wordle grids: one row of five per guess, so a 3/6 has three rows.
# A single row for every score (which an earlier version of this used) renders
# as one stray line and tells you nothing about layout.
PATTERNS = {
    3: "🟩🟨⬜⬜⬜\n🟩⬜🟨⬜⬜\n🟩🟩🟩🟩🟩",
    4: "🟩⬜🟨⬜⬜\n🟩🟨⬜⬜⬜\n🟩⬜🟨🟨⬜\n🟩🟩🟩🟩🟩",
    5: "🟨⬜⬜⬜⬜\n🟩⬜⬜⬜⬜\n🟩⬜🟨🟨⬜\n🟩🟨⬜🟨🟨\n🟩🟩🟩🟩🟩",
}


def week_start_for(today):
    """Monday of the current week."""
    return today - datetime.timedelta(days=today.weekday())


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    url = sys.argv[1]
    slug = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SLUG

    if 'zephyr' in url:
        print("REFUSING: that looks like the production database.")
        return 1

    conn = psycopg2.connect(url)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        cur.execute("SELECT id, COALESCE(display_name, name) FROM leagues WHERE slug = %s", (slug,))
        row = cur.fetchone()
        if not row:
            print(f"No league with slug {slug!r} — nothing seeded.")
            return 1
        league_id, league_name = row
        print(f"league {league_id} ({league_name}) / {slug}")

        player_ids = []
        for name in LONG_NAMES:
            cur.execute("SELECT id FROM players WHERE league_id = %s AND name = %s", (league_id, name))
            found = cur.fetchone()
            if found:
                player_ids.append(found[0])
                print(f"  keep   {name}  ({len(name)} chars)")
            else:
                cur.execute(
                    "INSERT INTO players (league_id, name, active) VALUES (%s, %s, TRUE) RETURNING id",
                    (league_id, name),
                )
                pid = cur.fetchone()[0]
                player_ids.append(pid)
                print(f"  add    {name}  ({len(name)} chars) -> player {pid}")

        # A Monday-anchored week so Weekly Totals and Season have something in
        # them, not just Latest.
        today = datetime.date.today()
        monday = week_start_for(today)
        days = (today - monday).days + 1
        base_wordle = 1503 + (monday - datetime.date(2025, 7, 31)).days

        added = 0
        for offset, pid in enumerate(player_ids):
            for d in range(days):
                wordle = base_wordle + d
                score = 3 + ((d + offset) % 3)          # cycles 3,4,5
                cur.execute(
                    "SELECT id FROM scores WHERE player_id = %s AND wordle_number = %s",
                    (pid, wordle),
                )
                if cur.fetchone():
                    continue
                cur.execute(
                    """INSERT INTO scores (player_id, wordle_number, score, date, emoji_pattern, timestamp)
                       VALUES (%s, %s, %s, %s, %s, NOW())""",
                    (pid, wordle, score, monday + datetime.timedelta(days=d), PATTERNS[score]),
                )
                added += 1

        conn.commit()
        print(f"  scores added: {added} (week of Wordle {base_wordle}, {days} day(s))")

        cur.execute(
            """SELECT p.name, COUNT(s.id) FROM players p
               LEFT JOIN scores s ON s.player_id = p.id
               WHERE p.league_id = %s GROUP BY p.name ORDER BY p.name""",
            (league_id,),
        )
        print("\n  roster:")
        for name, n in cur.fetchall():
            print(f"    {name:28s} {n} score(s)")
        return 0
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        return 1
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    raise SystemExit(main())
