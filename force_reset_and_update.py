#!/usr/bin/env python3
"""
Force Reset and Update Script
This script directly resets the weekly scores and updates the website HTML.
"""

import os
import sqlite3
import logging
import subprocess
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def direct_database_reset():
    """Directly reset scores in the database"""
    print("\n=== DIRECTLY RESETTING DATABASE ===")
    
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check if tables exist, create if not
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS latest_scores (
            player_id INTEGER,
            league_id INTEGER,
            score INTEGER,
            emoji_pattern TEXT,
            score_date TEXT,
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS season_winners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            league_id INTEGER,
            week_date TEXT,
            score INTEGER,
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
        """)
        
        # Clear latest_scores table
        cursor.execute("DELETE FROM latest_scores")
        
        # Calculate dates for weekly reset
        today = datetime.now().date()
        today_str = today.isoformat()
        
        # If today is Monday, get winners from last week and add to season_winners
        if today.weekday() == 0:  # Monday = 0
            print("Today is Monday - processing weekly winners...")
            
            # Get start of last week (7 days ago)
            days_since_last_monday = 7  # Since today is Monday, last Monday was 7 days ago
            last_monday = today - timedelta(days=days_since_last_monday)
            last_sunday = today - timedelta(days=1)
            monday_str = last_monday.strftime("%b %d")  # Format as "Aug 04"
            
            print(f"Finding winners for last week: {last_monday} to {last_sunday}")
            
            # Update all leagues
            for league_id in range(1, 6):  # 1-5 for all leagues
                # Get weekly winners
                cursor.execute("""
                SELECT p.id, p.name, MIN(s.score) as best_score 
FROM latest_scores s
JOIN players p ON s.player_id = p.id
WHERE s.league_id = ? 
AND s.score_date >= ? 
AND s.score_date < ? 
                AND s.score_date < ?
                GROUP BY p.id
                ORDER BY best_score
                LIMIT 1
                """, (league_id, last_monday.isoformat(), today.isoformat()))
                
                winner = cursor.fetchone()
                if winner:
                    player_id, name, score = winner
                    print(f"Weekly winner for league {league_id}: {name} with score {score}")
                    
                    # Add to season_winners table if not already there
                    cursor.execute("""
                    SELECT id FROM season_winners 
                    WHERE player_id = ? AND league_id = ? AND week_date = ?
                    """, (player_id, league_id, monday_str))
                    
                    if not cursor.fetchone():
                        cursor.execute("""
                        INSERT INTO season_winners (player_id, league_id, week_date, score)
                        VALUES (?, ?, ?, ?)
                        """, (player_id, league_id, monday_str, score))
                        print(f"Added {name} to season winners for league {league_id}")
                else:
                    print(f"No winner found for league {league_id}")
        
        # Update settings to reflect today's reset
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('last_reset_date', ?)", 
                      (today_str,))
                      
        # Force weekly reset flag to be updated
        if today.weekday() == 0:
            monday_str = today.strftime("%b %d")
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('last_weekly_reset', ?)", 
                          (monday_str,))
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("Database reset complete!")
        return True
    except Exception as e:
        print(f"Error resetting database: {e}")
        return False

def force_html_update():
    """Force update of all league HTML files"""
    print("\n=== FORCING HTML UPDATE ===")
    
    try:
        # Update all leagues
        result = subprocess.run(["python", "update_all_correct_structure.py"], 
                              capture_output=True, text=True, check=False)
        
        print(f"HTML update output:\n{result.stdout}")
        if result.stderr:
            print(f"HTML update errors:\n{result.stderr}")
        
        # Fix tabs
        print("\nFixing tabs...")
        result = subprocess.run(["python", "fix_tabs.py"], 
                              capture_output=True, text=True, check=False)
        
        print(f"Fix tabs output:\n{result.stdout}")
        if result.stderr:
            print(f"Fix tabs errors:\n{result.stderr}")
        
        return True
    except Exception as e:
        print(f"Error updating HTML: {e}")
        return False

def run_safeguard():
    """Run scheduler safeguard to ensure website integrity"""
    print("\n=== RUNNING SAFEGUARD ===")
    
    try:
        result = subprocess.run(["python", "scheduler_safeguard.py"], 
                              capture_output=True, text=True, check=False)
        
        print(f"Safeguard output:\n{result.stdout}")
        if result.stderr:
            print(f"Safeguard errors:\n{result.stderr}")
        
        return True
    except Exception as e:
        print(f"Error running safeguard: {e}")
        return False

def main():
    """Main function"""
    print("\n===== FORCING IMMEDIATE RESET AND UPDATE =====")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Current weekday: {datetime.now().strftime('%A')}")
    print("=============================================\n")
    
    # 1. Direct database reset
    if direct_database_reset():
        print("✓ Database reset successful")
    else:
        print("× Database reset failed")
        return
    
    # 2. Force HTML update
    if force_html_update():
        print("✓ HTML update successful")
    else:
        print("× HTML update failed")
    
    # 3. Run safeguard
    if run_safeguard():
        print("✓ Safeguard check successful")
    else:
        print("× Safeguard check failed")
    
    print("\n===== RESET AND UPDATE COMPLETE =====")
    print("\nThe website should now be reset with:")
    print("1. Clear latest scores")
    print("2. Reset weekly stats")
    print("3. Updated Season table with last week's winners")
    print("\nCheck the website in your browser to confirm.")

if __name__ == "__main__":
    main()
