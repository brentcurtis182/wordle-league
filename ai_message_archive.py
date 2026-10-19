#!/usr/bin/env python3
"""Archive of AI-generated league messages, as sent.

One job: after an AI message goes out, record what was sent alongside the
deterministic scenario text it was generated from. The Monday fact-checker
reads this to verify every claim (win counts, clinches, ties, promotions)
against the DB — and to spot material facts the message should have mentioned
but didn't.

Fails SAFE: archiving must never block or break the send path. Any error is
logged and swallowed.
"""
import logging

from league_data_adapter import get_db_connection


def archive_sent_ai_message(league_id, message_type, week_wordle_number,
                            scenario_text, raw_ai_text, sent_text, model=None):
    """Record a sent AI message. Never raises.

    raw_ai_text is the model output BEFORE the fact-check guard; sent_text is
    what actually went to the league. They differ iff the guard intervened.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sent_ai_messages
                (league_id, message_type, week_wordle_number,
                 scenario_text, raw_ai_text, sent_text, model)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (league_id, message_type, week_wordle_number,
              scenario_text, raw_ai_text, sent_text, model))
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"Archived {message_type} message for league {league_id}, week {week_wordle_number}")
    except Exception as e:
        logging.error(f"Failed to archive {message_type} message for league {league_id}: {e}")


def recent_sent_messages(league_id, message_type, limit=8):
    """Recent messages of this type for this league, newest first. Never raises.

    Used to stop the per-score messages repeating themselves. The roast and
    perfect-score prompts were byte-identical on every call, so gpt-4o-mini
    returned its handful of favourite Wordle jokes over and over — high
    temperature reshuffles the wording, not the idea. Feeding the model what
    it already said is the part that actually fixes that.

    Returns a list of (sent_text, scenario_text). For these message types
    scenario_text carries the comedic angle that produced the message, so the
    caller can avoid reusing a recent angle as well as a recent joke.

    Fails SAFE: an empty list on any error, so a DB hiccup costs variety and
    never a message.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sent_text, scenario_text
            FROM sent_ai_messages
            WHERE league_id = %s AND message_type = %s
              AND sent_text IS NOT NULL AND sent_text <> ''
            ORDER BY sent_at DESC
            LIMIT %s
        """, (league_id, message_type, limit))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [(r[0], r[1] or '') for r in rows]
    except Exception as e:
        logging.error(f"Failed to read recent {message_type} messages for league {league_id}: {e}")
        return []
