import sqlite3

# Connect to the database
conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in database:", [table[0] for table in tables])

# Check scores table
print("\n=== scores table (Wordle #1500) ===")
try:
    cursor.execute("SELECT player_name, wordle_num, score, emoji_pattern FROM scores WHERE wordle_num = 1500")
    rows = cursor.fetchall()
    for row in rows:
        player_name = row[0]
        score = row[2]
        emoji_pattern = row[3] if row[3] else "No pattern"
        
        score_display = "X/6" if score == 7 else f"{score}/6"
        print(f"{player_name}: {score_display}")
        
        # Count rows in emoji pattern
        if emoji_pattern != "No pattern":
            row_count = emoji_pattern.count("\n") + 1
            print(f"  Pattern has {row_count} rows")
except Exception as e:
    print(f"Error with scores table: {e}")
    
# Check score table (singular)
print("\n=== score table (Wordle #1500) ===")
try:
    cursor.execute("SELECT p.name, s.wordle_number, s.score FROM score s JOIN player p ON s.player_id = p.id WHERE s.wordle_number = 1500")
    rows = cursor.fetchall()
    for row in rows:
        player_name = row[0]
        score = row[2]
        
        score_display = "X/6" if score == 7 else f"{score}/6"
        print(f"{player_name}: {score_display}")
except Exception as e:
    print(f"Error with score table: {e}")

conn.close()
