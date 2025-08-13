import sqlite3
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Connect to database
conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

# Today's date in YYYY-MM-DD format
today_str = datetime.now().strftime('%Y-%m-%d')
now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Wordle number we want to add
wordle_num = 1505

# Scores to add (player_name, score, league_id)
new_scores = [
    # Wordle Warriorz league (1)
    ("Brent", 7, 1),  # X/6 score is stored as 7
    
    # PAL league (3)
    ("Vox", 7, 3),    # X/6 score is stored as 7
    ("Fuzwuz", 6, 3),
    ("Starslider", 3, 3)
]

scores_added = 0

for score_data in new_scores:
    player_name, score, league_id = score_data
    
    # Check if score already exists
    cursor.execute("""
        SELECT id FROM scores 
        WHERE player_name = ? AND wordle_num = ? AND league_id = ?
    """, (player_name, wordle_num, league_id))
    
    if cursor.fetchone():
        logging.info(f"Score already exists for {player_name}, Wordle #{wordle_num}, league {league_id}")
        continue
    
    # Get player ID
    cursor.execute("""
        SELECT id FROM players WHERE name = ? AND league_id = ?
    """, (player_name, league_id))
    
    player_result = cursor.fetchone()
    if not player_result:
        logging.warning(f"Player not found: {player_name} in league {league_id}")
        continue
    
    player_id = player_result[0]
    
    # Insert into scores table
    cursor.execute("""
        INSERT INTO scores (player_name, score, wordle_num, league_id)
        VALUES (?, ?, ?, ?)
    """, (player_name, score, wordle_num, league_id))
    
    # Insert into score table
    cursor.execute("""
        INSERT INTO score (player_id, score, wordle_number, date, created_at, league_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (player_id, score, wordle_num, today_str, now_str, league_id))
    
    scores_added += 1
    logging.info(f"Added score for {player_name}: {score}/6 for Wordle #{wordle_num} in league {league_id}")

conn.commit()
conn.close()

logging.info(f"Successfully added {scores_added} new scores")
