import sqlite3
import logging
import argparse
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

def check_todays_scores(league_id=None):
    """Check scores for today in the database
    
    Args:
        league_id: Optional ID of the league to check scores for
    """
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check today's scores
        today = datetime.now().strftime('%Y-%m-%d')
        today_timestamp = f"{today}%"  # For LIKE query with timestamp
        
        if league_id is not None:
            cursor.execute('SELECT player_name, score, wordle_num, timestamp, league_id FROM scores WHERE timestamp LIKE ? AND league_id = ? ORDER BY score', 
                          (today_timestamp, league_id))
            logging.info(f"Checking scores for league ID: {league_id}")
        else:
            cursor.execute('SELECT player_name, score, wordle_num, timestamp, league_id FROM scores WHERE timestamp LIKE ? ORDER BY score', 
                          (today_timestamp,))
            logging.info("Checking scores for all leagues")
        today_scores = cursor.fetchall()
        
        logging.info(f"Found {len(today_scores)} scores for today ({today}):")
        for score in today_scores:
            league_str = f"League: {score[4]}" if len(score) > 4 else ""
            logging.info(f"Player: {score[0]}, Score: {score[1]}/6, Wordle #{score[2]} {league_str}")
        
        # Check specific players
        players_to_check = ['Evan', 'Joanna', 'Brent', 'Vox', 'Starslider']
        for player in players_to_check:
            if league_id is not None:
                cursor.execute('SELECT player_name, score, wordle_num, timestamp, league_id FROM scores WHERE player_name = ? AND timestamp LIKE ? AND league_id = ? ORDER BY wordle_num DESC', 
                              (player, today_timestamp, league_id))
            else:
                cursor.execute('SELECT player_name, score, wordle_num, timestamp, league_id FROM scores WHERE player_name = ? AND timestamp LIKE ? ORDER BY wordle_num DESC', 
                              (player, today_timestamp))
                
            player_scores = cursor.fetchall()
            if player_scores:
                for score in player_scores:
                    league_str = f" (League: {score[4]})" if len(score) > 4 else ""
                    logging.info(f"{player}'s score today: {score[1]}/6 for Wordle #{score[2]}{league_str}")
            else:
                league_str = f" in League {league_id}" if league_id is not None else ""
                logging.info(f"{player} has no score for today{league_str}")
                
        # Check for any PAL league scores specifically
        if league_id is None or league_id == 3:
            cursor.execute('SELECT player_name, score, wordle_num, timestamp FROM scores WHERE league_id = 3 AND timestamp LIKE ?', (today_timestamp,))
            pal_scores = cursor.fetchall()
            if pal_scores:
                logging.info(f"Found {len(pal_scores)} PAL league scores for today:")
                for score in pal_scores:
                    logging.info(f"PAL Player: {score[0]}, Score: {score[1]}/6, Wordle #{score[2]}")
            else:
                logging.info("No PAL league scores found for today")
        
        conn.close()
        
    except Exception as e:
        logging.error(f"Error checking database: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check Wordle scores for today')
    parser.add_argument('--league', type=int, help='League ID to check scores for')
    args = parser.parse_args()
    
    check_todays_scores(args.league)
