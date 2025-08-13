import sqlite3
import os
from datetime import datetime

# Connect to the database
db_path = os.environ.get('WORDLE_DB_PATH', 'wordle_league.db')
conn = sqlite3.connect(db_path)
cur = conn.cursor()

print(f"Using database at: {db_path}")
print("=" * 50)

# Check scores table for today's scores (1505)
print("Checking scores table for Wordle #1505:")
cur.execute("SELECT player_name, score, emoji_pattern, league_id FROM scores WHERE wordle_num = '1505'")
scores_results = cur.fetchall()
if scores_results:
    print(f"Found {len(scores_results)} scores in 'scores' table:")
    for row in scores_results:
        print(f"  Player: {row[0]}, Score: {row[1]}, League: {row[3]}")
else:
    print("No scores found in 'scores' table for Wordle #1505")

print("\n" + "=" * 50)

# Check score table for today's scores (1505)
print("Checking score table for Wordle #1505:")
cur.execute("""
    SELECT p.name, s.score, s.emoji_pattern, s.league_id 
    FROM score s 
    JOIN players p ON s.player_id = p.id 
    WHERE s.wordle_number = '1505'
""")
score_results = cur.fetchall()
if score_results:
    print(f"Found {len(score_results)} scores in 'score' table:")
    for row in score_results:
        print(f"  Player: {row[0]}, Score: {row[1]}, League: {row[3]}")
else:
    print("No scores found in 'score' table for Wordle #1505")

# Check the latest wordle number in each table
print("\n" + "=" * 50)
print("Latest Wordle numbers in database:")
cur.execute("SELECT MAX(wordle_num) FROM scores")
max_scores = cur.fetchone()[0]
print(f"Latest Wordle # in 'scores' table: {max_scores}")

cur.execute("SELECT MAX(wordle_number) FROM score")
max_score = cur.fetchone()[0]
print(f"Latest Wordle # in 'score' table: {max_score}")

conn.close()
