#!/usr/bin/env python
# Check database state and verify Joanna's score removal

import sqlite3
import logging
import os
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def check_joanna_score():
    """Check if Joanna's Wordle #1500 score still exists"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Find Joanna's ID
        cursor.execute("SELECT id FROM player WHERE name = 'Joanna'")
        result = cursor.fetchone()
        if not result:
            logging.info("Joanna not found in players table")
            conn.close()
            return False
        
        joanna_id = result[0]
        logging.info(f"Found Joanna's ID: {joanna_id}")
        
        # Check if score exists
        cursor.execute(
            "SELECT * FROM score WHERE player_id = ? AND wordle_number = 1500", 
            (joanna_id,)
        )
        score = cursor.fetchone()
        
        if score:
            logging.warning(f"⚠️ Joanna's Wordle #1500 score still exists: {score}")
            return True
        else:
            logging.info("✅ Joanna's Wordle #1500 score not found in database - correct!")
            return False
    except Exception as e:
        logging.error(f"Error checking Joanna's score: {e}")
        return None

def remove_joanna_score():
    """Remove Joanna's Wordle #1500 score"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Find Joanna's ID
        cursor.execute("SELECT id FROM player WHERE name = 'Joanna'")
        result = cursor.fetchone()
        if not result:
            logging.info("Joanna not found in players table")
            conn.close()
            return False
        
        joanna_id = result[0]
        
        # Delete the score
        cursor.execute(
            "DELETE FROM score WHERE player_id = ? AND wordle_number = 1500", 
            (joanna_id,)
        )
        
        if cursor.rowcount > 0:
            logging.info(f"✅ Removed {cursor.rowcount} Joanna Wordle #1500 score(s)")
            conn.commit()
            return True
        else:
            logging.info("No scores found to remove")
            return False
    except Exception as e:
        logging.error(f"Error removing Joanna's score: {e}")
        return False
    finally:
        conn.close()

def check_weekly_scores():
    """Check weekly scores in the database"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Get current Monday at 3:00 AM
        today = datetime.now()
        today_weekday = today.weekday()  # 0 is Monday
        days_since_monday = today_weekday
        start_of_week = today - timedelta(days=days_since_monday)
        start_of_week = start_of_week.replace(hour=3, minute=0, second=0, microsecond=0)
        start_of_week_str = start_of_week.strftime('%Y-%m-%d %H:%M:%S')
        
        logging.info(f"Current week start: {start_of_week_str}")
        
        # Get all scores since start of week
        cursor.execute("""
            SELECT s.wordle_number, s.date, p.name
            FROM score s
            JOIN player p ON s.player_id = p.id
            WHERE s.date >= ?
            ORDER BY s.date DESC
        """, (start_of_week_str,))
        
        weekly_scores = cursor.fetchall()
        
        logging.info(f"Found {len(weekly_scores)} scores since {start_of_week_str}:")
        for score in weekly_scores:
            logging.info(f"Wordle #{score[0]} - {score[2]} - {score[1]}")
        
        return weekly_scores
    except Exception as e:
        logging.error(f"Error checking weekly scores: {e}")
        return []
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logging.info("Checking database state...")
    
    # Check Joanna's score first
    joanna_has_score = check_joanna_score()
    
    if joanna_has_score:
        logging.info("Removing Joanna's score...")
        remove_joanna_score()
        joanna_has_score = check_joanna_score()
    
    # Check weekly scores
    logging.info("\nChecking weekly scores...")
    weekly_scores = check_weekly_scores()
    
    logging.info("\nDatabase check complete")
