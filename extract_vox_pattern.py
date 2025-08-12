#!/usr/bin/env python3
"""
Modified version of the extraction script to specifically log and display Vox's pattern
"""
import sqlite3
import os
import json
import logging
import sys
from datetime import datetime

# Setup logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("vox_pattern_extract.log"),
        logging.StreamHandler()
    ]
)

def get_scores_for_wordle_by_league(wordle_number, league_id):
    """
    Direct copy of the function from the original script to ensure we're using
    the exact same logic for extracting emoji patterns
    """
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get scores for the specified Wordle number and league
        cursor.execute("""
        SELECT p.name, p.nickname, s.score, s.emoji_pattern
        FROM scores s
        JOIN players p ON s.player_name = p.name AND s.league_id = p.league_id
        WHERE s.wordle_num = ? AND s.league_id = ?
        ORDER BY 
            CASE 
                WHEN s.score = 'X' THEN 7
                ELSE CAST(s.score AS INTEGER)
            END
        """, (wordle_number, league_id))
        
        result = cursor.fetchall()
        
        # Get all players from the league
        cursor.execute("""
        SELECT name, nickname 
        FROM players 
        WHERE league_id = ?
        """, (league_id,))
        
        all_players = cursor.fetchall()
        
        # Map of player name to score
        score_map = {row[0]: (row[2], row[3]) for row in result}
        
        scores = []
        
        for player in all_players:
            name = player[1] if player[1] else player[0]  # Use nickname if available
            
            has_score = player[0] in score_map
            
            if has_score:
                score = score_map[player[0]][0]
                emoji_pattern = score_map[player[0]][1]
                
                # Special handling for failed attempts
                score_value = "X" if score == "X" else int(score)
                
                # Detailed logging for Vox's pattern
                if player[0] == "Vox" and league_id == 3:
                    logging.info(f"VOX PATTERN FOUND - Score: {score}/6")
                    if emoji_pattern:
                        logging.info(f"Raw emoji_pattern length: {len(emoji_pattern)} characters")
                        logging.info(f"First 20 chars: {emoji_pattern[:20]}")
                        logging.info(f"Pattern with newlines shown as |: {emoji_pattern.replace('\n', '|')}")
                        logging.info("Pattern line by line:")
                        for i, line in enumerate(emoji_pattern.split('\n')):
                            logging.info(f"Line {i+1}: '{line}'")
                    else:
                        logging.info("No emoji pattern found for Vox")
            else:
                score_value = None
                emoji_pattern = None
            
            scores.append({
                'name': name,
                'has_score': has_score,
                'score': score_value,
                'emoji_pattern': emoji_pattern
            })
        
        conn.close()
        return scores
    except Exception as e:
        logging.error(f"Error getting scores: {e}")
        return []

def main():
    logging.info("Starting Vox pattern extraction")
    
    # PAL league ID is 3
    league_id = 3
    
    # Get the latest Wordle number from the database
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get the latest Wordle number
        cursor.execute("""
        SELECT MAX(wordle_num) 
        FROM scores
        WHERE league_id = ?
        """, (league_id,))
        
        latest_wordle = cursor.fetchone()[0]
        conn.close()
        
        logging.info(f"Latest Wordle number for PAL league: {latest_wordle}")
        
        # Now call our extraction function for this Wordle number
        scores = get_scores_for_wordle_by_league(latest_wordle, league_id)
        
        # Find Vox's score
        vox_score = next((score for score in scores if score['name'] == 'Vox'), None)
        
        if vox_score:
            logging.info("Vox's score found in extracted data")
            logging.info(f"Score: {vox_score['score']}/6")
            if vox_score['emoji_pattern']:
                logging.info("Emoji Pattern (as extracted by the export script):")
                logging.info(vox_score['emoji_pattern'])
            else:
                logging.info("No emoji pattern found in extracted data")
        else:
            logging.info("Vox not found in extracted scores")
        
        # Direct database query as a fallback
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT score, emoji_pattern
        FROM scores
        WHERE player_name = 'Vox' AND league_id = 3
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            logging.info("\nDirect database query for Vox's pattern:")
            if row[1]:
                logging.info(f"Pattern found with length: {len(row[1])} characters")
                
                # Format pattern for display
                formatted = ""
                for line in row[1].split('\n'):
                    if line.strip():
                        formatted += line + "\n"
                
                logging.info("Formatted Pattern:")
                logging.info(formatted)
            else:
                logging.info("No pattern found in direct query")
        else:
            logging.info("No score found for Vox in PAL league")
            
    except Exception as e:
        logging.error(f"Error: {e}")

if __name__ == "__main__":
    main()
