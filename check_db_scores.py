import sqlite3

conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

# Check for Wordle #1503 scores
print("Checking for Wordle #1503 scores:")
cursor.execute("SELECT phone_number, score, pattern, league_id FROM scores WHERE wordle_num = 1503")
results = cursor.fetchall()
if results:
    for row in results:
        print(f"Player ID: {row[0]}, Score: {row[1]}, Pattern: {row[2]}, League: {row[3]}")
else:
    print("No Wordle #1503 scores found")

# Get most recent Wordle number
print("\nMost recent Wordle number in database:")
cursor.execute("SELECT MAX(wordle_num) FROM scores")
max_wordle = cursor.fetchone()[0]
print(f"Latest Wordle number: {max_wordle}")

# Show scores for the most recent Wordle
print(f"\nScores for Wordle #{max_wordle}:")
cursor.execute("SELECT phone_number, score, pattern, league_id FROM scores WHERE wordle_num = ?", (max_wordle,))
for row in cursor.fetchall():
    print(f"Player ID: {row[0]}, Score: {row[1]}, Pattern: {row[2]}, League: {row[3]}")

conn.close()
