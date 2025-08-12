#!/usr/bin/env python3
import sqlite3
import os

# Connect to the database
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'wordle_league.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check Evan's failed attempts
cursor.execute("""
SELECT s.id, s.score, s.date, s.wordle_number, p.name 
FROM scores s 
JOIN players p ON s.player_id = p.id 
WHERE p.name = 'Evan' AND p.league_id = 1 
AND (s.score = '7' OR s.score = 7 OR s.score = 'X')
ORDER BY s.date DESC
""")

print("Evan's failed attempts:")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Score: {row[1]}, Date: {row[2]}, Wordle: {row[3]}")

# Also check weekly stats processing
print("\nChecking weekly stats processing:")
start_wordle = 1500
end_wordle = 1506

cursor.execute("""
SELECT p.name, COUNT(*) as failed_count
FROM scores s
JOIN players p ON s.player_id = p.id
WHERE p.league_id = 1
AND s.wordle_number >= ? AND s.wordle_number <= ?
AND (s.score = 7 OR s.score = '7' OR s.score = 'X')
GROUP BY p.name
""", (start_wordle, end_wordle))

print(f"Failed attempts in weekly range ({start_wordle}-{end_wordle}):")
for row in cursor.fetchall():
    print(f"Player: {row[0]}, Failed count: {row[1]}")

# Close connection
conn.close()
