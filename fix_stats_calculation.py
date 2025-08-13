#!/usr/bin/env python3
# Script to fix statistics calculation and handle special score values
import os
import sqlite3
import logging
from datetime import datetime, timedelta
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_stats_calculation.log"),
        logging.StreamHandler()
    ]
)

# Database path
WORDLE_DATABASE = 'wordle_league.db'

def fix_special_score_values():
    """Fix special score values like '-' in the database"""
    conn = None
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Find all special score values
        cursor.execute("""
        SELECT id, player_name, wordle_num, score, league_id 
        FROM scores 
        WHERE score NOT IN ('1', '2', '3', '4', '5', '6', 'X') AND score IS NOT NULL
        """)
        
        special_scores = cursor.fetchall()
        logging.info(f"Found {len(special_scores)} special score values in the database")
        
        for row in special_scores:
            id, player, wordle, score, league_id = row
            logging.info(f"Found special score '{score}' for player {player}, Wordle #{wordle}, league {league_id}")
            
            # Update to 'X' if it's a hyphen or similar placeholder
            # Handle different data types
            if isinstance(score, str):
                if score == '-' or score.lower() == 'none' or score == '':
                    cursor.execute("""
                    UPDATE scores SET score = ? WHERE id = ?
                    """, ('X', id))
                    logging.info(f"Updated score for {player}, Wordle #{wordle} from '{score}' to 'X'")
            elif score > 6:  # Handle integer scores > 6 (invalid Wordle scores)
                cursor.execute("""
                UPDATE scores SET score = ? WHERE id = ?
                """, ('X', id))
                logging.info(f"Updated score for {player}, Wordle #{wordle} from '{score}' to 'X'")
        
        conn.commit()
        logging.info(f"Fixed special score values in the database")
        return True
        
    except Exception as e:
        logging.error(f"Error fixing special score values: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def patch_export_script():
    """Create a patched version of export_leaderboard_multi_league.py"""
    try:
        # Read the original file
        with open('export_leaderboard_multi_league.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Create backup
        with open('export_leaderboard_multi_league.py.bak', 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Fix the score handling in get_weekly_stats_by_league function
        content = content.replace(
            "if score == 'X':",
            "if score in ('X', '-', 'None', ''):"
        )
        
        # Fix the score conversion in weekly stats
        content = content.replace(
            "weekly_scores.append(int(score))",
            """try:
                        weekly_scores.append(int(score))
                    except (ValueError, TypeError):
                        # Skip invalid score values
                        logging.warning(f"Skipping invalid score value: {score}")"""
        )
        
        # Fix the score conversion in all-time stats
        content = content.replace(
            "if score == 'X':\n                    failed_attempts += 1",
            """if score in ('X', '-', 'None', '') or not score:
                    failed_attempts += 1"""
        )
        
        content = content.replace(
            "scores_by_value[int(score)] += 1",
            """try:
                        scores_by_value[int(score)] += 1
                    except (ValueError, TypeError):
                        # Skip invalid score values
                        logging.warning(f"Skipping invalid score value: {score}")"""
        )
        
        # Fix sorting to properly handle None values
        content = content.replace(
            "# Sort by weekly score (lower is better)\n        # Sort by games played (descending) then weekly score (ascending)\n        stats.sort(key=lambda x: (",
            """# Sort by games played (most first), then by weekly score (lowest first)
        # First make sure all entries have numeric values for sorting
        for stat in stats:
            if stat['weekly_score'] is None:
                stat['weekly_score'] = float('inf')  # Use infinity for None values
            if stat['used_scores'] is None:
                stat['used_scores'] = 0
                
        # Sort by games played (descending) then weekly score (ascending)
        stats.sort(key=lambda x: ("""
        )
        
        # Make sure "No Score Posted" entries appear at the bottom
        content = content.replace(
            """            if name not in players_with_scores:
                daily_scores.append({
                    'name': name,
                    'has_score': False,
                    'score': None,
                    'emoji_pattern': None
                })""",
            """            if name not in players_with_scores:
                daily_scores.append({
                    'name': name,
                    'has_score': False,
                    'score': None,
                    'score_display': 'none',  # Add display class for CSS
                    'emoji_pattern': None
                })"""
        )
        
        # Write the patched file
        with open('export_leaderboard_multi_league.py', 'w', encoding='utf-8') as f:
            f.write(content)
            
        logging.info(f"Successfully patched export_leaderboard_multi_league.py")
        return True
        
    except Exception as e:
        logging.error(f"Error patching export script: {e}")
        return False

def run_export_script():
    """Run the patched export script"""
    try:
        import subprocess
        result = subprocess.run([sys.executable, "export_leaderboard_multi_league.py"], 
                                capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Successfully ran export script")
            print("Export script output:")
            print(result.stdout)
            return True
        else:
            logging.error(f"Export script failed: {result.stderr}")
            print("Export script error:")
            print(result.stderr)
            return False
            
    except Exception as e:
        logging.error(f"Error running export script: {e}")
        return False

def publish_website():
    """Publish the fixed website"""
    try:
        import subprocess
        result = subprocess.run([sys.executable, "publish_website.py"], 
                                capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Successfully published website")
            print("Publish script output:")
            print(result.stdout)
            return True
        else:
            logging.error(f"Publish script failed: {result.stderr}")
            print("Publish script error:")
            print(result.stderr)
            return False
            
    except Exception as e:
        logging.error(f"Error publishing website: {e}")
        return False

def main():
    logging.info("Starting fix for statistics calculation")
    
    # Step 1: Fix special score values in the database
    if fix_special_score_values():
        logging.info("Successfully fixed special score values in the database")
    else:
        logging.error("Failed to fix special score values in the database")
        return False
    
    # Step 2: Patch the export script
    if patch_export_script():
        logging.info("Successfully patched export script")
    else:
        logging.error("Failed to patch export script")
        return False
    
    # Step 3: Run the patched export script
    if run_export_script():
        logging.info("Successfully ran export script")
    else:
        logging.error("Failed to run export script")
        return False
    
    # Step 4: Publish the website
    if publish_website():
        logging.info("Successfully published website")
    else:
        logging.error("Failed to publish website")
        return False
    
    logging.info("Fix for statistics calculation completed successfully")
    return True

if __name__ == "__main__":
    main()
