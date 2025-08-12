import sqlite3

# Connect to the database
conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

# Get all players with scores for Wordle 1503 in league 1 (Wordle Warriorz)
cursor.execute("""
SELECT p.name, s.score 
FROM scores s 
JOIN players p ON s.player_id = p.id 
WHERE s.wordle_number = 1503 AND p.league_id = 1
ORDER BY p.name
""")

print("Players with scores for Wordle #1503 in Wordle Warriorz:")
all_scores = cursor.fetchall()
for row in all_scores:
    print(f"Name: {row[0]}, Score: {row[1]}")

# Close the connection
conn.close()
