#!/usr/bin/env python3
"""
Delete Keith's incorrect score for today
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

# Connect to the database
conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

# Get Keith's player ID in League 2
cursor.execute("""
SELECT id FROM players WHERE name = 'Keith' AND league_id = 2
""")
keith_id = cursor.fetchone()[0]
print(f"Keith's player ID in League 2: {keith_id}")

# Get today's Wordle number
todays_wordle = get_todays_wordle_number()
print(f"Today's Wordle number: {todays_wordle}")

# Delete Keith's score for today
cursor.execute("""
DELETE FROM scores WHERE player_id = ? AND wordle_number = ?
""", (keith_id, todays_wordle))

deleted_count = cursor.rowcount
print(f"Deleted {deleted_count} incorrect score entries for Keith")

conn.commit()
conn.close()
