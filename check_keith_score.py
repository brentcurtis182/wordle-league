#!/usr/bin/env python3
"""
Quick script to check if Keith has a score today in the database
"""
import sqlite3
from datetime import datetime

def get_todays_wordle_number():
    # Wordle #1503 = July 31, 2025
    ref_date = datetime(2025, 7, 31).date()
    ref_wordle = 1503
    today = datetime.now().date()
    days_since_ref = (today - ref_date).days
    return ref_wordle + days_since_ref

# Get today's Wordle number
todays_wordle = get_todays_wordle_number()
print(f"Today's Wordle number: {todays_wordle}")

# Connect to the database
conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

# Query for Keith in League 2
cursor.execute("""
SELECT p.name, s.wordle_number, s.score, s.emoji_pattern, s.timestamp
FROM scores s
JOIN players p ON s.player_id = p.id
WHERE p.name = 'Keith' AND p.league_id = 2 AND s.wordle_number = ?
""", (todays_wordle,))

keith_score = cursor.fetchone()
if keith_score:
    name, wordle_num, score, emoji, timestamp = keith_score
    print(f"PROBLEM: Keith has a score in League 2 for Wordle {wordle_num}")
    print(f"Score: {score}")
    print(f"Timestamp: {timestamp}")
    print(f"Emoji Pattern: {emoji}")
else:
    print("GOOD: Keith does NOT have a score in League 2 for today's Wordle")

# Now let's check Joanna's scores across all leagues
cursor.execute("""
SELECT p.name, p.league_id, l.name, s.wordle_number, s.score, s.timestamp
FROM scores s
JOIN players p ON s.player_id = p.id
JOIN leagues l ON p.league_id = l.id
WHERE p.name = 'Joanna' AND s.wordle_number = ?
""", (todays_wordle,))

joanna_scores = cursor.fetchall()
print("\nJoanna's scores for today:")
if joanna_scores:
    for name, league_id, league_name, wordle_num, score, timestamp in joanna_scores:
        print(f"League {league_id} ({league_name}): Score {score}, Timestamp: {timestamp}")
else:
    print("Joanna has no scores for today's Wordle")

conn.close()
