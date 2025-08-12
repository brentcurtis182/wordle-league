#!/usr/bin/env python3
"""
Check Database Structure

Inspects the database structure and existing scores to troubleshoot unified extraction
"""

import sqlite3
import datetime
from pprint import pprint

def check_db_structure():
    """Check the database structure and scores"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("Database tables:")
        for table in tables:
            print(f"- {table[0]}")
            
        # Check legacy scores table if it exists
        legacy_scores = []
        try:
            cursor.execute("SELECT name, league_id, score, wordle_number, date FROM score WHERE wordle_number = 1505")
            legacy_scores = cursor.fetchall()
        except sqlite3.OperationalError:
            print("\nLegacy 'score' table does not exist")
            
        if legacy_scores:
            print(f"\nScores for Wordle #1505 in legacy table:")
            for row in legacy_scores:
                print(f"{row}")
                
        # Check new unified scores table
        cursor.execute("""
        SELECT p.name, p.league_id, s.score, s.wordle_number, s.date 
        FROM scores s JOIN players p ON s.player_id = p.id 
        WHERE s.wordle_number = 1505
        """)
        unified_scores = cursor.fetchall()
        
        print(f"\nScores for Wordle #1505 in new unified table:")
        for row in unified_scores:
            print(f"{row}")
            
        # Check players table
        print("\nPlayers by league:")
        for league_id in [1, 2, 3]:
            cursor.execute("SELECT id, name, phone_number FROM players WHERE league_id = ?", (league_id,))
            players = cursor.fetchall()
            league_name = {1: "Wordle Warriorz", 2: "Wordle Gang", 3: "PAL"}[league_id]
            print(f"\nLeague {league_id} ({league_name}):")
            for player in players:
                print(f"  ID: {player[0]}, Name: {player[1]}, Phone: {player[2]}")
                
        # Check table schema for scores table
        print("\nUnified scores table schema:")
        cursor.execute("PRAGMA table_info(scores)")
        schema = cursor.fetchall()
        for col in schema:
            print(f"  {col}")
            
        # Check foreign keys
        print("\nForeign key constraints on scores table:")
        cursor.execute("PRAGMA foreign_key_list(scores)")
        fks = cursor.fetchall()
        for fk in fks:
            print(f"  {fk}")
            
        # Check indexes
        print("\nIndexes on scores table:")
        cursor.execute("PRAGMA index_list(scores)")
        indexes = cursor.fetchall()
        for idx in indexes:
            print(f"  {idx}")
            for i in idx:
                if isinstance(i, str) and idx[1] == i:
                    cursor.execute(f"PRAGMA index_info({i})")
                    idx_info = cursor.fetchall()
                    print(f"    Columns: {[col[2] for col in idx_info]}")
                    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print(f"Database inspection at {datetime.datetime.now()}\n")
    check_db_structure()
    print("\nInspection complete")
