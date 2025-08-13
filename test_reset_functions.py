import sqlite3
import logging
import os
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def test_daily_reset(force=True):
    """Test the daily reset function"""
    logging.info("Testing daily reset function")
    
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Create settings table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')
        
        # Get the last reset date from the settings table
        cursor.execute("SELECT value FROM settings WHERE key = 'last_reset_date'")
        result = cursor.fetchone()
        
        if result:
            last_update_date = result[0]
            logging.info(f"Last daily reset date: {last_update_date}")
        else:
            logging.info("No previous daily reset recorded")
        
        # Create latest_scores table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS latest_scores (
            player_id INTEGER,
            league_id INTEGER,
            score INTEGER,
            emoji_pattern TEXT,
            score_date TEXT,
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
        ''')
        
        # Count records in latest_scores
        cursor.execute("SELECT COUNT(*) FROM latest_scores")
        count = cursor.fetchone()[0]
        logging.info(f"Records in latest_scores before reset: {count}")
        
        # Get today's date
        today = datetime.now().date().isoformat()
        
        # Update the last reset date (to yesterday to force a reset)
        if force:
            yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('last_reset_date', ?)", (yesterday,))
            conn.commit()
            logging.info(f"Forced last_reset_date to yesterday: {yesterday}")
        
        # Clear latest scores table
        cursor.execute("DELETE FROM latest_scores")
        conn.commit()
        
        # Update the last reset date
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('last_reset_date', ?)", (today,))
        conn.commit()
        
        logging.info("Daily reset test completed successfully")
        return True
    except Exception as e:
        logging.error(f"Error testing daily reset: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def test_weekly_reset(force=True):
    """Test the weekly reset function"""
    logging.info("Testing weekly reset function")
    
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Create settings table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')
        
        # Check for weekly reset setting
        cursor.execute("SELECT value FROM settings WHERE key = 'last_weekly_reset'")
        result = cursor.fetchone()
        
        if result:
            last_weekly_reset = result[0]
            logging.info(f"Last weekly reset: {last_weekly_reset}")
        else:
            logging.info("No previous weekly reset recorded")
        
        # Create season_winners table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS season_winners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            league_id INTEGER,
            week_date TEXT,
            score INTEGER,
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
        ''')
        
        # Count records in season_winners
        cursor.execute("SELECT COUNT(*) FROM season_winners")
        count = cursor.fetchone()[0]
        logging.info(f"Current records in season_winners: {count}")
        
        # If force is True, pretend today is Monday
        if force:
            # Set last_weekly_reset to a month ago to force a reset
            old_date = (datetime.now() - timedelta(days=30)).strftime("%b %d")
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('last_weekly_reset', ?)", (old_date,))
            conn.commit()
            logging.info(f"Forced last_weekly_reset to {old_date}")
            
            # Get current date and last Monday
            today = datetime.now().date()
            
            # Find last Monday (7 days ago if today is Monday, otherwise earlier)
            days_since_last_monday = (today.weekday() + 7) % 7
            if days_since_last_monday == 0:
                days_since_last_monday = 7  # If today is Monday, use last Monday
                
            last_monday = today - timedelta(days=days_since_last_monday)
            monday_str = last_monday.strftime("%b %d")
            
            logging.info(f"Testing with last Monday as: {monday_str}")
            
            # Find winners for each league for the last week
            for league_id in range(1, 6):  # 1-5 for all leagues
                # Get weekly winners
                cursor.execute("""
                SELECT p.id, p.name, MIN(s.score) as best_score 
                FROM scores s
                JOIN players p ON s.player_id = p.id
                WHERE p.league_id = ? 
                AND s.date >= ? 
                AND s.date < ?
                GROUP BY p.id
                ORDER BY best_score
                LIMIT 1
                """, (league_id, last_monday.isoformat(), today.isoformat()))
                
                winner = cursor.fetchone()
                if winner:
                    player_id, name, score = winner
                    logging.info(f"Weekly winner for league {league_id}: {name} with score {score}")
                    
                    # Check if this winner is already in season_winners
                    cursor.execute("""
                    SELECT id FROM season_winners 
                    WHERE player_id = ? AND league_id = ? AND week_date = ?
                    """, (player_id, league_id, monday_str))
                    
                    if not cursor.fetchone():
                        cursor.execute("""
                        INSERT INTO season_winners (player_id, league_id, week_date, score)
                        VALUES (?, ?, ?, ?)
                        """, (player_id, league_id, monday_str, score))
                        logging.info(f"Added {name} as winner for league {league_id}")
                    else:
                        logging.info(f"Winner {name} already exists for league {league_id}")
                else:
                    logging.info(f"No winner found for league {league_id}")
            
            # Update the last weekly reset date
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('last_weekly_reset', ?)", (monday_str,))
            conn.commit()
            
            # Count records in season_winners after update
            cursor.execute("SELECT COUNT(*) FROM season_winners")
            new_count = cursor.fetchone()[0]
            logging.info(f"Records in season_winners after test: {new_count}")
            logging.info(f"Added {new_count - count} new winners")
        
        logging.info("Weekly reset test completed")
        return True
    except Exception as e:
        logging.error(f"Error testing weekly reset: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def check_database_tables():
    """Check if all required tables exist in the database"""
    logging.info("Checking database tables")
    
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check which tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        logging.info(f"Tables in database: {', '.join(tables)}")
        
        # Check for required tables
        required_tables = ['players', 'scores', 'latest_scores', 'settings', 'season_winners']
        for table in required_tables:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logging.info(f"Table '{table}' exists with {count} records")
            else:
                logging.warning(f"Table '{table}' does not exist")
                
        # Check settings values
        if 'settings' in tables:
            cursor.execute("SELECT key, value FROM settings")
            settings = cursor.fetchall()
            for key, value in settings:
                logging.info(f"Setting: {key} = {value}")
        
        return True
    except Exception as e:
        logging.error(f"Error checking database tables: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    logging.info("Starting reset function tests")
    
    # First check database tables
    check_database_tables()
    
    # Test daily reset
    test_daily_reset()
    
    # Test weekly reset
    test_weekly_reset()
    
    logging.info("Reset function tests completed")
