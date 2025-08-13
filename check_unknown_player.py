import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def check_players_and_scores():
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check all players
        cursor.execute("SELECT * FROM player")
        players = cursor.fetchall()
        
        print("\n===== ALL PLAYERS IN DATABASE =====")
        for player in players:
            # Try to get phone number if it exists in the schema
            phone = 'N/A'
            try:
                phone = player['phone'] if 'phone' in player.keys() else 'N/A'
            except:
                pass
            print(f"ID: {player['id']}, Name: {player['name']}, Phone: {phone}")
        
        # Check scores for Wordle #1500 with additional details
        cursor.execute("""
            SELECT s.id, s.player_id, p.name, s.score, s.emoji_pattern, s.date, s.created_at 
            FROM score s 
            JOIN player p ON s.player_id = p.id 
            WHERE s.wordle_number = 1500
            ORDER BY s.created_at
        """)
        scores = cursor.fetchall()
        
        print("\n===== DETAILED SCORES FOR WORDLE #1500 =====")
        if scores:
            for score in scores:
                emoji_rows = score['emoji_pattern'].count('\n') + 1 if score['emoji_pattern'] else 0
                score_display = "X/6" if score['score'] == 7 else f"{score['score']}/6"
                print(f"Score ID: {score['id']}")
                print(f"  Player: {score['name']} (ID: {score['player_id']})")
                print(f"  Score: {score_display} with {emoji_rows} rows of emoji")
                print(f"  Date: {score['date']}")
                print(f"  Created at: {score['created_at']}")
                print(f"  Emoji pattern: {score['emoji_pattern'][:30]}..." if score['emoji_pattern'] else "None")
                print("-" * 40)
        else:
            print("No scores found for Wordle #1500")
        
        # Check all scores for Unknown (5)
        cursor.execute("""
            SELECT s.wordle_number, s.score, s.date, s.created_at, s.emoji_pattern 
            FROM score s 
            JOIN player p ON s.player_id = p.id 
            WHERE p.name = 'Unknown (5)'
            ORDER BY s.wordle_number DESC
        """)
        unknown_scores = cursor.fetchall()
        
        print("\n===== ALL SCORES FOR UNKNOWN (5) =====")
        if unknown_scores:
            for score in unknown_scores:
                emoji_rows = score['emoji_pattern'].count('\n') + 1 if score['emoji_pattern'] else 0
                score_display = "X/6" if score['score'] == 7 else f"{score['score']}/6"
                print(f"Wordle #{score['wordle_number']}: {score_display}")
                print(f"  Date: {score['date']}")
                print(f"  Created: {score['created_at']}")
                print(f"  Emoji rows: {emoji_rows}")
                print("-" * 40)
        else:
            print("No scores found for Unknown (5)")
            
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_players_and_scores()
