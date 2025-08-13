import sqlite3
import os
import logging
import pprint

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def check_table_schema(conn, table_name):
    """Check schema of a specific table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    logging.info(f"Schema for table '{table_name}':\n{pprint.pformat([col[1] for col in columns])}")
    return columns

def check_pal_database():
    """Check PAL league players and phone numbers in the database"""
    
    db_path = 'wordle_league.db'
    if not os.path.exists(db_path):
        logging.error(f"Database file not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First, check what tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    logging.info("Tables in database:")
    for table in tables:
        logging.info(f"- {table[0]}")
    
    # Check schema for main tables
    for table in ['leagues', 'players', 'scores', 'league_players']:
        if (table,) in tables:
            check_table_schema(conn, table)
    
    # Get PAL league ID - adjust query based on schema
    cursor.execute("SELECT * FROM leagues WHERE name LIKE '%PAL%'")
    league_result = cursor.fetchone()
    
    # Print all leagues
    cursor.execute("SELECT * FROM leagues")
    all_leagues = cursor.fetchall()
    logging.info("All leagues in database:")
    for league in all_leagues:
        logging.info(f"League: {league}")
    
    if not league_result:
        logging.error("PAL league not found in database")
        conn.close()
        return
    
    # Determine correct column index for league_id based on schema
    # For now assume it's the first column, but we'll check schema to be sure
    pal_league_id = league_result[0]
    logging.info(f"PAL league details: {league_result}")
    
    # Check player table schema to confirm column names
    player_cols = check_table_schema(conn, 'players')
    
    # Check players in PAL league (players have league_id directly)
    cursor.execute("""
        SELECT name, phone_number, id 
        FROM players 
        WHERE league_id = ?
    """, (pal_league_id,))
    
    players = cursor.fetchall()
    logging.info(f"Found {len(players)} players")
    
    if not players:
        logging.warning("No players found")
        conn.close()
        return
    
    # Show player details
    logging.info(f"PAL league player details ({len(players)} players):")
    for row in players:
        if len(row) >= 3:
            name, phone, player_id = row
            logging.info(f"ID: {player_id}, Name: {name}, Phone: {phone}")
        else:
            logging.info(f"Row: {row}")
        
    # Check scores table structure
    check_table_schema(conn, 'scores')
    
    # Check if there are scores for PAL league
    try:
        cursor.execute("""
            SELECT COUNT(*)
            FROM scores
            WHERE league_id = ?
        """, (pal_league_id,))
    except sqlite3.OperationalError as e:
        logging.error(f"Score query error: {e}")
        cursor.execute("SELECT COUNT(*) FROM scores")
    
    score_count = cursor.fetchone()[0]
    logging.info(f"Found {score_count} total scores for PAL league")
    
    # Check most recent scores for PAL league
    cursor.execute("""
        SELECT player_name, wordle_num, score, timestamp
        FROM scores
        WHERE league_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
    """, (pal_league_id,))
    
    recent_scores = cursor.fetchall()
    if recent_scores:
        logging.info(f"Most recent {len(recent_scores)} PAL league scores:")
        for score in recent_scores:
            logging.info(f"Player: {score[0]}, Wordle #{score[1]}, Score: {score[2]}, Time: {score[3]}")
    else:
        logging.info("No recent PAL league scores found")
    
    # Check recent wordle numbers across all leagues
    cursor.execute("""
        SELECT DISTINCT wordle_num 
        FROM scores 
        ORDER BY wordle_num DESC
        LIMIT 10
    """)
    
    recent_wordles = cursor.fetchall()
    if recent_wordles:
        logging.info("Recent Wordle numbers across all leagues:")
        for row in recent_wordles:
            logging.info(f"Wordle #{row[0]}")
    
    # Check recent wordle numbers for PAL league specifically
    cursor.execute("""
        SELECT DISTINCT wordle_num 
        FROM scores 
        WHERE league_id = ?
        ORDER BY wordle_num DESC
        LIMIT 10
    """, (pal_league_id,))
    
    pal_wordles = cursor.fetchall()
    if pal_wordles:
        logging.info("Recent PAL league Wordle numbers:")
        for row in pal_wordles:
            logging.info(f"PAL Wordle #{row[0]}")
    else:
        logging.info("No Wordle numbers found for PAL league specifically")
    
    conn.close()

if __name__ == "__main__":
    check_pal_database()
