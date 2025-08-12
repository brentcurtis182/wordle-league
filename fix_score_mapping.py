#!/usr/bin/env python3
"""
Script to investigate and fix Keith/Joanna score mapping issue in League 2
"""

import sqlite3
import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("score_fix.log"),
        logging.StreamHandler()
    ]
)

def check_scores_and_mappings():
    """Check player mappings and recent scores for League 2"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # List all players in League 2
        logging.info("Players in League 2 (Wordle Gang):")
        cursor.execute("SELECT id, name, phone_number, nickname FROM players WHERE league_id = 2")
        league2_players = cursor.fetchall()
        for player in league2_players:
            logging.info(f"Player ID: {player[0]}, Name: {player[1]}, Phone: {player[2]}, Nickname: {player[3]}")
        
        # Get today's date
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        # Check today's scores by player ID
        logging.info(f"\nScores for today ({today}):")
        cursor.execute("""
            SELECT s.id, s.player_id, p.name, s.wordle_number, s.score, s.date, p.league_id 
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE s.date = ?
            ORDER BY p.league_id, p.name
        """, (today,))
        
        today_scores = cursor.fetchall()
        for score in today_scores:
            logging.info(f"Score ID: {score[0]}, Player ID: {score[1]}, Name: {score[2]}, " +
                         f"Wordle #: {score[3]}, Score: {score[4]}, Date: {score[5]}, League ID: {score[6]}")
        
        # Check Joanna's phone specifically
        logging.info("\nMessages from Joanna's phone:")
        cursor.execute("""
            SELECT p.id, p.name, p.league_id, s.wordle_number, s.score, s.date 
            FROM players p
            JOIN scores s ON p.id = s.player_id
            WHERE p.phone_number = '13109263555'
            ORDER BY s.date DESC, p.league_id
            LIMIT 10
        """)
        
        joanna_scores = cursor.fetchall()
        for score in joanna_scores:
            logging.info(f"Player ID: {score[0]}, Name: {score[1]}, League: {score[2]}, " +
                         f"Wordle #: {score[3]}, Score: {score[4]}, Date: {score[5]}")
        
        # Check for any scores assigned to Keith
        logging.info("\nScores assigned to Keith:")
        cursor.execute("""
            SELECT s.id, s.date, s.wordle_number, s.score, s.emoji_pattern 
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE p.name = 'Keith'
            ORDER BY s.date DESC
            LIMIT 10
        """)
        
        keith_scores = cursor.fetchall()
        for score in keith_scores:
            logging.info(f"Score ID: {score[0]}, Date: {score[1]}, Wordle #: {score[2]}, " +
                         f"Score: {score[3]}, Pattern: {score[4]}")
            
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error checking scores and mappings: {e}")
        return False

def identify_duplicate_scores():
    """Identify if the same score might be assigned to multiple players"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get today's date
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        # Check for duplicate scores from the same phone number
        logging.info("\nChecking for duplicate score assignments:")
        cursor.execute("""
            SELECT p.phone_number, COUNT(s.id) as score_count, GROUP_CONCAT(p.name) as player_names, 
                   s.wordle_number, s.score, s.date
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE s.date = ?
            GROUP BY p.phone_number, s.wordle_number, s.score
            HAVING score_count > 1
        """, (today,))
        
        duplicates = cursor.fetchall()
        if duplicates:
            for dup in duplicates:
                logging.warning(f"Duplicate score found - Phone: {dup[0]}, Count: {dup[1]}, " +
                               f"Players: {dup[2]}, Wordle #: {dup[3]}, Score: {dup[4]}, Date: {dup[5]}")
        else:
            logging.info("No duplicate score assignments found for today.")
            
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error identifying duplicates: {e}")
        return False

def get_user_decision():
    """Get user decision on how to fix the issue"""
    print("\nBased on the investigation, it appears that:")
    print("1. A score from Joanna may have been incorrectly assigned to Keith")
    print("2. This could be due to phone number mapping in the extraction process")
    print("\nPossible solutions:")
    print("1. Delete the incorrect score for Keith")
    print("2. Fix the extraction logic to properly distinguish leagues")
    print("3. Add a league identifier in the extraction process")
    
    choice = input("\nHow would you like to proceed? (1/2/3): ")
    return choice

def fix_score_assignment():
    """Fix the incorrect score assignment based on user decision"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get today's date
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        # Find Keith's score for today
        cursor.execute("""
            SELECT s.id, s.wordle_number, s.score
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE p.name = 'Keith' AND p.league_id = 2 AND s.date = ?
        """, (today,))
        
        keith_score = cursor.fetchone()
        
        if keith_score:
            score_id, wordle_number, score = keith_score
            
            # Confirm with the user
            print(f"\nFound Keith's score: ID {score_id}, Wordle #{wordle_number}, Score: {score}, Date: {today}")
            confirm = input("Do you want to delete this score? (y/n): ")
            
            if confirm.lower() == 'y':
                cursor.execute("DELETE FROM scores WHERE id = ?", (score_id,))
                conn.commit()
                logging.info(f"Deleted score ID {score_id} from Keith")
                print(f"Score ID {score_id} has been deleted.")
            else:
                logging.info("User chose not to delete the score")
                print("No changes made.")
        else:
            logging.info("No score found for Keith today")
            print("No score was found for Keith today.")
            
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error fixing score assignment: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def main():
    logging.info("Starting investigation into Keith/Joanna score mapping issue...")
    
    # Check current scores and mappings
    check_scores_and_mappings()
    
    # Check for duplicate score assignments
    identify_duplicate_scores()
    
    # Get user decision on how to fix
    choice = get_user_decision()
    
    # Implement the fix based on user choice
    if choice == '1':
        fix_score_assignment()
    elif choice == '2':
        print("\nTo fix the extraction logic, you'll need to update the extraction script.")
        print("Look for where phone numbers are mapped to player names and ensure league IDs are properly considered.")
    elif choice == '3':
        print("\nTo add a league identifier, consider modifying the message format or using separate threads for each league.")
    else:
        print("\nNo action taken. You can re-run this script later to fix the issue.")
    
    logging.info("Investigation completed. Check the log for details.")
    print("\nInvestigation completed. Results have been logged to 'score_fix.log'.")

if __name__ == "__main__":
    main()
