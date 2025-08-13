#!/usr/bin/env python3
import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = 'wordle_league.db'

def main():
    """Check emoji patterns in the database"""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check database schema
        cursor.execute("PRAGMA table_info(scores)")
        columns = [column[1] for column in cursor.fetchall()]
        logger.info(f"Scores table columns: {columns}")
        
        # Check if 'pattern' column exists
        if 'pattern' in columns:
            logger.info("'pattern' column exists in scores table")
        else:
            logger.error("'pattern' column does NOT exist in scores table!")
            return
            
        # Get current wordle number
        cursor.execute("SELECT MAX(wordle_num) FROM scores")
        latest_wordle = cursor.fetchone()[0]
        logger.info(f"Latest Wordle number in database: {latest_wordle}")
        
        # Get pattern examples from database
        cursor.execute("""
            SELECT p.name, s.score, s.pattern, s.league_id 
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE s.wordle_num = ?
            ORDER BY s.league_id, p.name
        """, (latest_wordle,))
        
        results = cursor.fetchall()
        
        if not results:
            logger.warning(f"No patterns found for Wordle #{latest_wordle}")
        
        for name, score, pattern, league_id in results:
            if pattern and pattern != "No emoji pattern available":
                logger.info(f"League {league_id}, {name}, Score: {score}, Pattern: {pattern}")
            else:
                logger.warning(f"League {league_id}, {name}, Score: {score}, Pattern: None or empty")
                
        # Count patterns by league
        logger.info("\nPattern counts by league:")
        cursor.execute("""
            SELECT s.league_id, COUNT(*) as total,
            SUM(CASE WHEN s.pattern IS NULL OR s.pattern = 'No emoji pattern available' THEN 0 ELSE 1 END) as with_pattern
            FROM scores s
            GROUP BY s.league_id
        """)
        
        for league_id, total, with_pattern in cursor.fetchall():
            logger.info(f"League {league_id}: {with_pattern}/{total} scores have patterns ({with_pattern/total*100:.1f}%)")
        
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
