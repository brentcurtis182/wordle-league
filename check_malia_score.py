import sqlite3
import os

# Get database path
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'wordle_league.db')

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First get Malia's player ID
    cursor.execute("SELECT id FROM player WHERE name = 'Malia'")
    player_id_result = cursor.fetchone()
    
    if not player_id_result:
        print("Malia not found in player table")
    else:
        player_id = player_id_result[0]
        print(f"Malia's player ID: {player_id}")
        
        # Get Malia's most recent score
        cursor.execute("""
            SELECT score, wordle_number, date 
            FROM score 
            WHERE player_id = ? 
            ORDER BY wordle_number DESC 
            LIMIT 1
        """, (player_id,))
        
        latest_score = cursor.fetchone()
        if latest_score:
            print(f"Latest score: {latest_score[0]} for Wordle #{latest_score[1]} on {latest_score[2]}")
        else:
            print("No scores found for Malia")
            
        # Specifically check for Wordle #1500
        cursor.execute("""
            SELECT score, date, emoji_pattern
            FROM score 
            WHERE player_id = ? AND wordle_number = 1500
        """, (player_id,))
        
        wordle_1500 = cursor.fetchone()
        if wordle_1500:
            print(f"\nWordle #1500 score: {wordle_1500[0]} on {wordle_1500[1]}")
            print("Has emoji pattern: Yes" if wordle_1500[2] else "Has emoji pattern: No")
            
            # Count newlines to determine number of rows in pattern
            if wordle_1500[2]:
                rows = wordle_1500[2].count('\n') + 1
                print(f"Emoji pattern has {rows} rows")
        else:
            print("\nNo score found for Wordle #1500")
    
    conn.close()

except Exception as e:
    print(f"Error: {e}")
