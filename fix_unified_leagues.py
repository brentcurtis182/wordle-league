#!/usr/bin/env python3
"""
Fix the league assignments in the unified player_scores table.

This script corrects the league_id values based on the correct player-league mappings.
"""

import os
import sqlite3
import sys

# Define database path
script_dir = os.path.dirname(os.path.abspath(__file__))
default_db_path = os.path.join(script_dir, 'wordle_league.db')
WORDLE_DATABASE = os.getenv('DATABASE_URI', default_db_path).replace('sqlite:///', '')

# Define the correct player-league assignments
LEAGUE_1_PLAYERS = ["Brent", "Evan", "Joanna", "Malia", "Nanna"]  # Warriorz
LEAGUE_2_PLAYERS = ["Brent", "Ana", "Kaylie", "Joanna", "Keith", "Rochelle", "Will", "Mylene"]  # Gang
LEAGUE_3_PLAYERS = ["Vox", "Fuzwuz", "Pants", "Starslider"]  # PAL

def fix_league_assignments():
    """Fix the league assignments in the player_scores table"""
    conn = None
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # First, check if we have any entries
        cursor.execute("SELECT COUNT(*) FROM player_scores")
        count = cursor.fetchone()[0]
        if count == 0:
            print("The player_scores table is empty. Nothing to fix.")
            return False
            
        # Get all unique players
        cursor.execute("SELECT DISTINCT player_name FROM player_scores")
        all_players = [row[0] for row in cursor.fetchall()]
        print(f"Found {len(all_players)} unique players in the table.")
        
        # Create a player_name to league_id mapping
        player_league_map = {}
        
        # Create entries for each player in each league
        updated_count = 0
        
        print("\nProcessing League 1 (Warriorz) players...")
        for player in LEAGUE_1_PLAYERS:
            # Get all scores for this player
            cursor.execute("""
            SELECT id, player_name, wordle_number FROM player_scores
            WHERE player_name = ?
            """, (player,))
            
            player_scores = cursor.fetchall()
            if not player_scores:
                print(f"  No scores found for {player} in League 1")
                continue
                
            for row_id, player_name, wordle_number in player_scores:
                # If this entry exists for the player in their correct league already, leave it
                cursor.execute("""
                SELECT COUNT(*) FROM player_scores
                WHERE player_name = ? AND wordle_number = ? AND league_id = 1
                """, (player_name, wordle_number))
                
                if cursor.fetchone()[0] == 0:
                    # This score doesn't exist in league 1, so we need to duplicate it
                    print(f"  Creating League 1 entry for {player_name} - Wordle {wordle_number}")
                    
                    # Get the full record
                    cursor.execute("""
                    SELECT player_id, player_name, wordle_number, score, emoji_pattern, timestamp
                    FROM player_scores
                    WHERE id = ?
                    """, (row_id,))
                    
                    record = cursor.fetchone()
                    if record:
                        # Insert as a new record for league 1
                        cursor.execute("""
                        INSERT OR IGNORE INTO player_scores
                        (player_id, player_name, wordle_number, score, emoji_pattern, timestamp, league_id)
                        VALUES (?, ?, ?, ?, ?, ?, 1)
                        """, record)
                        updated_count += 1
        
        print("\nProcessing League 2 (Gang) players...")
        for player in LEAGUE_2_PLAYERS:
            # Get all scores for this player
            cursor.execute("""
            SELECT id, player_name, wordle_number FROM player_scores
            WHERE player_name = ?
            """, (player,))
            
            player_scores = cursor.fetchall()
            if not player_scores:
                print(f"  No scores found for {player} in League 2")
                continue
                
            for row_id, player_name, wordle_number in player_scores:
                # If this entry exists for the player in their correct league already, leave it
                cursor.execute("""
                SELECT COUNT(*) FROM player_scores
                WHERE player_name = ? AND wordle_number = ? AND league_id = 2
                """, (player_name, wordle_number))
                
                if cursor.fetchone()[0] == 0:
                    # This score doesn't exist in league 2, so we need to duplicate it
                    print(f"  Creating League 2 entry for {player_name} - Wordle {wordle_number}")
                    
                    # Get the full record
                    cursor.execute("""
                    SELECT player_id, player_name, wordle_number, score, emoji_pattern, timestamp
                    FROM player_scores
                    WHERE id = ?
                    """, (row_id,))
                    
                    record = cursor.fetchone()
                    if record:
                        # Insert as a new record for league 2
                        cursor.execute("""
                        INSERT OR IGNORE INTO player_scores
                        (player_id, player_name, wordle_number, score, emoji_pattern, timestamp, league_id)
                        VALUES (?, ?, ?, ?, ?, ?, 2)
                        """, record)
                        updated_count += 1
        
        print("\nProcessing League 3 (PAL) players...")
        for player in LEAGUE_3_PLAYERS:
            # Special case for Pants who might not have any scores
            if player == "Pants":
                # Add an empty record for Pants if they don't exist
                cursor.execute("""
                SELECT COUNT(*) FROM player_scores
                WHERE player_name = ? AND league_id = 3
                """, (player,))
                
                if cursor.fetchone()[0] == 0:
                    print(f"  Adding placeholder entry for Pants in League 3")
                    
                    # Get latest wordle number
                    cursor.execute("""
                    SELECT wordle_number FROM player_scores
                    ORDER BY CAST(REPLACE(wordle_number, ',', '') AS INTEGER) DESC
                    LIMIT 1
                    """)
                    
                    latest_wordle = cursor.fetchone()
                    if latest_wordle:
                        # Create a placeholder entry for Pants
                        cursor.execute("""
                        INSERT OR IGNORE INTO player_scores
                        (player_name, wordle_number, score, timestamp, league_id)
                        VALUES (?, ?, 'No Score', ?, 3)
                        """, ("Pants", latest_wordle[0], "2025-08-01"))
                        updated_count += 1
                continue
                
            # Get all scores for this player
            cursor.execute("""
            SELECT id, player_name, wordle_number FROM player_scores
            WHERE player_name = ?
            """, (player,))
            
            player_scores = cursor.fetchall()
            if not player_scores:
                print(f"  No scores found for {player} in League 3")
                continue
                
            for row_id, player_name, wordle_number in player_scores:
                # If this entry exists for the player in their correct league already, leave it
                cursor.execute("""
                SELECT COUNT(*) FROM player_scores
                WHERE player_name = ? AND wordle_number = ? AND league_id = 3
                """, (player_name, wordle_number))
                
                if cursor.fetchone()[0] == 0:
                    # This score doesn't exist in league 3, so we need to duplicate it
                    print(f"  Creating League 3 entry for {player_name} - Wordle {wordle_number}")
                    
                    # Get the full record
                    cursor.execute("""
                    SELECT player_id, player_name, wordle_number, score, emoji_pattern, timestamp
                    FROM player_scores
                    WHERE id = ?
                    """, (row_id,))
                    
                    record = cursor.fetchone()
                    if record:
                        # Insert as a new record for league 3
                        cursor.execute("""
                        INSERT OR IGNORE INTO player_scores
                        (player_id, player_name, wordle_number, score, emoji_pattern, timestamp, league_id)
                        VALUES (?, ?, ?, ?, ?, ?, 3)
                        """, record)
                        updated_count += 1
        
        # Now clean up - remove entries for players in leagues they shouldn't be in
        print("\nCleaning up incorrect league assignments...")
        
        # For each league, remove players who shouldn't be there
        for league_id, correct_players in [
            (1, LEAGUE_1_PLAYERS),
            (2, LEAGUE_2_PLAYERS),
            (3, LEAGUE_3_PLAYERS)
        ]:
            cursor.execute("""
            SELECT DISTINCT player_name FROM player_scores
            WHERE league_id = ?
            """, (league_id,))
            
            players_in_league = [row[0] for row in cursor.fetchall()]
            for player in players_in_league:
                if player not in correct_players:
                    print(f"  Removing {player} from League {league_id} (doesn't belong)")
                    cursor.execute("""
                    DELETE FROM player_scores
                    WHERE player_name = ? AND league_id = ?
                    """, (player, league_id))
                    updated_count += 1
        
        conn.commit()
        print(f"\nFixed {updated_count} league assignments in player_scores table")
        return True
        
    except Exception as e:
        print(f"Error fixing league assignments: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

def verify_league_assignments():
    """Verify that the league assignments are correct"""
    conn = None
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        print("\nVerifying league assignments after fixes:")
        
        # For each league, check the players
        for league_id, correct_players, league_name in [
            (1, LEAGUE_1_PLAYERS, "Warriorz"),
            (2, LEAGUE_2_PLAYERS, "Gang"),
            (3, LEAGUE_3_PLAYERS, "PAL")
        ]:
            print(f"\nLeague {league_id} ({league_name}):")
            
            # Get players in this league
            cursor.execute("""
            SELECT DISTINCT player_name FROM player_scores
            WHERE league_id = ?
            """, (league_id,))
            
            players_in_league = [row[0] for row in cursor.fetchall()]
            print(f"  Players found: {', '.join(players_in_league)}")
            print(f"  Should have: {', '.join(correct_players)}")
            
            # Check for missing players
            missing = [p for p in correct_players if p not in players_in_league]
            if missing:
                print(f"  MISSING PLAYERS: {', '.join(missing)}")
                
            # Check for extra players
            extra = [p for p in players_in_league if p not in correct_players]
            if extra:
                print(f"  EXTRA PLAYERS: {', '.join(extra)}")
                
            # Count scores
            cursor.execute("""
            SELECT COUNT(*) FROM player_scores
            WHERE league_id = ?
            """, (league_id,))
            
            score_count = cursor.fetchone()[0]
            print(f"  Total scores: {score_count}")
            
            # Sample data for the latest wordle
            cursor.execute("""
            SELECT DISTINCT wordle_number 
            FROM player_scores 
            ORDER BY CAST(REPLACE(wordle_number, ',', '') AS INTEGER) DESC
            LIMIT 1
            """)
            
            latest_wordle = cursor.fetchone()
            if latest_wordle:
                print(f"\n  Latest scores (Wordle {latest_wordle[0]}):")
                
                cursor.execute("""
                SELECT player_name, score
                FROM player_scores
                WHERE league_id = ? AND wordle_number = ?
                ORDER BY player_name
                """, (league_id, latest_wordle[0]))
                
                latest_scores = cursor.fetchall()
                for score_row in latest_scores:
                    player, score = score_row
                    print(f"    {player}: {score}")
                    
        return True
        
    except Exception as e:
        print(f"Error verifying league assignments: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

def main():
    """Run the league assignment fix and verification"""
    print("=== Fixing League Assignments in Unified Table ===")
    
    # Fix the league assignments
    if fix_league_assignments():
        print("\nLeague assignments fixed successfully!")
    else:
        print("\nFailed to fix league assignments.")
        return
        
    # Verify the league assignments
    if verify_league_assignments():
        print("\nVerification complete!")
    else:
        print("\nVerification failed. Please check the data manually.")
    
if __name__ == "__main__":
    main()
