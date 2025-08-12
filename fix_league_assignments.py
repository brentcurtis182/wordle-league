import sqlite3
import os
from datetime import datetime

print("=== FIXING INCORRECT LEAGUE ASSIGNMENTS FOR WORDLE #1505 ===")

# Connect to the database
db_path = os.environ.get('WORDLE_DB_PATH', 'wordle_league.db')
conn = sqlite3.connect(db_path)
cur = conn.cursor()

print(f"Using database at: {db_path}")

# First, let's see what we have for Wordle #1505
print("\nBefore cleanup - Scores table:")
cur.execute("SELECT id, player_name, score, league_id FROM scores WHERE wordle_num = '1505'")
for row in cur.fetchall():
    print(f"ID: {row[0]}, Player: {row[1]}, Score: {row[2]}, League: {row[3]}")

print("\nBefore cleanup - Score table:")
cur.execute("""
    SELECT s.id, p.name, s.score, s.league_id 
    FROM score s 
    JOIN players p ON s.player_id = p.id 
    WHERE s.wordle_number = '1505'
""")
for row in cur.fetchall():
    print(f"ID: {row[0]}, Player: {row[1]}, Score: {row[2]}, League: {row[3]}")

# Remove incorrect league assignments from scores table
# Remove Joanna and Nanna from League 3 (they should only be in League 1)
print("\nRemoving incorrect entries from scores table...")
cur.execute("DELETE FROM scores WHERE wordle_num = '1505' AND player_name = 'Joanna' AND league_id = 3")
joanna_deleted = cur.rowcount
print(f"Deleted {joanna_deleted} incorrect entries for Joanna in League 3")

cur.execute("DELETE FROM scores WHERE wordle_num = '1505' AND player_name = 'Nanna' AND league_id = 3")
nanna_deleted = cur.rowcount
print(f"Deleted {nanna_deleted} incorrect entries for Nanna in League 3")

# Remove Keith from League 1 (he should only be in League 2)
cur.execute("DELETE FROM score WHERE wordle_number = '1505' AND player_id IN (SELECT id FROM players WHERE name = 'Keith') AND league_id = 1")
keith_deleted = cur.rowcount
print(f"Deleted {keith_deleted} incorrect entries for Keith in League 1")

# Commit changes
conn.commit()

# Check the results
print("\nAfter cleanup - Scores table:")
cur.execute("SELECT id, player_name, score, league_id FROM scores WHERE wordle_num = '1505'")
for row in cur.fetchall():
    print(f"ID: {row[0]}, Player: {row[1]}, Score: {row[2]}, League: {row[3]}")

print("\nAfter cleanup - Score table:")
cur.execute("""
    SELECT s.id, p.name, s.score, s.league_id 
    FROM score s 
    JOIN players p ON s.player_id = p.id 
    WHERE s.wordle_number = '1505'
""")
for row in cur.fetchall():
    print(f"ID: {row[0]}, Player: {row[1]}, Score: {row[2]}, League: {row[3]}")

conn.close()
print("\n=== CLEANUP COMPLETE ===")
