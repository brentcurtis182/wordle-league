import sqlite3
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def check_emoji_patterns():
    """Check emoji patterns for Wordle #1503 scores without displaying actual emojis"""
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get emoji patterns for Wordle #1503 scores
        cursor.execute("""
        SELECT player_name, wordle_num, score, length(emoji_pattern), league_id, timestamp 
        FROM scores 
        WHERE wordle_num = 1503 OR wordle_num = '1,503'
        ORDER BY league_id, player_name
        """)
        
        print("===== EMOJI PATTERN STATUS FOR WORDLE #1503 SCORES =====")
        scores = cursor.fetchall()
        missing_patterns = 0
        
        for player, wordle_num, score, pattern_length, league_id, timestamp in scores:
            league_name = "Warriorz" if league_id == 1 else "PAL" if league_id == 3 else f"League {league_id}"
            date_str = timestamp.split()[0] if timestamp else "N/A"
            
            if pattern_length > 0:
                pattern_status = f"Pattern Length: {pattern_length} chars"
            else:
                pattern_status = "MISSING"
                missing_patterns += 1
                
            print(f"{league_name}: {player} - {score}/6 on {date_str} - {pattern_status}")
                
        if missing_patterns > 0:
            print(f"\nWARNING: {missing_patterns} out of {len(scores)} scores are missing emoji patterns!")
        else:
            print("\nAll scores have emoji patterns! ✓")
            
        # Let's also check for duplicate scores to make sure we don't have any
        cursor.execute("""
        SELECT player_name, wordle_num, COUNT(*) as count
        FROM scores
        WHERE wordle_num = 1503 OR wordle_num = '1,503'
        GROUP BY player_name, wordle_num
        HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            print("\n===== DUPLICATE SCORES DETECTED =====")
            for player, wordle_num, count in duplicates:
                print(f"{player}: {count} entries for Wordle #{wordle_num}")
        else:
            print("\nNo duplicate scores detected for Wordle #1503.")
        
    except Exception as e:
        logging.error(f"Error checking emoji patterns: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_emoji_patterns()
