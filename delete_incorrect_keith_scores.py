#!/usr/bin/env python3
"""
Script to delete Keith's incorrectly assigned scores that match Joanna's scores
"""

import sqlite3
import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("keith_score_fix.log"),
        logging.StreamHandler()
    ]
)

def identify_and_delete_incorrect_scores():
    """Identify and delete Keith's scores that match Joanna's scores"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get today's date
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        # Find Keith's player ID
        cursor.execute("SELECT id FROM players WHERE name = 'Keith' AND league_id = 2")
        keith_id = cursor.fetchone()
        
        if not keith_id:
            logging.error("Could not find Keith in League 2")
            print("Error: Could not find Keith in League 2")
            conn.close()
            return False
            
        keith_id = keith_id[0]
        
        # Find Joanna's player ID for League 2
        cursor.execute("SELECT id FROM players WHERE name LIKE '%Joanna%' AND league_id = 2")
        joanna_id = cursor.fetchone()
        
        if not joanna_id:
            logging.error("Could not find Joanna in League 2")
            print("Error: Could not find Joanna in League 2")
            conn.close()
            return False
            
        joanna_id = joanna_id[0]
        
        # Find matches where Keith and Joanna have identical scores on the same date
        logging.info(f"Looking for matching scores between Keith (ID: {keith_id}) and Joanna (ID: {joanna_id})")
        cursor.execute("""
            SELECT k.id as keith_score_id, k.date, k.wordle_number, k.score,
                   j.id as joanna_score_id
            FROM scores k
            JOIN scores j ON k.date = j.date AND k.wordle_number = j.wordle_number AND k.score = j.score
            WHERE k.player_id = ? AND j.player_id = ?
            ORDER BY k.date DESC
        """, (keith_id, joanna_id))
        
        matching_scores = cursor.fetchall()
        
        if not matching_scores:
            logging.info("No matching scores found between Keith and Joanna")
            print("No matching scores found between Keith and Joanna")
        else:
            print(f"Found {len(matching_scores)} matching scores between Keith and Joanna:")
            for i, score in enumerate(matching_scores):
                keith_score_id, date, wordle_num, score_value, joanna_score_id = score
                print(f"{i+1}. Date: {date}, Wordle #{wordle_num}, Score: {score_value}")
                print(f"   Keith's Score ID: {keith_score_id}, Joanna's Score ID: {joanna_score_id}")
                
            print("\nThese are likely incorrect assignments to Keith.")
            choice = input("Delete all these scores for Keith? (y/n): ")
            
            if choice.lower() == 'y':
                # Delete all Keith's matching scores
                keith_score_ids = [score[0] for score in matching_scores]
                
                # Convert list to string for SQL query
                ids_str = ','.join('?' for _ in keith_score_ids)
                cursor.execute(f"DELETE FROM scores WHERE id IN ({ids_str})", keith_score_ids)
                conn.commit()
                
                logging.info(f"Deleted {len(keith_score_ids)} incorrect scores for Keith")
                print(f"Successfully deleted {len(keith_score_ids)} incorrect scores for Keith")
            else:
                logging.info("User chose not to delete scores")
                print("No scores deleted")
        
        conn.close()
        return True
        
    except Exception as e:
        logging.error(f"Error identifying and deleting scores: {e}")
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def check_extraction_code():
    """Check for potential issues in the extraction code"""
    try:
        extraction_file = 'direct_hidden_extraction.py'
        
        if not os.path.exists(extraction_file):
            logging.warning(f"Could not find extraction file: {extraction_file}")
            return False
            
        with open(extraction_file, 'r', encoding='utf-8') as f:
            code = f.read()
            
        # Look for the player mapping logic
        if "def extract_hidden_scores" in code:
            logging.info("Found extract_hidden_scores function")
            print("\nIssue Diagnosis:")
            print("The problem is likely in the 'extract_hidden_scores' function in direct_hidden_extraction.py")
            print("When extracting scores from messages, the system:")
            print("1. Correctly maps Joanna's phone number to her in both leagues")
            print("2. But also incorrectly assigns her score to Keith in League 2")
            print("\nPossible Fix:")
            print("In direct_hidden_extraction.py, ensure that when mapping phone numbers to players:")
            print("- Each message is only assigned to the player who actually sent it")
            print("- League 2 score assignments should verify the player before saving")
            
        return True
    except Exception as e:
        logging.error(f"Error checking extraction code: {e}")
        return False

def main():
    logging.info("Starting to fix Keith's incorrect scores...")
    
    # Identify and delete incorrect scores
    identify_and_delete_incorrect_scores()
    
    # Provide guidance on fixing the root cause
    print("\nTo prevent this issue in the future:")
    print("1. Check the extraction logic in direct_hidden_extraction.py")
    print("2. Ensure that when a message is received from Joanna's phone:")
    print("   - It correctly assigns to Joanna in both leagues")
    print("   - But does NOT assign to any other player like Keith")
    print("3. Consider adding additional logging to trace the score assignment process")
    
    logging.info("Score fixing process completed")

if __name__ == "__main__":
    import os
    main()
