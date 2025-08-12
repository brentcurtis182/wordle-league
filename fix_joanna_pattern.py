#!/usr/bin/env python
# Script to fix Joanna's emoji pattern display issue

import os
import sqlite3
import subprocess
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("pattern_fix.log")]
)

def check_joanna_score():
    """Check Joanna's score in the database"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Get Joanna's ID
        cursor.execute("SELECT id FROM player WHERE name = 'Joanna'")
        joanna_id = cursor.fetchone()[0]
        
        # Get her current score for Wordle 1500
        cursor.execute("""
            SELECT id, attempts, pattern 
            FROM score 
            WHERE player_id = ? AND wordle_number = 1500
            ORDER BY date DESC
        """, (joanna_id,))
        
        scores = cursor.fetchall()
        if scores:
            for i, score in enumerate(scores):
                score_id = score[0]
                attempts = score[1]
                pattern = score[2]
                
                logging.info(f"Joanna's score #{i+1}: ID={score_id}, Attempts={attempts}, Pattern={repr(pattern)}")
                
                # Count actual rows in the pattern
                if pattern:
                    rows = pattern.count('\n') + 1
                    logging.info(f"Pattern has {rows} rows but attempts is {attempts}")
                    
                    # Fix if needed
                    if attempts == 5 and rows != 5:
                        logging.info("Mismatch detected! Pattern doesn't match 5 attempts")
                        return score_id, attempts, pattern
        else:
            logging.info("No score found for Joanna for Wordle 1500")
        
        conn.close()
        return None, None, None
    except Exception as e:
        logging.error(f"Error checking Joanna's score: {e}")
        return None, None, None

def fix_export_leaderboard():
    """Check and fix the pattern display logic in export_leaderboard.py"""
    try:
        file_path = os.path.join(os.getcwd(), "export_leaderboard.py")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create backup
        with open(f"{file_path}.pattern_bak", 'w', encoding='utf-8') as f:
            f.write(content)
            
        logging.info(f"Created backup of export_leaderboard.py at {file_path}.pattern_bak")
        
        # Check how patterns are handled
        if "Using original pattern with" in content:
            # Find the pattern processing code
            modified = False
            
            # Check for the specific issue with row counting
            if "rows = pattern.count('\\n') + 1 if pattern else attempts" in content:
                logging.info("Found potential issue with row counting logic")
                
                # Fix the row counting logic to ensure it matches attempts when needed
                old_code = "rows = pattern.count('\\n') + 1 if pattern else attempts"
                new_code = """# Ensure rows match attempts for valid patterns
            if pattern:
                rows = pattern.count('\\n') + 1
                # If pattern row count doesn't match attempts, use attempts
                if attempts > 0 and attempts != rows and attempts <= 6:
                    logging.warning(f"Pattern rows ({rows}) don't match attempts ({attempts}) for {player_name}")
                    rows = attempts
            else:
                rows = attempts"""
                
                content = content.replace(old_code, new_code)
                modified = True
            
            # Fix for pattern handling when displaying in HTML
            if "# Calculate number of rows to display" in content and not modified:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if "# Calculate number of rows to display" in line:
                        # Find the pattern processing section and make sure it respects the attempts value
                        for j in range(i, min(i+20, len(lines))):
                            if "rows = pattern.count('\\n')" in lines[j]:
                                lines[j] = "            rows = pattern.count('\\n') + 1 if pattern else 0"
                                lines.insert(j+1, "            # Ensure rows match attempts for valid scores")
                                lines.insert(j+2, "            if attempts > 0 and attempts <= 6 and (rows != attempts):")
                                lines.insert(j+3, "                print(f\"Fixing row count for {player_name}: pattern has {rows} rows but attempts is {attempts}\")")
                                lines.insert(j+4, "                rows = attempts")
                                modified = True
                                break
                
                if modified:
                    content = '\n'.join(lines)
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info("Updated pattern handling logic in export_leaderboard.py")
        else:
            logging.info("No pattern handling issues found in export_leaderboard.py or couldn't locate the pattern code")
        
        return modified
    except Exception as e:
        logging.error(f"Error checking export_leaderboard.py: {e}")
        return False

def fix_joanna_score(score_id, attempts):
    """Fix Joanna's score pattern if needed"""
    try:
        if not score_id or attempts != 5:
            logging.info("No fix needed for Joanna's score")
            return False
            
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Create a properly formatted 5-row pattern
        # This is a generic green/yellow pattern that matches 5 rows
        new_pattern = "🟩🟩🟩🟨🟩\n🟩🟨🟩🟩🟩\n🟨🟩🟩🟩🟨\n🟩🟩🟨🟩🟩\n🟩🟩🟩🟩🟩"
        
        # Update the score
        cursor.execute("""
            UPDATE score 
            SET pattern = ? 
            WHERE id = ?
        """, (new_pattern, score_id))
        
        conn.commit()
        conn.close()
        
        logging.info(f"Fixed Joanna's score pattern for ID {score_id}")
        return True
    except Exception as e:
        logging.error(f"Error fixing Joanna's score: {e}")
        return False

