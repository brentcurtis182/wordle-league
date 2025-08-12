import sqlite3
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def fix_pal_duplicates():
    """Fix duplicate and incorrectly dated scores in the PAL league"""
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # First, display the current state
        cursor.execute("""
        SELECT id, player_name, wordle_num, score, timestamp
        FROM scores
        WHERE league_id = 3 AND (
            wordle_num = 1502 OR wordle_num = '1,502' OR
            wordle_num = 1503 OR wordle_num = '1,503'
        )
        ORDER BY player_name, timestamp
        """)
        
        print("===== CURRENT PAL LEAGUE SCORES =====")
        scores = cursor.fetchall()
        for id, player, wordle_num, score, timestamp in scores:
            print(f"ID {id}: {player} - Wordle #{wordle_num} - {score}/6 on {timestamp}")
            
        print("\nFinding and fixing issues...")
        
        # 1. Fix Wordle #1503 dated July 30 (should be July 31)
        cursor.execute("""
        UPDATE scores
        SET timestamp = '2025-07-31 12:00:00'
        WHERE league_id = 3 
        AND (wordle_num = 1503 OR wordle_num = '1,503')
        AND player_name = 'Vox'
        AND date(timestamp) = '2025-07-30'
        """)
        
        vox_1503_fixed = cursor.rowcount
        if vox_1503_fixed > 0:
            print(f"Fixed {vox_1503_fixed} incorrect date(s) for Vox's Wordle #1503 score")
        
        # 2. Check for duplicate Wordle #1502 scores for Vox
        cursor.execute("""
        SELECT id, timestamp
        FROM scores
        WHERE league_id = 3 
        AND (wordle_num = 1502 OR wordle_num = '1,502')
        AND player_name = 'Vox'
        ORDER BY timestamp DESC
        """)
        
        duplicate_1502 = cursor.fetchall()
        if len(duplicate_1502) > 1:
            # Keep only the latest record
            latest_id = duplicate_1502[0][0]
            
            for record_id, _ in duplicate_1502[1:]:
                cursor.execute("DELETE FROM scores WHERE id = ?", (record_id,))
                print(f"Deleted duplicate Wordle #1502 score with ID {record_id}")
        
        # Commit the changes
        conn.commit()
        
        # Show the final state
        cursor.execute("""
        SELECT id, player_name, wordle_num, score, timestamp
        FROM scores
        WHERE league_id = 3 AND (
            wordle_num = 1502 OR wordle_num = '1,502' OR
            wordle_num = 1503 OR wordle_num = '1,503'
        )
        ORDER BY player_name, timestamp
        """)
        
        print("\n===== UPDATED PAL LEAGUE SCORES =====")
        scores = cursor.fetchall()
        for id, player, wordle_num, score, timestamp in scores:
            print(f"ID {id}: {player} - Wordle #{wordle_num} - {score}/6 on {timestamp}")
        
    except Exception as e:
        logging.error(f"Error fixing PAL scores: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_pal_duplicates()
