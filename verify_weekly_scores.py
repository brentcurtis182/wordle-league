#!/usr/bin/env python3
"""
Script to verify the weekly scores are correctly pulled from both database tables.
This shows exactly which scores are being counted for each player in each league.
"""

import os
import sys
import sqlite3
import json
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('verify_weekly_scores.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Define paths
script_dir = os.path.dirname(os.path.abspath(__file__))
default_db_path = os.path.join(script_dir, 'wordle_league.db')
WORDLE_DATABASE = os.getenv('DATABASE_URI', default_db_path).replace('sqlite:///', '')

def get_raw_scores_for_player(league_id, player_name, player_id=None):
    """Get all scores for a player from both tables without filtering"""
    conn = None
    scores = []
    
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Get scores from the scores table
        cursor.execute("""
        SELECT wordle_num, score, emoji_pattern, timestamp, 'scores' as source
        FROM scores
        WHERE player_name = ? AND league_id = ? 
        ORDER BY CAST(REPLACE(wordle_num, ',', '') AS INTEGER)
        """, (player_name, league_id))
        
        scores_from_scores_table = cursor.fetchall()
        scores.extend(scores_from_scores_table)
        
        # If we have player_id, also get scores from score table
        if player_id:
            cursor.execute("""
            SELECT wordle_number, score, emoji_pattern, date, 'score' as source
            FROM score
            WHERE player_id = ? AND league_id = ?
            ORDER BY CAST(REPLACE(wordle_number, ',', '') AS INTEGER)
            """, (player_id, league_id))
            
            scores_from_score_table = cursor.fetchall()
            scores.extend(scores_from_score_table)
        
        return scores
        
    except Exception as e:
        logging.error(f"Error getting raw scores: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_player_scores_for_wordle_range(league_id, player_name, min_wordle, max_wordle):
    """Get scores for a player within a specific range of Wordle numbers"""
    conn = None
    result = {
        'player_name': player_name,
        'league_id': league_id,
        'min_wordle': min_wordle,
        'max_wordle': max_wordle,
        'scores': [],
        'valid_scores': 0,
        'failed_attempts': 0
    }
    
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # First get player_id if available
        cursor.execute("SELECT id FROM players WHERE name = ? AND league_id = ?", (player_name, league_id))
        player_id_result = cursor.fetchone()
        player_id = player_id_result[0] if player_id_result else None
        
        # Get scores from the scores table
        scores_from_scores = []
        cursor.execute("""
        SELECT wordle_num, score, emoji_pattern, timestamp
        FROM scores
        WHERE player_name = ? AND league_id = ? 
        ORDER BY CAST(REPLACE(wordle_num, ',', '') AS INTEGER)
        """, (player_name, league_id))
        
        for row in cursor.fetchall():
            wordle_num, score, emoji_pattern, timestamp = row
            
            try:
                # Clean wordle number
                clean_wordle = str(wordle_num).replace(',', '')
                wordle_int = int(clean_wordle)
                
                if min_wordle <= wordle_int <= max_wordle:
                    scores_from_scores.append({
                        'wordle_num': wordle_int,
                        'score': score,
                        'emoji_pattern': emoji_pattern,
                        'timestamp': timestamp,
                        'source': 'scores'
                    })
            except (ValueError, TypeError) as e:
                logging.warning(f"Invalid Wordle number in scores table: {wordle_num} - {e}")
        
        # Get scores from the score table if we have player_id
        scores_from_score = []
        if player_id:
            cursor.execute("""
            SELECT wordle_number, score, emoji_pattern, date
            FROM score
            WHERE player_id = ? AND league_id = ?
            ORDER BY CAST(REPLACE(wordle_number, ',', '') AS INTEGER)
            """, (player_id, league_id))
            
            for row in cursor.fetchall():
                wordle_num, score, emoji_pattern, timestamp = row
                
                try:
                    # Clean wordle number
                    clean_wordle = str(wordle_num).replace(',', '')
                    wordle_int = int(clean_wordle)
                    
                    if min_wordle <= wordle_int <= max_wordle:
                        scores_from_score.append({
                            'wordle_num': wordle_int,
                            'score': score,
                            'emoji_pattern': emoji_pattern,
                            'timestamp': timestamp,
                            'source': 'score'
                        })
                except (ValueError, TypeError) as e:
                    logging.warning(f"Invalid Wordle number in score table: {wordle_num} - {e}")
        
        # Merge scores from both tables, avoiding duplicates
        processed_wordles = set()
        combined_scores = []
        
        # First add all scores from scores table
        for score_data in scores_from_scores:
            wordle_num = score_data['wordle_num']
            if wordle_num not in processed_wordles:
                processed_wordles.add(wordle_num)
                combined_scores.append(score_data)
                
                # Count valid scores and failed attempts
                score_val = score_data['score']
                if score_val == 'X':
                    result['failed_attempts'] += 1
                elif score_val not in ('-', 'None', '') and score_val is not None:
                    try:
                        int(score_val)
                        result['valid_scores'] += 1
                    except (ValueError, TypeError):
                        pass
        
        # Then add scores from score table that we haven't seen yet
        for score_data in scores_from_score:
            wordle_num = score_data['wordle_num']
            if wordle_num not in processed_wordles:
                processed_wordles.add(wordle_num)
                combined_scores.append(score_data)
                
                # Count valid scores and failed attempts
                score_val = score_data['score']
                if score_val == 'X':
                    result['failed_attempts'] += 1
                elif score_val not in ('-', 'None', '') and score_val is not None:
                    try:
                        int(score_val)
                        result['valid_scores'] += 1
                    except (ValueError, TypeError):
                        pass
        
        # Sort by Wordle number
        combined_scores.sort(key=lambda x: x['wordle_num'])
        result['scores'] = combined_scores
        
        return result
        
    except Exception as e:
        logging.error(f"Error getting player scores: {e}")
        return result
    finally:
        if conn:
            conn.close()

def verify_league_scores(league_id, min_wordle, max_wordle):
    """Verify scores for all players in a league for a specific Wordle range"""
    conn = None
    
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Get all players for this league
        players = []
        
        # First try to get players from the players table
        try:
            cursor.execute("SELECT name FROM players WHERE league_id = ?", (league_id,))
            player_rows = cursor.fetchall()
            players = [row[0] for row in player_rows]
        except Exception as e:
            logging.warning(f"Error getting players from players table: {e}")
        
        # If no players found, try scores table as fallback
        if not players:
            try:
                cursor.execute("SELECT DISTINCT player_name FROM scores WHERE league_id = ?", (league_id,))
                player_rows = cursor.fetchall()
                players = [row[0] for row in player_rows]
            except Exception as e:
                logging.warning(f"Error getting players from scores table: {e}")
        
        # Special case for PAL league
        if league_id == 3 and "Pants" not in players:
            players.append("Pants")
        
        print(f"League {league_id} - Verifying scores for Wordle range {min_wordle}-{max_wordle}")
        print(f"Found {len(players)} players: {', '.join(players)}")
        print("-" * 50)
        
        all_player_results = []
        
        for player_name in players:
            player_result = get_player_scores_for_wordle_range(league_id, player_name, min_wordle, max_wordle)
            all_player_results.append(player_result)
            
            print(f"\nPlayer: {player_name}")
            print(f"  Valid scores: {player_result['valid_scores']}")
            print(f"  Failed attempts: {player_result['failed_attempts']}")
            
            if player_result['scores']:
                print(f"  Specific scores:")
                for score_data in player_result['scores']:
                    print(f"    Wordle #{score_data['wordle_num']}: {score_data['score']} (from {score_data['source']} table)")
            else:
                print("  No scores found in this range")
        
        return all_player_results
                
    except Exception as e:
        logging.error(f"Error verifying league scores: {e}")
        return []
    finally:
        if conn:
            conn.close()

def main():
    """Verify weekly scores for each league"""
    print("=== Weekly Score Verification ===\n")
    
    # For weekly stats, we need to verify Wordles #1500-1504
    # These are the Wordles from this week according to the user's data
    min_wordle = 1500  # Start of week
    max_wordle = 1504  # Latest Wordle
    
    # Verify League 1 (Warriorz)
    print("\n=== LEAGUE 1 (Wordle Warriorz) ===")
    league1_results = verify_league_scores(1, min_wordle, max_wordle)
    
    # Verify League 3 (PAL)
    print("\n=== LEAGUE 3 (Wordle PAL) ===")
    league3_results = verify_league_scores(3, min_wordle, max_wordle)
    
    # Print summary
    print("\n=== EXPECTED VS ACTUAL COUNTS ===")
    print("League 1 (Warriorz):")
    print("  Brent: Expected 5 scores, Actual", next((r['valid_scores'] for r in league1_results if r['player_name'] == 'Brent'), 0))
    print("  Evan: Expected 4 scores, Actual", next((r['valid_scores'] for r in league1_results if r['player_name'] == 'Evan'), 0))
    print("  Joanna: Expected 5 scores, Actual", next((r['valid_scores'] for r in league1_results if r['player_name'] == 'Joanna'), 0))
    print("  Malia: Expected 4 scores, Actual", next((r['valid_scores'] for r in league1_results if r['player_name'] == 'Malia'), 0))
    print("  Nanna: Expected 4 scores, Actual", next((r['valid_scores'] for r in league1_results if r['player_name'] == 'Nanna'), 0))
    
    print("\nLeague 3 (PAL):")
    print("  Vox: Expected 3 scores, Actual", next((r['valid_scores'] for r in league3_results if r['player_name'] == 'Vox'), 0))
    print("  Fuzwuz: Expected 2 scores, Actual", next((r['valid_scores'] for r in league3_results if r['player_name'] == 'Fuzwuz'), 0))
    print("  Starslider: Expected 2 scores, Actual", next((r['valid_scores'] for r in league3_results if r['player_name'] == 'Starslider'), 0))
    
if __name__ == "__main__":
    main()
