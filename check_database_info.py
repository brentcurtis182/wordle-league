import sqlite3

# Connect to the database
conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

# Check what Wordle numbers exist in the database
cursor.execute("SELECT DISTINCT wordle_number FROM scores ORDER BY wordle_number DESC")
wordle_numbers = cursor.fetchall()
print("Wordle numbers in database:", [row[0] for row in wordle_numbers])

# Check league players
cursor.execute("SELECT league_id, name FROM players ORDER BY league_id, name")
players = cursor.fetchall()
print("\nPlayers by league:")
for row in players:
    print(f"League {row[0]}: {row[1]}")

# Check the most recent scores
print("\nMost recent scores:")
cursor.execute("""
SELECT p.league_id, p.name, s.wordle_number, s.score
FROM scores s 
JOIN players p ON s.player_id = p.id 
ORDER BY s.wordle_number DESC, p.league_id, p.name
LIMIT 10
""")
recent_scores = cursor.fetchall()
for row in recent_scores:
    print(f"League {row[0]}: {row[1]} - Wordle #{row[2]} - Score: {row[3]}")

# Close the connection
conn.close()
