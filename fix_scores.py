#!/usr/bin/env python
"""
Fix incorrect scores in the Wordle League database
"""
import sqlite3
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Database path
DATABASE_PATH = 'wordle_league.db'

def fix_scores():
    """Fix incorrect scores for Wordle #1500"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Correct scores for Wordle #1500
    correct_scores = {
        'Evan': 7,      # X/6
        'Joanna': 6,    # 6/6 (should be 6 based on your feedback)
        'Brent': 6,     # 6/6
        'Nanna': 6,     # 6/6 (correct based on your evidence)
        'Malia': 7      # X/6
    }
    
    print("Fixing scores for Wordle #1500...")
    for player_name, correct_score in correct_scores.items():
        # Update scores table
        cursor.execute(
            "UPDATE scores SET score = ? WHERE player_name = ? AND wordle_num = 1500",
            (correct_score, player_name)
        )
        
        score_display = "X/6" if correct_score == 7 else f"{correct_score}/6"
        rows_updated = cursor.rowcount
        if rows_updated > 0:
            print(f"✓ Updated {player_name}'s score to {score_display} in 'scores' table")
        else:
            print(f"! No change needed for {player_name} in 'scores' table (already {score_display})")
        
        # Also update score table using player_id
        try:
            # Get player_id
            cursor.execute("SELECT id FROM player WHERE name = ?", (player_name,))
            player_row = cursor.fetchone()
            
            if player_row:
                player_id = player_row[0]
                
                cursor.execute(
                    "UPDATE score SET score = ? WHERE player_id = ? AND wordle_number = 1500",
                    (correct_score, player_id)
                )
                
                rows_updated = cursor.rowcount
                if rows_updated > 0:
                    print(f"✓ Updated {player_name}'s score to {score_display} in 'score' table")
                else:
                    print(f"! No change needed for {player_name} in 'score' table")
            else:
                print(f"! Could not find player_id for {player_name}")
        except Exception as e:
            print(f"! Error updating 'score' table for {player_name}: {e}")
    
    # Commit changes
    conn.commit()
    
    # Verify the updates
    print("\nVerifying fixes:")
    cursor.execute(
        "SELECT player_name, score FROM scores WHERE wordle_num = 1500 ORDER BY player_name"
    )
    for row in cursor.fetchall():
        player_name = row[0]
        score = row[1]
        expected = correct_scores.get(player_name)
        
        if expected is None:
            print(f"! Unexpected player {player_name} in database")
        elif score == expected:
            score_display = "X/6" if score == 7 else f"{score}/6"
            print(f"✓ {player_name}: {score_display} - CORRECT")
        else:
            score_display = "X/6" if score == 7 else f"{score}/6"
            expected_display = "X/6" if expected == 7 else f"{expected}/6"
            print(f"! {player_name}: {score_display} - INCORRECT (should be {expected_display})")
            
    conn.close()

def update_website():
    """Update the website with the fixed scores"""
    try:
        import subprocess
        logging.info("Running integrated_auto_update.py to update the website...")
        
        # Run the script with skip-extraction flag to avoid overwriting our fixes
        result = subprocess.run(
            ["python", "integrated_auto_update.py", "--skip-extraction", "--publish-only"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Website updated successfully")
            return True
        else:
            print(f"! Error updating website: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"! Exception running website update: {e}")
        return False

if __name__ == "__main__":
    print("=== Wordle League Score Fix Tool ===")
    fix_scores()
    print("\nUpdating website with corrected scores...")
    update_website()
    print("\nDone!")
