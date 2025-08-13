#!/usr/bin/env python3
"""
Unified Scores Database Module

This module provides a single interface to interact with the new unified scores table.
All database operations for scores should go through this module to ensure consistency.
"""

import sqlite3
import logging
from datetime import datetime

# Database path
DB_PATH = "wordle_league.db"

def get_player_id(player_name, league_id, conn=None):
    """
    Get the player ID for a given player name and league ID.
    
    Args:
        player_name: Player name
        league_id: League ID
        conn: SQLite connection (optional, will create a new one if None)
        
    Returns:
        int: Player ID or None if not found
    """
    should_close = False
    try:
        if conn is None:
            conn = sqlite3.connect(DB_PATH)
            should_close = True
            
        cursor = conn.cursor()
        
        # Get the player ID
        cursor.execute(
            "SELECT id FROM players WHERE name = ? AND league_id = ?", 
            (player_name, league_id)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        else:
            logging.warning(f"Player '{player_name}' not found in league {league_id}")
            return None
    
    except Exception as e:
        logging.error(f"Error getting player ID: {e}")
        return None
    
    finally:
        if should_close and conn:
            conn.close()

def save_score(player_name, league_id, wordle_number, score, date=None, emoji_pattern=None):
    """
    Save a Wordle score to the database using the new unified schema.
    
    Args:
        player_name: Player name
        league_id: League ID
        wordle_number: Wordle number
        score: Score value (1-6 or 'X')
        date: Score date (defaults to today)
        emoji_pattern: Emoji pattern (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Convert string 'X' score to numeric 7 (for failed attempts)
        if score == 'X' or score == 'x':
            numeric_score = 7
        else:
            numeric_score = int(score)
            
        # Set default date to today if not provided
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get the player ID
        player_id = get_player_id(player_name, league_id, conn)
        if not player_id:
            logging.error(f"Cannot save score for unknown player '{player_name}' in league {league_id}")
            return False
            
        # Check if score already exists
        cursor.execute(
            "SELECT id, score, emoji_pattern FROM scores WHERE player_id = ? AND wordle_number = ?", 
            (player_id, wordle_number)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Score already exists, update it
            logging.info(f"Updating existing score for {player_name} (league {league_id}) on Wordle {wordle_number}")
            
            # Only update emoji pattern if provided
            if emoji_pattern:
                cursor.execute(
                    "UPDATE scores SET score = ?, emoji_pattern = ?, date = ? WHERE id = ?", 
                    (numeric_score, emoji_pattern, date, existing[0])
                )
            else:
                # Keep existing emoji pattern if available
                existing_pattern = existing[2] if len(existing) > 2 and existing[2] else None
                cursor.execute(
                    "UPDATE scores SET score = ?, date = ? WHERE id = ?", 
                    (numeric_score, date, existing[0])
                )
                
        else:
            # Insert new score
            logging.info(f"Inserting new score for {player_name} (league {league_id}) on Wordle {wordle_number}")
            cursor.execute(
                "INSERT INTO scores (player_id, wordle_number, score, date, emoji_pattern) VALUES (?, ?, ?, ?, ?)", 
                (player_id, wordle_number, numeric_score, date, emoji_pattern)
            )
            
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logging.error(f"Error saving score: {e}")
        return False

def get_score(player_name, league_id, wordle_number):
    """
    Get a Wordle score from the database.
    
    Args:
        player_name: Player name
        league_id: League ID
        wordle_number: Wordle number
        
    Returns:
        dict: Score data or None if not found
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get the player ID
        player_id = get_player_id(player_name, league_id, conn)
        if not player_id:
            return None
            
        # Get the score
        cursor.execute(
            """
            SELECT s.score, s.emoji_pattern, s.date, p.name 
            FROM scores s 
            JOIN players p ON s.player_id = p.id
            WHERE s.player_id = ? AND s.wordle_number = ?
            """, 
            (player_id, wordle_number)
        )
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            # Convert numeric 7 back to 'X' for failed attempts
            display_score = 'X' if result[0] == 7 else result[0]
            
            return {
                'score': display_score,
                'emoji_pattern': result[1],
                'date': result[2],
                'player_name': result[3]
            }
        else:
            return None
        
    except Exception as e:
        logging.error(f"Error getting score: {e}")
        return None

def get_scores_for_league(league_id, wordle_number=None, date=None):
    """
    Get all scores for a league, optionally filtered by Wordle number or date.
    
    Args:
        league_id: League ID
        wordle_number: Wordle number (optional)
        date: Score date (optional)
        
    Returns:
        list: List of score dictionaries
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = """
        SELECT s.score, s.emoji_pattern, s.date, p.name, s.wordle_number
        FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE p.league_id = ?
        """
        
        params = [league_id]
        
        if wordle_number:
            query += " AND s.wordle_number = ?"
            params.append(wordle_number)
            
        if date:
            query += " AND s.date = ?"
            params.append(date)
            
        query += " ORDER BY p.name, s.wordle_number DESC"
        
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        
        conn.close()
        
        scores = []
        for result in results:
            # Convert numeric 7 back to 'X' for failed attempts
            display_score = 'X' if result[0] == 7 else result[0]
            
            scores.append({
                'score': display_score,
                'emoji_pattern': result[1],
                'date': result[2],
                'player_name': result[3],
                'wordle_number': result[4]
            })
            
        return scores
        
    except Exception as e:
        logging.error(f"Error getting scores for league {league_id}: {e}")
        return []

def get_recent_scores(days=7):
    """
    Get all scores from the past N days across all leagues.
    
    Args:
        days: Number of days to look back
        
    Returns:
        dict: Dictionary of scores by league
    """
    try:
        # Calculate the date N days ago
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = """
        SELECT s.score, s.emoji_pattern, s.date, p.name, s.wordle_number, p.league_id
        FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE s.date >= ?
        ORDER BY p.league_id, p.name, s.wordle_number DESC
        """
        
        cursor.execute(query, (from_date,))
        results = cursor.fetchall()
        
        conn.close()
        
        # Organize scores by league
        scores_by_league = {}
        for result in results:
            # Convert numeric 7 back to 'X' for failed attempts
            display_score = 'X' if result[0] == 7 else result[0]
            league_id = result[5]
            
            if league_id not in scores_by_league:
                scores_by_league[league_id] = []
                
            scores_by_league[league_id].append({
                'score': display_score,
                'emoji_pattern': result[1],
                'date': result[2],
                'player_name': result[3],
                'wordle_number': result[4]
            })
            
        return scores_by_league
        
    except Exception as e:
        logging.error(f"Error getting recent scores: {e}")
        return {}

def get_all_players():
    """
    Get all players from the database, grouped by league.
    
    Returns:
        dict: Dictionary of player lists by league
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT id, name, league_id, phone_number
        FROM players
        ORDER BY league_id, name
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        players_by_league = {}
        for result in results:
            player_id, name, league_id, phone = result
            
            if league_id not in players_by_league:
                players_by_league[league_id] = []
                
            players_by_league[league_id].append({
                'id': player_id,
                'name': name,
                'phone': phone
            })
            
        return players_by_league
        
    except Exception as e:
        logging.error(f"Error getting players: {e}")
        return {}
