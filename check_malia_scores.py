import sqlite3
import os

# Get database path
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'wordle_league.db')

print(f"Checking database at: {db_path}")
print(f"Database exists: {os.path.exists(db_path)}")

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check Malia's recent scores
    print("\nMalia's recent scores:")
    cursor.execute("""
        SELECT wordle_number, score, emoji_pattern, date 
        FROM scores 
        WHERE name = 'Malia' 
        ORDER BY wordle_number DESC 
        LIMIT 5
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"Wordle #{row[0]}: Score: {row[1]}, Date: {row[3]}")
        if row[2]:  # If emoji pattern exists
            print(f"Emoji Pattern:\n{row[2]}")
        print("-" * 50)
    
    # Check today's wordle number from the database
    cursor.execute("""
        SELECT MAX(wordle_number) 
        FROM scores
    """)
    max_wordle = cursor.fetchone()[0]
    print(f"\nLatest Wordle number in database: {max_wordle}")
    
    # Get all scores for the latest wordle
    cursor.execute("""
        SELECT name, score, emoji_pattern, date 
        FROM scores 
        WHERE wordle_number = ?
        ORDER BY name
    """, (max_wordle,))
    rows = cursor.fetchall()
    print(f"\nAll scores for Wordle #{max_wordle}:")
    for row in rows:
        print(f"Player: {row[0]}, Score: {row[1]}, Date: {row[3]}")
        if row[2]:  # If emoji pattern exists
            print(f"Emoji Pattern:\n{row[2]}")
        print("-" * 50)
    
    # Close connection
    conn.close()

except Exception as e:
    print(f"Error accessing database: {e}")
