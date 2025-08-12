#!/usr/bin/env python
# Test script for PAL league Wordle number query
# This script only reads from the database and prints results
# It does NOT modify any files or push to GitHub

import sqlite3
import json
from datetime import datetime

# Database location (same as in other scripts)
WORDLE_DATABASE = "wordle_league.db"

def test_query_with_both_formats():
    """Test querying scores with both comma and non-comma Wordle number formats"""
    conn = None
    
    try:
        print(f"Testing PAL league query with both Wordle number formats")
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        league_id = 3  # PAL league
        wordle_number = "1502"  # Test with this Wordle number
        
        # Format both ways
        wordle_with_comma = f"{int(wordle_number):,d}"  # Will be "1,502"
        wordle_without_comma = wordle_number  # Will be "1502"
        
        print(f"Testing query for:")
        print(f"  League ID: {league_id}")
        print(f"  Wordle without comma: '{wordle_without_comma}'")
        print(f"  Wordle with comma: '{wordle_with_comma}'")
        
        # First try the original query with just the non-comma format
        print("\n=== ORIGINAL QUERY (non-comma format only) ===")
        cursor.execute("""
        SELECT p.name, p.nickname, s.score, s.emoji_pattern, s.wordle_num
        FROM scores s
        JOIN players p ON s.player_name = p.name AND s.league_id = p.league_id
        WHERE s.wordle_num = ? AND s.league_id = ?
        """, (wordle_without_comma, league_id))
        
        results = cursor.fetchall()
        if results:
            print(f"Found {len(results)} results:")
            for row in results:
                print(f"  Player: {row[0]}, Score: {row[2]}, Wordle #: {row[4]}")
        else:
            print("No results found with non-comma format")
        
        # Next try with just the comma format
        print("\n=== TESTING WITH COMMA FORMAT ONLY ===")
        cursor.execute("""
        SELECT p.name, p.nickname, s.score, s.emoji_pattern, s.wordle_num
        FROM scores s
        JOIN players p ON s.player_name = p.name AND s.league_id = p.league_id
        WHERE s.wordle_num = ? AND s.league_id = ?
        """, (wordle_with_comma, league_id))
        
        results = cursor.fetchall()
        if results:
            print(f"Found {len(results)} results:")
            for row in results:
                print(f"  Player: {row[0]}, Score: {row[2]}, Wordle #: {row[4]}")
        else:
            print("No results found with comma format")
        
        # Finally try with both formats using OR
        print("\n=== TESTING WITH BOTH FORMATS (OR logic) ===")
        cursor.execute("""
        SELECT p.name, p.nickname, s.score, s.emoji_pattern, s.wordle_num
        FROM scores s
        JOIN players p ON s.player_name = p.name AND s.league_id = p.league_id
        WHERE (s.wordle_num = ? OR s.wordle_num = ?) AND s.league_id = ?
        """, (wordle_without_comma, wordle_with_comma, league_id))
        
        results = cursor.fetchall()
        if results:
            print(f"Found {len(results)} results:")
            for row in results:
                print(f"  Player: {row[0]}, Score: {row[2]}, Wordle #: {row[4]}")
        else:
            print("No results found with either format")
            
        # Also check for ANY scores in the PAL league
        print("\n=== CHECKING FOR ANY SCORES IN PAL LEAGUE ===")
        cursor.execute("""
        SELECT s.player_name, s.wordle_num, s.score, s.emoji_pattern
        FROM scores s
        WHERE s.league_id = ?
        LIMIT 10
        """, (league_id,))
        
        results = cursor.fetchall()
        if results:
            print(f"Found {len(results)} scores in PAL league:")
            for row in results:
                print(f"  Player: {row[0]}, Wordle #: {row[1]}, Score: {row[2]}")
        else:
            print("No scores found in PAL league")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    test_query_with_both_formats()
