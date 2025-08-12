import sqlite3

# Connect to the database
conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

# Get Nanna's score
cursor.execute("""
SELECT p.name, s.score, s.emoji_pattern 
FROM scores s 
JOIN players p ON s.player_id = p.id 
WHERE p.name = 'Nanna' AND s.wordle_number = 1503
""")

nanna_score = cursor.fetchone()
if nanna_score:
    print(f"Name: {nanna_score[0]}")
    print(f"Score: {nanna_score[1]}")
    print(f"Emoji Pattern: {nanna_score[2]}")
    
    # Check length of emoji rows
    if nanna_score[2]:
        rows = nanna_score[2].strip().split('\n')
        print(f"Number of emoji rows: {len(rows)}")
        print("Rows:")
        for i, row in enumerate(rows):
            print(f"  Row {i+1}: {row}")
else:
    print("No score found for Nanna")

# Get all scores for Wordle 1503
print("\nAll scores for Wordle 1503:")
cursor.execute("""
SELECT p.name, s.score, s.emoji_pattern 
FROM scores s 
JOIN players p ON s.player_id = p.id 
WHERE s.wordle_number = 1503
ORDER BY p.name
""")

all_scores = cursor.fetchall()
for row in all_scores:
    print(f"\nName: {row[0]}")
    print(f"Score: {row[1]}")
    print(f"Emoji Pattern: {row[2]}")
    
    # Count emoji rows
    if row[2]:
        rows = row[2].strip().split('\n')
        print(f"Number of emoji rows: {len(rows)}")

# Close the connection
conn.close()
