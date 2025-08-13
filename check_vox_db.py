import sqlite3

# Connect to the database
conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

# Check Vox's scores in PAL league (league_id = 3)
cursor.execute("SELECT wordle_num, score FROM scores WHERE league_id = 3 AND player_name = 'Vox'")
vox_scores = cursor.fetchall()
print("Vox scores in PAL league:")
for row in vox_scores:
    print(f"Wordle #{row[0]} - Score: {row[1]}")

# Check all scores in PAL league
cursor.execute("SELECT player_name, wordle_num, score FROM scores WHERE league_id = 3 ORDER BY player_name, wordle_num")
pal_scores = cursor.fetchall()
print("\nAll scores in PAL league:")
for row in pal_scores:
    print(f"Player: {row[0]} - Wordle #{row[1]} - Score: {row[2]}")

# Check format of wordle numbers in other leagues
cursor.execute("SELECT league_id, wordle_num FROM scores GROUP BY league_id, wordle_num")
wordle_nums = cursor.fetchall()
print("\nWordle number formats by league:")
for row in wordle_nums:
    print(f"League ID: {row[0]} - Wordle #: {row[1]}")

conn.close()
