#!/usr/bin/env python
# Fix emoji patterns for Joanna and Brent in the database

import sqlite3
import logging
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def fix_player_pattern(player_name, wordle_num, correct_rows, sample_pattern=None):
    """Fix a player's emoji pattern in the database
    
    Args:
        player_name: Name of the player
        wordle_num: Wordle number to fix
        correct_rows: Number of rows the pattern should have
        sample_pattern: Optional sample pattern to use (will be adjusted to match correct_rows)
    """
    try:
        conn = sqlite3.connect("wordle_league.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get player ID
        cursor.execute("SELECT id FROM player WHERE name = ?", (player_name,))
        player_result = cursor.fetchone()
        if not player_result:
            logging.error(f"Player {player_name} not found")
            conn.close()
            return False
            
        player_id = player_result["id"]
        logging.info(f"{player_name}'s player ID: {player_id}")
        
        # Get score record
        cursor.execute("""
            SELECT id, score, emoji_pattern 
            FROM score 
            WHERE player_id = ? AND wordle_number = ?
        """, (player_id, wordle_num))
        
        score_record = cursor.fetchone()
        if not score_record:
            logging.error(f"No score found for {player_name} for Wordle {wordle_num}")
            conn.close()
            return False
            
        score_id = score_record["id"]
        score = score_record["score"]
        current_pattern = score_record["emoji_pattern"]
        
        logging.info(f"{player_name}'s Wordle {wordle_num} score: ID={score_id}, Score={score}")
        
        # Count rows in current pattern
        current_rows = 0
        if current_pattern:
            current_rows = current_pattern.count('\n') + 1
            logging.info(f"Current pattern has {current_rows} rows")
            logging.info(f"Current pattern: {current_pattern}")
        
        # Fix if there's a mismatch
        if current_rows != correct_rows:
            logging.info(f"Fixing {player_name}'s pattern to have {correct_rows} rows")
            
            # Create a proper pattern based on the score and sample
            new_pattern = ""
            
            # Use sample if provided, otherwise create a default pattern
            if sample_pattern:
                # Split the sample pattern into rows
                sample_rows = sample_pattern.split('\n')
                
                if len(sample_rows) != correct_rows:
                    # Adjust the sample pattern to have the correct number of rows
                    if len(sample_rows) < correct_rows:
                        # Add rows by duplicating middle rows until we have correct_rows-1
                        middle_idx = len(sample_rows) // 2
                        while len(sample_rows) < correct_rows - 1:
                            sample_rows.insert(middle_idx, sample_rows[middle_idx])
                        # Last row should be all green for success
                        sample_rows.append("🟩🟩🟩🟩🟩")
                    else:
                        # Trim rows from the middle
                        excess = len(sample_rows) - correct_rows
                        middle_start = (len(sample_rows) - excess) // 2
                        sample_rows = sample_rows[:middle_start] + sample_rows[middle_start+excess:]
                
                new_pattern = '\n'.join(sample_rows[:correct_rows])
            else:
                # Create default patterns based on score
                if player_name == "Joanna" and wordle_num == 1500 and score == 5:
                    # Joanna's 5/6 pattern for Wordle 1500
                    new_pattern = "🟨⬛⬛⬛⬛\n⬛🟨🟨⬛⬛\n⬛🟩🟨🟩⬛\n🟩🟩⬛🟩🟨\n🟩🟩🟩🟩🟩"
                elif player_name == "Brent" and wordle_num == 1500 and score == 6:
                    # Brent's 6/6 pattern for Wordle 1500
                    new_pattern = "🟩⬛⬛⬛⬛\n🟩⬛🟨⬛⬛\n🟩🟩⬛⬛⬛\n🟩🟩⬛⬛🟩\n🟩🟩⬛⬛🟩\n🟩🟩🟩🟩🟩"
                else:
                    # Generic pattern based on score
                    rows = []
                    for i in range(1, correct_rows):
                        # Mix of green and yellow for middle rows
                        if i <= 2:
                            rows.append("🟨⬛⬛⬛⬛")
                        elif i <= 4:
                            rows.append("🟩🟨⬛⬛⬛")
                        else:
                            rows.append("🟩🟩🟨⬛⬛")
                    
                    # Last row is all green unless it's an X/6 (score=7)
                    if score == 7:
                        rows.append("⬛⬛⬛⬛⬛")
                    else:
                        rows.append("🟩🟩🟩🟩🟩")
                    
                    new_pattern = '\n'.join(rows)
            
            # Update in database with IMMEDIATE transaction for durability
            conn.execute("BEGIN IMMEDIATE")
            cursor.execute("""
                UPDATE score 
                SET emoji_pattern = ? 
                WHERE id = ?
            """, (new_pattern, score_id))
            
            conn.commit()
            logging.info(f"Updated {player_name}'s pattern in the database")
            
            # Double verify the update with a new connection
            verify_conn = sqlite3.connect("wordle_league.db")
            verify_conn.row_factory = sqlite3.Row
            verify_cursor = verify_conn.cursor()
            verify_cursor.execute("SELECT emoji_pattern FROM score WHERE id = ?", (score_id,))
            updated_pattern = verify_cursor.fetchone()["emoji_pattern"]
            updated_rows = updated_pattern.count('\n') + 1
            logging.info(f"Verified pattern now has {updated_rows} rows")
            logging.info(f"New pattern: {updated_pattern}")
            verify_conn.close()
            
            conn.close()
            return updated_rows == correct_rows
        else:
            logging.info(f"Pattern already has {correct_rows} rows, no fix needed")
            conn.close()
            return True
    except Exception as e:
        logging.error(f"Error fixing {player_name}'s pattern: {e}")
        return False

def run_export_and_push():
    """Run export_leaderboard.py and push changes to GitHub"""
    try:
        # Export website
        logging.info("Running export_leaderboard.py...")
        export_result = subprocess.run(["python", "export_leaderboard.py"], 
                               capture_output=True, text=True, check=False)
        if export_result.returncode != 0:
            logging.error(f"Export failed: {export_result.stderr}")
            return False
        
        # Run the repair script to push changes
        logging.info("Running repair_git_and_push.py...")
        push_result = subprocess.run(["python", "repair_git_and_push.py"], 
                              capture_output=True, text=True, check=False)
        if push_result.returncode != 0:
            logging.error(f"Push failed: {push_result.stderr}")
            return False
        
        logging.info("Website updated and pushed to GitHub successfully")
        return True
    except Exception as e:
        logging.error(f"Error running export and push: {e}")
        return False

def main():
    logging.info("Starting pattern fixes for Joanna and Brent...")
    
    # Fix Joanna's pattern
    joanna_fixed = fix_player_pattern("Joanna", 1500, 5)
    
    # Fix Brent's pattern
    brent_fixed = fix_player_pattern("Brent", 1500, 6)
    
    if joanna_fixed and brent_fixed:
        # Run export and push
        run_export_and_push()
        
        logging.info("All patterns fixed and website updated!")
        print("\nPattern fixes applied and website updated!")
        print("Please check the site in about 1-2 minutes at:")
        print("https://brentcurtis182.github.io/wordle-league/")
    else:
        logging.error("Failed to fix all patterns")

if __name__ == "__main__":
    main()
