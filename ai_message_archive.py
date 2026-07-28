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
