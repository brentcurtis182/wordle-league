#!/usr/bin/env python3
"""Create the sent_ai_messages archive table.

Stores every AI-generated league message as sent, together with the
deterministic scenario/context text it was generated from. This is the
foundation for the Monday fact-checker: without an archive of what was
actually sent (and what the code TOLD the AI), discrepancies can only be
reconstructed by hand from raw scores after the fact.

Columns:
    league_id           -- league the message went to
    message_type        -- e.g. 'sunday_race' (other AI message types later)
    week_wordle_number  -- week-start Wordle # (same key weekly_winners uses)
    scenario_text       -- deterministic text the code built (ground truth input)
    raw_ai_text         -- what the model produced BEFORE the fact-check guard
    sent_text           -- what actually went to the league (after guard/re-roll)
    model               -- model id used
    sent_at             -- timestamp

raw_ai_text vs sent_text differing = the guard intervened; no separate flag
needed.

Idempotent -- safe to re-run.

Usage:
    DATABASE_URL="<public_url>" python migrations/add_sent_ai_messages.py
"""
import os
import psycopg2


def main():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise SystemExit("DATABASE_URL not set")

    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sent_ai_messages (
            id SERIAL PRIMARY KEY,
            league_id INTEGER NOT NULL,
            message_type TEXT NOT NULL,
            week_wordle_number INTEGER,
            scenario_text TEXT,
            raw_ai_text TEXT,
            sent_text TEXT NOT NULL,
            model TEXT,
            sent_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    print("Created table sent_ai_messages (if not exists)")

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_sent_ai_messages_league_week
        ON sent_ai_messages (league_id, message_type, week_wordle_number)
    """)
    print("Created index idx_sent_ai_messages_league_week (if not exists)")

    cur.execute("SELECT COUNT(*) FROM sent_ai_messages")
    print(f"sent_ai_messages rows: {cur.fetchone()[0]}")

    cur.close()
    conn.close()
    print("Migration complete.")


if __name__ == '__main__':
    main()
