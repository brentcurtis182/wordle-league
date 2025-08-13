import sqlite3
import sys
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def check_emoji_patterns():
    """Check emoji patterns for Wordle #1503 scores using safe output"""
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check if emoji_pattern column exists
        cursor.execute("PRAGMA table_info(scores)")
        columns = [col[1] for col in cursor.fetchall()]
        has_emoji_pattern = 'emoji_pattern' in columns
        
        if not has_emoji_pattern:
            print("The database doesn't have an emoji_pattern column!")
            return
        
        # Get emoji patterns for Wordle #1503 scores
        cursor.execute("""
        SELECT player_name, wordle_num, score, emoji_pattern, league_id, timestamp 
        FROM scores 
        WHERE wordle_num = 1503 OR wordle_num = '1,503'
        ORDER BY league_id, player_name
        """)
        
        print("===== EMOJI PATTERNS FOR WORDLE #1503 SCORES =====")
        scores = cursor.fetchall()
        missing_patterns = 0
        
        for player, wordle_num, score, emoji_pattern, league_id, timestamp in scores:
            league_name = "Warriorz" if league_id == 1 else "PAL" if league_id == 3 else f"League {league_id}"
            date_str = timestamp.split()[0] if timestamp else "N/A"
            
            if emoji_pattern:
                # Count green, yellow and gray squares
                try:
                    greens = emoji_pattern.count('🟩')
                    yellows = emoji_pattern.count('🟨')
                    grays = emoji_pattern.count('⬜') + emoji_pattern.count('⬛')
                    pattern_info = f"[Pattern: {greens}🟩 {yellows}🟨 {grays}⬜]"
                except:
                    # If emoji counting fails, just show length
                    pattern_info = f"[Pattern length: {len(emoji_pattern)}]"
            else:
                missing_patterns += 1
                pattern_info = "[Pattern: MISSING]"
                
            print(f"{league_name}: {player} - {score}/6 on {date_str} {pattern_info}")
                
        if missing_patterns > 0:
            print(f"\nWARNING: {missing_patterns} out of {len(scores)} scores are missing emoji patterns!")
        else:
            print("\nAll scores have emoji patterns! ✓")
            
    except Exception as e:
        logging.error(f"Error checking emoji patterns: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_emoji_patterns()
