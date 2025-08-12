#!/usr/bin/env python3
"""
Delete Keith's incorrect reaction score for today's Wordle
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

# Get Keith's player ID in League 2 (Wordle Gang)
cursor.execute("""
SELECT id FROM players WHERE name = 'Keith' AND league_id = 2
""")
keith_id = cursor.fetchone()[0]
print(f"Keith's player ID in League 2: {keith_id}")

# Get today's Wordle number
todays_wordle = get_todays_wordle_number()
print(f"Today's Wordle number: {todays_wordle}")

# Delete Keith's incorrect reaction score for today
cursor.execute("""
DELETE FROM scores WHERE player_id = ? AND wordle_number = ?
""", (keith_id, todays_wordle))

deleted_count = cursor.rowcount
print(f"Deleted {deleted_count} incorrect score entries for Keith")

conn.commit()
conn.close()

print("Now let's verify no incorrect scores remain:")

# Connect again to check
conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

cursor.execute("""
SELECT s.id, p.name, s.wordle_number, s.score
FROM scores s
JOIN players p ON s.player_id = p.id
WHERE p.name = 'Keith' AND p.league_id = 2 AND s.wordle_number = ?
""", (todays_wordle,))

remaining = cursor.fetchall()
if remaining:
    print(f"WARNING: Keith still has {len(remaining)} scores!")
    for row in remaining:
        print(f"ID: {row[0]}, Name: {row[1]}, Wordle: {row[2]}, Score: {row[3]}")
else:
    print("SUCCESS: Keith has no more incorrect scores for today")

conn.close()