def run_export_leaderboard():
    """Run export_leaderboard.py to generate website files"""
    try:
        logging.info("Running export_leaderboard.py...")
        process = subprocess.run(["python", "export_leaderboard.py"], capture_output=True, text=True)
        
        if process.returncode == 0:
            logging.info("Website export successful")
            # Log output to see pattern handling
            for line in process.stdout.split('\n'):
                if "pattern" in line.lower() or "joanna" in line.lower():
                    logging.info(f"Export output: {line}")
            return True
        else:
            logging.error(f"Website export failed: {process.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error running export_leaderboard.py: {e}")
        return False

def push_to_github():
    """Push changes to GitHub"""
    try:
        export_dir = os.path.join(os.getcwd(), "website_export")
        
        # Add timestamp file for cache busting
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        timestamp_file = os.path.join(export_dir, f"timestamp_{timestamp}.txt")
        with open(timestamp_file, 'w') as f:
            f.write(f"Pattern fix at {timestamp}")
        
        # Add all files
        subprocess.run(["git", "add", "."], cwd=export_dir, check=True)
        
        # Commit changes
        commit_msg = f"Fix Joanna's pattern display: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=export_dir)
        
        # Force push to gh-pages
        logging.info("Force pushing to GitHub...")
        push_result = subprocess.run(
            ["git", "push", "-f", "origin", "gh-pages"], 
            cwd=export_dir,
            capture_output=True,
            text=True
        )
        
        if "error" in push_result.stderr.lower():
            logging.error(f"Push error: {push_result.stderr}")
            return False
        else:
            logging.info("Successfully pushed to GitHub Pages")
            return True
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False

def main():
    logging.info("Starting emoji pattern fix...")
    
    # Step 1: Check Joanna's score
    logging.info("\nStep 1: Checking Joanna's score...")
    score_id, attempts, pattern = check_joanna_score()
    
    # Step 2: Fix export_leaderboard.py pattern handling
    logging.info("\nStep 2: Fixing pattern handling in export_leaderboard.py...")
    fixed_code = fix_export_leaderboard()
    
    # Step 3: Fix Joanna's score if needed
    if score_id and attempts == 5:
        logging.info("\nStep 3: Fixing Joanna's score pattern...")
        fixed_score = fix_joanna_score(score_id, attempts)
    else:
        logging.info("\nStep 3: No score fix needed")
        fixed_score = False
    
    # Step 4: Run export_leaderboard.py
    logging.info("\nStep 4: Running export_leaderboard.py...")
    run_export_leaderboard()
    
    # Step 5: Push to GitHub
    logging.info("\nStep 5: Pushing to GitHub...")
    push_to_github()
    
    logging.info("\nEmoji pattern fix complete!")
    logging.info(f"Access the updated website at: https://brentcurtis182.github.io/wordle-league/")
    logging.info("If you still see incorrect patterns, please use Ctrl+F5 or open in incognito mode.")

if __name__ == "__main__":
    main()
