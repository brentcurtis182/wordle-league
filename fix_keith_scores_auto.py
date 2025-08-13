#!/usr/bin/env python3
"""
Automatic script to fix Keith's incorrectly assigned scores and analyze the root cause
"""

import sqlite3
import datetime
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("keith_fix_auto.log"),
        logging.StreamHandler()
    ]
)

def delete_incorrect_scores():
    """Delete Keith's scores that match Joanna's scores"""
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
        
        # Find today's matching scores between Keith and Joanna
        logging.info(f"Looking for today's matching scores between Keith (ID: {keith_id}) and Joanna (ID: {joanna_id})")
        cursor.execute("""
            SELECT k.id as keith_score_id, k.date, k.wordle_number, k.score
            FROM scores k
            JOIN scores j ON k.date = j.date AND k.wordle_number = j.wordle_number AND k.score = j.score
            WHERE k.player_id = ? AND j.player_id = ? AND k.date = ?
        """, (keith_id, joanna_id, today))
        
        matching_scores = cursor.fetchall()
        
        if not matching_scores:
            logging.info(f"No matching scores found between Keith and Joanna for today ({today})")
            print(f"No matching scores found between Keith and Joanna for today ({today})")
            conn.close()
            return True
            
        # Display found matches
        print(f"Found {len(matching_scores)} incorrect score assignments for Keith on {today}:")
        for i, score in enumerate(matching_scores):
            keith_score_id, date, wordle_num, score_value = score
            print(f"{i+1}. Score ID: {keith_score_id}, Date: {date}, Wordle #{wordle_num}, Score: {score_value}")
            
        # Delete all Keith's matching scores from today
        keith_score_ids = [score[0] for score in matching_scores]
        
        # Convert list to string for SQL query
        ids_str = ','.join('?' for _ in keith_score_ids)
        cursor.execute(f"DELETE FROM scores WHERE id IN ({ids_str})", keith_score_ids)
        conn.commit()
        
        logging.info(f"Deleted {len(keith_score_ids)} incorrect scores for Keith")
        print(f"Successfully deleted {len(keith_score_ids)} incorrect scores for Keith")
        
        conn.close()
        return True
        
    except Exception as e:
        logging.error(f"Error deleting incorrect scores: {e}")
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def analyze_extraction_code():
    """Analyze extraction code for the root cause"""
    extraction_files = [
        'direct_hidden_extraction.py',
        'integrated_auto_update_multi_league.py'
    ]
    
    issue_found = False
    potential_fixes = []
    
    for file_name in extraction_files:
        if not os.path.exists(file_name):
            logging.warning(f"File not found: {file_name}")
            continue
            
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                code = f.read()
                
            # Look for specific patterns
            if file_name == 'direct_hidden_extraction.py':
                if "extract_hidden_scores" in code:
                    lines = code.split('\n')
                    player_mapping_lines = []
                    league_id_check_lines = []
                    
                    for i, line in enumerate(lines):
                        if "player = get_player_by_phone" in line:
                            player_mapping_lines.append((i+1, line))
                        if "league_id" in line and "==" in line:
                            league_id_check_lines.append((i+1, line))
                            
                    if player_mapping_lines:
                        issue_found = True
                        logging.info(f"Found player mapping logic in {file_name}:")
                        for line_num, line in player_mapping_lines:
                            logging.info(f"Line {line_num}: {line.strip()}")
                            
                        # Suggest a fix
                        potential_fixes.append({
                            'file': file_name,
                            'issue': "Player mapping doesn't consider league IDs properly",
                            'fix': "Ensure that player mapping checks the league_id when finding players by phone number"
                        })
                        
            elif file_name == 'integrated_auto_update_multi_league.py':
                if "league_id" in code and "find_conversations" in code:
                    issue_found = True
                    
                    # Check if league IDs are being passed correctly
                    if "extract_hidden_scores" in code and "league_id" in code and "league_name" in code:
                        logging.info(f"League ID is being passed to extraction function in {file_name}")
                        
                        # But there might still be an issue with how it's used
                        potential_fixes.append({
                            'file': file_name,
                            'issue': "League ID may not be used correctly in player identification",
                            'fix': "Ensure league ID is used when identifying players from phone numbers"
                        })
        
        except Exception as e:
            logging.error(f"Error analyzing {file_name}: {e}")
    
    # Print analysis results
    if issue_found:
        print("\nRoot Cause Analysis:")
        print("-----------------")
        print("Found potential issues in the extraction code:")
        
        for i, fix in enumerate(potential_fixes):
            print(f"\n{i+1}. File: {fix['file']}")
            print(f"   Issue: {fix['issue']}")
            print(f"   Suggested Fix: {fix['fix']}")
            
        print("\nRecommended Solution:")
        print("-------------------")
        print("1. Modify the player lookup logic to use BOTH phone number AND league_id when finding players")
        print("2. Add checks to prevent assigning the same score to multiple players in the same league")
        print("3. Add more logging to trace the score assignment process")
        print("\nExample code fix:")
        print("```python")
        print("# Before:")
        print("player = get_player_by_phone(phone)")
        print("")
        print("# After:")
        print("player = get_player_by_phone_and_league(phone, league_id)")
        print("```")
    else:
        print("\nCould not identify a clear issue in the extraction code.")
        print("Please manually review the score assignment logic in direct_hidden_extraction.py")
    
    return issue_found

def main():
    logging.info("Starting automatic fix for Keith's incorrect scores...")
    
    # Delete incorrect scores
    delete_incorrect_scores()
    
    # Analyze extraction code
    analyze_extraction_code()
    
    # Remind about scheduler
    print("\nRemember to re-enable the scheduler once the extraction code has been fixed.")
    logging.info("Automatic fix process completed")

if __name__ == "__main__":
    main()
