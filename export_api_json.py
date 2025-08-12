import os
import json
import logging
import sqlite3
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# These will be defined when called from the main script
WORDLE_DATABASE = None
EXPORT_DIR = None
API_DIR = None

def export_league_data_to_json(db_path=None, export_dir=None):
    """Export all league data to JSON files for API consumption"""
    # Use parameters or global variables
    db_path = db_path or WORDLE_DATABASE
    export_dir = export_dir or EXPORT_DIR
    
    # Make sure we have valid paths
    if not db_path or not os.path.exists(db_path):
        logging.error(f"Invalid database path: {db_path}")
        return False
    
    if not export_dir:
        logging.error("Export directory not specified")
        return False
        
    # Set up API directory
    api_dir = os.path.join(export_dir, 'api')
    if not os.path.exists(api_dir):
        os.makedirs(api_dir)
        
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all leagues
        cursor.execute("SELECT league_id, name FROM leagues")
        leagues_data = cursor.fetchall()
        
        if not leagues_data:
            logging.error("No leagues found in database")
            return False
            
        # Build data structure for all leagues
        all_data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "leagues": {}
        }
        
        # Process each league
        for league_id, league_name in leagues_data:
            logging.info(f"Exporting JSON data for league {league_name} (ID: {league_id})")
            
            # Add league data with integer key
            all_data['leagues'][league_id] = {
                "id": league_id,
                "name": league_name,
                "scores": []
            }
            
            # Get today's Wordle number
            wordle_num = calculate_wordle_number()
            
            # Get all scores for this league
            cursor.execute("""
                SELECT s.wordle_number, p.name, p.nickname, s.score, s.emoji_pattern, s.timestamp 
                FROM scores s
                JOIN players p ON s.player_id = p.id
                WHERE p.league_id = ?
                ORDER BY s.wordle_number DESC, s.timestamp DESC
            """, (league_id,))
            
            scores_data = cursor.fetchall()
            
            # Format scores for JSON
            scores = []
            for score_row in scores_data:
                player_name = score_row[2] if score_row[2] else score_row[1]  # Use nickname if available
                
                scores.append({
                    'wordle_number': score_row[0],
                    'name': player_name,
                    'score': score_row[3],
                    'emoji_pattern': score_row[4],
                    'timestamp': score_row[5]
                })
            
            # Add this league's data to the all_data structure
            all_data['leagues'][league_id] = {
                'id': league_id,
                'name': league_name,
                'scores': scores
            }
        
        # Write the latest.json file with all leagues data
        latest_json_path = os.path.join(api_dir, 'latest.json')
        with open(latest_json_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
            
        logging.info(f"Exported latest.json with data for {len(all_data['leagues'])} leagues")
        
        # Also export individual league JSON files
        for league_id, league_data in all_data['leagues'].items():
            league_json_path = os.path.join(api_dir, f'league_{league_id}.json')
            with open(league_json_path, 'w', encoding='utf-8') as f:
                json.dump(league_data, f, ensure_ascii=False, indent=2)
                
            logging.info(f"Exported league_{league_id}.json for {league_data['name']}")
            
        return True
        
    except Exception as e:
        logging.error(f"Error exporting league data to JSON: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return False
    finally:
        if conn:
            conn.close()

def calculate_wordle_number():
    """Calculate today's Wordle number"""
    # Wordle #0 was on June 19, 2021
    start_date = datetime(2021, 6, 19)
    today = datetime.now()
    
    # Calculate days since Wordle #0
    delta = today - start_date
    return delta.days

if __name__ == "__main__":
    if export_league_data_to_json():
        print("Successfully exported league data to JSON")
    else:
        print("Failed to export league data to JSON")
