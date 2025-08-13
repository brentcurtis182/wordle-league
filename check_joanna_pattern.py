#!/usr/bin/env python
# Check Joanna's pattern in the database

import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def check_joanna_pattern():
    """Check Joanna's emoji pattern in the database"""
    conn = sqlite3.connect("wordle_league.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get Joanna's player ID
    cursor.execute("SELECT id FROM player WHERE name = 'Joanna'")
    joanna_id = cursor.fetchone()["id"]
    logging.info(f"Joanna's player ID: {joanna_id}")
    
    # Get her current score for Wordle 1500
    cursor.execute("""
        SELECT id, score, emoji_pattern 
        FROM score 
        WHERE player_id = ? AND wordle_number = 1500
    """, (joanna_id,))
    
    score_record = cursor.fetchone()
    if not score_record:
        logging.error("No score found for Joanna for Wordle 1500")
        conn.close()
        return
        
    score_id = score_record["id"]
    score = score_record["score"]
    pattern = score_record["emoji_pattern"]
    
    logging.info(f"Joanna's Wordle 1500 score: ID={score_id}, Score={score}")
    
    # Count rows in pattern
    rows = 0
    if pattern:
        rows = pattern.count('\n') + 1
        logging.info(f"Pattern has {rows} rows")
        logging.info(f"Pattern: {pattern}")
    
    # Fix if there's a mismatch
    if score == 5 and rows != 5:
        logging.info("Pattern doesn't match score, needs fixing")
        
        # Create a proper 5-row pattern
        new_pattern = "🟨⬛⬛⬛⬛\n⬛🟨🟨⬛⬛\n⬛🟩🟨🟩⬛\n🟩🟩⬛🟩🟨\n🟩🟩🟩🟩🟩"
        
        # Update in database
        cursor.execute("""
            UPDATE score 
            SET emoji_pattern = ? 
            WHERE id = ?
        """, (new_pattern, score_id))
        
        conn.commit()
        logging.info("Updated Joanna's pattern in the database")
        
        # Verify the update
        cursor.execute("SELECT emoji_pattern FROM score WHERE id = ?", (score_id,))
        updated_pattern = cursor.fetchone()["emoji_pattern"]
        updated_rows = updated_pattern.count('\n') + 1
        logging.info(f"Verified pattern now has {updated_rows} rows")
        logging.info(f"New pattern: {updated_pattern}")
    else:
        if score == 5:
            logging.info("Pattern already matches score, no fix needed")
        else:
            logging.info("Score is not 5, so pattern might be correct")
    
    conn.close()

if __name__ == "__main__":
    check_joanna_pattern()
