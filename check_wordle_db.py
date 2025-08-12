import sqlite3
import datetime

conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

# Get table schema
cursor.execute("PRAGMA table_info(scores)")
columns = [col[1] for col in cursor.fetchall()]
print(f"Database columns: {columns}")

# Check for most recent scores
print("\nMost recent scores in database:")
cursor.execute("SELECT MAX(wordle_num) FROM scores")
max_wordle = cursor.fetchone()[0]
print(f"Latest Wordle number: {max_wordle}")

# Get scores by wordle number
def get_scores_for_wordle(wordle_num):
    cursor.execute("""
        SELECT scores.*, players.name 
        FROM scores 
        LEFT JOIN players ON scores.phone_number = players.phone_number 
        WHERE wordle_num = ?
    """, (wordle_num,))
    rows = cursor.fetchall()
    
    if not rows:
        print(f"No scores found for Wordle #{wordle_num}")
        return
    
    print(f"\nScores for Wordle #{wordle_num}:")
    print("-" * 40)
    
    for row in rows:
        # Handle case where joined data might have different column count
        score_data = dict(zip(columns, row[:len(columns)]))
        player_name = row[-1] if len(row) > len(columns) else "Unknown"
        
        print(f"Player: {player_name} (Phone: {score_data.get('phone_number', 'N/A')})")
        print(f"Score: {score_data.get('score', 'N/A')}")
        print(f"Pattern: {score_data.get('pattern', 'N/A')}")
        print(f"League: {score_data.get('league_id', 'N/A')}")
        
        if 'date_played' in score_data and score_data['date_played']:
            print(f"Date: {score_data['date_played']}")
            
        print("-" * 40)

# Check recent Wordle scores
get_scores_for_wordle("1503")  # Today's Wordle
get_scores_for_wordle("1502")  # Yesterday's Wordle

# Get the most recent scores by date
print("\nMost recent scores by date:")
cursor.execute("""
    SELECT wordle_num, MAX(date_created) as latest_date 
    FROM scores 
    GROUP BY wordle_num 
    ORDER BY latest_date DESC 
    LIMIT 5
""")

for row in cursor.fetchall():
    wordle_num, latest_date = row
    print(f"Wordle #{wordle_num} - Latest entry on {latest_date}")

conn.close()
